"""
LG Smart Factory — Role-Based Access & Dashboard System (Phase 5.2)
====================================================================
Defines roles, permissions, priority queues, and role-specific
AI recommendations. Maps auth roles to page access.
"""

from dataclasses import dataclass, field
from typing import List, Dict

# ─────────────────────────────────────────────────────────────────────────────
# ROLE DEFINITIONS  (keys = emoji-prefixed display names for sidebar)
# ─────────────────────────────────────────────────────────────────────────────
ROLES = {
    "👑 Admin": {
        "modules":     ["🏠  Dashboard","🏭  Production","📦  Warehouse",
                        "🛠  Maintenance","✅  Quality","⚠  Safety",
                        "📸  Incidents","🔮  Simulator","📄  Executive Reports"],
        "color":       "#7a0026",
        "icon":        "👑",
        "description": "Full system access · All modules · All alerts",
        "badge":       "FULL ACCESS",
    },
    "🏭 Factory Manager": {
        "modules":     ["🏠  Dashboard","🏭  Production","📦  Warehouse",
                        "🛠  Maintenance","✅  Quality","⚠  Safety",
                        "📸  Incidents","🔮  Simulator","📄  Executive Reports"],
        "color":       "#1e3a5f",
        "icon":        "🏭",
        "description": "Enterprise ops · All modules · Executive view",
        "badge":       "MANAGER",
    },
    "🏭 Production Supervisor": {
        "modules":     ["🏠  Dashboard","🏭  Production","📸  Incidents"],
        "color":       "#1d4ed8",
        "icon":        "🏭",
        "description": "Production metrics · Downtime · Shift analytics",
        "badge":       "PRODUCTION",
    },
    "🛠 Maintenance Engineer": {
        "modules":     ["🏠  Dashboard","🛠  Maintenance","📸  Incidents",
                        "🔮  Simulator"],
        "color":       "#92400e",
        "icon":        "🛠",
        "description": "Machine health · Risk alerts · Repair queue",
        "badge":       "MAINTENANCE",
    },
    "📦 Warehouse Executive": {
        "modules":     ["🏠  Dashboard","📦  Warehouse","📸  Incidents"],
        "color":       "#0f766e",
        "icon":        "📦",
        "description": "Inventory · Suppliers · Stock alerts",
        "badge":       "WAREHOUSE",
    },
    "✅ Quality Inspector": {
        "modules":     ["🏠  Dashboard","✅  Quality","📸  Incidents"],
        "color":       "#166534",
        "icon":        "✅",
        "description": "Defect analytics · Failed inspections · Audit",
        "badge":       "QUALITY",
    },
    "⚠ Safety Officer": {
        "modules":     ["🏠  Dashboard","⚠  Safety","📸  Incidents"],
        "color":       "#9f1239",
        "icon":        "⚠",
        "description": "Incidents · Severity · Emergency escalation",
        "badge":       "SAFETY",
    },
}

# Map auth role names (from Supabase users table) to ROLES keys (emoji-prefixed)
AUTH_TO_ROLE_KEY = {
    "Admin":                 "👑 Admin",
    "Factory Manager":       "🏭 Factory Manager",
    "Production Supervisor": "🏭 Production Supervisor",
    "Maintenance Engineer":  "🛠 Maintenance Engineer",
    "Warehouse Executive":   "📦 Warehouse Executive",
    "Quality Inspector":     "✅ Quality Inspector",
    "Safety Officer":        "⚠ Safety Officer",
}

# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY LEVELS
# ─────────────────────────────────────────────────────────────────────────────
class P:
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"

PRIORITY_STYLE = {
    P.CRITICAL: {"bg":"#fff1f2","border":"#f43f5e","text":"#9f1239","dot":"#f43f5e","icon":"🔴"},
    P.HIGH:     {"bg":"#fff7ed","border":"#f97316","text":"#9a3412","dot":"#f97316","icon":"🟠"},
    P.MEDIUM:   {"bg":"#fffbeb","border":"#f59e0b","text":"#92400e","dot":"#f59e0b","icon":"🟡"},
    P.LOW:      {"bg":"#eff6ff","border":"#3b82f6","text":"#1e40af","dot":"#3b82f6","icon":"🔵"},
}

@dataclass
class Task:
    priority:    str
    title:       str
    detail:      str
    action:      str
    module:      str
    assignee:    str = ""

