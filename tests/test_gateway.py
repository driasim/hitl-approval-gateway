"""Unit tests for hitl-approval-gateway."""

import pytest
from hitl_gateway.models import RiskLevel, ApprovalStatus
from hitl_gateway.gateway import HITLGateway


def test_safe_action_auto_approved():
    gateway = HITLGateway()

    def read_logs(service: str):
        return f"logs for {service}"

    res = gateway.intercept_and_execute(
        agent_id="agent-01",
        tool_name="get_service_logs",
        arguments={"service": "auth"},
        executor=read_logs,
    )
    assert res["status"] == "executed"
    assert res["result"] == "logs for auth"


def test_destructive_action_intercepted():
    gateway = HITLGateway()

    def drop_database(db: str):
        return f"dropped {db}"

    res = gateway.intercept_and_execute(
        agent_id="agent-01",
        tool_name="drop_user_table",
        arguments={"db": "prod"},
        executor=drop_database,
    )
    assert res["status"] == "awaiting_approval"
    req_id = res["request_id"]
    assert req_id in gateway.pending_requests


def test_human_approval_flow():
    gateway = HITLGateway()

    executed = False
    def delete_order(order_id: int):
        nonlocal executed
        executed = True
        return f"Deleted order {order_id}"

    # Intercept
    intercept_res = gateway.intercept_and_execute(
        agent_id="agent-01",
        tool_name="delete_pending_order",
        arguments={"order_id": 994},
        executor=delete_order,
    )
    req_id = intercept_res["request_id"]
    assert executed is False

    # Human Approves
    approve_res = gateway.approve_request(
        request_id=req_id,
        approver="alice@corp.com",
        executor=delete_order,
    )
    assert approve_res["status"] == "executed"
    assert executed is True
