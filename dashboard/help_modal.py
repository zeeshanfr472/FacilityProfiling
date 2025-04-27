"""
Help modal component for the facility checklist application.
This provides detailed guidance for users when filling the form.
"""

import dash_bootstrap_components as dbc
from dash import html

# Dictionary of field help texts
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

def create_help_modal():
    """Create the help modal component"""
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Help", id="help-modal-title")),
            dbc.ModalBody(html.Div(id="help-modal-content")),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-help-modal", className="ms-auto", n_clicks=0)
            ),
        ],
        id="help-modal",
        size="lg",
        is_open=False,
    )

def get_help_buttons():
    """Create a dictionary of help buttons for each field"""
    help_buttons = {}
    
    for field_id in field_help.keys():
        help_buttons[field_id] = dbc.Button(
            "?",
            id={"type": "help-button", "field": field_id},
            className="ms-2 rounded-circle",
            color="light",
            size="sm",
            style={"width": "24px", "height": "24px", "padding": "0", "font-weight": "bold"}
        )
    
    return help_buttons
