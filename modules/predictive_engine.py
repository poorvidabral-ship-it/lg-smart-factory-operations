"""
LG Smart Factory — Predictive Maintenance Engine (Phase 3.2)
=============================================================
Calculates breakdown probability, risk scores, urgency,
operational impact, and generates predictive alerts.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class MachinePrediction:
    machine_id:      str
    health_score:    float
    risk_score:      float          # 0–100
    breakdown_prob:  float          # 0–100 (%)
    urgency:         str            # LOW / MEDIUM / HIGH / CRITICAL
    impact_units:    int            # potential production loss per day
    impact_label:    str            # human-readable
    status:          str            # operational status suggestion
    alert:           str            # short alert text
    recommendation:  str            # action to take


@dataclass
class PredictiveReport:
    fleet_avg_risk:       float
    critical_count:       int
    high_count:           int
    medium_count:         int
    low_count:            int
    total_impact_units:   int
    predictions:          List[MachinePrediction] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# RISK SCORE CALCULATION
# ─────────────────────────────────────────────────────────────────────────────
def calculate_risk_score(health: float, downtime: float, pending_tasks: int) -> float:
    """
    Calculate a 0–100 risk score based on:
    - Health score (lower = higher risk)
    - Downtime (higher = higher risk)
    - Pending maintenance tasks
    """
    health_risk = max(0, 100 - health) * 0.5
    dt_risk = min(downtime / 60 * 100, 100) * 0.3
    task_risk = min(pending_tasks * 10, 100) * 0.2
    return round(min(health_risk + dt_risk + task_risk, 100), 1)


# ─────────────────────────────────────────────────────────────────────────────
# BREAKDOWN PROBABILITY
# ─────────────────────────────────────────────────────────────────────────────
def predict_breakdown_probability(health: float, risk_score: float) -> float:
    """
    Predict breakdown probability percentage using health + risk.
    Uses a weighted formula calibrated to industrial patterns.
    """
    base = max(0, 100 - health) * 0.6
    risk_factor = risk_score * 0.3
    random_variance = np.random.uniform(-3, 3)
    prob = min(base + risk_factor + random_variance, 100)
    return round(max(prob, 0), 1)


# ─────────────────────────────────────────────────────────────────────────────
# MAINTENANCE URGENCY CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────
def classify_maintenance_urgency(risk_score: float, breakdown_prob: float) -> str:
    """
    Classify urgency level based on risk score and breakdown probability.
    """
    if risk_score >= 75 or breakdown_prob >= 70:
        return "CRITICAL"
    elif risk_score >= 55 or breakdown_prob >= 45:
        return "HIGH"
    elif risk_score >= 30 or breakdown_prob >= 20:
        return "MEDIUM"
    return "LOW"


# ─────────────────────────────────────────────────────────────────────────────
# OPERATIONAL IMPACT ESTIMATION
# ─────────────────────────────────────────────────────────────────────────────
def estimate_operational_impact(risk_score: float, breakdown_prob: float, target_per_line: int = 6000) -> tuple:
    """
    Estimate potential production loss in units/day.
    Returns (units, label).
    """
    impact_factor = (risk_score / 100) * (breakdown_prob / 100)
    units = int(impact_factor * target_per_line)
    if units >= 4000:
        label = f"Critical loss: {units:,} units/day"
    elif units >= 2000:
        label = f"High loss: {units:,} units/day"
    elif units >= 500:
        label = f"Moderate loss: {units:,} units/day"
    else:
        label = f"Low impact: {units:,} units/day"
    return (units, label)


# ─────────────────────────────────────────────────────────────────────────────
# GENERATE PREDICTIVE ALERTS
# ─────────────────────────────────────────────────────────────────────────────
def generate_predictive_alerts(predictions: List[MachinePrediction]) -> List[str]:
    """
    Generate human-readable alert strings from predictions.
    """
    alerts = []
    critical = [p for p in predictions if p.urgency == "CRITICAL"]
    high = [p for p in predictions if p.urgency == "HIGH"]

    if critical:
        ids = ", ".join(p.machine_id for p in critical[:3])
        alerts.append(f"🔴 CRITICAL: {len(critical)} machine(s) — {ids} — immediate failure risk")
    if high:
        ids = ", ".join(p.machine_id for p in high[:3])
        alerts.append(f"🟠 HIGH: {len(high)} machine(s) — {ids} — requires urgent inspection")
    if not critical and not high:
        alerts.append("🟢 No predictive alerts — all machines within safe parameters")

    return alerts


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PREDICTIVE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
def run_predictive_analysis(
    maint_df: pd.DataFrame,
    prod_df: Optional[pd.DataFrame] = None,
    target_per_line: int = 6000
) -> PredictiveReport:
    """
    Run full predictive maintenance analysis on the maintenance dataframe.
    Returns a PredictiveReport with per-machine predictions and fleet summary.
    """
    if maint_df.empty:
        return PredictiveReport(
            fleet_avg_risk=0, critical_count=0, high_count=0,
            medium_count=0, low_count=0, total_impact_units=0
        )

    predictions: List[MachinePrediction] = []
    dt_col = next((c for c in ["Downtime_Min", "Downtime_min", "Downtime"]
                   if c in maint_df.columns), None)
    status_col = next((c for c in ["Maintenance_Status", "Status"]
                       if c in maint_df.columns), None)

    for _, row in maint_df.iterrows():
        machine_id = str(row.get("Machine_ID", "Unknown"))
        health = float(row.get("Health_Score", 50))
        downtime = float(row.get(dt_col, 0)) if dt_col else 0
        pending = 1 if status_col and str(row.get(status_col, "")).lower() == "pending" else 0

        risk_score = calculate_risk_score(health, downtime, pending)
        breakdown_prob = predict_breakdown_probability(health, risk_score)
        urgency = classify_maintenance_urgency(risk_score, breakdown_prob)
        impact_units, impact_label = estimate_operational_impact(
            risk_score, breakdown_prob, target_per_line
        )

        if risk_score >= 70:
            status = "STOP REQUIRED"
            rec = "Take offline immediately. Initiate emergency maintenance."
        elif risk_score >= 50:
            status = "SCHEDULE REPAIR"
            rec = "Schedule repair within this shift. Prepare replacement parts."
        elif risk_score >= 25:
            status = "MONITOR CLOSELY"
            rec = "Increase inspection frequency. Monitor key parameters."
        else:
            status = "NORMAL"
            rec = "Continue standard preventive maintenance schedule."

        alert = f"{urgency} risk · {breakdown_prob}% failure prob · {impact_label}"

        predictions.append(MachinePrediction(
            machine_id=machine_id,
            health_score=health,
            risk_score=risk_score,
            breakdown_prob=breakdown_prob,
            urgency=urgency,
            impact_units=impact_units,
            impact_label=impact_label,
            status=status,
            alert=alert,
            recommendation=rec,
        ))

    critical = [p for p in predictions if p.urgency == "CRITICAL"]
    high = [p for p in predictions if p.urgency == "HIGH"]
    medium = [p for p in predictions if p.urgency == "MEDIUM"]
    low = [p for p in predictions if p.urgency == "LOW"]

    total_impact = sum(p.impact_units for p in predictions)
    avg_risk = round(np.mean([p.risk_score for p in predictions]), 1) if predictions else 0

    return PredictiveReport(
        fleet_avg_risk=avg_risk,
        critical_count=len(critical),
        high_count=len(high),
        medium_count=len(medium),
        low_count=len(low),
        total_impact_units=total_impact,
        predictions=sorted(predictions, key=lambda p: p.risk_score, reverse=True),
    )
