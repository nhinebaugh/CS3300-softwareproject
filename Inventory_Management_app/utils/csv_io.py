#Export/import csv files
from typing import Iterable, Dict
import csv
from datetime import datetime, timezone

LOCAL_TZ = datetime.now().astimezone().tzinfo
UTC = timezone.utc

def _to_local(ts: str | None) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts
    

def export_to_csv(rows: Iterable[Dict], filepath: str) -> None:
    rows = list(rows)
    if not rows:
        #write only headers if no data
        headers = ["id", "sku", "name", "unit_cost", "price", "quantity", "min_quantity", "barcode", "active", "created_at", "updated_at"]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return
    
    preferred = ["id", "sku", "name", "unit_cost", "price", "quantity", "min_quantity", "barcode", "active", "created_at", "updated_at"]
    headers = [h for h in preferred if h in rows[0]]+ [k for k in rows[0].keys() if k not in preferred]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            r = dict(r) #make a copy
            if "created_at" in r:
                r["created_at"] = _to_local(r["created_at"])
            if "updated_at" in r:
                r["updated_at"] = _to_local(r["updated_at"])
            writer.writerow({k: r.get(k, "") for k in headers})