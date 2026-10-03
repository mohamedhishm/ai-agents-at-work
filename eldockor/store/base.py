"""
Store interface for the ELDOCTOR AI Agent.

This defines the contract between the Agent and the data layer.
The Agent never accesses data directly — it always goes through the Store.
"""

from abc import ABC, abstractmethod
from typing import Any


class Store(ABC):
    """Abstract base for all data stores."""

    @abstractmethod
    def search_products(self, query: str) -> list[dict]:
        """Search for products by name, part number, or category."""
        pass

    @abstractmethod
    def check_stock(self, product_id: str) -> dict:
        """Check stock for a specific product."""
        pass

    @abstractmethod
    def get_product(self, product_id: str) -> dict | None:
        """Get a single product by ID."""
        pass

    @abstractmethod
    def get_inventory_summary(self) -> list[dict]:
        """Get all inventory with current quantities and status."""
        pass

    @abstractmethod
    def get_low_stock_items(self, threshold: int = 5) -> list[dict]:
        """Get products below a stock threshold."""
        pass

    @abstractmethod
    def create_order(
        self,
        customer_id: str,
        items: list[dict],
        idempotency_key: str | None = None
    ) -> dict:
        """Create a new order."""
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> dict:
        """Get order status and details."""
        pass

    @abstractmethod
    def get_customer_orders(self, customer_id: str) -> list[dict]:
        """Get all orders for a customer."""
        pass

    @abstractmethod
    def prepare_reorder(self, product_id: str, quantity: int) -> dict:
        """Create a draft replenishment request."""
        pass
