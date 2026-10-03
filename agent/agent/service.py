"""
Agent service — provides a clean interface for running the agent.

This module is the entry point for both:
1. Interactive terminal use
2. Programmatic use (import and call invoke_agent)
"""

import argparse
import sys
from typing import TypedDict, Annotated

from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agent.graph import create_agent_graph, invoke_agent, run_interactive
from agent.store.file_store import FileStore, get_store


# ---------------------------------------------------------------------------
# Multi-turn state for pending orders
# ---------------------------------------------------------------------------

class AgentState(TypedDict, total=False):
    """Extended state for multi-turn conversation."""
    messages: list
    user_role: str
    user_id: str
    pending_action: str | None  # e.g. "create_order"
    pending_order: dict | None  # e.g. {"product_id": "...", "quantity": 4}
    pending_product: dict | None  # Selected product info


def create_agent_graph_with_state(
    user_role: str = "customer",
    user_id: str = "unknown"
):
    """
    Create agent graph with multi-turn state support.

    This extends the base graph with state tracking for:
    - Pending orders
    - Confirmation flows
    - Order modifications
    """
    # Create the base graph
    base_app = create_agent_graph(user_role, user_id)

    # For now, we use the simple invoke_agent which handles
    # basic multi-turn via conversation_history parameter.
    # The full state machine can be added incrementally.

    return base_app


# ---------------------------------------------------------------------------
# Test functions
# ---------------------------------------------------------------------------

def test_agent_response(message: str, role: str = "customer", user_id: str = "CUST-001") -> str:
    """Test a single agent response."""
    print(f"\n{'='*50}")
    print(f"User ({role}): {message}")
    print(f"{'='*50}")
    response = invoke_agent(message, role, user_id)
    print(f"\nAgent: {response}\n")
    return response


def create_order_demo() -> None:
    """Demo: create a sample order to test the flow."""
    print("=== Order Creation Demo ===\n")

    store = get_store()

    # First search
    print("1. Searching for 'فلاتر زيت'...")
    results = store.search_products("فلاتر زيت")
    if results:
        for r in results:
            print(f"   - {r['name']} ({r['product_id']}): "
                  f"{r['price']} EGP, stock: {r['available_quantity']}")
    else:
        print("   No results found.")

    # Check stock for first product
    if results:
        pid = results[0]["product_id"]
        print(f"\n2. Checking stock for {pid} (quantity=2)...")
        stock = store.check_stock(pid)
        print(f"   Product: {stock.get('product_name', 'Unknown')}")
        print(f"   Available: {stock.get('available_quantity', 0)}")

    # Create order
    if results:
        print(f"\n3. Creating order for CUST-001...")
        order_result = store.create_order(
            customer_id="CUST-001",
            items=[{"product_id": pid, "quantity": 2}],
            idempotency_key="demo-order-001"
        )
        print(f"   Success: {order_result.get('success')}")
        print(f"   Order ID: {order_result.get('order_id')}")
        print(f"   Status: {order_result.get('status')}")
        print(f"   Total: {order_result.get('total')} EGP")
        if order_result.get('message'):
            print(f"   Message: {order_result.get('message')}")

        # Check order status
        print(f"\n4. Checking order status...")
        order_status = store.get_order_status(order_result.get("order_id"))
        print(f"   Order: {order_status.get('order_id')}")
        print(f"   Status: {order_status.get('status')}")

    print("\n=== Demo Complete ===\n")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ELDOCTOR AI Operations Agent"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demo of the agent capabilities"
    )
    parser.add_argument(
        "--test",
        type=str,
        nargs="?",
        const="عايز فلتر زيت",
        help="Test agent with a specific message"
    )
    parser.add_argument(
        "--role",
        type=str,
        choices=["customer", "admin"],
        default="customer",
        help="User role for the test"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive terminal session"
    )

    args = parser.parse_args()

    if args.demo:
        create_order_demo()
    elif args.test:
        test_agent_response(args.test, args.role)
    elif args.interactive:
        run_interactive()
    else:
        # Default: run interactive
        run_interactive()


if __name__ == "__main__":
    main()
