"""Database setup for JSON storage."""
from app.db.json_storage import init_db, get_user, get_all_users, create_user, update_user
from app.db.json_storage import get_transactions, create_transaction

# Re-export for compatibility
__all__ = [
    "init_db",
    "get_user",
    "get_all_users",
    "create_user",
    "update_user",
    "get_transactions",
    "create_transaction",
]
