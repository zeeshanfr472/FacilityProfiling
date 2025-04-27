import dash
from dash import dcc, html, Input, Output, State, callback, no_update, dash_table, ALL
import dash_bootstrap_components as dbc
import requests
import json
from datetime import datetime
import pandas as pd
import os
from dash.exceptions import PreventUpdate
from dashboard.visualization import (
    create_condition_chart,
    create_facility_type_chart,
    create_inspection_status_chart,
    create_zone_map,
)

# Get the API URL from environment variable
API_BASE_URL = os.getenv("API_BASE_URL", "")

# If API_BASE_URL is not set in environment, set a default based on current app URL
if not API_BASE_URL:
    API_BASE_URL = ""

# First, configure the Dash app to use the correct requests_pathname_prefix
# This makes it flexible for both local development and deployment
requests_pathname_prefix = os.getenv("DASH_PATHNAME_PREFIX", "/dashboard/")

app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    requests_pathname_prefix=requests_pathname_prefix
)

# Define app title and metadata
app.title = "Facility Checklist Dashboard"

# Add catch-all route handling to handle both root and dashboard prefix
@app.server.route('/', defaults={'path': ''})
@app.server.route('/<path:path>')
def catch_all(path):
    return app.index_string

# Rest of the file remains the same