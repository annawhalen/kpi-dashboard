"""
layouts.py
----------
Dashboard layout components.
Defines the full page structure, header KPI cards,
and tab panels for each section of the dashboard.
"""

from dash import dcc, html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from metrics import get_summary_kpis


COLORS = {
    "primary": "#1B4F72",
    "secondary": "#2E86C1",
    "accent": "#27AE60",
    "warning": "#E67E22",
    "danger": "#E74C3C",
    "light": "#EBF5FB",
    "white": "#FFFFFF",
    "gray": "#7F8C8D",
    "dark": "#2C3E50",
}

CARD_STYLE = {
    "backgroundColor": COLORS["white"],
    "borderRadius": "8px",
    "padding": "16px 20px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
    "flex": "1",
    "minWidth": "160px",
    "textAlign": "center",
}

HEADER_STYLE = {
    "backgroundColor": COLORS["primary"],
    "padding": "20px 32px",
    "color": COLORS["white"],
    "marginBottom": "24px",
}


def kpi_card(label: str, value: str, color: str = "#1B4F72") -> html.Div:
    """Single KPI summary card."""
    return html.Div([
        html.P(label, style={
            "margin": "0 0 6px 0",
            "fontSize": "12px",
            "color": COLORS["gray"],
            "fontWeight": "600",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
        }),
        html.H3(value, style={
            "margin": "0",
            "fontSize": "24px",
            "fontWeight": "700",
            "color": color,
        }),
    ], style=CARD_STYLE)


def create_layout(data: dict) -> html.Div:
    """Build the full dashboard layout."""
    kpis = get_summary_kpis(data)

    return html.Div([

        # Header
        html.Div([
            html.H1("Marketplace KPI Dashboard", style={
                "margin": "0 0 4px 0",
                "fontSize": "26px",
                "fontWeight": "700",
            }),
            html.P("Real-time performance metrics across users, revenue, and marketplace health",
                   style={"margin": "0", "opacity": "0.8", "fontSize": "14px"}),
        ], style=HEADER_STYLE),

        # KPI Cards Row
        html.Div([
            kpi_card("DAU", kpis["DAU"]),
            kpi_card("MAU", kpis["MAU"]),
            kpi_card("Stickiness", kpis["Stickiness"], COLORS["accent"]),
            kpi_card("GMV (30d)", kpis["GMV (30d)"], COLORS["accent"]),
            kpi_card("GMV Growth", kpis["GMV Growth MoM"],
                     COLORS["accent"] if "+" in kpis["GMV Growth MoM"] else COLORS["danger"]),
            kpi_card("Avg Order Value", kpis["Avg Order Value"]),
            kpi_card("Conversion Rate", kpis["Conversion Rate"]),
            kpi_card("Repeat Purchase", kpis["Repeat Purchase Rate"]),
            kpi_card("Seller Retention", kpis["Seller Retention"]),
            kpi_card("New Users (30d)", kpis["New Users (30d)"]),
        ], style={
            "display": "flex",
            "flexWrap": "wrap",
            "gap": "12px",
            "padding": "0 32px 24px 32px",
        }),

        # Tabs
        html.Div([
            dcc.Tabs(id="tabs", value="tab-overview", children=[
                dcc.Tab(label="Overview", value="tab-overview"),
                dcc.Tab(label="Funnel", value="tab-funnel"),
                dcc.Tab(label="Retention", value="tab-retention"),
                dcc.Tab(label="Sellers", value="tab-sellers"),
            ], style={"marginBottom": "24px"}),

            html.Div(id="tab-content"),

        ], style={"padding": "0 32px 32px 32px"}),

    ], style={
        "fontFamily": "Inter, Segoe UI, Arial, sans-serif",
        "backgroundColor": "#F4F6F9",
        "minHeight": "100vh",
    })
