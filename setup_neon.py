import os
import sys
import secrets
from dotenv import load_dotenv
import argparse

# Load existing environment variables
load_dotenv()

def generate_secret_key():
    """Generate a secure secret key for JWT tokens"""
    return secrets.token_hex(32)

def update_env_file(connection_string, secret_key):
    """Update the .env file with new database configuration"""
    try:
        # Read current .env file
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                env_content = f.read()
        else:
            env_content = """# Google Sheets configuration (kept for migration purposes)
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json
SPREADSHEET_ID=1b20hdwuVXdrWlFIgewH3lqKEI3XNNJ6h5aH4iDsWxE8
USERS_SPREADSHEET_ID=1b20hdwuVXdrWlFIgewH3lqKEI3XNNJ6h5aH4iDsWxE8
"""

        # Update or add DATABASE_URL
        if "DATABASE_URL=" in env_content:
            env_content = "\n".join([
                line if not line.startswith("DATABASE_URL=") else f"DATABASE_URL={connection_string}"
                for line in env_content.split("\n")
            ])
        else:
            env_content += f"\n# Neon PostgreSQL configuration\nDATABASE_URL={connection_string}\n"

        # Update or add SECRET_KEY
        if "SECRET_KEY=" in env_content:
            env_content = "\n".join([
                line if not line.startswith("SECRET_KEY=") else f"SECRET_KEY={secret_key}"
                for line in env_content.split("\n")
            ])
        else:
            env_content += f"\n# JWT Secret Key\nSECRET_KEY={secret_key}\n"

        # Write updated content back to .env
        with open(".env", "w") as f:
            f.write(env_content)

        print("✅ .env file updated successfully!")
        return True
    except Exception as e:
        print(f"❌ Error updating .env file: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Set up Neon PostgreSQL for your facility checklist app")
    parser.add_argument("--connection", help="Neon PostgreSQL connection string")
    parser.add_argument("--generate-key", action="store_true", help="Generate a new secret key")
    
    args = parser.parse_args()
    
    # If no arguments provided, prompt interactively
    if not args.connection and not args.generate_key:
        print("=" * 80)
        print("Facility Checklist - Neon PostgreSQL Setup")
        print("=" * 80)
        print("\nThis script will help you configure your application to use Neon PostgreSQL.")
        print("You'll need your Neon connection details ready.\n")
        
        # Ask for connection details
        use_connection_string = input("Do you have a full Neon connection string? (y/n): ").lower() == 'y'
        
        if use_connection_string:
            connection_string = input("Enter your Neon connection string: ")
        else:
            username = input("Enter Neon username: ")
            password = input("Enter Neon password: ")
            host = input("Enter Neon host endpoint: ")
            database = input("Enter database name (default 'facilitychecklist'): ") or "facilitychecklist"
            
            # Build the connection string
            connection_string = f"postgresql://{username}:{password}@{host}/{database}"
        
        # Ask about secret key
        generate_new_key = input("Generate new JWT secret key? (y/n): ").lower() == 'y'
        
        if generate_new_key:
            secret_key = generate_secret_key()
            print(f"Generated new secret key: {secret_key}")
        else:
            secret_key = os.getenv("SECRET_KEY", "my-very-secret-key")
    else:
        # Use command line arguments
        connection_string = args.connection or os.getenv("DATABASE_URL")
        
        if args.generate_key:
            secret_key = generate_secret_key()
            print(f"Generated new secret key: {secret_key}")
        else:
            secret_key = os.getenv("SECRET_KEY", "my-very-secret-key")
    
    # Update .env file
    if connection_string:
        update_env_file(connection_string, secret_key)
    else:
        print("❌ No connection string provided. .env file not updated.")
        return
    
    # Verify configuration
    print("\nVerifying configuration...")
    load_dotenv()  # Reload env variables
    
    if os.getenv("DATABASE_URL") == connection_string:
        print("✅ DATABASE_URL is correctly set in .env")
    else:
        print("❌ DATABASE_URL was not properly set in .env")
    
    if os.getenv("SECRET_KEY") == secret_key:
        print("✅ SECRET_KEY is correctly set in .env")
    else:
        print("❌ SECRET_KEY was not properly set in .env")
    
    # Next steps
    print("\n" + "=" * 80)
    print("Next steps:")
    print("1. Install dependencies:       pip install -r requirements.txt")
    print("2. Test database connection:   python test_db_connection.py")
    print("3. Migrate data from Sheets:   python migrate_data.py")
    print("4. Start the FastAPI server:   python run_server.py")
    print("5. Start the Dash frontend:    cd dashboard && python run.py")
    print("=" * 80)

if __name__ == "__main__":
    main()
