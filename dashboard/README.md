# Facility Checklist Dashboard

This is a Dash-based frontend for the Facility Checklist application. It provides a user interface to interact with the FastAPI backend for managing facility inspection data.

## Features

- User authentication (login/register)
- View all facility inspections in a tabular format
- Add new facility inspections
- Edit existing inspections
- Delete inspections
- Responsive design with Bootstrap

## Setup Instructions

1. Make sure your FastAPI backend is running (the main application in the parent directory)

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the Dash application:
   ```
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:8050/
   ```

## Project Structure

- `app.py`: Main Dash application with layouts and callbacks
- `requirements.txt`: Python package dependencies
- `assets/`: (optional) Custom CSS and JavaScript files

## Authentication

The dashboard uses token-based authentication with the FastAPI backend. The token is stored in the browser's localStorage for session management.

## Note

Ensure the backend API URL in `app.py` matches your FastAPI setup (default is http://127.0.0.1:8000).
