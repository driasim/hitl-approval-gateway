# `hitl-approval-gateway` 🚦

[![CI](https://github.com/driasim/hitl-approval-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/driasim/hitl-approval-gateway/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Human-in-the-loop (HITL) authorization gateway and policy engine for dangerous AI agent actions.**

Allowing LLM agents to autonomously execute production database drops, refunds, file deletions, or shell commands is an unacceptable enterprise risk.

`hitl-approval-gateway` is a policy middleware that intercepts high-risk agent tool calls, halts execution, issues a cryptographically tracked approval request, and only executes the tool when explicitly signed off by a human operator.

---

## ⚡ Quickstart

### Installation

```bash
git clone https://github.com/driasim/hitl-approval-gateway.git
cd hitl-approval-gateway
pip install -e .
```

### Python SDK Usage

```python
from hitl_gateway.gateway import HITLGateway

gateway = HITLGateway()

def process_refund(amount: float, customer: str):
    return f"Refunded ${amount} to {customer}"

# 1. Agent attempts destructive/financial action
result = gateway.intercept_and_execute(
    agent_id="finance-agent-01",
    tool_name="process_refund_payment",
    arguments={"amount": 1500.0, "customer": "cust_492"},
    executor=process_refund,
)

if result["status"] == "awaiting_approval":
    print("Action blocked pending sign-off:", result["request_id"])

    # 2. Human manager approves (via Slack button, dashboard, or CLI)
    executed = gateway.approve_request(
        request_id=result["request_id"],
        approver="compliance_lead@company.com",
        executor=process_refund,
    )
    print("Executed safely:", executed["result"])
```

---

## 🧪 Running Tests

```bash
pytest -v tests/
```

---

## 📄 License
MIT © Ibrahim Aliyu Saddique (`@driasim`)
