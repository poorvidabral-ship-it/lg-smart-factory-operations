"""
LG Smart Factory — Supabase Database Layer (Phase 5.1)
=======================================================
Cloud database connector for live operational data.
"""

import os
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Optional, List, Dict
from supabase import create_client


# ── Client ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# ── Generic helpers ──────────────────────────────────────────────────────────
def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return datetime.now().strftime("%Y-%m-%d")


# ── Load tables as DataFrames ────────────────────────────────────────────────
TABLES = {
    "production":  {"columns": ["Date", "Product", "Prod_line", "shift", "Target",
                                 "Actual", "Downtime_min", "Machine_Status"]},
    "warehouse":   {"columns": ["Date", "material", "Current_stock", "Minimum_stock",
                                 "Supplier", "Unit_Cost"]},
    "maintenance": {"columns": ["Date", "Machine_ID", "Health_Score",
                                 "Risk_Level", "Maintenance_Status", "Prod_line"]},
    "quality":     {"columns": ["Date", "Product", "Quality_Score",
                                 "Inspection_Status", "Defective_Units"]},
    "safety":      {"columns": ["Date", "Severity", "Employees_Affected",
                                 "Safety_Status", "Prod_line"]},
}


def load_table(table_name: str) -> pd.DataFrame:
    """Load all rows from a Supabase table into a DataFrame."""
    supabase = get_supabase()
    response = supabase.table(table_name).select("*").execute()
    rows = response.data or []
    cols = TABLES.get(table_name, {}).get("columns", [])
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows)
    # Rename DB lowercase columns to PascalCase as app expects
    renames = {
        "date": "Date", "product": "Product", "target": "Target",
        "actual": "Actual", "shift": "shift",
        "prod_line": "Prod_line", "machine_status": "Machine_Status",
        "downtime_min": "Downtime_min", "machine_id": "Machine_ID",
        "health_score": "Health_Score", "risk_level": "Risk_Level",
        "maintenance_status": "Maintenance_Status",
        "current_stock": "Current_stock", "minimum_stock": "Minimum_stock",
        "unit_cost": "Unit_Cost", "supplier": "Supplier",
        "quality_score": "Quality_Score", "inspection_status": "Inspection_Status",
        "defective_units": "Defective_Units",
        "employees_affected": "Employees_Affected",
        "safety_status": "Safety_Status", "severity": "Severity",
    }
    df = df.rename(columns=renames)
    existing = [c for c in cols if c in df.columns]
    return df[existing] if existing else df


def get_available_dates() -> List[str]:
    """Get sorted unique dates from production table."""
    supabase = get_supabase()
    response = supabase.table("production").select("date").execute()
    dates = sorted(set(r["date"] for r in (response.data or []) if r.get("date")), reverse=True)
    return dates


# ── Inserts ──────────────────────────────────────────────────────────────────
def insert_record(table_name: str, data: dict) -> dict:
    """Insert a row into a Supabase table. Returns the inserted row."""
    supabase = get_supabase()
    response = supabase.table(table_name).insert(data).execute()
    if response.data:
        return response.data[0]
    return {}


# ── Incidents ────────────────────────────────────────────────────────────────
def add_incident(title: str, description: str, department: str,
                 severity: str, image_path: str = "") -> dict:
    """Add an incident to the incident_log table."""
    data = {
        "timestamp": _now(),
        "title": title,
        "description": description,
        "department": department,
        "severity": severity,
        "image_path": image_path,
        "status": "Open",
    }
    return insert_record("incident_log", data)


def get_incidents(department: Optional[str] = None,
                  severity: Optional[str] = None,
                  limit: int = 50) -> List[Dict]:
    """Load incidents with optional filters."""
    supabase = get_supabase()
    query = supabase.table("incident_log").select("*").order("created_at", desc=True).limit(limit)
    if department:
        query = query.eq("department", department)
    if severity:
        query = query.eq("severity", severity)
    response = query.execute()
    return response.data or []


def get_incident_stats() -> dict:
    """Get incident counts by severity."""
    incidents = get_incidents(limit=1000)
    total = len(incidents)
    by_sev = {}
    for i in incidents:
        s = i.get("severity", "UNKNOWN")
        by_sev[s] = by_sev.get(s, 0) + 1
    return {"total": total, "by_severity": by_sev}
