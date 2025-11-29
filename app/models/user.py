"""User model (Pydantic for JSON storage)."""
from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    """User model for storing user information."""
    
    id: Optional[int] = None
    name: str
    risk_profile: str  # low | medium | high
    goals: Optional[str] = None
    # Additional onboarding fields
    age_range: Optional[str] = None  # e.g., "18-24", "25-34", etc.
    income_range: Optional[str] = None  # e.g., "25k-50k", "50k-100k", etc.
    debt: Optional[float] = None  # Total debt amount
    emi: Optional[float] = None  # Monthly EMI
    existing_savings: Optional[float] = None  # Existing savings amount
    
    class Config:
        """Pydantic config."""
        from_attributes = True
