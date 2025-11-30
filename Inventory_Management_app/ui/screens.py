#screen file for the different tkinter screens.
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

from ..services import InventoryService
from ..dao import ItemDAO

LOW_STOCK = "Low Stock"
#inventory screen class that shows the inventory items in a sinle table with different actions.
class InventoryScreen(ttk.Frame):
    def __init__(self, master, service: InventoryService):
        super().__init__(master, padding=10)
        self.service = service

        #search bar + new item button
        top = ttk.Frame(self)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Search:").pack(side=tk.LEFT)

        self.search_var = tk.StringVar()

        entry = ttk.Entry(top, textvariable=self.search_var, width=32)
        entry.pack(side=tk.LEFT, padx=6)
        entry.bind("<Return>", lambda _e: self.refresh())
                
        ttk.Button(top, text="Go", command=self.refresh).pack(side=tk.LEFT)
        ttk.Button(top, text="New Item", command=self.new_item).pack(side=tk.RIGHT)

        #table for inventory items
        cols = ("id", "sku", "name", "barcode", "quantity", "min_quantity", "price")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        self.tree.tag_configure(LOW_STOCK, background="#ffe6e6")
        headers = {
            "id": "ID",
            "sku": "SKU",
            "name": "Name",
            "barcode": "Barcode",
            "quantity": "Qty",
            "min_quantity": "Min",
            "price": "Price"
        }

        for c in cols:
            self.tree.heading(c, text=headers[c])
            anchor = tk.W if c in ("sku", "name") else tk.E
            if c in ("id", "quantity", "min_quantity"):
                width = 60
            elif c in ("sku", "barcode"):
                width = 140
            elif c == "name":
                width = 220
            else:  # price
                width = 90
            self.tree.column(c, anchor=anchor, width=width)

        #hide id col
        self.tree.column("id", width=0, stretch=False)

        self.tree.pack(fill=tk.BOTH, expand=True, pady=8)

        #actions to reveive, issue, refresh, edit, delete
        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.X)
        ttk.Button(bottom, text="Receive", command=lambda: self.adjust(+1)).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Issue", command=lambda: self.adjust(-1)).pack(side=tk.LEFT, padx=6)
        ttk.Button(bottom, text="Refresh", command=self.refresh).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Edit Item", command=self.edit_item).pack(side=tk.RIGHT)
        ttk.Button(bottom, text="Delete Item", command=self.delete_item).pack(side=tk.RIGHT, padx=6)

        #double click to open issue/receive dialog
        self.tree.bind("<Double-1>", lambda _e: self.adjust(+1))

        self.refresh()
    #helper to get selected item id
    def selected_item_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        values = self.tree.item(sel[0], "values")
        return int(values[0]) #id is first col
    #refresh the inventory table to ensure latest data
    def refresh(self):
        #clear
        for lid in self.tree.get_children():
            self.tree.delete(lid)
        term = self.search_var.get().strip()
        rows = self.service.list_items(name_like=term, only_active=True)

        for r in rows:
            tags = ()
            if int(r.get("quantity", 0)) < int(r.get("min_quantity", 0)):
                tags = (LOW_STOCK,)
            self.tree.insert(
                "", tk.END,
                values=(
                    r["id"],
                    r["sku"],
                    r["name"],
                    r.get("barcode") or "",
                    r["quantity"],
                    r["min_quantity"],
                    f'{float(r["price"]):.2f}',
                ),
                tags=tags
            )

    #action handlers for buttons such as new item, adjust stock, edit item, delete item
    def new_item(self):
        ItemDialog(self, self.service, on_saved=self.refresh)

    def adjust(self, sign: int):
        item_id = self.selected_item_id()
        if not item_id:
            messagebox.showinfo("Select Item", "Please select an item in the table.")
            return
        AdjustDialog(self, self.service, item_id, sign, on_committed=self.refresh)
    def edit_item(self):
        item_id = self.selected_item_id()
        if not item_id:
            messagebox.showinfo("Select Item", "Please select an item in the inventory to edit.")
            return
        ItemDialog(self, self.service, item_id=item_id, on_saved=self.refresh)

    def delete_item(self):
        item_id = self.selected_item_id()
        if not item_id:
            messagebox.showinfo("Select Item", "Please select an item in the inventory to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected item?"):
            self.service.delete_item(item_id)
            self.refresh()