# ─────────────────────────────────────────────────────────────────────────────
# TASK QUEUE GENERATORS
# ─────────────────────────────────────────────────────────────────────────────
def build_task_queue(engines: dict, role: str) -> List[Task]:
    from modules.ai_engine import SEV

    SEV_TO_PRIORITY = {
        SEV.CRITICAL: P.CRITICAL,
        "high":       P.HIGH,
        SEV.MEDIUM:   P.MEDIUM,
        SEV.LOW:      P.LOW,
        SEV.OK:       P.LOW,
    }

    ROLE_MODULES = {
        "👑 Admin":                  ["production","maintenance","warehouse","quality","safety"],
        "🏭 Factory Manager":        ["production","maintenance","warehouse","quality","safety"],
        "🏭 Production Supervisor":  ["production"],
        "🛠 Maintenance Engineer":   ["maintenance","production"],
        "📦 Warehouse Executive":    ["warehouse"],
        "✅ Quality Inspector":      ["quality"],
        "⚠ Safety Officer":         ["safety"],
    }
    allowed = ROLE_MODULES.get(role, list(engines.keys()))

    tasks: List[Task] = []
    for key, result in engines.items():
        if key not in allowed:
            continue
        for alert in result.alerts:
            if alert.severity == SEV.OK:
                continue
            tasks.append(Task(
                priority = SEV_TO_PRIORITY.get(alert.severity, P.LOW),
                title    = alert.title,
                detail   = alert.detail,
                action   = alert.action,
                module   = result.module,
                assignee = _default_assignee(key),
            ))

    order = [P.CRITICAL, P.HIGH, P.MEDIUM, P.LOW]
    tasks.sort(key=lambda t: order.index(t.priority))
    return tasks

def _default_assignee(module_key: str) -> str:
    return {
        "production":  "Production Supervisor",
        "maintenance": "Maintenance Engineer",
        "warehouse":   "Warehouse Executive",
        "quality":     "Quality Inspector",
        "safety":      "Safety Officer",
    }.get(module_key, "Manager")

# ─────────────────────────────────────────────────────────────────────────────
# ROLE-SPECIFIC AI RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────
def get_role_recommendations(engines: dict, role: str) -> List[Dict]:
    recs = []
    prod  = engines.get("production")
    maint = engines.get("maintenance")
    wh    = engines.get("warehouse")
    qual  = engines.get("quality")
    saf   = engines.get("safety")

    admin_or_manager = role in ["👑 Admin", "🏭 Factory Manager"]

    if admin_or_manager or role == "🏭 Production Supervisor":
        if prod:
            recs.append({
                "icon": "⚡", "title": "Production Efficiency",
                "body": prod.summary, "status": prod.overall_status,
            })
        if maint:
            recs.append({
                "icon": "🛠", "title": "Maintenance Impact",
                "body": maint.summary, "status": maint.overall_status,
            })

    if admin_or_manager or role == "🛠 Maintenance Engineer":
        if maint:
            recs.append({
                "icon": "🔧", "title": "Fleet Health Status",
                "body": maint.summary, "status": maint.overall_status,
            })
        if prod:
            recs.append({
                "icon": "📉", "title": "Downtime Intelligence",
                "body": prod.summary, "status": prod.overall_status,
            })

    if admin_or_manager or role == "✅ Quality Inspector":
        if qual:
            recs.append({
                "icon": "🔍", "title": "Quality Assurance",
                "body": qual.summary, "status": qual.overall_status,
            })
        if wh:
            recs.append({
                "icon": "📦", "title": "Component Supply Quality",
                "body": wh.summary, "status": wh.overall_status,
            })

    if admin_or_manager or role == "⚠ Safety Officer":
        if saf:
            recs.append({
                "icon": "🚨", "title": "Safety Risk Assessment",
                "body": saf.summary, "status": saf.overall_status,
            })
        if prod:
            recs.append({
                "icon": "⚙", "title": "Production Line Safety",
                "body": prod.summary, "status": prod.overall_status,
            })

    if admin_or_manager or role == "📦 Warehouse Executive":
        if wh:
            recs.append({
                "icon": "📦", "title": "Warehouse Status",
                "body": wh.summary, "status": wh.overall_status,
            })

    if role == "👑 Admin":
        if wh:
            recs.append({
                "icon": "📦", "title": "Warehouse Status",
                "body": wh.summary, "status": wh.overall_status,
            })

    return recs[:5]
