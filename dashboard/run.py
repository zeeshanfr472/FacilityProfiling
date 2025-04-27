"""
Run script for the Facility Checklist Dashboard.
This allows starting the app with a proper entry point.
"""

from app import app

if __name__ == '__main__':
    app.run(debug=True)