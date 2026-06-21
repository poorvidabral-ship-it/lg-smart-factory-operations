"""
LG Smart Factory — AI Decision Engine  (Phase 2.1)
===================================================
Pure rule-based threshold detection for speed & reliability.
No LLM calls for threshold logic.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# SEVERITY LEVELS
# ─────────────────────────────────────────────────────────────────────────────
class SEV:
    CRITICAL = "critical"   # Immediate shutdown / escalation required
    HIGH     = "high"       # Urgent action within 1 hour
    MEDIUM   = "medium"     # Action within shift
    LOW      = "low"        # Monitor / scheduled action
    OK       = "ok"         # Normal operations

SEV_RANK = {SEV.OK: 0, SEV.LOW: 1, SEV.MEDIUM: 2, SEV.HIGH: 3, SEV.CRITICAL: 4}

# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Alert:
    severity:       str          # SEV constant
    module:         str          # e.g. "Production"
    title:          str          # Short headline
    detail:         str          # What was detected
    action:         str          # Immediate action
    prevention:     str          # Long-term fix
    metric:         str = ""     # The numeric value that triggered this
    ui_kind:        str = "info" # alert_row kind: success/warning/danger/info

@dataclass
class EngineResult:
    module:         str
    overall_status: str          # SEV constant
    status_label:   str          # Human label e.g. "CRITICAL RISK"
    alerts:         List[Alert]  = field(default_factory=list)
    kpi_badges:     dict         = field(default_factory=dict)
    summary:        str          = ""

# ─────────────────────────────────────────────────────────────────────────────
# THRESHOLDS  (single source of truth — change here to tune system-wide)
# ─────────────────────────────────────────────────────────────────────────────
THRESHOLDS = {
    # Production
    "prod_health_critical":     75.0,
    "prod_health_warning":      90.0,
    "prod_downtime_critical":   30.0,   # minutes
    "prod_downtime_warning":    20.0,
    "prod_line_downtime_spike": 45.0,   # single line total minutes
    "prod_gap_pct_warning":     10.0,   # % below target
    "prod_breakdown_risk_max":  0,      # >0 triggers alert

    # Maintenance
    "maint_health_critical":    40.0,
    "maint_health_warning":     60.0,
    "maint_critical_machines":  2,      # count
    "maint_pending_warning":    3,

    # Warehouse
    "wh_low_stock_critical":    3,      # count of SKUs below min
    "wh_low_stock_warning":     1,
    "wh_stock_health_warning":  85.0,   # %

    # Quality
    "qual_score_critical":      65.0,
    "qual_score_warning":       75.0,
    "qual_failed_critical":     5,
    "qual_failed_warning":      2,
    "qual_defect_pct_warning":  5.0,    # % defective of total inspected

    # Safety
    "safety_critical_max":      0,      # >0 = instant critical
    "safety_unresolved_warning":2,
    "safety_affected_warning":  5,      # employees
}

# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _worst(alerts: List[Alert]) -> str:
    if not alerts:
        return SEV.OK
    return max(alerts, key=lambda a: SEV_RANK[a.severity]).severity

def _sev_to_ui(sev: str) -> str:
    return {"critical":"danger","high":"danger","medium":"warning",
            "low":"info","ok":"success"}.get(sev, "info")

def _status_label(sev: str) -> str:
    return {"critical":"🔴 CRITICAL RISK","high":"🟠 HIGH RISK",
            "medium":"🟡 MODERATE RISK","low":"🔵 LOW RISK",
            "ok":"🟢 NORMAL OPERATIONS"}.get(sev, "UNKNOWN")

def _make_alert(sev, module, title, detail, action, prevention, metric="") -> Alert:
    return Alert(
        severity=sev, module=module, title=title,
        detail=detail, action=action, prevention=prevention,
        metric=metric, ui_kind=_sev_to_ui(sev)
    )

# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTION RISK ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def detect_production_risk(df: pd.DataFrame) -> EngineResult:
    alerts: List[Alert] = []
    T = THRESHOLDS

    if df.empty:
        return EngineResult("Production", SEV.LOW, "⚪ NO DATA", alerts,
                            summary="No production data loaded for this date.")

    total_target   = df["Target"].sum()
    total_actual   = df["Actual"].sum()
    avg_downtime   = df["Downtime_min"].mean()
    factory_health = round((total_actual / total_target) * 100, 1) if total_target > 0 else 0
    gap_pct        = round(((total_target - total_actual) / total_target) * 100, 1) if total_target > 0 else 0
    breakdown_risk = len(df[df["Machine_Status"] == "Breakdown Risk"])

    # ── Rule 1: Factory Health ─────────────────────────────────────────────
    if factory_health < T["prod_health_critical"]:
        alerts.append(_make_alert(
            SEV.CRITICAL, "Production",
            "Factory Output Below Critical Threshold",
            f"Factory health at {factory_health}% — {gap_pct}% below production target.",
            "Halt low-performing lines immediately. Deploy supervisors for manual assessment.",
            "Review shift scheduling, machine allocation, and raw material supply chain.",
            metric=f"{factory_health}%"
        ))
    elif factory_health < T["prod_health_warning"]:
        alerts.append(_make_alert(
            SEV.MEDIUM, "Production",
            "Factory Output Below Target",
            f"Factory health at {factory_health}% — output gap of {gap_pct}%.",
            "Identify bottleneck lines and reallocate workforce.",
            "Conduct root-cause analysis on underperforming production lines.",
            metric=f"{factory_health}%"
        ))

    # ── Rule 2: Average Downtime ───────────────────────────────────────────
    if avg_downtime > T["prod_downtime_critical"]:
        alerts.append(_make_alert(
            SEV.HIGH, "Production",
            "Critical Downtime Level Detected",
            f"Average line downtime is {avg_downtime:.1f} min — exceeds critical threshold of {T['prod_downtime_critical']} min.",
            "Dispatch maintenance team immediately to all active lines.",
            "Implement predictive maintenance schedule to prevent recurring downtime.",
            metric=f"{avg_downtime:.1f} min"
        ))
    elif avg_downtime > T["prod_downtime_warning"]:
        alerts.append(_make_alert(
            SEV.MEDIUM, "Production",
            "Elevated Downtime Warning",
            f"Average line downtime at {avg_downtime:.1f} min exceeds {T['prod_downtime_warning']} min warning level.",
            "Review maintenance logs for lines exceeding threshold.",
            "Schedule preventive maintenance during next planned shutdown.",
            metric=f"{avg_downtime:.1f} min"
        ))

    # ── Rule 3: Per-line downtime spike ───────────────────────────────────
    line_dt = df.groupby("Prod_line")["Downtime_min"].sum()
    spike_lines = line_dt[line_dt > T["prod_line_downtime_spike"]]
    if not spike_lines.empty:
        lines_str = ", ".join(spike_lines.index.astype(str))
        alerts.append(_make_alert(
            SEV.HIGH, "Production",
            f"Downtime Spike on Line(s): {lines_str}",
            f"Line(s) {lines_str} each logged >{T['prod_line_downtime_spike']} min downtime today.",
            f"Immediate inspection of line(s) {lines_str}. Escalate to shift manager.",
            "Install real-time vibration/thermal sensors on flagged lines.",
            metric=f"Max: {int(spike_lines.max())} min"
        ))

    # ── Rule 4: Breakdown Risk Machines ───────────────────────────────────
    if breakdown_risk > T["prod_breakdown_risk_max"]:
        alerts.append(_make_alert(
            SEV.CRITICAL, "Production",
            f"{breakdown_risk} Machine(s) at Breakdown Risk",
            f"{breakdown_risk} machine(s) flagged as Breakdown Risk across production lines.",
            "Take flagged machines offline immediately. Switch to backup units if available.",
            "Implement condition-based maintenance monitoring on all critical machines.",
            metric=f"{breakdown_risk} machines"
        ))

    # ── Rule 5: Output Gap Warning ─────────────────────────────────────────
    if gap_pct > T["prod_gap_pct_warning"] and factory_health >= T["prod_health_critical"]:
        alerts.append(_make_alert(
            SEV.LOW, "Production",
            "Production Output Gap Detected",
            f"Actual output is {gap_pct}% below daily target.",
            "Review shift productivity reports and identify slow products.",
            "Adjust daily targets based on realistic capacity utilisation.",
            metric=f"{gap_pct}% gap"
        ))

    # ── Summary ────────────────────────────────────────────────────────────
    if not alerts:
        alerts.append(_make_alert(
            SEV.OK, "Production",
            "All Production Systems Nominal",
            f"Factory health {factory_health}%. Avg downtime {avg_downtime:.1f} min. No anomalies detected.",
            "Continue standard operations.",
            "Maintain current production schedule.",
            metric=f"{factory_health}%"
        ))

    worst = _worst(alerts)
    summary = (f"Factory health {factory_health}% | Avg downtime {avg_downtime:.1f} min | "
               f"{breakdown_risk} breakdown risk | {len(alerts)} alert(s)")
    badges = {
        "Factory Health": (factory_health, "%", worst if factory_health < T["prod_health_warning"] else SEV.OK),
        "Avg Downtime":   (avg_downtime,    " min", SEV.HIGH if avg_downtime > T["prod_downtime_critical"] else SEV.OK),
        "Breakdown Risk": (breakdown_risk,  " machines", SEV.CRITICAL if breakdown_risk > 0 else SEV.OK),
    }
    return EngineResult("Production", worst, _status_label(worst), alerts, badges, summary)


# ─────────────────────────────────────────────────────────────────────────────
# MAINTENANCE RISK ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def detect_maintenance_risk(df: pd.DataFrame) -> EngineResult:
    alerts: List[Alert] = []
    T = THRESHOLDS

    if df.empty:
        return EngineResult("Maintenance", SEV.LOW, "⚪ NO DATA", alerts,
                            summary="No maintenance data loaded for this date.")

    avg_health    = df["Health_Score"].mean()
    critical_cnt  = len(df[df["Risk_Level"] == "High"])
    pending_cnt   = len(df[df["Maintenance_Status"] == "Pending"])
    low_health_df = df[df["Health_Score"] < T["maint_health_critical"]]

    # ── Rule 1: Critical low-health machines ──────────────────────────────
    if not low_health_df.empty:
        ids = ", ".join(low_health_df["Machine_ID"].astype(str).tolist()[:5])
        alerts.append(_make_alert(
            SEV.CRITICAL, "Maintenance",
            f"{len(low_health_df)} Machine(s) Below Critical Health Score",
            f"Machine(s) {ids} scored below {T['maint_health_critical']} — imminent failure risk.",
            "Take listed machines offline immediately. Initiate emergency maintenance protocol.",
            "Deploy condition monitoring sensors. Schedule biweekly health assessments.",
            metric=f"Min score: {int(low_health_df['Health_Score'].min())}"
        ))

    # ── Rule 2: Average health warning ────────────────────────────────────
    if avg_health < T["maint_health_warning"] and len(low_health_df) == 0:
        alerts.append(_make_alert(
            SEV.MEDIUM, "Maintenance",
            "Fleet Average Health Below Warning Level",
            f"Average machine health score is {avg_health:.1f} — below {T['maint_health_warning']} threshold.",
            "Schedule maintenance review for all machines scoring below 70.",
            "Increase maintenance frequency across the fleet.",
            metric=f"{avg_health:.1f}/100"
        ))

    # ── Rule 3: High-risk machine count ───────────────────────────────────
    if critical_cnt >= T["maint_critical_machines"]:
        alerts.append(_make_alert(
            SEV.HIGH, "Maintenance",
            f"{critical_cnt} High-Risk Machines Require Immediate Attention",
            f"{critical_cnt} machines classified as High Risk — exceeds safe operational threshold.",
            "Assign dedicated maintenance crew to each high-risk machine this shift.",
            "Install predictive analytics sensors on repeatedly failing machines.",
            metric=f"{critical_cnt} machines"
        ))
    elif critical_cnt > 0:
        alerts.append(_make_alert(
            SEV.LOW, "Maintenance",
            f"{critical_cnt} High-Risk Machine Flagged",
            f"{critical_cnt} machine(s) flagged as high risk today.",
            "Schedule inspection before next production cycle.",
            "Review operating parameters and lubrication records.",
            metric=f"{critical_cnt} machine"
        ))

    # ── Rule 4: Pending maintenance backlog ───────────────────────────────
    if pending_cnt > T["maint_pending_warning"]:
        alerts.append(_make_alert(
            SEV.MEDIUM, "Maintenance",
            f"Maintenance Backlog: {pending_cnt} Tasks Pending",
            f"{pending_cnt} maintenance tasks are pending — backlog exceeds safe threshold.",
            "Prioritise by machine risk level. Deploy additional technicians if needed.",
            "Review maintenance staffing plan and preventive scheduling cadence.",
            metric=f"{pending_cnt} tasks"
        ))

    if not alerts:
        alerts.append(_make_alert(
            SEV.OK, "Maintenance",
            "All Machines Operating Within Safe Parameters",
            f"Avg health {avg_health:.1f}/100. {critical_cnt} critical. {pending_cnt} pending tasks.",
            "Continue standard maintenance schedule.",
            "Maintain current preventive maintenance programme.",
            metric=f"{avg_health:.1f}/100"
        ))

    worst   = _worst(alerts)
    summary = (f"Avg health {avg_health:.1f} | {critical_cnt} critical | "
               f"{pending_cnt} pending | {len(low_health_df)} below critical score")
    return EngineResult("Maintenance", worst, _status_label(worst), alerts,
                        kpi_badges={}, summary=summary)


# ─────────────────────────────────────────────────────────────────────────────
# WAREHOUSE RISK ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def detect_warehouse_risk(df: pd.DataFrame) -> EngineResult:
    alerts: List[Alert] = []
    T = THRESHOLDS

    if df.empty:
        return EngineResult("Warehouse", SEV.LOW, "⚪ NO DATA", alerts,
                            summary="No warehouse data loaded for this date.")

    low_stock_df  = df[df["Current_stock"] < df["Minimum_stock"]]
    low_cnt       = len(low_stock_df)
    total_skus    = len(df)
    stock_health  = round(((total_skus - low_cnt) / total_skus) * 100, 1) if total_skus > 0 else 100

    # ── Rule 1: Critical low-stock count ──────────────────────────────────
    if low_cnt >= T["wh_low_stock_critical"]:
        cat_col = "Category" if "Category" in low_stock_df.columns else "material"
        items = ", ".join(low_stock_df[cat_col].astype(str).unique()[:4].tolist())
        alerts.append(_make_alert(
            SEV.CRITICAL, "Warehouse",
            f"{low_cnt} SKUs Below Minimum Stock — Production Risk",
            f"{low_cnt} inventory items below minimum threshold. Affected categories: {items}.",
            "Trigger emergency purchase orders immediately. Notify procurement team.",
            "Set automated reorder points at 125% of minimum stock level.",
            metric=f"{low_cnt} SKUs"
        ))
    elif low_cnt >= T["wh_low_stock_warning"]:
        alerts.append(_make_alert(
            SEV.MEDIUM, "Warehouse",
            f"{low_cnt} SKU(s) Approaching Stock Shortage",
            f"{low_cnt} item(s) have fallen below minimum stock level.",
            "Place purchase orders within 24 hours to avoid production disruption.",
            "Review supplier lead times and adjust safety stock buffers.",
            metric=f"{low_cnt} SKU(s)"
        ))

    # ── Rule 2: Overall stock health ──────────────────────────────────────
    if stock_health < T["wh_stock_health_warning"] and low_cnt < T["wh_low_stock_critical"]:
        alerts.append(_make_alert(
            SEV.LOW, "Warehouse",
            "Inventory Health Below Target Level",
            f"Only {stock_health}% of SKUs are above minimum stock. Fleet-wide replenishment needed.",
            "Review all SKUs below 120% of minimum and place top-up orders.",
            "Implement weekly inventory audits and demand forecasting.",
            metric=f"{stock_health}%"
        ))

    # ── Rule 3: Zero-stock items ───────────────────────────────────────────
    zero_stock = df[df["Current_stock"] == 0]
    if not zero_stock.empty:
        zitems = ", ".join(zero_stock.get("Item_Name", zero_stock.index.astype(str)).astype(str).tolist()[:3])
        alerts.append(_make_alert(
            SEV.CRITICAL, "Warehouse",
            f"{len(zero_stock)} Item(s) at Zero Stock",
            f"Items with zero stock detected: {zitems}. Production halt risk is HIGH.",
            "Expedite emergency resupply. Halt production lines dependent on these items.",
            "Never allow safety stock below 20% of minimum. Add automated low-stock alerts.",
            metric=f"{len(zero_stock)} items"
        ))

    if not alerts:
        alerts.append(_make_alert(
            SEV.OK, "Warehouse",
            "All Inventory Levels Within Safe Range",
            f"Stock health {stock_health}%. {total_skus} SKUs all above minimum threshold.",
            "Continue standard replenishment cycle.",
            "Maintain current inventory management programme.",
            metric=f"{stock_health}%"
        ))

    worst   = _worst(alerts)
    summary = f"{low_cnt} low-stock items | stock health {stock_health}% | {total_skus} total SKUs"
    return EngineResult("Warehouse", worst, _status_label(worst), alerts,
                        kpi_badges={}, summary=summary)


# ─────────────────────────────────────────────────────────────────────────────
# QUALITY RISK ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def detect_quality_risk(df: pd.DataFrame) -> EngineResult:
    alerts: List[Alert] = []
    T = THRESHOLDS

    if df.empty:
        return EngineResult("Quality", SEV.LOW, "⚪ NO DATA", alerts,
                            summary="No quality data loaded for this date.")

    total_insp  = len(df)
    failed_cnt  = len(df[df["Inspection_Status"] == "Failed"])
    defectives  = int(df["Defective_Units"].sum())
    avg_score   = df["Quality_Score"].mean()
    defect_pct  = round((defectives / (df["Defective_Units"].sum() + df.get("Passed_Units",
                         pd.Series([0]*len(df))).sum() + 1)) * 100, 1)

    # ── Rule 1: Critical quality score ────────────────────────────────────
    if avg_score < T["qual_score_critical"]:
        worst_prod = df.groupby("Product")["Quality_Score"].mean().idxmin()
        alerts.append(_make_alert(
            SEV.CRITICAL, "Quality",
            "Quality Score Below Critical Threshold",
            f"Average quality score {avg_score:.1f} — below critical threshold of {T['qual_score_critical']}. "
            f"Worst performer: {worst_prod}.",
            "Stop shipment of flagged product batches. Initiate 100% manual re-inspection.",
            "Root-cause analysis mandatory within 24h. Review assembly parameters.",
            metric=f"{avg_score:.1f}/100"
        ))
    elif avg_score < T["qual_score_warning"]:
        alerts.append(_make_alert(
            SEV.MEDIUM, "Quality",
            "Quality Score Below Target",
            f"Average quality score {avg_score:.1f} is below the {T['qual_score_warning']} target.",
            "Flag batches with score <75 for additional QC review before dispatch.",
            "Audit assembly line calibration settings and operator training records.",
            metric=f"{avg_score:.1f}/100"
        ))

    # ── Rule 2: Failed inspections ────────────────────────────────────────
    if failed_cnt >= T["qual_failed_critical"]:
        alerts.append(_make_alert(
            SEV.CRITICAL, "Quality",
            f"Critical Inspection Failure Rate: {failed_cnt} Failed",
            f"{failed_cnt} inspections failed today ({round(failed_cnt/total_insp*100,1)}% failure rate).",
            "Quarantine all failed batch output. Escalate to Quality Director immediately.",
            "Deploy Six Sigma analysis on failure patterns. Review supplier component quality.",
            metric=f"{failed_cnt} failures"
        ))
    elif failed_cnt >= T["qual_failed_warning"]:
        alerts.append(_make_alert(
            SEV.MEDIUM, "Quality",
            f"{failed_cnt} Inspection Failures Detected",
            f"{failed_cnt} inspections have failed today.",
            "Review failed batches. Assign QC engineer to investigate failure root cause.",
            "Increase inspection frequency for affected product lines.",
            metric=f"{failed_cnt} failures"
        ))

    # ── Rule 3: High defective unit count ─────────────────────────────────
    if defectives > 0:
        worst_def_prod = df.groupby("Product")["Defective_Units"].sum().idxmax()
        sev = SEV.HIGH if defectives > 50 else SEV.LOW
        alerts.append(_make_alert(
            sev, "Quality",
            f"{defectives:,} Defective Units Logged",
            f"{defectives:,} defective units recorded today. Highest in: {worst_def_prod}.",
            f"Isolate {worst_def_prod} line output. Initiate defect triage protocol.",
            "Review tooling calibration and incoming component inspection records.",
            metric=f"{defectives:,} units"
        ))

    if not alerts:
        alerts.append(_make_alert(
            SEV.OK, "Quality",
            "All Quality Metrics Within Acceptable Range",
            f"Avg score {avg_score:.1f}/100. {failed_cnt} failures. {defectives} defectives.",
            "Continue standard quality monitoring.",
            "Maintain current inspection cadence and calibration schedule.",
            metric=f"{avg_score:.1f}/100"
        ))

    worst   = _worst(alerts)
    summary = (f"Avg score {avg_score:.1f} | {failed_cnt} failures | "
               f"{defectives} defectives | {total_insp} inspections")
    return EngineResult("Quality", worst, _status_label(worst), alerts,
                        kpi_badges={}, summary=summary)


# ─────────────────────────────────────────────────────────────────────────────
# SAFETY ESCALATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def detect_safety_risk(df: pd.DataFrame) -> EngineResult:
    alerts: List[Alert] = []
    T = THRESHOLDS

    if df.empty:
        return EngineResult("Safety", SEV.LOW, "⚪ NO DATA", alerts,
                            summary="No safety data loaded for this date.")

    total_incidents = len(df)
    critical_cnt    = len(df[df["Severity"] == "Critical"])
    affected        = int(df["Employees_Affected"].sum())
    unresolved      = len(df[df["Safety_Status"] != "Resolved"])

    # ── Rule 1: Any critical incident = immediate escalation ──────────────
    if critical_cnt > T["safety_critical_max"]:
        lines = df[df["Severity"] == "Critical"]["Prod_line"].unique()
        lines_str = ", ".join(str(l) for l in lines)
        alerts.append(_make_alert(
            SEV.CRITICAL, "Safety",
            f"CRITICAL SAFETY INCIDENT — Line(s): {lines_str}",
            f"{critical_cnt} critical safety incident(s) recorded on line(s) {lines_str}.",
            "STOP affected lines immediately. Evacuate if required. Notify HSE Officer NOW.",
            "Mandatory safety audit of affected lines before restart. Incident report within 2h.",
            metric=f"{critical_cnt} critical"
        ))

    # ── Rule 2: High unresolved count ─────────────────────────────────────
    if unresolved >= T["safety_unresolved_warning"]:
        alerts.append(_make_alert(
            SEV.HIGH, "Safety",
            f"{unresolved} Safety Incidents Remain Unresolved",
            f"{unresolved} open safety cases are unresolved — compounding risk.",
            "Assign each open case to a named safety officer. Set resolution deadline of 4h.",
            "Implement daily safety stand-up to clear incident backlog within same shift.",
            metric=f"{unresolved} open"
        ))

    # ── Rule 3: High employee impact ──────────────────────────────────────
    if affected >= T["safety_affected_warning"]:
        alerts.append(_make_alert(
            SEV.HIGH, "Safety",
            f"{affected} Employees Affected by Safety Incidents",
            f"{affected} workers impacted across all active production lines.",
            "Arrange immediate medical assessments for all affected employees.",
            "Review personal protective equipment compliance and line ergonomic assessments.",
            metric=f"{affected} workers"
        ))

    # ── Rule 4: Any incident at all ───────────────────────────────────────
    if total_incidents > 0 and critical_cnt == 0 and unresolved < T["safety_unresolved_warning"]:
        alerts.append(_make_alert(
            SEV.LOW, "Safety",
            f"{total_incidents} Non-Critical Incident(s) Logged",
            f"{total_incidents} safety event(s) recorded today — all non-critical.",
            "Log all incidents in the safety management system. Monitor for recurrence.",
            "Conduct safety briefing at start of next shift.",
            metric=f"{total_incidents} incidents"
        ))

    if not alerts:
        alerts.append(_make_alert(
            SEV.OK, "Safety",
            "No Safety Incidents Detected",
            "Zero incidents recorded. All safety systems operational.",
            "Continue standard safety monitoring and PPE compliance checks.",
            "Schedule next quarterly safety drill.",
            metric="0 incidents"
        ))

    worst   = _worst(alerts)
    summary = (f"{total_incidents} incidents | {critical_cnt} critical | "
               f"{affected} affected | {unresolved} unresolved")
    return EngineResult("Safety", worst, _status_label(worst), alerts,
                        kpi_badges={}, summary=summary)


# ─────────────────────────────────────────────────────────────────────────────
# FACTORY-WIDE SUMMARY ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def detect_factory_risk(prod_df, maint_df, wh_df, qual_df, safety_df) -> dict:
    """Run all engines and return a dict of EngineResult objects."""
    return {
        "production":  detect_production_risk(prod_df),
        "maintenance": detect_maintenance_risk(maint_df),
        "warehouse":   detect_warehouse_risk(wh_df),
        "quality":     detect_quality_risk(qual_df),
        "safety":      detect_safety_risk(safety_df),
    }


# ─────────────────────────────────────────────────────────────────────────────
# UI RENDER HELPERS  (theme-compatible)
# ─────────────────────────────────────────────────────────────────────────────
def render_engine_alerts(result: EngineResult, st_obj) -> None:
    """Render all alerts from an EngineResult using theme alert_row style."""
    SEV_ICON = {
        SEV.CRITICAL: "🔴",
        SEV.HIGH:     "🟠",
        SEV.MEDIUM:   "🟡",
        SEV.LOW:      "🔵",
        SEV.OK:       "🟢",
    }
    for a in result.alerts:
        icon = SEV_ICON.get(a.severity, "⚪")
        html = f"""
        <div class="alert-row alert-{a.ui_kind}" style="flex-direction:column;align-items:flex-start;gap:6px;padding:16px 18px;">
            <div style="display:flex;align-items:center;gap:10px;width:100%">
                <div class="alert-dot"></div>
                <strong style="font-size:14px;">{icon} {a.title}</strong>
                <span style="margin-left:auto;font-size:11px;opacity:0.7;font-weight:600;
                             background:rgba(0,0,0,0.06);padding:2px 10px;border-radius:20px;">
                    {a.severity.upper()} · {a.metric}
                </span>
            </div>
            <div style="font-size:13px;opacity:0.85;margin-left:18px;">{a.detail}</div>
            <div style="margin-left:18px;margin-top:4px;display:flex;gap:18px;flex-wrap:wrap;">
                <span style="font-size:12px;font-weight:600;">
                    ⚡ <span style="font-weight:500;">{a.action}</span>
                </span>
            </div>
            <div style="margin-left:18px;">
                <span style="font-size:12px;font-weight:600;">
                    🛡 <span style="font-weight:500;">{a.prevention}</span>
                </span>
            </div>
        </div>"""
        st_obj.markdown(html, unsafe_allow_html=True)


def status_badge_html(result: EngineResult) -> str:
    """Return a small HTML badge for the overall module status."""
    COLOR = {
        SEV.CRITICAL: ("#fff1f2","#9f1239","#f43f5e"),
        SEV.HIGH:     ("#fff7ed","#9a3412","#f97316"),
        SEV.MEDIUM:   ("#fffbeb","#92400e","#f59e0b"),
        SEV.LOW:      ("#eff6ff","#1e40af","#3b82f6"),
        SEV.OK:       ("#f0fdf4","#166534","#22c55e"),
    }
    bg, text, dot = COLOR.get(result.overall_status, COLOR[SEV.LOW])
    return f"""
    <div style="background:{bg};border:1px solid {dot}33;border-radius:10px;
                padding:10px 16px;margin-bottom:10px;display:flex;
                align-items:center;gap:10px;">
        <div style="width:9px;height:9px;border-radius:50%;background:{dot};
                    box-shadow:0 0 6px {dot}88;flex-shrink:0;"></div>
        <div>
            <div style="color:{text};font-size:13px;font-weight:700;">{result.module}</div>
            <div style="color:{text};font-size:11px;opacity:0.75;">{result.status_label}</div>
        </div>
    </div>"""