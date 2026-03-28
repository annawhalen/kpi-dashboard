"""
callbacks.py
------------
Dash callback functions for interactive dashboard behavior.
Handles tab switching and chart rendering for each panel.
"""

from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


COLORS = {
    "primary": "#1B4F72",
    "secondary": "#2E86C1",
    "accent": "#27AE60",
    "warning": "#E67E22",
    "danger": "#E74C3C",
    "light": "#EBF5FB",
    "gray": "#7F8C8D",
}

CHART_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Inter, Segoe UI, Arial", size=12),
    margin=dict(t=50, b=40, l=50, r=20),
    xaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
    yaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
)


def register_callbacks(app, data: dict):
    """Register all Dash callbacks with the app."""

    @app.callback(
        Output("tab-content", "children"),
        Input("tabs", "value")
    )
    def render_tab(tab):
        if tab == "tab-overview":
            return render_overview(data)
        elif tab == "tab-funnel":
            return render_funnel(data)
        elif tab == "tab-retention":
            return render_retention(data)
        elif tab == "tab-sellers":
            return render_sellers(data)
        return html.Div("Select a tab")


def chart_card(title: str, figure: go.Figure) -> html.Div:
    """Wrap a plotly figure in a styled card."""
    return html.Div([
        html.H4(title, style={
            "margin": "0 0 12px 0",
            "fontSize": "15px",
            "fontWeight": "600",
            "color": "#2C3E50",
        }),
        dcc.Graph(figure=figure, config={"displayModeBar": False}),
    ], style={
        "backgroundColor": "white",
        "borderRadius": "8px",
        "padding": "20px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
        "marginBottom": "20px",
    })


def render_overview(data: dict) -> html.Div:
    """Overview tab — DAU trend and GMV trend."""
    daily = data["daily_metrics"]

    # DAU trend
    fig_dau = go.Figure()
    fig_dau.add_trace(go.Scatter(
        x=daily["date"], y=daily["dau"],
        mode="lines", name="DAU",
        line=dict(color=COLORS["primary"], width=1.5),
        opacity=0.4,
    ))
    fig_dau.add_trace(go.Scatter(
        x=daily["date"], y=daily["dau_7d_avg"],
        mode="lines", name="7-Day Avg",
        line=dict(color=COLORS["primary"], width=2.5),
    ))
    fig_dau.update_layout(title="Daily Active Users", **CHART_LAYOUT)

    # GMV trend
    fig_gmv = go.Figure()
    fig_gmv.add_trace(go.Bar(
        x=daily["date"], y=daily["total_gmv"],
        name="Daily GMV",
        marker_color=COLORS["secondary"],
        opacity=0.6,
    ))
    fig_gmv.add_trace(go.Scatter(
        x=daily["date"], y=daily["gmv_7d_avg"],
        mode="lines", name="7-Day Avg",
        line=dict(color=COLORS["accent"], width=2.5),
    ))
    fig_gmv.update_layout(title="Daily GMV", **CHART_LAYOUT)

    # Orders trend
    fig_orders = go.Figure()
    fig_orders.add_trace(go.Scatter(
        x=daily["date"], y=daily["total_orders"],
        mode="lines+markers", name="Daily Orders",
        line=dict(color=COLORS["warning"], width=2),
        marker=dict(size=3),
    ))
    fig_orders.update_layout(title="Daily Orders", **CHART_LAYOUT)

    return html.Div([
        chart_card("Daily Active Users", fig_dau),
        chart_card("Daily GMV", fig_gmv),
        chart_card("Daily Orders", fig_orders),
    ])


def render_funnel(data: dict) -> html.Div:
    """Funnel tab — acquisition funnel visualization."""
    funnel = data["funnel_metrics"]

    fig_funnel = go.Figure(go.Funnel(
        y=funnel["step"],
        x=funnel["users"],
        textinfo="value+percent initial",
        marker=dict(color=[
            "#1B4F72", "#2874A6", "#2E86C1", "#3498DB", "#27AE60"
        ]),
    ))
    fig_funnel.update_layout(
        title="Acquisition Funnel",
        paper_bgcolor="white",
        font=dict(family="Inter, Segoe UI, Arial", size=13),
        margin=dict(t=50, b=40, l=150, r=50),
        height=420,
    )

    # Conversion rate bar
    fig_conv = go.Figure(go.Bar(
        x=funnel["step"],
        y=funnel["conversion_pct"],
        marker_color=COLORS["secondary"],
        text=[f"{v}%" for v in funnel["conversion_pct"]],
        textposition="outside",
    ))
    fig_conv.update_layout(
        title="Conversion Rate at Each Step (% of Page Views)",
        yaxis_title="% of Top",
        **CHART_LAYOUT
    )

    return html.Div([
        chart_card("Acquisition Funnel", fig_funnel),
        chart_card("Step Conversion Rates", fig_conv),
    ])


