"""
metrics.py
----------
KPI calculation functions used across the dashboard.
Each function takes a dataframe and returns a single metric value.
"""

import pandas as pd
import numpy as np


def calc_dau(daily_metrics: pd.DataFrame, days: int = 1) -> int:
    """Average daily active users over the last N days."""
    return int(daily_metrics.tail(days)["dau"].mean())


def calc_wau(events: pd.DataFrame) -> int:
    """Weekly active users — unique users active in the last 7 days."""
    cutoff = events["event_timestamp"].max() - pd.Timedelta(days=7)
    return int(events[events["event_timestamp"] >= cutoff]["user_id"].nunique())


def calc_mau(events: pd.DataFrame) -> int:
    """Monthly active users — unique users active in the last 30 days."""
    cutoff = events["event_timestamp"].max() - pd.Timedelta(days=30)
    return int(events[events["event_timestamp"] >= cutoff]["user_id"].nunique())


def calc_stickiness(daily_metrics: pd.DataFrame, events: pd.DataFrame) -> float:
    """
    DAU/MAU ratio — measures how often monthly users return daily.
    Higher = stickier product.
    """
    dau = calc_dau(daily_metrics, days=7)
    mau = calc_mau(events)
    return round(dau / mau * 100, 1) if mau > 0 else 0.0


def calc_total_gmv(orders: pd.DataFrame, days: int = 30) -> float:
    """Total GMV over the last N days."""
    cutoff = orders["created_at"].max() - pd.Timedelta(days=days)
    completed = orders[
        (orders["status"] == "completed") &
        (orders["created_at"] >= cutoff)
    ]
    return round(completed["gmv"].sum(), 2)


def calc_gmv_growth(orders: pd.DataFrame) -> float:
    """
    Month-over-month GMV growth rate.
    Compares last 30 days to prior 30 days.
    """
    latest = orders["created_at"].max()
    period1_start = latest - pd.Timedelta(days=30)
    period2_start = latest - pd.Timedelta(days=60)

    gmv_current = orders[
        (orders["status"] == "completed") &
        (orders["created_at"] >= period1_start)
    ]["gmv"].sum()

    gmv_prior = orders[
        (orders["status"] == "completed") &
        (orders["created_at"] >= period2_start) &
        (orders["created_at"] < period1_start)
    ]["gmv"].sum()

    if gmv_prior == 0:
        return 0.0
    return round((gmv_current - gmv_prior) / gmv_prior * 100, 1)


def calc_avg_order_value(orders: pd.DataFrame, days: int = 30) -> float:
    """Average order value over the last N days."""
    cutoff = orders["created_at"].max() - pd.Timedelta(days=days)
    completed = orders[
        (orders["status"] == "completed") &
        (orders["created_at"] >= cutoff)
    ]
    return round(completed["gmv"].mean(), 2) if len(completed) > 0 else 0.0


def calc_conversion_rate(funnel_metrics: pd.DataFrame) -> float:
    """Overall conversion rate from page view to purchase."""
    top = funnel_metrics[funnel_metrics["step"] == "Page View"]["users"].values
    bottom = funnel_metrics[funnel_metrics["step"] == "Purchase"]["users"].values
    if len(top) == 0 or top[0] == 0:
        return 0.0
    return round(bottom[0] / top[0] * 100, 2)


def calc_new_users(users: pd.DataFrame, days: int = 30) -> int:
    """Number of new signups in the last N days."""
    cutoff = users["signup_date"].max() - pd.Timedelta(days=days)
    return int((users["signup_date"] >= cutoff).sum())


def calc_repeat_purchase_rate(orders: pd.DataFrame) -> float:
    """
    Percentage of buyers who have made more than one purchase.
    Indicator of product stickiness and buyer satisfaction.
    """
    buyer_counts = (
        orders[orders["status"] == "completed"]
        .groupby("buyer_id")["order_id"]
        .count()
    )
    repeat_buyers = (buyer_counts > 1).sum()
    total_buyers = len(buyer_counts)
    return round(repeat_buyers / total_buyers * 100, 1) if total_buyers > 0 else 0.0


def calc_seller_retention(orders: pd.DataFrame) -> float:
    """
    Percentage of sellers active in the prior 30 days who
    are also active in the most recent 30 days.
    """
    latest = orders["created_at"].max()
    current_start = latest - pd.Timedelta(days=30)
    prior_start = latest - pd.Timedelta(days=60)

    current_sellers = set(
        orders[
            (orders["status"] == "completed") &
            (orders["created_at"] >= current_start)
        ]["seller_id"].unique()
    )

    prior_sellers = set(
        orders[
            (orders["status"] == "completed") &
            (orders["created_at"] >= prior_start) &
            (orders["created_at"] < current_start)
        ]["seller_id"].unique()
    )

    if len(prior_sellers) == 0:
        return 0.0
    retained = len(current_sellers & prior_sellers)
    return round(retained / len(prior_sellers) * 100, 1)


def get_summary_kpis(data: dict) -> dict:
    """
    Compute all summary KPIs for the dashboard header cards.

    Returns
    -------
    dict of KPI name -> value
    """
    orders = data["orders"]
    events = data["events"]
    users = data["users"]
    daily = data["daily_metrics"]
    funnel = data["funnel_metrics"]

    return {
        "DAU": f"{calc_dau(daily, days=7):,}",
        "MAU": f"{calc_mau(events):,}",
        "Stickiness": f"{calc_stickiness(daily, events)}%",
        "GMV (30d)": f"${calc_total_gmv(orders, days=30):,.0f}",
        "GMV Growth MoM": f"{calc_gmv_growth(orders):+.1f}%",
        "Avg Order Value": f"${calc_avg_order_value(orders):,.2f}",
        "Conversion Rate": f"{calc_conversion_rate(funnel)}%",
        "Repeat Purchase Rate": f"{calc_repeat_purchase_rate(orders)}%",
        "Seller Retention": f"{calc_seller_retention(orders)}%",
        "New Users (30d)": f"{calc_new_users(users, days=30):,}",
    }
