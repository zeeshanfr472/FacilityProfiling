import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_default_user(username="admin", password="admin"):
    """Create a default admin user in the database"""
    print(f"Creating default user '{username}'...")
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Check if user already exists
            result = connection.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": username}
            )
            
            if result.fetchone():
                print(f"User '{username}' already exists.")
                return
            
            # Hash the password
            password_hash = pwd_context.hash(password)
            
            # Insert the user
            connection.execute(
                text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"),
                {"username": username, "password_hash": password_hash}
            )
            connection.commit()
            
            print(f"Default user '{username}' created successfully.")
            print(f"Username: {username}")
            print(f"Password: {password}")
    except Exception as e:
        print(f"Error creating default user: {str(e)}")

if __name__ == "__main__":
    # Create default admin user
    create_default_user("admin", "admin")
    
    # You can also create additional users if needed
    # create_default_user("user1", "password1")
