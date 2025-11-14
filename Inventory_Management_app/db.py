#this will be the SQLite conection.
import sqlite3
from.schema import SCHEMA_SQL
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "inventory.db"

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def initialize_db() -> None:
    
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        