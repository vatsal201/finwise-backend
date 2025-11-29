"""JSON-based storage for users and transactions."""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from threading import Lock

# Data directory
DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
TRANSACTIONS_FILE = DATA_DIR / "transactions.json"

# Thread lock for file operations
_file_lock = Lock()


def _ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)


def _load_json(file_path: Path, default: List = None) -> List[Dict[str, Any]]:
    """Load JSON data from file."""
    if default is None:
        default = []
    
    if not file_path.exists():
        return default
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def _save_json(file_path: Path, data: List[Dict[str, Any]]):
    """Save JSON data to file."""
    with _file_lock:
        _ensure_data_dir()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


def init_db():
    """Initialize database by creating data directory and empty files if needed."""
    _ensure_data_dir()
    if not USERS_FILE.exists():
        _save_json(USERS_FILE, [])
    if not TRANSACTIONS_FILE.exists():
        _save_json(TRANSACTIONS_FILE, [])


# User operations
def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    users = _load_json(USERS_FILE, [])
    for user in users:
        if user.get("id") == user_id:
            return user
    return None


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users."""
    return _load_json(USERS_FILE, [])


def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user."""
    users = _load_json(USERS_FILE, [])
    
    # Generate new ID
    if users:
        new_id = max(u.get("id", 0) for u in users) + 1
    else:
        new_id = 1
    
    user_data["id"] = new_id
    users.append(user_data)
    _save_json(USERS_FILE, users)
    return user_data


def update_user(user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user by ID."""
    users = _load_json(USERS_FILE, [])
    for i, user in enumerate(users):
        if user.get("id") == user_id:
            user_data["id"] = user_id
            users[i] = user_data
            _save_json(USERS_FILE, users)
            return user_data
    return None


# Transaction operations
def get_transactions(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all transactions, optionally filtered by user_id."""
    transactions = _load_json(TRANSACTIONS_FILE, [])
    
    # Convert date strings back to date objects for compatibility
    for t in transactions:
        if isinstance(t.get("date"), str):
            try:
                t["date"] = datetime.strptime(t["date"], "%Y-%m-%d").date()
            except ValueError:
                t["date"] = date.today()
    
    if user_id is not None:
        transactions = [t for t in transactions if t.get("user_id") == user_id]
    
    # Sort by date descending
    transactions.sort(key=lambda x: x.get("date", date.min), reverse=True)
    return transactions


def create_transaction(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new transaction."""
    transactions = _load_json(TRANSACTIONS_FILE, [])
    
    # Generate new ID
    if transactions:
        new_id = max(t.get("id", 0) for t in transactions) + 1
    else:
        new_id = 1
    
    transaction_data["id"] = new_id
    
    # Convert date to string for JSON storage
    if isinstance(transaction_data.get("date"), date):
        transaction_data["date"] = transaction_data["date"].isoformat()
    
    transactions.append(transaction_data)
    _save_json(TRANSACTIONS_FILE, transactions)
    
    # Convert date back to date object for return
    if isinstance(transaction_data.get("date"), str):
        transaction_data["date"] = datetime.strptime(transaction_data["date"], "%Y-%m-%d").date()
    
    return transaction_data

