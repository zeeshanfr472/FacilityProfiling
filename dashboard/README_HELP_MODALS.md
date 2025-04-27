# Help Modals Implementation

This document explains how the help modals have been implemented in the Facility Checklist application.

## Overview

Help modals provide detailed guidance to users about what information should be entered in each field of the inspection form. Each field has a small "?" button next to its label that, when clicked, opens a modal with detailed field-specific help text.

## Implementation Details

### 1. Help Text Dictionary

The help text for each field is defined in a dictionary called `field_help` at the top of the `app.py` file. This dictionary maps field IDs to their corresponding help titles and descriptions:

```python
field_help = {
    "hvac-type": {
        "title": "HVAC Type",
        "description": """
            Select all types of air conditioning systems present in the facility. You may choose more than one option. 
            If the system type is not listed, select 'Other' and specify the type.
            
            **Options:** Window, Split, Cassette, Duct Concealed, Free Standing, Other.
        """
    },
    # More fields...
}
```

### 2. Help Buttons

Each form field label is paired with a help button that has a unique ID based on the field name:

```python
html.Div([
    dbc.Label("HVAC Type"),
    dbc.Button(
        "?",
        id={"type": "help-button", "field": "hvac-type"},
        color="link",
        size="sm",
        className="ms-1 p-0 text-decoration-none"
    )
], className="d-flex align-items-center")
```

The ID uses Dash's pattern-matching callbacks feature with a dictionary structure:
- `"type": "help-button"` - Identifies this as a help button
- `"field": "hvac-type"` - Identifies which field this help button corresponds to

### 3. Help Modal

A single modal component is defined in the app layout:

```python
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
)
```

### 4. Callback Function

A callback function handles the opening, closing, and content updating of the modal:

```python
@callback(
    [Output("help-modal", "is_open"),
     Output("help-modal-title", "children"),
     Output("help-modal-content", "children")],
    [Input({"type": "help-button", "field": ALL}, "n_clicks"),
     Input("close-help-modal", "n_clicks")],
    [State("help-modal", "is_open")]
)
def toggle_help_modal(help_clicks, close_clicks, is_open):
    # Logic to open the modal and show appropriate content
    # ...
```

This callback:
- Listens for clicks on any help button
- When a help button is clicked, it retrieves the corresponding field ID
- Fetches the title and description from the field_help dictionary
- Opens the modal and updates its content accordingly
- Handles closing the modal when the close button is clicked

### 5. Markdown Support

The help descriptions support Markdown formatting, allowing for:
- Bold text (`**bold**`)
- Bullet points
- Paragraphs
- Other Markdown formatting

This is rendered using the Dash `dcc.Markdown` component.

### 6. Styling

Custom CSS styles have been added in the `assets/custom_styles.css` file to:
- Style the help buttons
- Format the modal content
- Ensure proper alignment of labels and help buttons
- Make the help text more readable with appropriate spacing and font weights

## Adding New Help Text

To add help text for a new field:

1. Add an entry to the `field_help` dictionary with the field's ID
2. Ensure the help button uses the same field ID in its pattern-matching ID
3. The callback will automatically handle the new field

## Customizing the Help Modal

To customize the appearance or behavior of the help modal:

1. Modify the CSS in `assets/custom_styles.css` for styling changes
2. Update the modal component in `app.py` for structural changes
3. Adjust the callback logic for behavioral changes
