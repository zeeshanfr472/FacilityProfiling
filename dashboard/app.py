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
API_BASE_URL = os.getenv("API_BASE_URL", "https://facilityprofilingupdated.onrender.com")


# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(
    __name__, 
     requests_pathname_prefix='/dashboard/',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
server = app.server 

# Define app title and metadata
app.title = "Facility Checklist Dashboard"

# Add catch-all route handler for client-side routing
@app.server.route('/<path:path>')
def catch_all(path):
    return app.index_string

# Define field help text dictionary
field_help = {
    "hvac-type": {
        "title": "HVAC Type",
        "description": """
            Select all types of air conditioning systems present in the facility. You may choose more than one option. 
            If the system type is not listed, select 'Other' and specify the type.
            
            **Options:** Window, Split, Cassette, Duct Concealed, Free Standing, Other.
        """
    },
    "sprinkler": {
        "title": "Sprinkler System",
        "description": """
            Is a fire sprinkler system installed in this building? Select 'Yes' if the facility is equipped with a fire 
            sprinkler system for fire protection; select 'No' if it is not.
        """
    },
    "fire-alarm": {
        "title": "Fire Alarm System",
        "description": """
            Is a fire alarm system installed in this building? Select 'Yes' if a fire alarm system is present and 
            operational; select 'No' if there is none.
        """
    },
    "power-source": {
        "title": "Power Source",
        "description": """
            What electrical power sources are available in this building? Select all voltage levels supplied to the building. 
            More than one option may be applicable.
            
            **Examples:** 110V, 220V, 380V, 480V.
        """
    },
    "vcp-status": {
        "title": "VCP Status",
        "description": """
            What is the current status of the VCP (Ventilation Control Program) implementation for this building? Select:
            - 'Completed' if VCP is fully implemented.
            - 'In progress' if implementation is ongoing.
            - 'Not Applicable' if the building is not part of the program.
            - 'Planned' if implementation is scheduled (provide the planned date in the next field).
        """
    },
    "vcp-planned-date": {
        "title": "VCP Planned Date",
        "description": """
            If VCP implementation is planned, what is the scheduled date? Enter the planned start or completion date 
            for the VCP implementation.
        """
    },
    "smart-power-meter-status": {
        "title": "Smart Power Meter Status",
        "description": """
            Is a smart power meter installed in the facility? Select 'Yes' if a smart (digital) power meter is available 
            and functioning; select 'No' if not installed.
        """
    },
    "eifs": {
        "title": "Exterior Insulation Finishing System (EIFS)",
        "description": """
            Is Exterior Insulation Finishing System (EIFS) present? Select 'Yes' if the building uses EIFS 
            (an external wall cladding system for insulation and finish); select 'No' if it does not.
        """
    },
    "eifs-installed-year": {
        "title": "EIFS Installation Year",
        "description": """
            If EIFS is present, in what year was it installed? Enter the year the Exterior Insulation Finishing System 
            was installed. Leave blank if not applicable.
        """
    },
    "exterior-cladding-condition": {
        "title": "Exterior Cladding Condition",
        "description": """
            Rate the condition of the building's exterior wall cladding (EIFS):
            - Poor: Deterioration below 25%
            - Average: 25% to 50% intact
            - Good: 50% to 75% intact
            - Excellent: More than 75% intact
            
            Use visual inspection or records for assessment.
        """
    },
    "interior-architectural-condition": {
        "title": "Interior Architectural Condition",
        "description": """
            Rate the overall condition of interior finishes (paint, gypsum, doors, etc.):
            - Poor: Less than 25% in good shape
            - Average: 25% to 50% in good shape
            - Good: 50% to 75% in good shape
            - Excellent: More than 75% in good shape
            
            Base your answer on the most recent inspection.
        """
    },
    "fire-protection-system-obsolete": {
        "title": "Fire Protection System Obsolete",
        "description": """
            Is the building's fire protection system obsolete? Select 'Obsolete' if the system is outdated and needs 
            replacement or upgrade; otherwise select 'Not Obsolete'.
        """
    },
    "hvac-condition": {
        "title": "HVAC Condition",
        "description": """
            How many HVAC (Heating, Ventilation, and Air Conditioning) units are obsolete or in poor condition? 
            Enter the total number that need replacement or significant repair.
        """
    },
    "electrical-condition": {
        "title": "Electrical Condition",
        "description": """
            How many electrical systems or components are obsolete or in poor condition? Enter the total number that 
            need replacement or significant repair.
        """
    },
    "roofing-condition": {
        "title": "Roofing Condition",
        "description": """
            Rate the water proofing condition of the building's roof:
            - Poor: Major leaks or below 25% effective
            - Average: 25% to 50% effective
            - Good: 50% to 75% effective
            - Excellent: More than 75% effective
            
            Base this on inspection or maintenance records.
        """
    },
    "water-proofing-warranty": {
        "title": "Water Proofing Warranty",
        "description": """
            Does the building have a valid water proofing warranty? Select 'Yes' if there is a current warranty for the 
            roof's water proofing system; select 'No' if not. If 'Yes', provide the expiry date in the next field.
        """
    },
    "water-proofing-warranty-date": {
        "title": "Water Proofing Warranty Date",
        "description": """
            If there is a water proofing warranty, enter its expiry date. Provide the date when the current water proofing 
            warranty expires. Leave blank if not applicable.
        """
    },
    "full-inspection-completed": {
        "title": "Full Inspection Completed",
        "description": """
            Has a complete inspection of the facility been carried out? Select 'Yes' if all inspection requirements have 
            been fully met and documented; select 'No' if the inspection is still pending or incomplete.
        """
    },
    # Basic information fields
    "function-location-id": {
        "title": "Function Location ID",
        "description": """
            Enter the unique functional location identifier for this facility. This should be the standardized ID used 
            in your organization's facility management system.
        """
    },
    "sap-function-location": {
        "title": "SAP Function Location",
        "description": """
            Enter the SAP function location code if applicable. This is used for integration with SAP asset management systems.
        """
    },
    "building-name": {
        "title": "Building Name",
        "description": """
            Enter the official name of the building or facility as it appears in your organization's records.
        """
    },
    "building-number": {
        "title": "Building Number",
        "description": """
            Enter the building number or identifier used in your facility management system.
        """
    },
    "facility-type": {
        "title": "Facility Type",
        "description": """
            Enter the category or type of facility (e.g., Office, Warehouse, Manufacturing, Laboratory, etc.).
        """
    },
    "function": {
        "title": "Function",
        "description": """
            Enter the primary function or purpose of this facility within your organization.
        """
    },
    "macro-area": {
        "title": "Macro Area",
        "description": """
            Enter the broader geographical or organizational area where this facility is located.
        """
    },
    "micro-area": {
        "title": "Micro Area",
        "description": """
            Enter the specific sub-area or section within the macro area where this facility is located.
        """
    },
    "proponent": {
        "title": "Proponent",
        "description": """
            Enter the department, team or individual responsible for this facility.
        """
    },
    "zone": {
        "title": "Zone",
        "description": """
            Enter the zone designation for this facility according to your organization's zoning system.
        """
    },
    "latitude": {
        "title": "Latitude",
        "description": """
            The geographic latitude coordinate of the facility. This will be automatically captured when you click 
            "Refresh Location" if you allow location access in your browser.
        """
    },
    "longitude": {
        "title": "Longitude",
        "description": """
            The geographic longitude coordinate of the facility. This will be automatically captured when you click 
            "Refresh Location" if you allow location access in your browser.
        """
    }
}

