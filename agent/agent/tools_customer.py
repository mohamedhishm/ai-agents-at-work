"""
Customer-facing tools for the ELDOCTOR AI Agent.

These LangChain tools wrap the store operations for customer users.
"""

from langchain_core.tools import tool

from agent.store.base import Store


def create_customer_tools(store: Store):
    """
    Create customer tools bound to a specific store instance.

    Args:
        store: A Store implementation (e.g. FileStore)

    Returns:
        List of LangChain Tool objects
    """

    @tool
    def search_products(query: str) -> dict:
        """
        Search for auto parts by product name, description, or part number.

        Args:
            query: Search string (e.g. 'فلاتر زيت', 'Bosch', 'BOSCH-OF-101')

        Returns:
            Dictionary with 'results' list of matching products and 'count'.
            Each result has: product_id, name, category, part_number, price,
            available_quantity, supplier, reorder_threshold.
        """
        return {"results": store.search_products(query), "count": len(store.search_products(query))}

    @tool
    def check_stock(product_id: str) -> dict:
        """
        Check the current stock quantity for a specific product.

        Args:
            product_id: Product ID (e.g. 'PROD-001')

        Returns:
            Dictionary with product_id, product_name, available_quantity,
            category, price. Or error if product not found.
        """
        return store.check_stock(product_id)

    @tool
    def get_product_details(product_id: str) -> dict:
        """
        Get detailed information about a specific product.

        Args:
            product_id: Product ID (e.g. 'PROD-001')

        Returns:
            Full product details including all fields, or None if not found.
        """
        product = store.get_product(product_id)
        if product is None:
            return {"error": f"Product {product_id} not found"}
        return product

    @tool
    def create_order(
        customer_id: str,
        items: list[dict],
        idempotency_key: str | None = None
    ) -> dict:
        """
        Create a new order for a customer.

        Args:
            customer_id: Customer ID (e.g. 'CUST-001')
            items: List of dicts, each with 'product_id' and 'quantity'
            idempotency_key: Optional unique key to prevent duplicate orders

        Returns:
            Dictionary with success status, order_id, status, items, total,
            message, and errors (if any).
        """
        return store.create_order(customer_id, items, idempotency_key)

    @tool
    def propose_order(
        product_id: str,
        quantity: int,
        product_name: str | None = None,
        original_requested: int | None = None,
    ) -> dict:
        """
        Propose an order for confirmation when the requested quantity exceeds
        available stock. This tool does NOT create an actual order - it returns
        a structured proposal that the agent uses to set pending state.

        When the LLM calls this tool, the graph detects it and creates the
        pending_action / pending_order state so the next user message ("أيوه")
        can execute the real create_order.

        Args:
            product_id: The product to order
            quantity: The quantity to propose (usually the available quantity)
            product_name: Optional product name for display
            original_requested: The quantity the customer originally asked for

        Returns:
            Dictionary with status='proposed', product_id, quantity, and
            product_name. The graph uses this to set pending state.
        """
        product = store.get_product(product_id)
        name = product_name or (product.get("part_name") if product else product_id)
        return {
            "status": "proposed",
            "product_id": product_id,
            "quantity": quantity,
            "product_name": name,
            "original_requested": original_requested or quantity,
            "message": (
                f"اقتراح طلب: {name} - {quantity} قطعة. "
                f"أعتمد ب \"أيوه\" لتأكيد الطلب أو \"لا\" للإلغاء."
            ),
        }

    @tool
    def get_order_status(order_id: str) -> dict:
        """
        Get the status and details of a specific order.

        Args:
            order_id: Order ID (e.g. 'ORD-001')

        Returns:
            Dictionary with order_id, status, items, total, created_at,
            customer_id. Or error if order not found.
        """
        return store.get_order_status(order_id)

    @tool
    def get_customer_orders(customer_id: str) -> dict:
        """
        Get all orders for a specific customer.

        Args:
            customer_id: Customer ID (e.g. 'CUST-001')

        Returns:
            Dictionary with 'orders' list and 'count'.
        """
        orders = store.get_customer_orders(customer_id)
        return {"orders": orders, "count": len(orders)}

    return [
        search_products,
        check_stock,
        get_product_details,
        get_order_status,
        get_customer_orders,
        propose_order,
    ]
