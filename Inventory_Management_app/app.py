#This will be the application entry point will have Tk root and Navigation
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .db import initialize_db
from .services import InventoryService
from .ui.screens import InventoryScreen
from .utils.csv_io import export_to_csv
from .utils.backup import backup_database
#function to build the menu bar
def _build_menu(root: tk.Tk, svc: InventoryService, main_screen: InventoryScreen):
    menubar = tk.Menu(root)
    
    file_menu = tk.Menu(menubar, tearoff=0)
    #function for exporting to CSV
    def do_export_csv():
        rows = svc.list_items(name_like=main_screen.search_var.get(), only_active=True)
        path = filedialog.asksaveasfilename(
            parent=root,
            title="Export Inventory to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            export_to_csv(rows, path)
            messagebox.showinfo("Export Successful", f"Inventory exported {len(rows)} rows to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
    #function for backing up the database
    def do_backup():
        try:
            zip_path = backup_database()
            messagebox.showinfo("Backup Successful", f"Database backed up to:\n{zip_path}")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))
    
    file_menu.add_command(label="Export to CSV", command=do_export_csv)
    file_menu.add_command(label="Backup Database", command=do_backup)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.destroy)

    menubar.add_cascade(label="File", menu=file_menu)
    root.config(menu=menubar)

def main():
    initialize_db()

    root = tk.Tk()
    root.title("Inventory Management System")
    root.geometry("1000x640")

    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass

    svc = InventoryService()
    screen = InventoryScreen(root, svc)
    screen.pack(fill=tk.BOTH, expand=True)

    _build_menu(root, svc, screen)

    root.mainloop()

if __name__ == "__main__":
    main()
    
