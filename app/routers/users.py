"""Users router for user management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.db import create_user, get_user, get_all_users
from app.models.user import User
from typing import List

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[User])
def get_all_users_endpoint():
    """
    Get all users.
    
    Returns:
        List of all users
    """
    users = get_all_users()
    return users


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    name: str
    risk_profile: str  # low | medium | high
    goals: Optional[str] = None
    # Additional onboarding fields
    age_range: Optional[str] = None
    income_range: Optional[str] = None
    debt: Optional[float] = None
    emi: Optional[float] = None
    existing_savings: Optional[float] = None


@router.post("", response_model=User, status_code=201)
def create_user_endpoint(request: CreateUserRequest):
    """
    Create a new user.
    
    Args:
        request: User creation data
        
    Returns:
        Created user with ID
    """
    # Validate risk_profile
    if request.risk_profile not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=400,
            detail="risk_profile must be one of: low, medium, high"
        )
    
    # Create user data dict with all fields
    user_data = {
        "name": request.name,
        "risk_profile": request.risk_profile,
        "goals": request.goals,
        "age_range": request.age_range,
        "income_range": request.income_range,
        "debt": request.debt,
        "emi": request.emi,
        "existing_savings": request.existing_savings,
    }
    
    # Create user
    try:
        user = create_user(user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/{user_id}", response_model=User)
def get_user_endpoint(user_id: int):
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        User data
    """
    user = get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found"
        )
    return user

