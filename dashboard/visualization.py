import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
import pandas as pd
import numpy as np

def create_condition_chart(df):
    """Create a radar chart showing average condition metrics"""
    # Extract condition metrics
    condition_cols = [
        'exterior_cladding_condition', 
        'interior_architectural_condition',
        'hvac_condition',
        'electrical_condition',
        'roofing_condition'
    ]
    
    # Map text values to numeric for radar chart
    condition_map = {
        'Poor': 1,
        'Average': 2,
        'Good': 3,
        'Excellent': 4
    }
    
    # Create a copy to avoid modifying original data
    chart_data = df.copy()
    
    # Convert text conditions to numeric
    for col in ['exterior_cladding_condition', 'interior_architectural_condition', 'roofing_condition']:
        if col in chart_data.columns:
            chart_data[col] = chart_data[col].map(lambda x: condition_map.get(x, 0) if pd.notna(x) else 0)
    
    # Calculate averages, handling both numeric and text conditions
    condition_avgs = {}
    for col in condition_cols:
        if col in chart_data.columns:
            vals = pd.to_numeric(chart_data[col], errors='coerce')
            condition_avgs[col.replace('_condition', '').replace('_', ' ').title()] = vals.mean()
    
    # Create radar chart
    fig = go.Figure()
    
    categories = list(condition_avgs.keys())
    values = list(condition_avgs.values())
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Average Condition'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 4 if any(v > 3 for v in values) else 3]
            )
        ),
        showlegend=False,
        title="Facility Condition Overview"
    )
    
    return dcc.Graph(figure=fig)

def create_facility_type_chart(df):
    """Create a pie chart showing distribution of facility types"""
    if 'facility_type' not in df.columns:
        return None
    
    # Count facility types
    type_counts = df['facility_type'].value_counts().reset_index()
    type_counts.columns = ['Facility Type', 'Count']
    
    fig = px.pie(
        type_counts, 
        values='Count', 
        names='Facility Type',
        title='Facility Types Distribution',
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
    
    return dcc.Graph(figure=fig)

def create_inspection_status_chart(df):
    """Create a bar chart showing inspection completion status"""
    if 'full_inspection_completed' not in df.columns:
        return None
    
    # Count inspection statuses
    status_counts = df['full_inspection_completed'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Sort to always have "Yes" first
    status_counts = status_counts.sort_values('Status', ascending=False)
    
    fig = px.bar(
        status_counts,
        x='Status',
        y='Count',
        color='Status',
        title='Inspection Completion Status',
        color_discrete_map={'Yes': '#28a745', 'No': '#dc3545'}
    )
    
    fig.update_layout(
        xaxis_title=None,
        yaxis_title='Number of Facilities',
        showlegend=False
    )
    
    return dcc.Graph(figure=fig)

def create_zone_map(df):
    """Create a map visualization of facilities by zone"""
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        return None
    
    # Remove rows with missing coordinates
    map_data = df.dropna(subset=['latitude', 'longitude']).copy()
    
    if len(map_data) == 0:
        return None
    
    # Convert to numeric
    map_data['latitude'] = pd.to_numeric(map_data['latitude'], errors='coerce')
    map_data['longitude'] = pd.to_numeric(map_data['longitude'], errors='coerce')
    
    # Drop invalid coordinates
    map_data = map_data.dropna(subset=['latitude', 'longitude'])
    
    # Create hover text
    map_data['hover_text'] = map_data.apply(
        lambda row: f"<b>{row.get('building_name', 'Unknown')}</b><br>" +
                    f"Facility Type: {row.get('facility_type', 'Unknown')}<br>" +
                    f"Zone: {row.get('zone', 'Unknown')}<br>" +
                    f"Completed: {row.get('full_inspection_completed', 'Unknown')}",
        axis=1
    )
    
    fig = px.scatter_mapbox(
        map_data,
        lat='latitude',
        lon='longitude',
        hover_name='building_name',
        hover_data={
            'latitude': False,
            'longitude': False,
            'building_name': False,
            'facility_type': True,
            'zone': True
        },
        color='zone',
        color_discrete_sequence=px.colors.qualitative.Safe,
        zoom=10,
        title='Facility Locations by Zone'
    )
    
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        legend_title_text='Zone'
    )
    
    return dcc.Graph(figure=fig)