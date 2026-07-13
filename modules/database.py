"""
LG Smart Factory — Supabase Database Layer (Phase 5.1)
=======================================================
Cloud database connector for live operational data.
Falls back to local Excel files when Supabase is unreachable.
"""

import os
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Optional, List, Dict

_BASE = os.path.join(os.path.dirname(__file__), "..", "datalg2")
_FALLBACK_FILES = {
    "production":  "production_live.csv",
    "warehouse":   "warehouse.csv.xlsx",
    "maintenance": "maintenance.csv.xlsx",
    "quality":     "quality.csv.xlsx",
    "safety":      "safety.csv.xlsx",
}

_supabase_client = None

def get_supabase():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception:
        _supabase_client = None
        return None


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


def _load_local(table_name: str) -> pd.DataFrame:
    """Fallback: load from local Excel/CSV files when Supabase is unavailable."""
    fname = _FALLBACK_FILES.get(table_name)
    if not fname:
        return pd.DataFrame()
    fpath = os.path.join(_BASE, fname)
    if not os.path.exists(fpath):
        return pd.DataFrame()
    if fname.endswith(".xlsx"):
        df = pd.read_excel(fpath)
    else:
        df = pd.read_csv(fpath)
    # Normalise columns to match app expectations
    cols = TABLES.get(table_name, {}).get("columns", [])
    for old, new in {
        "date": "Date", "product": "Product", "target": "Target",
        "actual": "Actual", "prod_line": "Prod_line",
        "machine_status": "Machine_Status", "downtime_min": "Downtime_min",
        "machine_id": "Machine_ID", "health_score": "Health_Score",
        "risk_level": "Risk_Level", "maintenance_status": "Maintenance_Status",
        "current_stock": "Current_stock", "minimum_stock": "Minimum_stock",
        "unit_cost": "Unit_Cost", "quality_score": "Quality_Score",
        "inspection_status": "Inspection_Status", "defective_units": "Defective_Units",
        "employees_affected": "Employees_Affected", "safety_status": "Safety_Status",
    }.items():
        if old in df.columns:
            df = df.rename(columns={old: new})
    existing = [c for c in cols if c in df.columns]
    return df[existing] if existing else df


def load_table(table_name: str) -> pd.DataFrame:
    """Load all rows from a Supabase table (with local Excel fallback)."""
    supabase = get_supabase()
    if supabase is not None:
        try:
            response = supabase.table(table_name).select("*").execute()
            rows = response.data or []
            if rows:
                cols = TABLES.get(table_name, {}).get("columns", [])
                df = pd.DataFrame(rows)
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
        except Exception:
            pass
    # Fallback to local files
    return _load_local(table_name)


def get_available_dates() -> List[str]:
    """Get sorted unique dates from production table."""
    supabase = get_supabase()
    if supabase is not None:
        try:
            response = supabase.table("production").select("date").execute()
            dates = sorted(set(r["date"] for r in (response.data or []) if r.get("date")), reverse=True)
            return dates
        except Exception:
            pass
    df = _load_local("production")
    if "Date" in df.columns:
        return sorted(df["Date"].dropna().astype(str).unique(), reverse=True)
    return []


# ── Inserts ──────────────────────────────────────────────────────────────────
def insert_record(table_name: str, data: dict) -> dict:
    """Insert a row into a Supabase table. Returns the inserted row."""
    supabase = get_supabase()
    if supabase is not None:
        try:
            response = supabase.table(table_name).insert(data).execute()
            if response.data:
                return response.data[0]
        except Exception:
            pass
    st.warning(f"Supabase unavailable — record not saved to cloud")
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
    if supabase is not None:
        try:
            query = supabase.table("incident_log").select("*").order("created_at", desc=True).limit(limit)
            if department:
                query = query.eq("department", department)
            if severity:
                query = query.eq("severity", severity)
            response = query.execute()
            return response.data or []
        except Exception:
            pass
    return []


def get_incident_stats() -> dict:
    """Get incident counts by severity."""
    incidents = get_incidents(limit=1000)
    total = len(incidents)
    by_sev = {}
    for i in incidents:
        s = i.get("severity", "UNKNOWN")
        by_sev[s] = by_sev.get(s, 0) + 1
    return {"total": total, "by_severity": by_sev}
