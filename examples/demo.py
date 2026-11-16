"""Demonstration of Human-in-the-Loop policy interception and approval."""

from rich.console import Console
from rich.panel import Panel
from hitl_gateway.gateway import HITLGateway

console = Console()

def run():
    gateway = HITLGateway()

    def live_refund_tool(customer_id: str, amount_usd: float):
        return f"Processed refund of ${amount_usd} for {customer_id}"

    console.print("\n[bold blue]=== 1. Agent attempts high-risk tool call (Outbound Refund) ===[/bold blue]")
    intercept = gateway.intercept_and_execute(
        agent_id="support-monoagent-01",
        tool_name="process_refund_payment",
        arguments={"customer_id": "cust_8812", "amount_usd": 1250.00},
        executor=live_refund_tool,
    )

    console.print(Panel.fit(
        f"Status: [bold red]{intercept['status']}[/bold red]\n"
        f"Reason: {intercept['message']}\n"
        f"Pending Request ID: [bold yellow]{intercept['request_id']}[/bold yellow]",
        title="HITL Policy Gate",
    ))

    console.print("\n[bold green]=== 2. Human Manager Reviews & Approves Action ===[/bold green]")
    approved = gateway.approve_request(
        request_id=intercept["request_id"],
        approver="manager_sara@corp.com",
        executor=live_refund_tool,
    )
    console.print(f"Action Executed: [green]{approved['result']}[/green] (Signed off by {approved['approver']})")

if __name__ == "__main__":
    run()