def render_retention(data: dict) -> html.Div:
    """Retention tab — cohort retention heatmap."""
    matrix = data["cohort_matrix"]

    fig_heatmap = go.Figure(go.Heatmap(
        z=matrix.values,
        x=[f"Week {i}" for i in matrix.columns],
        y=matrix.index.tolist(),
        colorscale="Blues",
        text=matrix.values,
        texttemplate="%{text:.1f}%",
        textfont=dict(size=11),
        hoverongaps=False,
        colorbar=dict(title="Retention %"),
    ))
    fig_heatmap.update_layout(
        title="Weekly Cohort Retention Heatmap",
        paper_bgcolor="white",
        font=dict(family="Inter, Segoe UI, Arial", size=12),
        margin=dict(t=50, b=80, l=120, r=20),
        height=500,
        xaxis_title="Weeks Since Signup",
        yaxis_title="Cohort (Signup Week)",
    )

    # Retention curves
    fig_curves = go.Figure()
    palette = px.colors.sequential.Blues[2:]
    for i, (cohort, row) in enumerate(matrix.iterrows()):
        valid = row.dropna()
        color = palette[i % len(palette)]
        fig_curves.add_trace(go.Scatter(
            x=[f"Week {w}" for w in valid.index],
            y=valid.values,
            mode="lines+markers",
            name=str(cohort),
            line=dict(width=2, color=color),
            marker=dict(size=5),
        ))
    fig_curves.update_layout(
        title="Cohort Retention Curves",
        yaxis_title="Retention Rate (%)",
        yaxis=dict(range=[0, 105], gridcolor="#F0F0F0"),
        **{k: v for k, v in CHART_LAYOUT.items() if k != "yaxis"},
    )

    return html.Div([
        chart_card("Cohort Retention Heatmap", fig_heatmap),
        chart_card("Retention Curves by Cohort", fig_curves),
    ])


def render_sellers(data: dict) -> html.Div:
    """Sellers tab — top seller GMV and order volume."""
    sellers = data["seller_metrics"].head(20)

    fig_gmv = go.Figure(go.Bar(
        x=sellers["total_gmv"],
        y=sellers["seller_id"],
        orientation="h",
        marker_color=COLORS["primary"],
        opacity=0.85,
        text=[f"${v:,.0f}" for v in sellers["total_gmv"]],
        textposition="outside",
    ))
    fig_gmv.update_layout(
        title="Top 20 Sellers by GMV",
        xaxis_title="Total GMV ($)",
        yaxis=dict(autorange="reversed"),
        height=550,
        **CHART_LAYOUT,
    )

    fig_scatter = go.Figure(go.Scatter(
        x=sellers["total_orders"],
        y=sellers["total_gmv"],
        mode="markers",
        marker=dict(
            size=sellers["unique_buyers"] / sellers["unique_buyers"].max() * 30 + 6,
            color=sellers["avg_rating"],
            colorscale="RdYlGn",
            showscale=True,
            colorbar=dict(title="Avg Rating"),
            opacity=0.8,
        ),
        text=sellers["seller_id"],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Orders: %{x}<br>"
            "GMV: $%{y:,.0f}<br>"
            "<extra></extra>"
        ),
    ))
    fig_scatter.update_layout(
        title="Seller Performance — Orders vs GMV (bubble size = unique buyers)",
        xaxis_title="Total Orders",
        yaxis_title="Total GMV ($)",
        **CHART_LAYOUT,
    )

    return html.Div([
        chart_card("Top 20 Sellers by GMV", fig_gmv),
        chart_card("Seller Performance Overview", fig_scatter),
    ])
