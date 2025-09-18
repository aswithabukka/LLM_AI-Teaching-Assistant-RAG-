import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, User
from app.core.auth import get_password_hash
from app.config.settings import settings

# Create the database directory if it doesn't exist
db_dir = parent_dir / "data"
db_dir.mkdir(parents=True, exist_ok=True)

# Create the database engine with an absolute path
db_path = db_dir / "app.db"
db_url = f"sqlite:///{db_path}"
print(f"Using database at: {db_path}")

engine = create_engine(db_url)

# Create all tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Check if admin user already exists
    admin_exists = False
    try:
        # Try to query the users table
        admin_exists = db.query(User).filter(User.email == "admin@example.com").first() is not None
    except Exception as e:
        print(f"Error checking for admin user: {e}")
        admin_exists = False
    
    if not admin_exists:
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
    db.rollback()

finally:
    db.close()
