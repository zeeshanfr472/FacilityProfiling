# Facility Checklist Application

This application helps track facility inspections and visualize data.

## Migration from Google Sheets to Neon PostgreSQL

This application has been migrated from using Google Sheets to a Neon PostgreSQL database for improved performance, reliability, and scalability.

### Setup Instructions

1. **Set up a Neon PostgreSQL Database**

   - Go to [Neon Console](https://console.neon.tech/)
   - Sign up or log in to your account
   - Create a new project named "facilitychecklist"
   - Create a new database named "facilitychecklist"
   - Create a new role with username and password
   - Get your connection string which will look like:
     `postgresql://username:password@endpoint/facilitychecklist`

2. **Update Environment Variables**

   - Open the `.env` file
   - Update the `DATABASE_URL` with your Neon connection string
   - Generate a secure `SECRET_KEY` for JWT authentication

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Migrate Data from Google Sheets**

   - Ensure your Google Sheets credentials are still in place
   - Run the migration script:

   ```bash
   python migrate_data.py
   ```

5. **Start the FastAPI Backend**

   ```bash
   uvicorn main:app --reload
   ```

6. **Start the Dash Frontend**

   ```bash
   cd dashboard
   python run.py
   ```

## Directory Structure

- `.env` - Environment variables
- `main.py` - FastAPI backend
- `db_helper.py` - PostgreSQL database helper
- `migrate_data.py` - Data migration script
- `dashboard/` - Dash frontend application

## API Endpoints

- `POST /register` - Register a new user
- `POST /login` - Authenticate a user
- `GET /inspections` - Get all inspections
- `POST /inspection` - Create a new inspection
- `PUT /inspection/{id}` - Update an inspection
- `DELETE /inspection/{id}` - Delete an inspection

## Dashboard Features

- User authentication
- Facility inspection form
- Data visualization
- Inspection management

## Deployment on Neon

The application can be deployed using various methods. Here's a simple setup:

1. Deploy the FastAPI backend:
   - Use a service like Heroku, Render, or Railway
   - Ensure environment variables are set correctly
   - Configure the Neon database connection

2. Deploy the Dash frontend:
   - Deploy to a frontend hosting service
   - Update the API_BASE_URL in dashboard/app.py to point to your deployed backend

3. Configure Neon PostgreSQL:
   - Set appropriate access restrictions
   - Consider enabling SSL for secure connections
   - Set up automated backups

## Notes on PostgreSQL vs Google Sheets

- PostgreSQL offers proper data types, relationships, and constraints
- Improved performance for complex queries and larger datasets
- Better security and access control
- Proper transaction support
- Ability to scale with your application's growth
