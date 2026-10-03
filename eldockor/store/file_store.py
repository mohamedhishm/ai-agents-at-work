"""
File-based store implementation for the ELDOCTOR AI Agent.
Reads/writes JSON data files for products, inventory, orders, etc.
For production, this will be replaced by Omar's backend API client.
"""

import json
import os
from typing import Any

from eldockor.store.base import Store


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename: str) -> list[dict]:
    """Load a JSON file from the data directory."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(filename: str, data: list[dict]) -> None:
    """Save data to a JSON file."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class FileStore(Store):
    """File-based store using JSON files as the data source."""

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    def _get_products(self) -> list[dict]:
        return _load_json("products.json")

    def _save_products(self, products: list[dict]) -> None:
        _save_json("products.json", products)

    def search_products(self, query: str) -> list[dict]:
        """Search for products by name, part number, or category.

        Supports Arabic and English queries with word-level matching
        to handle Arabic morphology variations.
        """
        query_lower = query.lower().strip()
        products = self._get_products()
        results = []

        # Split query into words for flexible matching
        query_words = set(query_lower.split())

        for product in products:
            name = product.get("name", "")
            name_lower = name.lower()
            part_number = product.get("part_number", "").lower()
            category = product.get("category", "").lower()

            # Split product name into words
            name_words = set(name_lower.split())

            # 1. Direct substring match
            if (query_lower in name_lower or
                query_lower in part_number or
                query_lower in category):
                results.append(self._product_to_result(product))
                continue

            # 2. Word-level matching: any query word appears in product name
            if query_words & name_words:
                results.append(self._product_to_result(product))
                continue

            # 3. Arabic-to-English translation (whole query)
            arabic_to_english = {
                "فلاتر زيت": "oil filter",
                "فلاتر": "filter",
                "زيت": "oil",
                "فرامل": "brake pads",
                "بطارية": "battery",
                "إطارات": "tire",
                "زيوت": "oil",
                "هواء": "air",
                "تكييف": "ac",
                "إضاءة": "light",
                "قطران": "rotor",
                "كبح": "brake",
                "فلتر": "filter",
                "بوش": "bosch",
                "دينسو": "denso",
                "مايه": "mahle",
                "اتي": "ate",
                "ماهلي": "mahle",
                "ايطارات": "tire",
                "البطارية": "battery",
                "الفرامل": "brake pads",
                "الزيوت": "oil",
            }
            query_english = arabic_to_english.get(query_lower, None)
            if query_english:
                query_eng_lower = query_english.lower()
                if (query_eng_lower in name_lower or
                    query_eng_lower in part_number or
                    query_eng_lower in category):
                    results.append(self._product_to_result(product))
                    continue

                # Word-level English match
                eng_words = set(query_eng_lower.split())
                if eng_words & name_words:
                    results.append(self._product_to_result(product))
                    continue

        return results

    def _product_to_result(self, product: dict) -> dict:
        """Convert a product dict to search result format."""
        return {
            "product_id": product["product_id"],
            "name": product["name"],
            "category": product["category"],
            "part_number": product["part_number"],
            "price": product["price"],
            "available_quantity": product["available_quantity"],
            "supplier": product.get("supplier", ""),
            "reorder_threshold": product.get("reorder_threshold", 0)
        }

    def check_stock(self, product_id: str) -> dict:
        products = self._get_products()
        for product in products:
            if product["product_id"] == product_id:
                return {
                    "product_id": product["product_id"],
                    "product_name": product["name"],
                    "available_quantity": product["available_quantity"],
                    "category": product.get("category", ""),
                    "price": product.get("price", 0)
                }
        return {
            "product_id": product_id,
            "product_name": None,
            "available_quantity": 0,
            "error": "Product not found"
        }

    def get_product(self, product_id: str) -> dict | None:
        products = self._get_products()
        for product in products:
            if product["product_id"] == product_id:
                return dict(product)
        return None

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    def get_inventory_summary(self) -> list[dict]:
        products = self._get_products()
        return [
            {
                "product_id": p["product_id"],
                "name": p["name"],
                "category": p["category"],
                "part_number": p["part_number"],
                "price": p["price"],
                "available_quantity": p["available_quantity"],
                "reorder_threshold": p.get("reorder_threshold", 0),
                "stock_status": "in_stock" if p["available_quantity"] > 0 else "out_of_stock"
            }
            for p in products
        ]

    def get_low_stock_items(self, threshold: int = 5) -> list[dict]:
        products = self._get_products()
        low_stock = []
        for product in products:
            quantity = product["available_quantity"]
            threshold_configured = product.get("reorder_threshold", threshold)
            if quantity <= threshold_configured:
                low_stock.append({
                    "product_id": product["product_id"],
                    "name": product["name"],
                    "category": product["category"],
                    "available_quantity": quantity,
                    "reorder_threshold": threshold_configured,
                    "suggested_reorder_quantity": max(
                        threshold_configured * 2,
                        threshold_configured - quantity + 2
                    )
                })
        return low_stock

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def _get_orders(self) -> list[dict]:
        return _load_json("orders.json")

    def _save_orders(self, orders: list[dict]) -> None:
        _save_json("orders.json", orders)

    def create_order(
        self,
        customer_id: str,
        items: list[dict],
        idempotency_key: str | None = None
    ) -> dict:
        products = self._get_products()
        orders = self._get_orders()

        # Check for duplicate idempotency key
        if idempotency_key:
            for order in orders:
                if order.get("idempotency_key") == idempotency_key:
                    return {
                        "success": True,
                        "order_id": order["order_id"],
                        "status": order["status"],
                        "message": "Order already exists (idempotent request)",
                        "existing_order": order
                    }

        # Validate items and calculate total
        validated_items = []
        total = 0
        errors = []

        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]

            product = self.get_product(product_id)
            if product is None:
                errors.append(f"Product {product_id} not found")
                continue

            if product["available_quantity"] < quantity:
                errors.append(
                    f"{product['name']}: available {product['available_quantity']}, "
                    f"requested {quantity}"
                )
                continue

            validated_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "name": product["name"],
                "price": product["price"]
            })
            total += product["price"] * quantity

        if errors:
            return {
                "success": False,
                "order_id": None,
                "status": "failed",
                "items": validated_items,
                "total": total,
                "message": "Order creation failed: " + "; ".join(errors),
                "errors": errors
            }

        # Create the order
        order_num = len(orders) + 1
        order_id = f"ORD-{order_num:03d}"

        order = {
            "order_id": order_id,
            "customer_id": customer_id,
            "items": validated_items,
            "status": "confirmed",
            "total": total,
            "created_at": "2026-09-30T12:00:00Z",
            "idempotency_key": idempotency_key
        }
        orders.append(order)
        self._save_orders(orders)

        # Reduce inventory
        for item in validated_items:
            for product in products:
                if product["product_id"] == item["product_id"]:
                    product["available_quantity"] -= item["quantity"]

        self._save_products(products)

        return {
            "success": True,
            "order_id": order_id,
            "status": "confirmed",
            "items": validated_items,
            "total": total,
            "message": f"Order {order_id} created successfully. Total: {total} EGP"
        }

    def get_order_status(self, order_id: str) -> dict:
        orders = self._get_orders()
        for order in orders:
            if order["order_id"] == order_id:
                return {
                    "order_id": order["order_id"],
                    "status": order["status"],
                    "items": order["items"],
                    "total": order["total"],
                    "created_at": order.get("created_at", ""),
                    "customer_id": order["customer_id"]
                }
        return {
            "order_id": order_id,
            "status": None,
            "items": [],
            "total": 0,
            "error": "Order not found"
        }

    def get_customer_orders(self, customer_id: str) -> list[dict]:
        orders = self._get_orders()
        return [
            {
                "order_id": o["order_id"],
                "status": o["status"],
                "total": o["total"],
                "created_at": o.get("created_at", ""),
                "items_count": len(o["items"])
            }
            for o in orders
            if o["customer_id"] == customer_id
        ]

    # ------------------------------------------------------------------
    # Reorder drafts
    # ------------------------------------------------------------------

    def _get_reorder_drafts(self) -> list[dict]:
        return _load_json("reorder_drafts.json")

    def _save_reorder_drafts(self, drafts: list[dict]) -> None:
        _save_json("reorder_drafts.json", drafts)

    def prepare_reorder(self, product_id: str, quantity: int) -> dict:
        """Create a draft replenishment request (not a real PO)."""
        product = self.get_product(product_id)
        if product is None:
            return {
                "success": False,
                "draft_id": None,
                "message": f"Product {product_id} not found"
            }

        drafts = self._get_reorder_drafts()
        draft_num = len(drafts) + 1
        draft_id = f"DRAFT-{draft_num:03d}"

        draft = {
            "draft_id": draft_id,
            "product_id": product_id,
            "product_name": product["name"],
            "supplier": product.get("supplier", ""),
            "requested_quantity": quantity,
            "status": "draft",
            "created_at": "2026-09-30T12:00:00Z",
            "approved": False
        }
        drafts.append(draft)
        self._save_reorder_drafts(drafts)

        return {
            "success": True,
            "draft_id": draft_id,
            "product_id": product_id,
            "product_name": product["name"],
            "supplier": product.get("supplier", ""),
            "requested_quantity": quantity,
            "status": "draft",
            "message": f"Reorder draft {draft_id} created. Awaiting admin approval."
        }


# ---------------------------------------------------------------------------
# Singleton store instance
# ---------------------------------------------------------------------------

_store: FileStore | None = None


def get_store() -> FileStore:
    """Get the singleton store instance."""
    global _store
    if _store is None:
        _store = FileStore()
    return _store


def update_stock(product_id: str, new_quantity: int) -> dict:
    """Update stock for a product (used by tests)."""
    store = FileStore()
    products = store._get_products()
    for p in products:
        if p["product_id"] == product_id:
            p["available_quantity"] = new_quantity
            store._save_products(products)
            return {"success": True, "product_id": product_id, "new_quantity": new_quantity}
    return {"success": False, "error": "Product not found"}
