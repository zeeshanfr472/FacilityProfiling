import dash
from dash import dcc, html, Input, Output, State, callback, no_update, dash_table
import dash_bootstrap_components as dbc
import requests
import json
from datetime import datetime
import pandas as pd
from dash.exceptions import PreventUpdate
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler("dashboard_debug.log"),
                       logging.StreamHandler()
                   ])
logger = logging.getLogger(__name__)

# Import your visualization functions
from visualization import (create_condition_chart, create_facility_type_chart, 
                          create_inspection_status_chart, create_zone_map)

# Define the API base URL
API_BASE_URL = "http://127.0.0.1:8000"  # Adjust if your FastAPI is running on a different port

# Create a wrapper for requests to log API calls
def api_request(method, url, **kwargs):
    """Wrapper around requests to log API calls and responses"""
    full_url = f"{API_BASE_URL}{url}"
    logger.debug(f"API Request: {method} {full_url}")
    
    if 'json' in kwargs:
        logger.debug(f"Request data: {kwargs['json']}")
    
    if 'headers' in kwargs:
        # Log headers except Authorization token (for security)
        safe_headers = kwargs['headers'].copy()
        if 'Authorization' in safe_headers:
            safe_headers['Authorization'] = "Bearer ***"
        logger.debug(f"Headers: {safe_headers}")
    
    try:
        response = getattr(requests, method.lower())(full_url, **kwargs)
        logger.debug(f"Response status: {response.status_code}")
        try:
            logger.debug(f"Response content: {response.json()}")
        except:
            logger.debug(f"Response content: {response.text[:500]}...")
        return response
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        traceback.print_exc()
        raise e

# This debug code focuses on the edit and delete functionality, so I'll only include
# the related callbacks. Copy just these functions into your app.py or test them in this file.

# Callback for edit form
def load_edit_form(row_number, data):
    """Load edit form with inspection data"""
    logger.debug(f"Loading edit form for inspection {row_number}")
    logger.debug(f"Data store contains {len(data.get('inspections', []))} inspections")
    
    if not row_number or not data or 'inspections' not in data:
        logger.warning("No row number or inspection data available")
        return html.Div("No inspection selected for editing")
    
    try:
        # Find the inspection data for the given row number
        inspection = None
        for insp in data['inspections']:
            if str(insp.get('row_number')) == str(row_number):
                inspection = insp
                logger.debug(f"Found matching inspection: {insp.get('row_number')}")
                break
        
        if not inspection:
            logger.warning(f"Inspection with ID {row_number} not found in data store")
            return html.Div([
                html.P(f"Inspection with ID {row_number} not found. This may be because the database was reset."),
                html.P("Please return to the dashboard and try to edit an existing inspection."),
                dbc.Button("Return to Dashboard", href="/dashboard", color="primary", className="mt-2")
            ])
        
        # Create a form pre-filled with the inspection data
        logger.debug(f"Creating form with inspection data: {inspection}")
        
        edit_form = html.Div([
            dbc.Form([
                html.H4("Building Information", className="mt-4"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Function Location ID"),
                        dbc.Input(id="function-location-id", type="text", value=inspection.get('function_location_id', ''), placeholder="Enter Function Location ID")
                    ], width=6),
                    # ... other form fields ...
                ], className="mb-3"),
                # ... Rest of form ...
                
                # Include visible debug information in the form
                html.Div([
                    html.Hr(),
                    html.H5("Debug Information"),
                    html.P(f"Inspection ID: {row_number}"),
                    html.P(f"Row Number: {inspection.get('row_number')}"),
                    html.Pre(json.dumps(inspection, indent=2))
                ], className="mt-4 p-3 bg-light border"),
                
                dbc.Button("Update", id="update-inspection", color="primary", className="mt-4"),
                dbc.Button("Delete", id="delete-inspection", color="danger", className="mt-4 ms-2"),
                html.Div(id="edit-status", className="mt-3")
            ]),
            dcc.Store(id='current-row-number', data=row_number)
        ])
        
        return edit_form
    except Exception as e:
        logger.error(f"Error loading edit form: {traceback.format_exc()}")
        return html.Div([
            html.P(f"Error loading edit form: {str(e)}", className="text-danger"),
            html.Pre(traceback.format_exc()),
            dbc.Button("Return to Dashboard", href="/dashboard", color="primary", className="mt-2")
        ])

