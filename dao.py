#CRUD file operations

from typing import Any, Dict, List, Optional
from pathlib import Path
from db import get_connection

def _rowdict(row) -> Dict[str, Any]:
    return dict(row) if row is not None else None

class ItemDAO:
    @staticmethod
    def create_items(items: dict[str, Any]) -> int:
        """keys expected in items: sku, name, quantity, min_quantity, unit_cost, price, barcode, active
        Inserts a new item into the database and returns the new item's ID.
        """
        cols = ["sku", "name", "quantity", "min_quantity", "unit_cost", "price", "barcode", "active"]
        vals = [items.get(k) for k in cols]
        placeholders = ",".join(["?"] * len(cols))
        with get_connection() as conn:
            cursor = conn.execute(
                f"Insert into items ({','.join(cols)}) values ({placeholders})", vals)
            return cursor.lastrowid
        
    @staticmethod
    def get_item_by_id(item_id: int) -> Optional[Dict[str, Any]]:
        #gets item by ID
        with get_connection() as conn:
            row = conn.execute("Select * from items where id=?", (item_id,)).fetchone()
            return _rowdict(row)
        
    @staticmethod
    def get_item_by_sku(sku: str) -> Optional[Dict[str, Any]]:
        #gets item by SKU
        with get_connection() as conn:
            row = conn.execute("Select * from items where sku=?", (sku,)).fetchone()
            return _rowdict(row)
        
    @staticmethod
    def list(name_like: str = "", only_active: bool = True) -> List[Dict[str, Any]]:
        #lists items in the Database
        query = "Select * from items where 1=1"
        params: List[Any] = []
        if name_like:
            query += " and name like ?"
            params.append(f"%{name_like}%")
        if only_active:
            query += " and active=1"
        query += " order by name collate nocase"
        with get_connection() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]
        
    @staticmethod
    def update_items(item_id: int, fields: dict[str, Any]) -> None:
        #updates item in the database
        if not fields:
            return
        cols = [f"{k}=?" for k in fields.keys()]
        params = list(fields.values()) + [item_id]
        with get_connection() as conn:
            conn.execute(f"Update items set {', '.join(cols)}, updated_at=Current_TIMESTAMP WHERE id=?", params,)

    @staticmethod
    def soft_delete_item(item_id: int) -> None:
        #soft deletes item in the database
        with get_connection() as conn:
            conn.execute("Update items set active=0, updated_at=Current_TIMESTAMP WHERE id=?", (item_id,),)