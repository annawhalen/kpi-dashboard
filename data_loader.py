"""
data_loader.py
--------------
Loads and preprocesses data for the KPI dashboard.
Computes all metrics used across dashboard panels.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def load_all_data() -> dict:
    """
    Load raw data and compute all KPI metrics.

    Returns
    -------
    dict with keys:
        - orders
        - events
        - users
        - daily_metrics
        - funnel_metrics
        - seller_metrics
        - cohort_matrix
    """
    try:
        orders = pd.read_csv("data/orders.csv", parse_dates=["created_at"])
        events = pd.read_csv("data/marketplace_events.csv", parse_dates=["event_timestamp"])
        users = pd.read_csv("data/users.csv", parse_dates=["signup_date"])
    except FileNotFoundError:
        print("Data files not found. Run generate_data.py first.")
        return {}

    return {
        "orders": orders,
        "events": events,
        "users": users,
        "daily_metrics": compute_daily_metrics(orders, events),
        "funnel_metrics": compute_funnel_metrics(events),
        "seller_metrics": compute_seller_metrics(orders),
        "cohort_matrix": compute_cohort_matrix(events, users),
    }


def compute_daily_metrics(orders: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Compute daily active users, GMV, orders, and new signups."""
    daily_events = (
        events.groupby(events["event_timestamp"].dt.date)["user_id"]
        .nunique()
        .reset_index()
        .rename(columns={"event_timestamp": "date", "user_id": "dau"})
    )

    daily_orders = (
        orders[orders["status"] == "completed"]
        .groupby(orders["created_at"].dt.date)
        .agg(
            total_orders=("order_id", "count"),
            total_gmv=("gmv", "sum"),
            unique_buyers=("buyer_id", "nunique"),
        )
        .reset_index()
        .rename(columns={"created_at": "date"})
    )

    daily = daily_events.merge(daily_orders, on="date", how="left").fillna(0)
    daily["date"] = pd.to_datetime(daily["date"])
    daily["gmv_7d_avg"] = daily["total_gmv"].rolling(7, min_periods=1).mean()
    daily["dau_7d_avg"] = daily["dau"].rolling(7, min_periods=1).mean()

    return daily.sort_values("date")


def compute_funnel_metrics(events: pd.DataFrame) -> pd.DataFrame:
    """Compute overall funnel conversion rates."""
    funnel_steps = [
        ("Page View", "page_view"),
        ("Listing View", "listing_view"),
        ("Signup Complete", "signup_complete"),
        ("Add to Cart", "add_to_cart"),
        ("Purchase", "purchase_complete"),
    ]

    records = []
    for label, event_type in funnel_steps:
        count = events[events["event_type"] == event_type]["user_id"].nunique()
        records.append({"step": label, "users": count})

    df = pd.DataFrame(records)
    top = df["users"].iloc[0]
    df["conversion_pct"] = (df["users"] / top * 100).round(2)
    return df


def compute_seller_metrics(orders: pd.DataFrame) -> pd.DataFrame:
    """Compute top seller performance metrics."""
    completed = orders[orders["status"] == "completed"]

    seller_metrics = (
        completed.groupby("seller_id")
        .agg(
            total_orders=("order_id", "count"),
            total_gmv=("gmv", "sum"),
            unique_buyers=("buyer_id", "nunique"),
            avg_order_value=("gmv", "mean"),
            avg_rating=("seller_rating", "mean"),
        )
        .reset_index()
        .sort_values("total_gmv", ascending=False)
    )

    seller_metrics["gmv_rank"] = seller_metrics["total_gmv"].rank(ascending=False).astype(int)
    return seller_metrics.head(50)


def compute_cohort_matrix(events: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    """Compute weekly cohort retention matrix."""
    users = users.copy()
    events = events.copy()

    users["cohort_week"] = pd.to_datetime(users["signup_date"]).dt.to_period("W")
    events["activity_week"] = pd.to_datetime(events["event_timestamp"]).dt.to_period("W")

    merged = events.merge(users[["user_id", "cohort_week"]], on="user_id", how="left")
    merged["week_number"] = (merged["activity_week"] - merged["cohort_week"]).apply(
        lambda x: x.n if hasattr(x, "n") else np.nan
    )
    merged = merged[merged["week_number"].between(0, 8)]

    activity = (
        merged.groupby(["cohort_week", "week_number"])["user_id"]
        .nunique()
        .reset_index(name="active_users")
    )

    cohort_sizes = activity[activity["week_number"] == 0].set_index("cohort_week")["active_users"]
    activity["cohort_size"] = activity["cohort_week"].map(cohort_sizes)
    activity["retention_rate"] = (activity["active_users"] / activity["cohort_size"] * 100).round(1)

    matrix = activity.pivot(index="cohort_week", columns="week_number", values="retention_rate")
    matrix.index = matrix.index.astype(str)
    return matrix.tail(10)
