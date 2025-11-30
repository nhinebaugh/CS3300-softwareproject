#services file allowing us to recieve issue and things like that.
from typing import Any, Dict, List, Optional
from Inventory_Management_app.db import get_connection
from Inventory_Management_app.dao import ItemDAO

class InventoryService:
    def _generate_sku(self) -> str:
        #sequential SKU generator based on item count
        with get_connection() as conn:
            row = conn.execute("Select Count(*) as n from items").fetchone()
            n = (row["n"] or 0) + 1
        return f"SKU-{n:06d}"
    
    def create_item(self, data: dict[str, Any]) -> int:
        #item validation and creation
        if not data.get("name"):
            raise ValueError("Name is required")
        if "quantity" in data and data["quantity"] is None:
            data["quantity"] = 0
        if "min_quantity" in data and data["min_quantity"] is None:
            data["min_quantity"] = 0
        if data.get("price", 0) < 0 or data.get("unit_cost", 0) < 0:
            raise ValueError("Price and Unit Cost must be greater than or equal to 0")
        
        # Auto-generate SKU if not provided
        if not data.get("sku"):
            data["sku"] = self._generate_sku()

        #ensures cols exist with default values
        data.setdefault("quantity", 0)
        data.setdefault("min_quantity", 0)
        data.setdefault("unit_cost", 0.0)
        data.setdefault("price", 0.0)
        data.setdefault("barcode", None)
        data.setdefault("active", 1)

        return ItemDAO.create_items(data)
    
    def list_items(self, name_like: str = "", only_active: bool = True) -> List[Dict[str, Any]]:
        #lists items in the inventory
        return ItemDAO.list(name_like=name_like, only_active=only_active)
    
    def receive_stock(self, item_id: int, quantity: int, reason: str = "receive", ref: str = "") -> None:
        # receives stock into inventory
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        
        with get_connection() as conn:
            conn.execute("BEGIN")
            # Update item quantity
            conn.execute(
                "Update items set quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (quantity, item_id),
            )
            #audit log can be added here
            conn.execute(
                "Insert into stock_txns (item_id, delta, reason, ref) values (?, ?, ?, ?)",
                (item_id, quantity, reason, ref),
            )
            conn.commit()

    def issue_stock(self, item_id: int, quantity: int, reason: str = "issue", ref: str = "") -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
            
        with get_connection() as conn:
            current = conn.execute("Select quantity from items where id = ?", (item_id,)).fetchone()
            if not current:
                raise ValueError("Item not found.")
            if current["quantity"] < quantity:
                raise ValueError("Insufficient stock.")
                
            conn.execute("BEGIN")
            conn.execute(
                "Update items set quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (quantity, item_id),
            )
            #audit log
            conn.execute(
                "Insert into stock_txns (item_id, delta, reason, ref) values (?, ?, ?, ?)",
                (item_id, -quantity, reason, ref),
            )

            conn.commit()

    def recalculate_quantity(self, item_id: int) -> None:
        #recalculates quantity based on stock transactions
        with get_connection() as conn:
            row = conn.execute(
                "Select Coalesce(Sum(delta), 0) as total from stock_txns where item_id = ?", (item_id,)
            ).fetchone()
            total = row["total"] if row else 0
            conn.execute(
                "Update items set quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (total, item_id),
            )

    def update_item(self, item_id: int, fields: dict[str, Any]) -> None:
        #updates item details
        if not fields:
            return
        return ItemDAO.update_item(item_id, fields)
    
    def delete_item(self, item_id: int) -> None:
        #deletes item the inventory permanently
        with get_connection() as conn:
            conn.execute("DELETE FROM items WHERE id = ?", (item_id,))