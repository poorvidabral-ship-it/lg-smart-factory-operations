"""
LG Smart Factory — Visual Incident Reporting System (Phase 3.3)
================================================================
Upload fault images, report incidents, classify severity,
and maintain a live operational incident feed.
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st
from modules.theme import kpi_card, alert_row, panel_title, divider

# ── Storage path ──────────────────────────────────────────────────────────────
INCIDENTS_DIR = "data"
INCIDENTS_FILE = os.path.join(INCIDENTS_DIR, "incidents.json")
IMAGES_DIR = os.path.join(INCIDENTS_DIR, "incident_images")

# ── Departments ───────────────────────────────────────────────────────────────
DEPARTMENTS = ["Production", "Warehouse", "Maintenance", "Quality", "Safety"]
SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


# ─────────────────────────────────────────────────────────────────────────────
# STORAGE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _ensure_dirs():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    if not os.path.exists(INCIDENTS_FILE):
        with open(INCIDENTS_FILE, "w") as f:
            json.dump([], f)


def _load_incidents() -> List[Dict]:
    _ensure_dirs()
    try:
        with open(INCIDENTS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_incidents(incidents: List[Dict]):
    _ensure_dirs()
    with open(INCIDENTS_FILE, "w") as f:
        json.dump(incidents, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# SAVE INCIDENT
# ─────────────────────────────────────────────────────────────────────────────
def save_incident(
    description: str,
    department: str,
    severity: str,
    reporter: str = "",
    image_path: str = "",
) -> Dict:
    """
    Save a new incident to the JSON store.
    Returns the incident dict.
    """
    incident = {
        "id":          str(uuid.uuid4())[:8],
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "description": description,
        "department":  department,
        "severity":    severity.upper(),
        "reporter":    reporter or "Unknown",
        "image_path":  image_path,
        "status":      "Open",
    }
    incidents = _load_incidents()
    incidents.insert(0, incident)
    _save_incidents(incidents)
    return incident


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFY INCIDENT SEVERITY
# ─────────────────────────────────────────────────────────────────────────────
def classify_incident(description: str, department: str) -> str:
    """
    Auto-classify severity based on keywords and department.
    Returns LOW / MEDIUM / HIGH / CRITICAL.
    """
    desc_lower = description.lower()
    critical_kw = ["fire", "flood", "explosion", "collapse", "emergency",
                   "shutdown", "evacuate", "injury", "fatality", "chemical spill",
                   "gas leak", "major breakdown"]
    high_kw = ["breakdown", "damage", "defect", "failure", "malfunction",
               "stoppage", "downtime", "safety hazard", "risk", "fault",
               "crack", "leak", "overheating", "vibration"]
    medium_kw = ["issue", "problem", "concern", "check", "inspect",
                 "irregular", "anomaly", "abnormal", "warning"]

    for kw in critical_kw:
        if kw in desc_lower:
            return "CRITICAL"
    for kw in high_kw:
        if kw in desc_lower:
            return "HIGH"
    for kw in medium_kw:
        if kw in desc_lower:
            return "MEDIUM"

    if department == "Safety":
        return "MEDIUM"
    return "LOW"


# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD INCIDENT — Full Form + Save
# ─────────────────────────────────────────────────────────────────────────────
def upload_incident():
    """
    Render the incident upload form, handle submission, save to store.
    Returns the submitted incident dict or None.
    """
    st.markdown(panel_title("📸", "Report New Incident"), unsafe_allow_html=True)

    with st.form("incident_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            department = st.selectbox("Department", DEPARTMENTS)
            severity_override = st.selectbox("Severity (override)", ["AUTO"] + SEVERITIES)
        with col2:
            reporter = st.text_input("Reported by", placeholder="Your name")
            uploaded_file = st.file_uploader(
                "Attach image (optional)",
                type=["jpg", "jpeg", "png", "bmp", "webp"],
            )

        description = st.text_area(
            "Incident Description",
            placeholder="Describe what happened, location, equipment involved...",
            height=100,
        )

        submitted = st.form_submit_button("🚨 Submit Incident Report", use_container_width=True)

        if submitted:
            if not description.strip():
                st.error("Please provide an incident description.")
                return None

            # Save image if uploaded
            image_path = ""
            if uploaded_file is not None:
                _ensure_dirs()
                ext = os.path.splitext(uploaded_file.name)[1] or ".jpg"
                filename = f"{uuid.uuid4()}{ext}"
                image_path = os.path.join(IMAGES_DIR, filename)
                with open(image_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            # Classify severity
            if severity_override == "AUTO":
                severity = classify_incident(description, department)
            else:
                severity = severity_override

            incident = save_incident(
                description=description.strip(),
                department=department,
                severity=severity,
                reporter=reporter.strip() or "Unknown",
                image_path=image_path,
            )

            st.success(f"✅ Incident #{incident['id']} reported — {severity} severity")
            return incident

    return None


# ─────────────────────────────────────────────────────────────────────────────
# RENDER INCIDENT CARD
# ─────────────────────────────────────────────────────────────────────────────
def render_incident_card(incident: Dict):
    """
    Render a single incident as a styled card.
    """
    sev = incident["severity"]
    sev_colors = {
        "CRITICAL": {"bg": "#fff1f2", "border": "#ef4444", "text": "#9f1239", "icon": "🔴"},
        "HIGH":     {"bg": "#fff7ed", "border": "#f97316", "text": "#9a3412", "icon": "🟠"},
        "MEDIUM":   {"bg": "#fffbeb", "border": "#f59e0b", "text": "#92400e", "icon": "🟡"},
        "LOW":      {"bg": "#eff6ff", "border": "#3b82f6", "text": "#1e40af", "icon": "🔵"},
    }
    c = sev_colors.get(sev, sev_colors["LOW"])

    has_image = bool(incident.get("image_path")) and os.path.exists(incident.get("image_path", ""))

    st.markdown(f"""
    <div style="background:{c['bg']};border:1px solid {c['border']}33;border-left:4px solid {c['border']};
                border-radius:14px;padding:16px 18px;margin-bottom:12px;
                box-shadow:0 2px 8px rgba(0,0,0,0.04);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:18px;">{c['icon']}</span>
                <strong style="font-size:14px;color:{c['text']};">#{incident.get('id','?')}</strong>
                <span style="font-size:11px;background:{c['border']}18;color:{c['text']};
                          padding:2px 10px;border-radius:20px;font-weight:700;">{sev}</span>
                <span style="font-size:11px;color:#64748b;">{incident['department']}</span>
            </div>
            <div style="font-size:11px;color:#94a3b8;">
                {incident.get('timestamp','')} · {incident.get('reporter','Unknown')}
            </div>
        </div>
        <div style="font-size:13px;color:#374151;line-height:1.6;">{incident['description']}</div>
    </div>
    """, unsafe_allow_html=True)

    if has_image:
        st.image(incident["image_path"], width=400)


# ─────────────────────────────────────────────────────────────────────────────
# RENDER INCIDENT FEED
# ─────────────────────────────────────────────────────────────────────────────
def render_incident_feed(
    department_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    max_items: int = 50,
):
    """
    Render the full incident feed with optional filters.
    """
    incidents = _load_incidents()

    if department_filter and department_filter != "ALL":
        incidents = [i for i in incidents if i["department"] == department_filter]
    if severity_filter and severity_filter != "ALL":
        incidents = [i for i in incidents if i["severity"] == severity_filter]

    if not incidents:
        st.markdown(alert_row("✅ No incidents reported for the selected filters.", "success"),
                    unsafe_allow_html=True)
        return

    st.markdown(f"**{len(incidents)} incident(s) found**")

    for inc in incidents[:max_items]:
        render_incident_card(inc)


# ─────────────────────────────────────────────────────────────────────────────
# INCIDENT SUMMARY STATS
# ─────────────────────────────────────────────────────────────────────────────
def render_incident_stats():
    """
    Render summary KPI cards for the incident dashboard.
    """
    incidents = _load_incidents()
    total = len(incidents)
    critical = len([i for i in incidents if i["severity"] == "CRITICAL"])
    high = len([i for i in incidents if i["severity"] == "HIGH"])
    open_cases = len([i for i in incidents if i.get("status") == "Open"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("📋", "Total Incidents", str(total)), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("🔴", "Critical", str(critical),
                              badge="URGENT" if critical > 0 else "CLEAR"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("🟠", "High", str(high),
                              badge="ATTENTION" if high > 0 else "CLEAR"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("🔓", "Open Cases", str(open_cases),
                              badge="OPEN" if open_cases > 0 else "RESOLVED"), unsafe_allow_html=True)
