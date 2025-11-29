"""Script to create a test user in the database."""
from app.db.db import init_db, create_user

# Initialize database
init_db()

# Create test user
user_data = {
    "name": "Test User",
    "risk_profile": "medium",
    "goals": "Save for emergency fund and invest for retirement"
}

try:
    user = create_user(user_data)
    print(f"✅ Created user with ID: {user['id']}")
    print(f"   Name: {user['name']}")
    print(f"   Risk Profile: {user['risk_profile']}")
    print(f"   Goals: {user['goals']}")
except Exception as e:
    print(f"❌ Error creating user: {e}")
