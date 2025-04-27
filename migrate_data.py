import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from db_helper import create_tables, migrate_from_sheets
import sys

load_dotenv()

# Google Sheets Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "./credentials.json")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
USERS_SPREADSHEET_ID = os.getenv("USERS_SPREADSHEET_ID")

def get_sheets_data():
    """Fetch data from Google Sheets"""
    try:
        creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Get inspections data
        inspections_sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        inspections_data = inspections_sheet.get_all_records()
        
        # Get users data - handle different worksheet structures
        users_sheet = None
        try:
            # Try to get the 'users' worksheet first
            users_sheet = client.open_by_key(USERS_SPREADSHEET_ID).worksheet("users")
        except Exception as e:
            print(f"Warning: Could not find 'users' worksheet: {str(e)}")
            # Fallback to the first sheet
            users_sheet = client.open_by_key(USERS_SPREADSHEET_ID).sheet1
        
        if users_sheet:
            users_data = users_sheet.get_all_records()
        else:
            users_data = []
            
        # Debug print data structure for validation
        if inspections_data:
            print(f"Sample inspection record keys: {list(inspections_data[0].keys())}")
        if users_data:
            print(f"Sample user record keys: {list(users_data[0].keys())}")
            
        return inspections_data, users_data
    except Exception as e:
        print(f"Error in get_sheets_data: {str(e)}")
        raise

def run_migration():
    """Run the full migration process"""
    print("Starting migration from Google Sheets to PostgreSQL...")
    
    # Create database tables
    print("Creating database tables...")
    create_tables()
    
    # Get data from Google Sheets
    print("Fetching data from Google Sheets...")
    try:
        inspections_data, users_data = get_sheets_data()
        print(f"Fetched {len(inspections_data)} inspections and {len(users_data)} users.")
    except Exception as e:
        print(f"Error fetching data from Google Sheets: {str(e)}")
        return
    
    # Check if we have no data to migrate
    if not inspections_data and not users_data:
        print("No data to migrate. Please check your Google Sheets configuration.")
        return
    
    # Migrate data to PostgreSQL
    print("Migrating data to PostgreSQL...")
    try:
        # Migrate one record at a time to isolate issues
        for i, user in enumerate(users_data):
            try:
                migrate_from_sheets([],  [user])
                print(f"Migrated user {i+1}/{len(users_data)}")
            except Exception as e:
                print(f"Error migrating user {i+1}: {str(e)}")
                continue
        
        for i, inspection in enumerate(inspections_data):
            try:
                migrate_from_sheets([inspection], [])
                print(f"Migrated inspection {i+1}/{len(inspections_data)}")
            except Exception as e:
                print(f"Error migrating inspection {i+1}: {str(e)}")
                continue
                
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error migrating data to PostgreSQL: {str(e)}")
        return

if __name__ == "__main__":
    run_migration()
