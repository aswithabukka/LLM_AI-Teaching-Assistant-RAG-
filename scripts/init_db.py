import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.models.database import User
from app.core.auth import get_password_hash

def init_db():
    """Initialize the database with a default admin user."""
    print("Creating database tables...")
    # Make sure to create all tables first
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        
        if not admin_user:
            print("Creating default admin user...")
            # Create default admin user
            admin_user = User(
                email="admin@example.com",
                hashed_password=get_password_hash("adminpassword"),
                is_active=True,
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created successfully.")
            print("Email: admin@example.com")
            print("Password: adminpassword")
        else:
            print("Admin user already exists.")
    
    except Exception as e:
        print(f"Error initializing database: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