# Callback for the update button
def update_inspection(n_clicks, token_data, row_number, *args):
    """Update an inspection record"""
    if n_clicks is None:
        return no_update, no_update
    
    logger.debug(f"Update button clicked for inspection {row_number}")
    
    if not token_data:
        logger.warning("No token data available")
        return html.Div("Session expired. Please log in again.", className="text-danger"), no_update
    
    try:
        # Create a dict with all form values
        form_values = {
            "function_location_id": args[0],
            "sap_function_location": args[1],
            # ... other form fields ...
        }
        
        logger.debug(f"Update data: {form_values}")
        
        # Validate required fields
        required_fields = [
            'function_location_id', 'building_name', 'facility_type', 
            'sprinkler', 'fire_alarm', 'vcp_status', 'full_inspection_completed'
        ]
        
        missing_fields = [field for field in required_fields if not form_values.get(field)]
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return html.Div([
                html.P(f"Please fill in the following required fields:", className="text-danger"),
                html.Ul([html.Li(field.replace('_', ' ').title()) for field in missing_fields])
            ]), no_update
        
        # Use the stored token
        headers = {
            "Authorization": f"Bearer {token_data.get('access_token')}",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Sending PUT request to /inspection/{row_number}")
        response = api_request("PUT", f"/inspection/{row_number}", json=form_values, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Successfully updated inspection {row_number}")
            # Redirect to dashboard after successful update
            return html.Div("Inspection updated successfully!"), "/dashboard"
        else:
            error_msg = response.json().get("detail", "Failed to update inspection.")
            logger.error(f"API error: {error_msg}")
            return html.Div([
                html.P(f"Error: {error_msg}", className="text-danger"),
                html.Pre(f"Status code: {response.status_code}\nResponse: {response.text}")
            ]), no_update
    except Exception as e:
        logger.error(f"Error updating inspection: {traceback.format_exc()}")
        return html.Div([
            html.P(f"An error occurred: {str(e)}", className="text-danger"),
            html.Pre(traceback.format_exc())
        ]), no_update

# Callback for the delete button
def delete_inspection_from_edit(n_clicks, token_data, row_number):
    """Delete an inspection record from edit form"""
    if n_clicks is None:
        raise PreventUpdate
    
    logger.debug(f"Delete button clicked for inspection {row_number}")
    
    if not token_data:
        logger.warning("No token data available")
        return html.Div("Session expired. Please log in again.", className="text-danger"), no_update
    
    try:
        # Use the stored token
        headers = {"Authorization": f"Bearer {token_data.get('access_token')}"}
        
        logger.debug(f"Sending DELETE request to /inspection/{row_number}")
        response = api_request("DELETE", f"/inspection/{row_number}", headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Successfully deleted inspection {row_number}")
            # Redirect to dashboard after successful deletion
            return html.Div("Inspection deleted successfully!"), "/dashboard"
        else:
            error_msg = response.json().get("detail", "Failed to delete inspection.")
            logger.error(f"API error: {error_msg}")
            return html.Div([
                html.P(f"Error: {error_msg}", className="text-danger"),
                html.Pre(f"Status code: {response.status_code}\nResponse: {response.text}")
            ]), no_update
    except Exception as e:
        logger.error(f"Error deleting inspection: {traceback.format_exc()}")
        return html.Div([
            html.P(f"An error occurred: {str(e)}", className="text-danger"),
            html.Pre(traceback.format_exc())
        ]), no_update

# For testing these functions individually
if __name__ == "__main__":
    logger.info("Debug app initializing...")
    # You can add test code here to manually test the functions