#dialogs for adding/editing items and adjusting stock
class ItemDialog(tk.Toplevel):
    def __init__(self, master, service: InventoryService, item_id=None, on_saved=None):
        super().__init__(master)
        self.title("New Item")
        self.service = service
        self.on_saved = on_saved
        self.item_id = item_id
        self.transient(master)
        self.grab_set()

        body = ttk.Frame(self, padding=10)
        body.pack(fill=tk.BOTH, expand=True)

        self.var_name = tk.StringVar()
        self.var_sku = tk.StringVar()
        self.var_price = tk.StringVar()
        self.var_min = tk.StringVar()
        self.var_barcode = tk.StringVar()

        self._row(body, "Name*", self.var_name)
        self._row(body, "SKU", self.var_sku)
        self._row(body, "Price", self.var_price)
        self._row(body, "Min Qty", self.var_min)
        self._row(body, "Barcode", self.var_barcode)

        if self.item_id:
            item = ItemDAO.get_item_by_id(self.item_id)
            self.var_name.set(item["name"])
            self.var_sku.set(item["sku"])
            self.var_price.set(str(item["price"]))
            self.var_min.set(str(item["min_quantity"]))
            self.var_barcode.set(item.get("barcode") or "")

        btns = ttk.Frame(body)
        btns.pack(fill=tk.X, pady=(8,0))
        ttk.Button(btns, text="Save", command=self.on_save).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=6)

        self.bind("<Return>", lambda e: self.on_save())
    #helper to create a row in the dialog
    def _row(self, parent, label, var):
        r = ttk.Frame(parent)
        r.pack(fill=tk.X, pady=4)
        ttk.Label(r, text=label, width=14).pack(side=tk.LEFT)
        ttk.Entry(r, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
    #handler for saving the item
    def on_save(self):
        try:
            data: Dict[str, Any] = {
                "name": self.var_name.get().strip(),
                "sku": self.var_sku.get().strip() or None,
                "price": float(self.var_price.get() or 0),
                "min_quantity": int(self.var_min.get() or 0),
                "barcode": self.var_barcode.get().strip() or None,
            }
            if self.item_id:
                self.service.update_items(self.item_id, data)
            else:
                self.service.create_item(data)

            if self.on_saved:
                self.on_saved()
            self.destroy()
        except Exception as ex:
            messagebox.showerror("Errored", str(ex))
#Adjust stock dialog for receiving or issuing stock
class AdjustDialog(tk.Toplevel):
    def __init__(self, master, service: InventoryService, item_id: int, sign: int, on_committed=None):
        super().__init__(master)
        self.title("Receive Quantity" if sign > 0 else "Issue Stock")
        self.service = service
        self.item_id = item_id
        self.sign = sign
        self.on_committed = on_committed
        self.transient(master)
        self.grab_set()

        body = ttk.Frame(self, padding=10)
        body.pack(fill=tk.BOTH, expand=True)

        self.var_qty = tk.StringVar()
        self.var_reason = tk.StringVar(value="receive" if sign > 0 else "issue")
        self.var_ref = tk.StringVar()

        self._row(body, "Quantity", self.var_qty)
        self._row(body, "Reason", self.var_reason)
        self._row(body, "Ref", self.var_ref)

        btns = ttk.Frame(body)
        btns.pack(fill=tk.X, pady=(8,0))
        ttk.Button(btns, text="Commit", command=self.on_commit).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=6)

        self.bind("<Return>", lambda e: self.on_commit())
    #helper to create a row in the dialog
    def _row(self, parent, label, var):
        r = ttk.Frame(parent)
        r.pack(fill=tk.X, pady=4)
        ttk.Label(r, text=label, width=14).pack(side=tk.LEFT)
        ttk.Entry(r, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
    #handler for committing the stock adjustment

    def on_commit(self):
        try:
            qty = int(self.var_qty.get() or 0)
            reason = self.var_reason.get().strip() or ("receive" if self.sign > 0 else "issue")
            ref = self.var_ref.get().strip()
            if self.sign > 0:
                self.service.receive_stock(self.item_id, qty, reason, ref)
            else:
                self.service.issue_stock(self.item_id, qty, reason, ref)
            if self.on_committed:
                self.on_committed()
            self.destroy()
        except Exception as ex:
            messagebox.showerror("Errored", str(ex))
