"""Transaction model (Pydantic for JSON storage)."""
from pydantic import BaseModel
from datetime import date
from typing import Optional


class Transaction(BaseModel):
    """Transaction model for storing financial transactions."""
    
    id: Optional[int] = None
    user_id: int
    amount: float
    type: str  # income | expense
    tag: Optional[str] = None
    category: Optional[str] = None  # needs | wants
    date: date
    
    class Config:
        """Pydantic config."""
        from_attributes = True
