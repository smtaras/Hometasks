import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# PostgreSQL Connection String (Docker local instance)
DATABASE_URL = "postgresql://vasko_user:vasko_password@localhost:5432/vasko_shop_db"

# Raw CSV File Paths
RAW_FILES = {
    "customers": DATA_DIR / "customers.csv",
    "products": DATA_DIR / "products.csv",
    "orders": DATA_DIR / "orders.csv",
    "order_items": DATA_DIR / "order_items.csv",
}