"""
LG Smart Factory — Agentic AI Operations System (Phase 4.1)
============================================================
Multi-agent architecture: each domain has a specialized AI agent
that continuously monitors, assesses risk, and escalates.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class AgentDecision:
    agent_name:     str               # "Production Agent"
    severity:       str               # CRITICAL / HIGH / MEDIUM / LOW / OK
    priority:       int               # 0–100 score
    issue:          str               # Short headline
    detail:         str               # What was detected
    action:         str               # Recommended action
    metric:         str = ""          # Key metric value
    module_key:     str = ""          # matching engine key


@dataclass
class CoordinatorReport:
    overall_severity:  str
    overall_priority:  int
    summary:           str
    decisions:         List[AgentDecision] = field(default_factory=list)
    cross_correlations: List[str]          = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTION AGENT
# ─────────────────────────────────────────────────────────────────────────────
def production_agent(df: pd.DataFrame) -> AgentDecision:
    """
    Monitors efficiency, detects bottlenecks, tracks downtime.
    """
    if df.empty:
        return AgentDecision("Production Agent", "OK", 0,
                             "No production data", "", "",
                             module_key="production")

    total_target = df["Target"].sum()
    total_actual = df["Actual"].sum()
    avg_dt = df["Downtime_min"].mean()
    health = round((total_actual / total_target) * 100, 1) if total_target > 0 else 0
    breakdown_risk = len(df[df["Machine_Status"] == "Breakdown Risk"])
    line_dt = df.groupby("Prod_line")["Downtime_min"].sum()
    worst_line = str(line_dt.idxmax()) if not line_dt.empty else ""
    worst_dt = int(line_dt.max()) if not line_dt.empty else 0

    gap = total_target - total_actual
    gap_pct = round((gap / total_target) * 100, 1) if total_target > 0 else 0

    issues = []
    priority = 0

    if health < 75:
        issues.append(f"Factory health critical at {health}%")
        priority = max(priority, 90)
    elif health < 90:
        issues.append(f"Factory health below target at {health}%")
        priority = max(priority, 60)
    else:
        priority = max(priority, 10)

    if avg_dt > 30:
        issues.append(f"Avg downtime {avg_dt:.1f} min exceeds critical threshold")
        priority = max(priority, 85)
    elif avg_dt > 20:
        issues.append(f"Avg downtime {avg_dt:.1f} min above warning level")
        priority = max(priority, 55)

    if worst_dt > 45:
        issues.append(f"Downtime spike on {worst_line}: {worst_dt} min")
        priority = max(priority, 80)

    if breakdown_risk > 0:
        issues.append(f"{breakdown_risk} machine(s) at breakdown risk")
        priority = max(priority, 75)

    if gap_pct > 10:
        issues.append(f"Output gap {gap_pct}% — {int(gap):,} units below target")
        priority = max(priority, 50)

    if not issues:
        return AgentDecision("Production Agent", "OK", 10,
                             f"Production stable at {health}% health",
                             f"All lines nominal. Avg downtime {avg_dt:.1f} min.",
                             "Continue standard operations.",
                             metric=f"{health}%", module_key="production")

    severity = "CRITICAL" if priority >= 80 else "HIGH" if priority >= 55 else "MEDIUM"
    issue_text = issues[0]
    detail_text = "; ".join(issues[:3])
    action_text = "Immediate intervention required" if severity == "CRITICAL" else \
                  "Schedule corrective action" if severity == "HIGH" else "Monitor closely"

    return AgentDecision("Production Agent", severity, priority,
                         issue_text, detail_text, action_text,
                         metric=f"{health}% health · {avg_dt:.1f}m DT",
                         module_key="production")


# ─────────────────────────────────────────────────────────────────────────────
# MAINTENANCE AGENT
# ─────────────────────────────────────────────────────────────────────────────
def maintenance_agent(df: pd.DataFrame) -> AgentDecision:
    """
    Monitors machine health, predicts breakdowns, prioritizes maintenance.
    """
    if df.empty:
        return AgentDecision("Maintenance Agent", "OK", 0,
                             "No maintenance data", "", "",
                             module_key="maintenance")

    avg_health = df["Health_Score"].mean()
    critical = len(df[df["Risk_Level"] == "High"])
    pending = len(df[df["Maintenance_Status"] == "Pending"])
    low_health = len(df[df["Health_Score"] < 40])

    issues = []
    priority = 0

    if low_health > 0:
        issues.append(f"{low_health} machine(s) below critical health score of 40")
        priority = max(priority, 95)

    if critical >= 3:
        issues.append(f"{critical} high-risk machines exceed safe threshold")
        priority = max(priority, 85)
    elif critical > 0:
        issues.append(f"{critical} high-risk machine(s) detected")
        priority = max(priority, 60)

    if avg_health < 60:
        issues.append(f"Fleet health {avg_health:.1f}/100 below warning level")
        priority = max(priority, 70)
    elif avg_health < 80:
        issues.append(f"Fleet health {avg_health:.1f}/100 needs attention")
        priority = max(priority, 40)

    if pending > 5:
        issues.append(f"Maintenance backlog: {pending} tasks pending")
        priority = max(priority, 65)
    elif pending > 2:
        issues.append(f"{pending} maintenance tasks awaiting execution")
        priority = max(priority, 35)

    if not issues:
        return AgentDecision("Maintenance Agent", "OK", 10,
                             f"Fleet healthy at {avg_health:.1f}/100",
                             f"{critical} critical, {pending} pending tasks.",
                             "Continue preventive maintenance schedule.",
                             metric=f"{avg_health:.1f}/100", module_key="maintenance")

    severity = "CRITICAL" if priority >= 80 else "HIGH" if priority >= 55 else "MEDIUM"
    action_text = "Immediate maintenance escalation" if severity == "CRITICAL" else \
                  "Schedule repair within shift" if severity == "HIGH" else "Increase monitoring"

    return AgentDecision("Maintenance Agent", severity, priority,
                         issues[0], "; ".join(issues[:3]), action_text,
                         metric=f"{avg_health:.1f}/100 · {critical} critical",
                         module_key="maintenance")


# ─────────────────────────────────────────────────────────────────────────────
# SAFETY AGENT
# ─────────────────────────────────────────────────────────────────────────────
def safety_agent(df: pd.DataFrame) -> AgentDecision:
    """
    Monitors safety incidents, classifies severity, escalates hazards.
    """
    if df.empty:
        return AgentDecision("Safety Agent", "OK", 0,
                             "No safety data", "", "",
                             module_key="safety")

    total = len(df)
    critical_cnt = len(df[df["Severity"] == "Critical"])
    affected = int(df["Employees_Affected"].sum())
    unresolved = len(df[df["Safety_Status"] != "Resolved"])

    issues = []
    priority = 0

    if critical_cnt > 0:
        lines = df[df["Severity"] == "Critical"]["Prod_line"].unique()
        issues.append(f"{critical_cnt} CRITICAL incident(s) on {', '.join(str(l) for l in lines)}")
        priority = max(priority, 100)

    if unresolved >= 3:
        issues.append(f"{unresolved} incidents unresolved — compounding risk")
        priority = max(priority, 80)
    elif unresolved > 0:
        issues.append(f"{unresolved} open incident(s) need resolution")
        priority = max(priority, 50)

    if affected >= 10:
        issues.append(f"{affected} employees affected by safety incidents")
        priority = max(priority, 75)
    elif affected >= 5:
        issues.append(f"{affected} employees affected")
        priority = max(priority, 45)

    if total > 0 and critical_cnt == 0:
        issues.append(f"{total} non-critical incident(s) logged today")
        priority = max(priority, 20)

    if not issues:
        return AgentDecision("Safety Agent", "OK", 0,
                             "No safety incidents", "All clear.",
                             "Continue standard monitoring.",
                             module_key="safety")

    severity = "CRITICAL" if priority >= 80 else "HIGH" if priority >= 55 else "MEDIUM"
    action_text = "EMERGENCY: Stop affected lines, evacuate if needed" if severity == "CRITICAL" else \
                  "Escalate to HSE officer within the hour" if severity == "HIGH" else "Log and monitor"

    return AgentDecision("Safety Agent", severity, priority,
                         issues[0], "; ".join(issues[:3]), action_text,
                         metric=f"{critical_cnt} critical · {affected} affected",
                         module_key="safety")


# ─────────────────────────────────────────────────────────────────────────────
# WAREHOUSE AGENT
# ─────────────────────────────────────────────────────────────────────────────
def warehouse_agent(df: pd.DataFrame) -> AgentDecision:
    """
    Monitors inventory, detects shortages, analyzes supply risk.
    """
    if df.empty:
        return AgentDecision("Warehouse Agent", "OK", 0,
                             "No warehouse data", "", "",
                             module_key="warehouse")

    total_skus = len(df)
    low_stock = len(df[df["Current_stock"] < df["Minimum_stock"]])
    zero_stock = len(df[df["Current_stock"] == 0])
    stock_health = round(((total_skus - low_stock) / total_skus) * 100, 1) if total_skus > 0 else 100

    issues = []
    priority = 0

    if zero_stock > 0:
        items = df[df["Current_stock"] == 0]["Category"].unique() if "Category" in df.columns else []
        issues.append(f"{zero_stock} item(s) at ZERO stock — production halt risk")
        priority = max(priority, 95)

    if low_stock >= 5:
        issues.append(f"{low_stock} SKUs below minimum — critical shortage risk")
        priority = max(priority, 80)
    elif low_stock >= 2:
        issues.append(f"{low_stock} SKUs below minimum threshold")
        priority = max(priority, 55)
    elif low_stock > 0:
        issues.append(f"{low_stock} SKU(s) approaching stock shortage")
        priority = max(priority, 30)

    if stock_health < 80:
        issues.append(f"Stock health {stock_health}% — supply chain risk")
        priority = max(priority, 60)

    if not issues:
        return AgentDecision("Warehouse Agent", "OK", 5,
                             f"Stock healthy at {stock_health}%",
                             f"All {total_skus} SKUs above minimum thresholds.",
                             "Continue standard replenishment.",
                             metric=f"{stock_health}%", module_key="warehouse")

    severity = "CRITICAL" if priority >= 80 else "HIGH" if priority >= 55 else "MEDIUM"
    action_text = "Emergency procurement required" if severity == "CRITICAL" else \
                  "Place replenishment orders within 24h" if severity == "HIGH" else "Review stock levels"

    return AgentDecision("Warehouse Agent", severity, priority,
                         issues[0], "; ".join(issues[:3]), action_text,
                         metric=f"{low_stock} low · {zero_stock} zero",
                         module_key="warehouse")


# ─────────────────────────────────────────────────────────────────────────────
# QUALITY AGENT
# ─────────────────────────────────────────────────────────────────────────────
def quality_agent(df: pd.DataFrame) -> AgentDecision:
    """
    Tracks inspection failures, identifies defect spikes, monitors consistency.
    """
    if df.empty:
        return AgentDecision("Quality Agent", "OK", 0,
                             "No quality data", "", "",
                             module_key="quality")

    total = len(df)
    failed = len(df[df["Inspection_Status"] == "Failed"])
    defects = int(df["Defective_Units"].sum())
    avg_score = df["Quality_Score"].mean()

    issues = []
    priority = 0

    if avg_score < 65:
        issues.append(f"Quality score {avg_score:.1f} — critical defect risk")
        priority = max(priority, 90)
    elif avg_score < 75:
        issues.append(f"Quality score {avg_score:.1f} below acceptable level")
        priority = max(priority, 65)
    elif avg_score < 85:
        issues.append(f"Quality score {avg_score:.1f} needs improvement")
        priority = max(priority, 35)

    if failed >= 5:
        issues.append(f"{failed} inspections failed — {round(failed/total*100,1)}% failure rate")
        priority = max(priority, 85)
    elif failed >= 2:
        issues.append(f"{failed} inspections failed today")
        priority = max(priority, 50)
    elif failed > 0:
        issues.append(f"{failed} inspection failure(s) detected")
        priority = max(priority, 25)

    if defects > 100:
        issues.append(f"{defects:,} defective units — major quality incident")
        priority = max(priority, 80)
    elif defects > 50:
        issues.append(f"{defects:,} defective units logged")
        priority = max(priority, 55)
    elif defects > 0:
        issues.append(f"{defects} defective units detected")
        priority = max(priority, 20)

    if not issues:
        return AgentDecision("Quality Agent", "OK", 5,
                             f"Quality nominal at {avg_score:.1f}/100",
                             f"All inspections passed. {defects} defects.",
                             "Continue standard quality monitoring.",
                             metric=f"{avg_score:.1f}/100", module_key="quality")

    severity = "CRITICAL" if priority >= 80 else "HIGH" if priority >= 55 else "MEDIUM"
    action_text = "Stop shipment, initiate full re-inspection" if severity == "CRITICAL" else \
                  "Quarantine affected batches" if severity == "HIGH" else "Increase sampling frequency"

    return AgentDecision("Quality Agent", severity, priority,
                         issues[0], "; ".join(issues[:3]), action_text,
                         metric=f"{avg_score:.1f}/100 · {defects} defects",
                         module_key="quality")


# ─────────────────────────────────────────────────────────────────────────────
# AGENT COORDINATOR
# ─────────────────────────────────────────────────────────────────────────────
def agent_coordinator(prod_df, maint_df, wh_df, qual_df, safety_df) -> CoordinatorReport:
    """
    Runs all agents, combines results, detects cross-domain correlations.
    """
    decisions = [
        production_agent(prod_df),
        maintenance_agent(maint_df),
        warehouse_agent(wh_df),
        quality_agent(qual_df),
        safety_agent(safety_df),
    ]

    # Overall priority = weighted average of top agents
    priorities = sorted([d.priority for d in decisions], reverse=True)
    top_3 = priorities[:3]
    overall_priority = int(np.mean(top_3)) if top_3 else 0

    # Overall severity = highest severity across agents
    sev_order = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "OK": 1}
    overall_severity = max(decisions, key=lambda d: sev_order.get(d.severity, 0)).severity

    # Cross-domain correlations
    correlations = []
    prod_d = next(d for d in decisions if d.module_key == "production")
    maint_d = next(d for d in decisions if d.module_key == "maintenance")
    qual_d = next(d for d in decisions if d.module_key == "quality")
    safety_d = next(d for d in decisions if d.module_key == "safety")
    wh_d = next(d for d in decisions if d.module_key == "warehouse")

    high_agents = [d for d in decisions if d.severity in ("CRITICAL", "HIGH")]

    if len(high_agents) >= 3:
        names = " + ".join(d.agent_name.replace(" Agent", "") for d in high_agents[:3])
        correlations.append(f"⚠ Multi-domain crisis: {names} all report elevated risk — coordinated response required")

    if prod_d.severity in ("CRITICAL", "HIGH") and maint_d.severity in ("CRITICAL", "HIGH"):
        correlations.append("🔗 Production-Maintenance correlation: Downtime likely driven by machine health degradation")

    if maint_d.severity in ("CRITICAL", "HIGH") and qual_d.severity in ("CRITICAL", "HIGH"):
        correlations.append("🔗 Maintenance-Quality correlation: Machine health decline may be causing defect spike")

    if wh_d.severity in ("CRITICAL", "HIGH") and prod_d.severity in ("CRITICAL", "HIGH"):
        correlations.append("🔗 Warehouse-Production correlation: Material shortages impacting output")

    if safety_d.severity in ("CRITICAL", "HIGH"):
        correlations.append("🚨 Safety escalation active: All non-critical operations should review safety protocols")

    if not correlations:
        if overall_severity == "OK":
            correlations.append("✅ All agents report nominal — no cross-domain issues detected")
        else:
            correlations.append("ℹ No significant cross-domain correlations at this time")

    # Summary
    sev_labels = {"CRITICAL": "🔴 CRISIS", "HIGH": "🟠 ELEVATED", "MEDIUM": "🟡 MODERATE", "LOW": "🔵 LOW", "OK": "🟢 NOMINAL"}
    critical_count = len([d for d in decisions if d.severity == "CRITICAL"])
    high_count = len([d for d in decisions if d.severity == "HIGH"])
    nominal_count = len([d for d in decisions if d.severity == "OK"])

    if critical_count > 0:
        summary = f"{sev_labels[overall_severity]} — {critical_count} critical, {high_count} high — immediate cross-functional response required"
    elif high_count > 0:
        summary = f"{sev_labels[overall_severity]} — {high_count} agents escalated — coordinated action recommended"
    elif nominal_count == 5:
        summary = f"{sev_labels[overall_severity]} — All 5 agents report normal operations"
    else:
        summary = f"{sev_labels[overall_severity]} — {5 - nominal_count} agent(s) flagged minor issues"

    return CoordinatorReport(
        overall_severity=overall_severity,
        overall_priority=overall_priority,
        summary=summary,
        decisions=decisions,
        cross_correlations=correlations,
    )