# Create the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='token-store', storage_type='local'),
    dcc.Store(id='inspection-data-store', storage_type='memory'),
    html.Div(id='page-content'),
    
    # Add submission notification modal
    dbc.Modal(
        [
            dbc.ModalHeader("Form Submission"),
            dbc.ModalBody([
                html.Div([
                    dbc.Spinner(size="lg", color="primary", type="grow"),
                    html.P("Your data is being uploaded, please wait...", 
                           className="mt-3 text-center")
                ], className="text-center")
            ]),
        ],
        id="submission-modal",
        centered=True,
        is_open=False,
    ),
    
    # Add help modal
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Field Help", id="help-modal-title")),
            dbc.ModalBody(html.Div(id="help-modal-content", className="markdown-content")),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-help-modal", className="ms-auto", n_clicks=0)
            ),
        ],
        id="help-modal",
        size="lg",
        is_open=False,
    ),
])

app.clientside_callback(
    """
    function(n_clicks, field) {
        if (!n_clicks) return window.dash_clientside.no_update;
        
        // Get the help modal elements
        const modal = document.getElementById('help-modal');
        const title = document.getElementById('help-modal-title');
        const content = document.getElementById('help-modal-content');
        
        // Toggle the modal
        if (modal && title && content) {
            // Show the modal
            if (modal.style.display !== 'block') {
                modal.style.display = 'block';
                modal.classList.add('show');
                document.body.classList.add('modal-open');
                
                // Add backdrop
                let backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("help-modal", "is_open", allow_duplicate=True),
    [Input({"type": "help-button", "field": ALL}, "n_clicks")],
    [State({"type": "help-button", "field": ALL}, "id")],
    prevent_initial_call=True
)


# Authentication Components
login_layout = html.Div([
    dbc.Container([
        html.H1("Facility Checklist - Login", className="text-center mt-5 mb-4"),
        dbc.Card([
            dbc.CardBody([
                dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Username", html_for="username-input"),
                            dbc.Input(type="text", id="username-input", placeholder="Enter username")
                        ])
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Password", html_for="password-input"),
                            dbc.Input(type="password", id="password-input", placeholder="Enter password")
                        ])
                    ], className="mb-3"),
                    dbc.Button("Login", id="login-button", color="primary", className="mt-3"),
                    html.Div(id="login-error", className="text-danger mt-2")
                ])
            ])
        ], className="shadow-sm"),
        html.Div([
            html.P("Need an account?"),
            dbc.Button("Register", id="goto-register-button", color="secondary", className="mt-1", href="/register")
        ], className="text-center mt-3")
    ], className="mt-5")
])

register_layout = html.Div([
    dbc.Container([
        html.H1("Facility Checklist - Register", className="text-center mt-5 mb-4"),
        dbc.Card([
            dbc.CardBody([
                dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Username", html_for="register-username-input"),
                            dbc.Input(type="text", id="register-username-input", placeholder="Enter username")
                        ])
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Password", html_for="register-password-input"),
                            dbc.Input(type="password", id="register-password-input", placeholder="Enter password")
                        ])
                    ], className="mb-3"),
                    dbc.Button("Register", id="register-button", color="primary", className="mt-3"),
                    html.Div(id="register-error", className="text-danger mt-2"),
                    html.Div(id="register-success", className="text-success mt-2")
                ])
            ])
        ], className="shadow-sm"),
        html.Div([
            html.P("Already have an account?"),
            dbc.Button("Login", id="goto-login-button", color="secondary", className="mt-1", href="/login")
        ], className="text-center mt-3")
    ], className="mt-5")
])

# Main Dashboard Components
def build_inspection_form():
    """Function to create the inspection form with help buttons"""
    return dbc.Form([
        html.H4("Building Information", className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Function Location ID"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "function-location-id"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="function-location-id", type="text", placeholder="Enter Function Location ID")
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("SAP Function Location"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "sap-function-location"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="sap-function-location", type="text", placeholder="Enter SAP Function Location")
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Building Name"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "building-name"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="building-name", type="text", placeholder="Enter Building Name")
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Building Number"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "building-number"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="building-number", type="text", placeholder="Enter Building Number")
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Facility Type"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "facility-type"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="facility-type", type="text", placeholder="Enter Facility Type")
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Function"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "function"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="function", type="text", placeholder="Enter Function")
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Macro Area"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "macro-area"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="macro-area", type="text", placeholder="Enter Macro Area")
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Micro Area"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "micro-area"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="micro-area", type="text", placeholder="Enter Micro Area")
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Proponent"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "proponent"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="proponent", type="text", placeholder="Enter Proponent")
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Zone"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "zone"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="zone", type="text", placeholder="Enter Zone")
            ], width=6)
        ], className="mb-3"),
        
        html.H4("Building Systems", className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("HVAC Type"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "hvac-type"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Checklist(
                    id="hvac-type",
                    options=[
                        {"label": "Window", "value": "Window"},
                        {"label": "Split", "value": "Split"},
                        {"label": "Cassette", "value": "Cassette"},
                        {"label": "Duct Concealed", "value": "Duct Concealed"},
                        {"label": "Free Standing", "value": "Free Standing"},
                        {"label": "Other", "value": "Other"}
                    ],
                    inline=True
                )
            ], width=12)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Sprinkler"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "sprinkler"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="sprinkler",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    inline=True
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Fire Alarm"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "fire-alarm"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="fire-alarm",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    inline=True
                )
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Power Source"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "power-source"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Checklist(
                    id="power-source",
                    options=[
                        {"label": "110V", "value": "110V"},
                        {"label": "220V", "value": "220V"},
                        {"label": "380V", "value": "380V"},
                        {"label": "480V", "value": "480V"}
                    ],
                    inline=True
                )
            ], width=12)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("VCP Status"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "vcp-status"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Select(
                    id="vcp-status",
                    options=[
                        {"label": "Completed", "value": "Completed"},
                        {"label": "Inprogress", "value": "Inprogress"},
                        {"label": "Not Applicable", "value": "Not Applicable"},
                        {"label": "Planned", "value": "Planned"}
                    ]
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("VCP Planned Date"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "vcp-planned-date"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="vcp-planned-date", type="date")
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Smart Power Meter Status"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "smart-power-meter-status"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="smart-power-meter-status",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    inline=True
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("EIFS"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "eifs"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="eifs",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    inline=True
                )
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("EIFS Installed Year"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "eifs-installed-year"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="eifs-installed-year", type="number", min=1900, max=2100)
            ], width=6)
        ], className="mb-3"),
        
        html.H4("Building Condition", className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Exterior Cladding Condition"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "exterior-cladding-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Select(
                    id="exterior-cladding-condition",
                    options=[
                        {"label": "Poor", "value": "Poor"},
                        {"label": "Average", "value": "Average"},
                        {"label": "Good", "value": "Good"},
                        {"label": "Excellent", "value": "Excellent"}
                    ]
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Interior Architectural Condition"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "interior-architectural-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Select(
                    id="interior-architectural-condition",
                    options=[
                        {"label": "Poor", "value": "Poor"},
                        {"label": "Average", "value": "Average"},
                        {"label": "Good", "value": "Good"},
                        {"label": "Excellent", "value": "Excellent"}
                    ]
                )
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Fire Protection System Obsolete"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "fire-protection-system-obsolete"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="fire-protection-system-obsolete",
                    options=[
                        {"label": "Obsolete", "value": "Obsolete"},
                        {"label": "Not Obsolete", "value": "Not Obsolete"}
                    ],
                    inline=True
                )
            ], width=12)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("HVAC Condition (1-10)"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "hvac-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="hvac-condition", type="number", min=1, max=10)
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Electrical Condition (1-10)"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "electrical-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="electrical-condition", type="number", min=1, max=10)
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Roofing Condition"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "roofing-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Select(
                    id="roofing-condition",
                    options=[
                        {"label": "Poor", "value": "Poor"},
                        {"label": "Average", "value": "Average"},
                        {"label": "Good", "value": "Good"},
                        {"label": "Excellent", "value": "Excellent"}
                    ]
                )
            ], width=6)
        ], className="mb-3"),
        
        html.H4("Additional Information", className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Water Proofing Warranty"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "water-proofing-warranty"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="water-proofing-warranty",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    inline=True
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Water Proofing Warranty Date"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "water-proofing-warranty-date"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="water-proofing-warranty-date", type="date")
            ], width=6)
        ], className="mb-3"),
        
        # Location Information
        dbc.Row([
            dbc.Col([
                dbc.Label("Location Coordinates"),
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dbc.Label("Latitude", className="mb-0"),
                                    dbc.Button(
                                        "?",
                                        id={"type": "help-button", "field": "latitude"},
                                        color="link",
                                        size="sm",
                                        className="ms-1 p-0 text-decoration-none"
                                    )
                                ], className="d-flex align-items-center"),
                                dbc.Input(id="latitude", type="number", step="0.000001", readonly=True),
                            ], width=6),
                            dbc.Col([
                                html.Div([
                                    dbc.Label("Longitude", className="mb-0"),
                                    dbc.Button(
                                        "?",
                                        id={"type": "help-button", "field": "longitude"},
                                        color="link",
                                        size="sm",
                                        className="ms-1 p-0 text-decoration-none"
                                    )
                                ], className="d-flex align-items-center"),
                                dbc.Input(id="longitude", type="number", step="0.000001", readonly=True),
                            ], width=6),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dbc.Button("Refresh Location", id="get-location-button", 
                                            color="secondary", size="sm", className="me-2"),
                                    html.Span(id="location-loading-output", className="text-muted fst-italic small")
                                ], className="d-flex align-items-center")
                            ], width=12)
                        ]),
                    ])
                ], className="mb-3")
            ], width=12)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Full Inspection Completed"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "full-inspection-completed"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="full-inspection-completed",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    inline=True
                )
            ], width=12)
        ], className="mb-3"),
        
        dbc.Button("Submit", id="submit-inspection", color="primary", className="mt-4"),
        html.Div(id="submit-status", className="mt-3")
    ])

# Dashboard layout with navigation
dashboard_layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard", active="exact")),
            dbc.NavItem(dbc.NavLink("Add Inspection", href="/add-inspection")),
            dbc.NavItem(dbc.NavLink("Analytics", href="/analytics")),
            dbc.NavItem(dbc.NavLink("Logout", href="/logout", id="logout-button")),
        ],
        brand="Facility Checklist Dashboard",
        brand_href="/dashboard",
        color="primary",
        dark=True,
    ),
    html.Div(id='dashboard-content')
])

# Dashboard home page
dashboard_home = html.Div([
    dbc.Container([
        html.H1("Facility Inspections", className="my-4"),
        
        # Filter section
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Facility filter
                    dbc.Col([
                        html.Label("Facility"),
                        dbc.Select(
                            id="facility-filter",
                            options=[{"label": "All Facilities", "value": "all"}],
                            value="all",
                        )
                    ], width=12, md=2),
                    
                    # Area filter
                    dbc.Col([
                        html.Label("Area"),
                        dbc.Select(
                            id="area-filter",
                            options=[{"label": "All Areas", "value": "all"}],
                            value="all",
                        )
                    ], width=12, md=2),
                    
                    # Status filter
                    dbc.Col([
                        html.Label("Status"),
                        dbc.Select(
                            id="status-filter",
                            options=[
                                {"label": "All", "value": "all"},
                                {"label": "Completed", "value": "Yes"},
                                {"label": "Not Completed", "value": "No"}
                            ],
                            value="all",
                        )
                    ], width=12, md=2),
                    
                    # Date range filters
                    dbc.Col([
                        html.Label("Start Date"),
                        dbc.Input(id="start-date-filter", type="date")
                    ], width=12, md=2),
                    
                    dbc.Col([
                        html.Label("End Date"),
                        dbc.Input(id="end-date-filter", type="date")
                    ], width=12, md=2),
                    
                    # Filter buttons
                    dbc.Col([
                        html.Div([
                            dbc.Button("Apply", id="apply-filters", color="primary", className="me-2"),
                            dbc.Button("Reset", id="reset-filters", color="secondary")
                        ], className="d-flex align-items-end h-100")
                    ], width=12, md=2),
                ]),
            ])
        ], className="mb-4"),
        
        # Quick Stats Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Quick Stats")),
                    dbc.CardBody(id="quick-stats")
                ], className="mb-4")
            ])
        ]),
        
        # Inspections Table 
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5("Inspections Overview", className="d-inline"),
                            dbc.Button(
                                html.I(className="fas fa-sync-alt"), 
                                id="refresh-table",
                                color="link",
                                className="float-end"
                            )
                        ])
                    ]),
                    dbc.CardBody([
                        html.Div(id="inspections-table-container")
                    ])
                ])
            ])
        ])
    ])
])

# Analytics page
analytics_page = html.Div([
    dbc.Container([
        html.H1("Facility Analytics", className="my-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Facility Condition Overview")),
                    dbc.CardBody(id="condition-chart-container")
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Facility Types")),
                    dbc.CardBody(id="facility-type-chart-container")
                ])
            ], width=6)
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Inspection Completion Status")),
                    dbc.CardBody(id="inspection-status-chart-container")
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Facility Locations")),
                    dbc.CardBody(id="zone-map-container")
                ])
            ], width=6)
        ])
    ])
])

# Add inspection page
add_inspection_page = html.Div([
    dbc.Container([
        html.H1("Add New Inspection", className="my-4"),
        html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Inspection Form")),
                        dbc.CardBody([
                            build_inspection_form()
                        ])
                    ])
                ])
            ])
        ])
    ])
])

# Edit inspection page
edit_inspection_page = html.Div([
    dbc.Container([
        html.H1("Edit Inspection", className="my-4"),
        html.Div(id="edit-form-container")
    ])
])

# Callbacks

# Help button callback to open the modal with appropriate content
# Help button callback to open the modal with appropriate content
# Help button callback to open the modal with appropriate content
@callback(
    [Output("help-modal", "is_open"),
     Output("help-modal-title", "children"),
     Output("help-modal-content", "children")],
    [Input({"type": "help-button", "field": ALL}, "n_clicks")],
    [State("help-modal", "is_open")]
)
def toggle_help_modal(help_clicks, is_open):
    ctx = dash.callback_context
    
    # If no buttons have been clicked yet, return no update
    if not ctx.triggered:
        return no_update, no_update, no_update
    
    # If a help button was clicked
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id and "help-button" in button_id:
        try:
            # Get the field from the triggered prop_id
            triggered_id = json.loads(button_id)
            field = triggered_id["field"]
            
            # Get the help text for this field
            if field in field_help:
                title = field_help[field]["title"]
                content = dcc.Markdown(field_help[field]["description"])
                return True, title, content
        except:
            # If there's any error parsing the button ID, don't update
            pass
    
    # If the close button was clicked or any error occurred
    return is_open, no_update, no_update


# Add a separate callback just for closing the modal
@callback(
    Output("help-modal", "is_open", allow_duplicate=True),
    [Input("close-help-modal", "n_clicks")],
    [State("help-modal", "is_open")],
    prevent_initial_call=True
)
def close_help_modal(n_clicks, is_open):
    if n_clicks:
        return False
    return is_open

# URL routing callback
@callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    # Check local storage for token
    # This is a client-side callback, so we can't directly check the token's validity
    
    if pathname == '/login' or pathname == '/':
        return login_layout
    elif pathname == '/register':
        return register_layout
    elif pathname == '/dashboard':
        return dashboard_layout
    elif pathname == '/add-inspection':
        # Set the dashboard content to the add inspection page
        return html.Div([
            dashboard_layout,
            html.Script("document.getElementById('dashboard-content').innerHTML = '';")
        ])
    elif pathname == '/analytics':
        # Set the dashboard content to the analytics page
        return html.Div([
            dashboard_layout,
            html.Script("document.getElementById('dashboard-content').innerHTML = '';")
        ])
    elif pathname == '/logout':
        # Clear token and redirect to login
        return login_layout
    elif pathname and pathname.startswith('/edit-inspection/'):
        # Extract the row number from the URL
        row_number = pathname.split('/')[-1]
        # Return the dashboard layout with edit form
        return html.Div([
            dashboard_layout,
            html.Script("document.getElementById('dashboard-content').innerHTML = '';"),
            dcc.Store(id='edit-row-number', data=row_number)
        ])
    else:
        return html.H1("404 Page Not Found")

# Set dashboard content based on URL
@callback(
    Output('dashboard-content', 'children'),
    [Input('url', 'pathname')]
)
def set_dashboard_content(pathname):
    if pathname == '/dashboard':
        return dashboard_home
    elif pathname == '/add-inspection':
        return add_inspection_page
    elif pathname == '/analytics':
        return analytics_page
    elif pathname and pathname.startswith('/edit-inspection/'):
        return edit_inspection_page
    else:
        return html.Div()  # Empty div for other routes

# Login callback
@callback(
    [Output('login-error', 'children'),
     Output('url', 'pathname'),
     Output('token-store', 'data')],  # Added this output
    [Input('login-button', 'n_clicks')],
    [State('username-input', 'value'),
     State('password-input', 'value')]
)
def login_user(n_clicks, username, password):
    if n_clicks is None:
        return "", no_update, no_update
    
    if not username or not password:
        return "Please enter both username and password", no_update, no_update
    
    try:
        login_data = {
            "username": username,
            "password": password
        }
        response = requests.post(f"{API_BASE_URL}/login", data=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            # Store token and redirect to dashboard
            return "", "/dashboard", token_data
        else:
            error_msg = response.json().get("detail", "Login failed. Please check your credentials.")
            return error_msg, no_update, no_update
    except Exception as e:
        return f"An error occurred: {str(e)}", no_update, no_update

# Register callback
@callback(
    [Output('register-error', 'children'),
     Output('register-success', 'children')],
    [Input('register-button', 'n_clicks')],
    [State('register-username-input', 'value'),
     State('register-password-input', 'value')]
)
def register_user(n_clicks, username, password):
    if n_clicks is None:
        return "", ""
    
    if not username or not password:
        return "Please enter both username and password", ""
    
    try:
        register_data = {
            "username": username,
            "password": password
        }
        response = requests.post(f"{API_BASE_URL}/register", data=register_data)
        
        if response.status_code == 200:
            return "", "Registration successful! You can now login."
        else:
            error_msg = response.json().get("detail", "Registration failed.")
            return error_msg, ""
    except Exception as e:
        return f"An error occurred: {str(e)}", ""

# Get all inspections and store in memory
@callback(
    Output('inspection-data-store', 'data'),
    [Input('url', 'pathname'),
     Input('token-store', 'data')]
)
def get_inspection_data(pathname, token_data):
    if pathname not in ['/dashboard', '/analytics']:
        return no_update
    
    if not token_data:
        # Return empty data if no token
        return {"inspections": []}
    
    try:
        headers = {"Authorization": f"Bearer {token_data.get('access_token')}"}
        response = requests.get(f"{API_BASE_URL}/inspections", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return {"inspections": []}
    except Exception as e:
        print(f"Error fetching inspections: {str(e)}")
        return {"inspections": []}

# Display quick stats
@callback(
    [Output('facility-filter', 'options'),
     Output('area-filter', 'options')],
    [Input('inspection-data-store', 'data')]
)
def update_filter_options(data):
    if not data or 'inspections' not in data or not data['inspections']:
        return [{"label": "All Facilities", "value": "all"}], [{"label": "All Areas", "value": "all"}]
    
    inspections = data['inspections']
    
    # Get unique facility types
    facility_types = sorted(set(insp.get('facility_type', '') for insp in inspections if insp.get('facility_type')))
    facility_options = [{"label": "All Facilities", "value": "all"}] + [
        {"label": ft, "value": ft} for ft in facility_types
    ]
    
    # Get unique areas (combining macro and micro areas)
    macro_areas = set(insp.get('macro_area', '') for insp in inspections if insp.get('macro_area'))
    micro_areas = set(insp.get('micro_area', '') for insp in inspections if insp.get('micro_area'))
    all_areas = sorted(macro_areas.union(micro_areas))
    area_options = [{"label": "All Areas", "value": "all"}] + [
        {"label": area, "value": area} for area in all_areas
    ]
    
    return facility_options, area_options

@callback(
    [Output('facility-filter', 'value'),
     Output('area-filter', 'value'),
     Output('status-filter', 'value'),
     Output('start-date-filter', 'value'),
     Output('end-date-filter', 'value')],
    [Input('reset-filters', 'n_clicks')]
)
def reset_filters(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    
    return "all", "all", "all", None, None

@callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input('inspections-table', 'active_cell')],
    [State('inspections-table', 'data'),
     State('token-store', 'data')],
    prevent_initial_call=True
)
def handle_table_click(active_cell, data, token_data):
    if not active_cell:
        raise PreventUpdate
    
    # Check if the clicked cell is in the Actions column
    if active_cell['column_id'] == 'row_number':
        row_index = active_cell['row']
        cell_value = data[row_index]['row_number']
        
        # Parse the row number from the markdown link
        if "/edit-inspection/" in cell_value:
            # Extract the row number and navigate to edit page
            row_number = cell_value.split("/edit-inspection/")[1].split(")")[0]
            return f"/edit-inspection/{row_number}"
        elif "#" in cell_value:
            # Handle delete action - will need to trigger a modal or perform delete
            # This could be enhanced to show a confirmation modal
            row_number = cell_value.split("#")[1].split(")")[0]
            # For now, we'll just navigate to a URL that the delete handler can catch
            return f"/delete-inspection/{row_number}"
    
    raise PreventUpdate

# Load inspections table
@callback(
    Output('inspections-table-container', 'children'),
    [Input('inspection-data-store', 'data'),
     Input('apply-filters', 'n_clicks')],
    [State('facility-filter', 'value'),
     State('area-filter', 'value'),
     State('status-filter', 'value'),
     State('start-date-filter', 'value'),
     State('end-date-filter', 'value')]
)
def load_inspections_table(data, n_clicks, facility, area, status, start_date, end_date):
    if not data or 'inspections' not in data or not data['inspections']:
        return html.Div("No inspections found. Add some using the 'Add Inspection' page.")
    
    try:
        inspections = data['inspections']
        
        # Apply filters if they are set
        filtered_inspections = inspections
        if facility and facility != "all":
            filtered_inspections = [i for i in filtered_inspections if i.get('facility_type') == facility]
        if area and area != "all":
            filtered_inspections = [i for i in filtered_inspections if i.get('macro_area') == area or i.get('micro_area') == area]
        if status and status != "all":
            filtered_inspections = [i for i in filtered_inspections if i.get('full_inspection_completed') == status]
        if start_date:
            # Assuming there's a created_date field - adjust if your data uses a different field
            filtered_inspections = [i for i in filtered_inspections if i.get('created_date', '') >= start_date]
        if end_date:
            filtered_inspections = [i for i in filtered_inspections if i.get('created_date', '') <= end_date]
        
        # Create a DataFrame for the table
        df = pd.DataFrame(filtered_inspections)
        
        # Format the data for display
        # Select columns to display
        display_cols = ['function_location_id', 'building_name', 'facility_type', 'full_inspection_completed']
        
        # Create the table
        table = dash_table.DataTable(
            id='inspections-table',
            columns=[
                {"name": "Function Location ID", "id": "function_location_id"},
                {"name": "Building Name", "id": "building_name"},
                {"name": "Facility Type", "id": "facility_type"},
                {"name": "Inspection Completed", "id": "full_inspection_completed"},
                {"name": "Actions", "id": "row_number", "presentation": "markdown"}
            ],
            data=[
                {
                    "function_location_id": row.get('function_location_id', ''),
                    "building_name": row.get('building_name', ''),
                    "facility_type": row.get('facility_type', ''),
                    "full_inspection_completed": row.get('full_inspection_completed', ''),
                    "row_number": f"[Edit](/edit-inspection/{row.get('row_number', '')})"
                }
                for i, row in df.iterrows()
            ],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
                'padding': '10px'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'full_inspection_completed', 'filter_query': '{full_inspection_completed} contains "Yes"'},
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'color': 'green'
                },
                {
                    'if': {'column_id': 'full_inspection_completed', 'filter_query': '{full_inspection_completed} contains "No"'},
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'color': 'red'
                }
            ],
            page_size=10,
            page_current=0,
            sort_action='native',
            filter_action='native',
            row_selectable=False,
            cell_selectable=False
        )
        
        # Calculate pagination info
        total_pages = (len(filtered_inspections) - 1) // 10 + 1
        pagination = html.Div([
            html.Span(f"Page 1 of {total_pages}", id="pagination-info", className="me-3"),
            dbc.ButtonGroup([
                dbc.Button("« First", id="page-first", color="light", size="sm"),
                dbc.Button("‹ Previous", id="page-prev", color="light", size="sm"),
                dbc.Button("Next ›", id="page-next", color="light", size="sm"),
                dbc.Button("Last »", id="page-last", color="light", size="sm"),
            ], className="float-end")
        ], className="mt-3")
        
        return html.Div([table, pagination])
    except Exception as e:
        return html.Div(f"An error occurred loading the table: {str(e)}")
    
# Create visualization charts
@callback(
    [Output('condition-chart-container', 'children'),
     Output('facility-type-chart-container', 'children'),
     Output('inspection-status-chart-container', 'children'),
     Output('zone-map-container', 'children')],
    [Input('inspection-data-store', 'data'),
     Input('url', 'pathname')]
)
def update_analytics_charts(data, pathname):
    if pathname != '/analytics' or not data or 'inspections' not in data:
        return no_update, no_update, no_update, no_update
    
    try:
        inspections = data['inspections']
        if not inspections:
            return (
                html.Div("No data available for visualization"),
                html.Div("No data available for visualization"),
                html.Div("No data available for visualization"),
                html.Div("No data available for visualization")
            )
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(inspections)
        
        # Create charts
        condition_chart = create_condition_chart(df)
        facility_type_chart = create_facility_type_chart(df)
        inspection_status_chart = create_inspection_status_chart(df)
        zone_map = create_zone_map(df)
        
        # Handle cases where some charts couldn't be created
        if condition_chart is None:
            condition_chart = html.Div("Not enough data to create condition chart")
        if facility_type_chart is None:
            facility_type_chart = html.Div("Not enough data to create facility type chart")
        if inspection_status_chart is None:
            inspection_status_chart = html.Div("Not enough data to create inspection status chart")
        if zone_map is None:
            zone_map = html.Div("Not enough location data to create map")
        
        return condition_chart, facility_type_chart, inspection_status_chart, zone_map
    except Exception as e:
        error_msg = html.Div(f"An error occurred generating charts: {str(e)}")
        return error_msg, error_msg, error_msg, error_msg

# Submit inspection callback
@callback(
    [Output('submit-status', 'children'),
     Output('submission-modal', 'is_open')],
    [Input('submit-inspection', 'n_clicks')],
    [State('token-store', 'data'), 
     State('function-location-id', 'value'),
     State('sap-function-location', 'value'),
     State('building-name', 'value'),
     State('building-number', 'value'),
     State('facility-type', 'value'),
     State('function', 'value'),
     State('macro-area', 'value'),
     State('micro-area', 'value'),
     State('proponent', 'value'),
     State('zone', 'value'),
     State('hvac-type', 'value'),
     State('sprinkler', 'value'),
     State('fire-alarm', 'value'),
     State('power-source', 'value'),
     State('vcp-status', 'value'),
     State('vcp-planned-date', 'value'),
     State('smart-power-meter-status', 'value'),
     State('eifs', 'value'),
     State('eifs-installed-year', 'value'),
     State('exterior-cladding-condition', 'value'),
     State('interior-architectural-condition', 'value'),
     State('fire-protection-system-obsolete', 'value'),
     State('hvac-condition', 'value'),
     State('electrical-condition', 'value'),
     State('roofing-condition', 'value'),
     State('water-proofing-warranty', 'value'),
     State('water-proofing-warranty-date', 'value'),
     State('full-inspection-completed', 'value'),
     State('latitude', 'value'),
     State('longitude', 'value')]
)
def submit_inspection(n_clicks, token_data, *args):
    if n_clicks is None:
        return "", False
     # Show the modal immediately when button is clicked
    if dash.callback_context.triggered[0]['prop_id'] == 'submit-inspection.n_clicks':
    
        if not token_data:
            return html.Div("Session expired. Please log in again.", className="text-danger"), False
        
        # Create a dict with all form values
        form_values = {
            "function_location_id": args[0],
            "sap_function_location": args[1],
            "building_name": args[2],
            "building_number": args[3],
            "facility_type": args[4],
            "function": args[5],
            "macro_area": args[6],
            "micro_area": args[7],
            "proponent": args[8],
            "zone": args[9],
            "hvac_type": args[10] or [],
            "sprinkler": args[11],
            "fire_alarm": args[12],
            "power_source": args[13] or [],
            "vcp_status": args[14],
            "vcp_planned_date": args[15],
            "smart_power_meter_status": args[16],
            "eifs": args[17],
            "eifs_installed_year": args[18],
            "exterior_cladding_condition": args[19],
            "interior_architectural_condition": args[20],
            "fire_protection_system_obsolete": args[21],
            "hvac_condition": args[22],
            "electrical_condition": args[23],
            "roofing_condition": args[24],
            "water_proofing_warranty": args[25],
            "water_proofing_warranty_date": args[26],
            "full_inspection_completed": args[27],
            "latitude": args[28],
            "longitude": args[29]
        }
        
        # Validate required fields
        required_fields = [
            'function_location_id', 'building_name', 'facility_type', 
            'sprinkler', 'fire_alarm', 'vcp_status', 'full_inspection_completed'
        ]
        
        missing_fields = [field for field in required_fields if not form_values.get(field)]
        if missing_fields:
            return html.Div([
                html.P(f"Please fill in the following required fields:", className="text-danger"),
                html.Ul([html.Li(field.replace('_', ' ').title()) for field in missing_fields])
            ]), False
        
        try:
            # Use the stored token
            headers = {
                "Authorization": f"Bearer {token_data.get('access_token')}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/inspection",
                json=form_values,
                headers=headers
            )
            
            if response.status_code == 200:
                    return html.Div([
                        html.P("Inspection submitted successfully!", className="text-success"),
                        dbc.Button("View All Inspections", href="/dashboard", color="primary", className="mt-2")
                    ]), False
            else:
                error_msg = response.json().get("detail", "Failed to submit inspection.")
                return html.Div(f"Error: {error_msg}", className="text-danger"), False
        except Exception as e:
            return html.Div(f"An error occurred: {str(e)}", className="text-danger"), False
    return "", False

@callback(
    Output('submission-modal', 'is_open', allow_duplicate=True),
    [Input('submit-inspection', 'n_clicks')],
    prevent_initial_call=True
)
def show_modal_on_submit(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    return True

def create_edit_form(inspection):
    """Create a complete edit form with all fields"""
    return dbc.Form([
        html.H4("Building Information", className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Function Location ID"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "function-location-id"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="function-location-id", type="text", value=inspection.get('function_location_id', ''))
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("SAP Function Location"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "sap-function-location"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="sap-function-location", type="text", value=inspection.get('sap_function_location', ''))
            ], width=6)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Building Name"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "building-name"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="building-name", type="text", value=inspection.get('building_name', ''))
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Building Number"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "building-number"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="building-number", type="text", value=inspection.get('building_number', ''))
            ], width=6)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Facility Type"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "facility-type"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="facility-type", type="text", value=inspection.get('facility_type', ''))
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Function"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "function"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="function", type="text", value=inspection.get('function', ''))
            ], width=6)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Macro Area"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "macro-area"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="macro-area", type="text", value=inspection.get('macro_area', ''))
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Micro Area"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "micro-area"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="micro-area", type="text", value=inspection.get('micro_area', ''))
            ], width=6)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Proponent"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "proponent"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="proponent", type="text", value=inspection.get('proponent', ''))
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Zone"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "zone"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="zone", type="text", value=inspection.get('zone', ''))
            ], width=6)
        ], className="mb-3"),
        
        html.H4("Building Systems", className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("HVAC Type"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "hvac-type"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Checklist(
                    id="hvac-type",
                    options=[
                        {"label": "Window", "value": "Window"},
                        {"label": "Split", "value": "Split"},
                        {"label": "Cassette", "value": "Cassette"},
                        {"label": "Duct Concealed", "value": "Duct Concealed"},
                        {"label": "Free Standing", "value": "Free Standing"},
                        {"label": "Other", "value": "Other"}
                    ],
                    value=inspection.get('hvac_type', []),
                    inline=True
                )
            ], width=12)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Sprinkler"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "sprinkler"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="sprinkler",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    value=inspection.get('sprinkler', ''),
                    inline=True
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Fire Alarm"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "fire-alarm"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="fire-alarm",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    value=inspection.get('fire_alarm', ''),
                    inline=True
                )
            ], width=6)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Power Source"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "power-source"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Checklist(
                    id="power-source",
                    options=[
                        {"label": "110V", "value": "110V"},
                        {"label": "220V", "value": "220V"},
                        {"label": "380V", "value": "380V"},
                        {"label": "480V", "value": "480V"}
                    ],
                    value=inspection.get('power_source', []),
                    inline=True
                )
            ], width=12)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("VCP Status"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "vcp-status"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Select(
                    id="vcp-status",
                    options=[
                        {"label": "Completed", "value": "Completed"},
                        {"label": "Inprogress", "value": "Inprogress"},
                        {"label": "Not Applicable", "value": "Not Applicable"},
                        {"label": "Planned", "value": "Planned"}
                    ],
                    value=inspection.get('vcp_status', '')
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("VCP Planned Date"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "vcp-planned-date"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="vcp-planned-date", type="date", value=inspection.get('vcp_planned_date', ''))
            ], width=6)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Smart Power Meter Status"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "smart-power-meter-status"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="smart-power-meter-status",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    value=inspection.get('smart_power_meter_status', ''),
                    inline=True
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("EIFS"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "eifs"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="eifs",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    value=inspection.get('eifs', ''),
                    inline=True
                )
            ], width=6)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("EIFS Installed Year"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "eifs-installed-year"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="eifs-installed-year", type="number", min=1900, max=2100, value=inspection.get('eifs_installed_year', ''))
            ], width=6)
        ], className="mb-3"),
        
        html.H4("Building Condition", className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Exterior Cladding Condition"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "exterior-cladding-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Select(
                    id="exterior-cladding-condition",
                    options=[
                        {"label": "Poor", "value": "Poor"},
                        {"label": "Average", "value": "Average"},
                        {"label": "Good", "value": "Good"},
                        {"label": "Excellent", "value": "Excellent"}
                    ],
                    value=inspection.get('exterior_cladding_condition', '')
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Interior Architectural Condition"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "interior-architectural-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Select(
                    id="interior-architectural-condition",
                    options=[
                        {"label": "Poor", "value": "Poor"},
                        {"label": "Average", "value": "Average"},
                        {"label": "Good", "value": "Good"},
                        {"label": "Excellent", "value": "Excellent"}
                    ],
                    value=inspection.get('interior_architectural_condition', '')
                )
            ], width=6)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Fire Protection System Obsolete"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "fire-protection-system-obsolete"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="fire-protection-system-obsolete",
                    options=[
                        {"label": "Obsolete", "value": "Obsolete"},
                        {"label": "Not Obsolete", "value": "Not Obsolete"}
                    ],
                    value=inspection.get('fire_protection_system_obsolete', ''),
                    inline=True
                )
            ], width=12)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("HVAC Condition (1-10)"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "hvac-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="hvac-condition", type="number", min=1, max=10, value=inspection.get('hvac_condition', ''))
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Electrical Condition (1-10)"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "electrical-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="electrical-condition", type="number", min=1, max=10, value=inspection.get('electrical_condition', ''))
            ], width=6)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Roofing Condition"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "roofing-condition"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Select(
                    id="roofing-condition",
                    options=[
                        {"label": "Poor", "value": "Poor"},
                        {"label": "Average", "value": "Average"},
                        {"label": "Good", "value": "Good"},
                        {"label": "Excellent", "value": "Excellent"}
                    ],
                    value=inspection.get('roofing_condition', '')
                )
            ], width=6)
        ], className="mb-3"),
        
        html.H4("Additional Information", className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Water Proofing Warranty"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "water-proofing-warranty"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="water-proofing-warranty",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    value=inspection.get('water_proofing_warranty', ''),
                    inline=True
                )
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Label("Water Proofing Warranty Date"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "water-proofing-warranty-date"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.Input(id="water-proofing-warranty-date", type="date", value=inspection.get('water_proofing_warranty_date', ''))
            ], width=6)
        ], className="mb-3"),
        
        # Location Information
        dbc.Row([
            dbc.Col([
                dbc.Label("Location Coordinates"),
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dbc.Label("Latitude", className="mb-0"),
                                    dbc.Button(
                                        "?",
                                        id={"type": "help-button", "field": "latitude"},
                                        color="link",
                                        size="sm",
                                        className="ms-1 p-0 text-decoration-none"
                                    )
                                ], className="d-flex align-items-center"),
                                dbc.Input(id="latitude", type="number", step="0.000001", value=inspection.get('latitude', '')),
                            ], width=6),
                            dbc.Col([
                                html.Div([
                                    dbc.Label("Longitude", className="mb-0"),
                                    dbc.Button(
                                        "?",
                                        id={"type": "help-button", "field": "longitude"},
                                        color="link",
                                        size="sm",
                                        className="ms-1 p-0 text-decoration-none"
                                    )
                                ], className="d-flex align-items-center"),
                                dbc.Input(id="longitude", type="number", step="0.000001", value=inspection.get('longitude', '')),
                            ], width=6),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dbc.Button("Refresh Location", id="get-location-button", 
                                            color="secondary", size="sm", className="me-2"),
                                    html.Span(id="location-loading-output", className="text-muted fst-italic small")
                                ], className="d-flex align-items-center")
                            ], width=12)
                        ]),
                    ])
                ], className="mb-3")
            ], width=12)
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Label("Full Inspection Completed"),
                    dbc.Button(
                        "?",
                        id={"type": "help-button", "field": "full-inspection-completed"},
                        color="link",
                        size="sm",
                        className="ms-1 p-0 text-decoration-none"
                    )
                ], className="d-flex align-items-center"),
                dbc.RadioItems(
                    id="full-inspection-completed",
                    options=[
                        {"label": "Yes", "value": "Yes"},
                        {"label": "No", "value": "No"}
                    ],
                    value=inspection.get('full_inspection_completed', ''),
                    inline=True
                )
            ], width=12)
        ], className="mb-3"),
        
        # Buttons
        dbc.Button("Update Inspection", id="update-inspection", color="primary", className="mt-4"),
        dbc.Button("Delete Inspection", id="delete-inspection", color="danger", className="mt-4 ms-2"),
        dbc.Button("Cancel", href="/dashboard", color="secondary", className="mt-4 ms-2"),
        html.Div(id="edit-status", className="mt-3")
    ])

# Load the edit form
@callback(
    Output('edit-form-container', 'children'),
    [Input('edit-row-number', 'data')],
    [State('token-store', 'data')]
)
def load_edit_form(row_number, token_data):
    """Load and populate the edit form for an existing inspection"""
    if not row_number or not token_data:
        return html.Div("No inspection selected for editing", className="text-danger")
    
    try:
        # Get the inspection data from the API
        headers = {"Authorization": f"Bearer {token_data.get('access_token')}"}
        response = requests.get(f"{API_BASE_URL}/inspections", headers=headers)
        
        if response.status_code != 200:
            return html.Div("Failed to fetch inspection data", className="text-danger")
        
        data = response.json()
        
        # Find the inspection with the matching row number
        inspection = None
        for insp in data.get('inspections', []):
            if str(insp.get('row_number')) == str(row_number):
                inspection = insp
                break
        
        if not inspection:
            return html.Div(f"Inspection #{row_number} not found", className="text-danger")
        
        # Convert comma-separated strings to lists if needed
        if isinstance(inspection.get('hvac_type', ''), str):
            inspection['hvac_type'] = [x.strip() for x in inspection['hvac_type'].split(',') if x.strip()]
        if isinstance(inspection.get('power_source', ''), str):
            inspection['power_source'] = [x.strip() for x in inspection['power_source'].split(',') if x.strip()]
        
        # Use the create_edit_form function to generate a complete form with all fields
        return html.Div([
            create_edit_form(inspection),
            dcc.Store(id='current-row-number', data=row_number)
        ])
        
    except Exception as e:
        return html.Div(f"Error loading edit form: {str(e)}", className="text-danger")

# Update inspection callback
@callback(
    [Output('edit-status', 'children'),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('update-inspection', 'n_clicks')],
    [State('token-store', 'data'),
     State('current-row-number', 'data'),
     # All the field states here
     State('function-location-id', 'value'),
     State('sap-function-location', 'value'),
     State('building-name', 'value'),
     State('building-number', 'value'),
     State('facility-type', 'value'),
     State('function', 'value'),
     State('macro-area', 'value'),
     State('micro-area', 'value'),
     State('proponent', 'value'),
     State('zone', 'value'),
     State('hvac-type', 'value'),
     State('sprinkler', 'value'),
     State('fire-alarm', 'value'),
     State('power-source', 'value'),
     State('vcp-status', 'value'),
     State('vcp-planned-date', 'value'),
     State('smart-power-meter-status', 'value'),
     State('eifs', 'value'),
     State('eifs-installed-year', 'value'),
     State('exterior-cladding-condition', 'value'),
     State('interior-architectural-condition', 'value'),
     State('fire-protection-system-obsolete', 'value'),
     State('hvac-condition', 'value'),
     State('electrical-condition', 'value'),
     State('roofing-condition', 'value'),
     State('water-proofing-warranty', 'value'),
     State('water-proofing-warranty-date', 'value'),
     State('full-inspection-completed', 'value'),
     State('latitude', 'value'),
     State('longitude', 'value')],
    prevent_initial_call=True
)
def update_inspection(n_clicks, token_data, row_number, *args):
    if n_clicks is None or not n_clicks:
        raise PreventUpdate
    
    if not token_data or not row_number:
        return html.Div("Session expired or missing data. Please log in again.", className="text-danger"), no_update
    
    # Create a dict with form values (same as in the create function)
    form_values = {
        "function_location_id": args[0],
        "sap_function_location": args[1],
        "building_name": args[2],
        "building_number": args[3],
        "facility_type": args[4],
        "function": args[5],
        "macro_area": args[6],
        "micro_area": args[7],
        "proponent": args[8],
        "zone": args[9],
        "hvac_type": args[10] or [],
        "sprinkler": args[11],
        "fire_alarm": args[12],
        "power_source": args[13] or [],
        "vcp_status": args[14],
        "vcp_planned_date": args[15],
        "smart_power_meter_status": args[16],
        "eifs": args[17],
        "eifs_installed_year": args[18],
        "exterior_cladding_condition": args[19],
        "interior_architectural_condition": args[20],
        "fire_protection_system_obsolete": args[21],
        "hvac_condition": args[22],
        "electrical_condition": args[23],
        "roofing_condition": args[24],
        "water_proofing_warranty": args[25],
        "water_proofing_warranty_date": args[26],
        "full_inspection_completed": args[27],
        "latitude": args[28],
        "longitude": args[29]
    }
    
    # Validate required fields
    required_fields = [
        'function_location_id', 'building_name', 'facility_type', 
        'sprinkler', 'fire_alarm', 'vcp_status', 'full_inspection_completed'
    ]
    
    missing_fields = [field for field in required_fields if not form_values.get(field)]
    if missing_fields:
        return html.Div([
            html.P(f"Please fill in the following required fields:", className="text-danger"),
            html.Ul([html.Li(field.replace('_', ' ').title()) for field in missing_fields])
        ]), no_update
    
    try:
        # Use the stored token
        headers = {
            "Authorization": f"Bearer {token_data.get('access_token')}",
            "Content-Type": "application/json"
        }
        
        response = requests.put(
            f"{API_BASE_URL}/inspection/{row_number}",
            json=form_values,
            headers=headers
        )
        
        if response.status_code == 200:
            # Redirect to dashboard after successful update
            return html.Div("Inspection updated successfully!", className="text-success"), "/dashboard"
        else:
            error_msg = response.json().get("detail", "Failed to update inspection.")
            return html.Div(f"Error: {error_msg}", className="text-danger"), no_update
    except Exception as e:
        return html.Div(f"An error occurred: {str(e)}", className="text-danger"), no_update

# Delete inspection callback
@callback(
    [Output('edit-status', 'children', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('delete-inspection', 'n_clicks')],
    [State('token-store', 'data'),
     State('current-row-number', 'data')],
    prevent_initial_call=True
)
def delete_inspection(n_clicks, token_data, row_number):
    if n_clicks is None or not n_clicks:
        raise PreventUpdate
    
    if not token_data or not row_number:
        return html.Div("Session expired or missing data. Please log in again.", className="text-danger"), no_update
    
    try:
        # Use the stored token
        headers = {"Authorization": f"Bearer {token_data.get('access_token')}"}
        response = requests.delete(
            f"{API_BASE_URL}/inspection/{row_number}",
            headers=headers
        )
        
        if response.status_code == 200:
            # Redirect to dashboard after successful deletion
            return html.Div("Inspection deleted successfully!", className="text-success"), "/dashboard"
        else:
            error_msg = response.json().get("detail", "Failed to delete inspection.")
            return html.Div(f"Error: {error_msg}", className="text-danger"), no_update
    except Exception as e:
        return html.Div(f"An error occurred: {str(e)}", className="text-danger"), no_update

# Logout callback
@callback(
    [Output('token-store', 'clear_data'),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('logout-button', 'n_clicks')],
    prevent_initial_call=True
)
def logout(n_clicks):
    if n_clicks is None:
        return no_update, no_update
    
    # Clear token and redirect to login
    return True, '/login'

# Auto-detect location on page load
@callback(
    Output('location-loading-output', 'children'),
    [Input('url', 'pathname')]
)
def auto_get_location(pathname):
    """Automatically detect location when the inspection form loads"""
    if pathname == '/add-inspection':
        return "Location detection will start when you open the page..."
    return ""

# First clientside callback for route protection
app.clientside_callback(
    """
    function(pathname, token) {
        // Protected routes
        const protectedRoutes = ['/dashboard', '/add-inspection', '/analytics', '/edit-inspection'];
        // Check if current path is protected
        const isProtected = protectedRoutes.some(route => pathname.startsWith(route));
        
        if (isProtected && !token) {
            // Redirect to login if no token
            return '/login';
        }
        return pathname;
    }
    """,
    Output('url', 'pathname', allow_duplicate=True),
    [Input('url', 'pathname'),
     Input('token-store', 'data')],
    prevent_initial_call=True
)

# Second clientside callback for geolocation
app.clientside_callback(
    """
    function(pathname) {
        // Function to get location
        function getLocation() {
            var loadingEl = document.getElementById('location-loading-output');
            
            if (loadingEl) {
                loadingEl.innerText = "Getting your location...";
            }
            
            if (!navigator.geolocation) {
                if (loadingEl) {
                    loadingEl.innerText = "Geolocation is not supported by your browser";
                }
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    // Success
                    var latEl = document.getElementById('latitude');
                    var lonEl = document.getElementById('longitude');
                    
                    if (latEl && position.coords.latitude) {
                        latEl.value = position.coords.latitude;
                    }
                    
                    if (lonEl && position.coords.longitude) {
                        lonEl.value = position.coords.longitude;
                    }
                    
                    if (loadingEl) {
                        loadingEl.innerText = "✓ Location captured! Coordinates updated.";
                    }
                },
                function(error) {
                    // Error
                    console.error('Error getting location:', error);
                    if (loadingEl) {
                        loadingEl.innerText = "Error getting location: " + error.message;
                    }
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        }
        
        // Auto-detect location on add inspection page
        if (pathname === '/add-inspection') {
            // Wait a moment for the elements to be rendered
            setTimeout(getLocation, 1000);
        }
        
        return pathname;
    }
    """,
    Output('url', 'pathname', allow_duplicate=True),
    [Input('url', 'pathname')],
    prevent_initial_call=True
)

# Handle location button click
app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update, ''];
        }
        
        let loadingMessage = 'Getting your location...';
        
        // Check if geolocation is available
        if (!navigator.geolocation) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update, 'Geolocation is not supported by your browser'];
        }
        
        return new Promise(function(resolve, reject) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    // Success
                    resolve([
                        position.coords.latitude,
                        position.coords.longitude,
                        'Location successfully captured!'
                    ]);
                },
                function(error) {
                    // Error
                    console.error('Error getting location:', error);
                    resolve([
                        window.dash_clientside.no_update,
                        window.dash_clientside.no_update,
                        'Error getting location: ' + error.message
                    ]);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        });
    }
    """,
    [Output("latitude", "value"),
     Output("longitude", "value"),
     Output("location-loading-output", "children", allow_duplicate=True)],  # Added allow_duplicate=True
    [Input("get-location-button", "n_clicks")],
    prevent_initial_call=True
)

# Add CSS for styling the help modal content
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Add custom styles for the modals */
            .markdown-content {
                line-height: 1.6;
            }
            .markdown-content p {
                margin-bottom: 1rem;
            }
            .markdown-content strong {
                font-weight: 600;
            }
            
            /* Style for help buttons */
            .help-btn {
                width: 20px;
                height: 20px;
                padding: 0;
                border-radius: 50%;
                font-size: 12px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-left: 5px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
