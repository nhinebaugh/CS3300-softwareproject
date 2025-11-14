#backup file sript used to back up the DB
from pathlib import Path
from datetime import datetime
import zipfile
from ..db import DB_PATH

def backup_database(dest_dir: str | None = None) -> str:
    db_path = Path(DB_PATH)
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    pkg_root = db_path.parent.parent
    backups_dir = Path(dest_dir) if dest_dir else pkg_root / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = backups_dir / f"backup_{stamp}.zip"

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, arcname=f"{db_path.parent.name}/{db_path.name}")
    
    return str(zip_path)