"""
Admin-facing tools for the ELDOCTOR AI Agent.

These LangChain tools wrap the store operations for admin users.
Admin tools include everything customer tools have, plus operational tools.
"""

from langchain_core.tools import tool

from agent.agent.store.base import Store


def create_admin_tools(store: Store):
    """
    Create admin tools bound to a specific store instance.

    Admin tools include:
    - All customer tools (search, stock, orders)
    - Inventory tools (summary, low stock)
    - Reorder draft tools

    Args:
        store: A Store implementation (e.g. FileStore)

    Returns:
        List of LangChain Tool objects
    """

    # --- Customer tools (also available to admin) ---

    @tool
    def search_products(query: str) -> dict:
        """
        Search for auto parts by product name, description, or part number.

        Args:
            query: Search string (e.g. 'فلاتر زيت', 'Bosch', 'BOSCH-OF-101')

        Returns:
            Dictionary with 'results' list and 'count'.
        """
        results = store.search_products(query)
        return {"results": results, "count": len(results)}

    @tool
    def check_stock(product_id: str) -> dict:
        """
        Check the current stock quantity for a specific product.

        Args:
            product_id: Product ID (e.g. 'PROD-001')

        Returns:
            Dictionary with product stock info.
        """
        return store.check_stock(product_id)

    @tool
    def get_product_details(product_id: str) -> dict:
        """
        Get detailed information about a specific product.

        Args:
            product_id: Product ID (e.g. 'PROD-001')

        Returns:
            Full product details or error.
        """
        product = store.get_product(product_id)
        if product is None:
            return {"error": f"Product {product_id} not found"}
        return product

    @tool
    def create_order(
        customer_id: str, items: list[dict], idempotency_key: str | None = None
    ) -> dict:
        """
        Create a new order for a customer.

        Args:
            customer_id: Customer ID
            items: List of { product_id, quantity }
            idempotency_key: Optional unique key

        Returns:
            Order creation result.
        """
        return store.create_order(customer_id, items, idempotency_key)

    @tool
    def get_order_status(order_id: str) -> dict:
        """
        Get the status of a specific order.

        Args:
            order_id: Order ID (e.g. 'ORD-001')

        Returns:
            Order status and details.
        """
        return store.get_order_status(order_id)

    @tool
    def get_customer_orders(customer_id: str) -> dict:
        """
        Get all orders for a specific customer.

        Args:
            customer_id: Customer ID

        Returns:
            Dictionary with orders list and count.
        """
        orders = store.get_customer_orders(customer_id)
        return {"orders": orders, "count": len(orders)}

    # --- Admin-specific tools ---

    @tool
    def get_inventory_summary() -> dict:
        """
        Get a complete summary of all inventory items.

        Returns:
            List of all products with their current quantities, prices,
            categories, and stock status (in_stock / out_of_stock).
        """
        summary = store.get_inventory_summary()
        total_value = sum(
            item["available_quantity"] * item["price"] for item in summary
        )
        return {
            "items": summary,
            "total_items": len(summary),
            "total_value_egp": total_value,
            "out_of_stock_count": sum(
                1 for item in summary if item["available_quantity"] == 0
            ),
            "low_stock_count": sum(
                1
                for item in summary
                if 0 < item["available_quantity"] <= item.get("reorder_threshold", 5)
            ),
        }

    @tool
    def get_low_stock_items(threshold: int = 5) -> dict:
        """
        Get products that are below a stock threshold.

        Args:
            threshold: Minimum quantity before flagging as low stock.
                       If not provided, uses each product's configured threshold.

        Returns:
            List of low-stock products with suggested reorder quantities.
        """
        low_stock = store.get_low_stock_items(threshold)
        return {
            "items": low_stock,
            "count": len(low_stock),
            "threshold_used": threshold,
        }

    @tool
    def prepare_reorder(product_id: str, quantity: int) -> dict:
        """
        Create a draft replenishment request for a product.

        This creates a DRAFT that needs admin approval before a real
        purchase order is sent to the supplier.

        Args:
            product_id: Product ID to reorder
            quantity: Quantity to request from supplier

        Returns:
            Dictionary with draft_id, product info, requested quantity,
            supplier, and status.
        """
        return store.prepare_reorder(product_id, quantity)

    @tool
    def list_reorder_drafts() -> dict:
        """
        List all pending reorder drafts.

        Returns:
            List of all draft replenishment requests with their status.
        """
        drafts = store._get_reorder_drafts()
        return {
            "drafts": drafts,
            "count": len(drafts),
            "pending_count": sum(1 for d in drafts if d["status"] == "draft"),
        }

    return [
        # Customer tools
        search_products,
        check_stock,
        get_product_details,
        create_order,
        get_order_status,
        get_customer_orders,
        # Admin tools
        get_inventory_summary,
        get_low_stock_items,
        prepare_reorder,
        list_reorder_drafts,
    ]
