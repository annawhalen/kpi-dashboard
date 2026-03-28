"""
app.py
------
Entry point for the KPI dashboard.
Run this file to start the Dash app locally.

Usage:
    pip install -r requirements.txt
    python generate_data.py
    python app.py
"""

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd

from data_loader import load_all_data
from layouts import create_layout
from callbacks import register_callbacks

app = dash.Dash(
    __name__,
    title="Marketplace KPI Dashboard",
    suppress_callback_exceptions=True
)

server = app.server

# Load data on startup
data = load_all_data()

# Set layout
app.layout = create_layout(data)

# Register all callbacks
register_callbacks(app, data)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
