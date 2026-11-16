"""Gateway middleware intercepting tool executions for human approval."""

import fnmatch
import uuid
from typing import Any, Callable, Dict, List, Optional
from hitl_gateway.models import RiskLevel, ApprovalStatus, ApprovalRequest, PolicyRule


DEFAULT_RULES: List[PolicyRule] = [
    PolicyRule(
        rule_id="RULE-PROD-WRITE",
        tool_name_pattern="*delete*|*drop*|*terminate*",
        risk_level=RiskLevel.CRITICAL,
        description="Destructive deletion or termination operations require explicit manager sign-off.",
    ),
    PolicyRule(
        rule_id="RULE-FINANCIAL-LIMIT",
        tool_name_pattern="*transfer*|*payment*|*refund*",
        risk_level=RiskLevel.HIGH,
        description="Outbound financial movements require verification.",
    ),
    PolicyRule(
        rule_id="RULE-EXEC-SHELL",
        tool_name_pattern="*shell*|*exec*|*bash*",
        risk_level=RiskLevel.HIGH,
        description="Arbitrary shell or command execution.",
    ),
]


class HITLGateway:
    """Policy engine and authorization gate for agent tool execution."""

    def __init__(self, rules: Optional[List[PolicyRule]] = None):
        self.rules = rules or DEFAULT_RULES
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.audit_log: List[ApprovalRequest] = []

    def evaluate_risk(self, tool_name: str, arguments: Dict[str, Any]) -> tuple[RiskLevel, List[str]]:
        highest_risk = RiskLevel.LOW
        triggered = []

        for rule in self.rules:
            patterns = rule.tool_name_pattern.split("|")
            if any(fnmatch.fnmatch(tool_name.lower(), p.lower()) for p in patterns):
                triggered.append(rule.rule_id)
                if rule.risk_level == RiskLevel.CRITICAL:
                    highest_risk = RiskLevel.CRITICAL
                elif rule.risk_level == RiskLevel.HIGH and highest_risk != RiskLevel.CRITICAL:
                    highest_risk = RiskLevel.HIGH
                elif rule.risk_level == RiskLevel.MEDIUM and highest_risk == RiskLevel.LOW:
                    highest_risk = RiskLevel.MEDIUM

        return highest_risk, triggered

    def intercept_and_execute(
        self,
        agent_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        executor: Callable[..., Any],
    ) -> Dict[str, Any]:
        risk, triggered_rules = self.evaluate_risk(tool_name, arguments)

        # Low/Medium risk: auto-approve
        if risk in (RiskLevel.LOW, RiskLevel.MEDIUM):
            res = executor(**arguments)
            req = ApprovalRequest(
                request_id=f"req-{uuid.uuid4().hex[:8]}",
                agent_id=agent_id,
                tool_name=tool_name,
                arguments=arguments,
                risk_level=risk,
                triggered_rules=triggered_rules,
                status=ApprovalStatus.AUTO_APPROVED,
            )
            self.audit_log.append(req)
            return {"status": "executed", "result": res, "request": req}

        # High/Critical risk: queue for human approval
        req = ApprovalRequest(
            request_id=f"req-{uuid.uuid4().hex[:8]}",
            agent_id=agent_id,
            tool_name=tool_name,
            arguments=arguments,
            risk_level=risk,
            triggered_rules=triggered_rules,
            status=ApprovalStatus.PENDING,
        )
        self.pending_requests[req.request_id] = req
        self.audit_log.append(req)

        return {
            "status": "awaiting_approval",
            "message": f"Action blocked by policy: Tool '{tool_name}' classified as {risk.value}. Awaiting human approval.",
            "request_id": req.request_id,
            "risk_level": risk.value,
        }

    def approve_request(
        self,
        request_id: str,
        approver: str,
        executor: Callable[..., Any],
    ) -> Dict[str, Any]:
        req = self.pending_requests.pop(request_id, None)
        if not req:
            raise KeyError(f"Pending approval request {request_id} not found.")

        req.status = ApprovalStatus.APPROVED
        req.approver = approver
        result = executor(**req.arguments)
        return {"status": "executed", "result": result, "approver": approver}

    def reject_request(self, request_id: str, approver: str, reason: str) -> ApprovalRequest:
        req = self.pending_requests.pop(request_id, None)
        if not req:
            raise KeyError(f"Pending approval request {request_id} not found.")

        req.status = ApprovalStatus.REJECTED
        req.approver = approver
        req.rejection_reason = reason
        return req
