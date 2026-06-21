"""
LG Smart Factory — Digital Twin & Operational Scenario Intelligence (Phase 4.2)
=================================================================================
Advanced simulation engine: impact cascade, cost calculator, recovery prediction,
risk heatmap, resilience scoring, scenario library, and AI strategy mode.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import numpy as np

# ── Cost defaults (₹ per minute) ─────────────────────────────────────────────
DEFAULT_COST_PER_MINUTE = 15000


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SimulationInput:
    scenario_id:           str   = "custom"
    downtime_min:          float = 15.0
    machine_failure_count: int   = 0
    inventory_shortage:    int   = 0
    safety_severity:       str   = "LOW"
    production_load_pct:   float = 100.0
    quality_fail_rate:     int   = 0
    cost_per_minute:       int   = DEFAULT_COST_PER_MINUTE


@dataclass
class ImpactCascade:
    production_drop_pct:   float
    inventory_delay_hrs:   float
    delivery_risk:         str       # LOW / MEDIUM / HIGH / CRITICAL
    customer_impact:       str
    cascade_summary:       str


@dataclass
class RecoveryEstimate:
    recovery_hours:        float
    engineers_required:    int
    units_lost_during:     int
    cost_of_recovery:      int
    recommendation:        str


@dataclass
class LineRisk:
    line_id:   str
    risk:      str       # LOW / MEDIUM / HIGH / CRITICAL
    score:     float     # 0-100


@dataclass
class SimulationResult:
    production_impact_pct:  float
    production_loss_units:  int
    risk_level:             str
    maintenance_pressure:   str
    quality_impact_pct:     float
    safety_escalation:      str
    health_impact:          float
    financial_loss:         int
    resilience_score:       float
    recovery:               Optional[RecoveryEstimate] = None
    cascade:                Optional[ImpactCascade]    = None
    line_risks:             List[LineRisk]             = field(default_factory=list)
    strategy:               str                        = ""
    recommended_action:     str                        = ""
    confidence:             float                      = 0.0
    scenario_name:          str                        = "Custom Scenario"
    summary:                str                        = ""
    details:                List[str]                  = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO LIBRARY
# ─────────────────────────────────────────────────────────────────────────────
SCENARIOS = {
    "machine_breakdown": {
        "name": "Machine Breakdown",
        "params": SimulationInput(
            scenario_id="machine_breakdown",
            downtime_min=40, machine_failure_count=2,
            inventory_shortage=5, safety_severity="MEDIUM",
            production_load_pct=85, quality_fail_rate=3,
        ),
    },
    "warehouse_shortage": {
        "name": "Warehouse Shortage",
        "params": SimulationInput(
            scenario_id="warehouse_shortage",
            downtime_min=10, machine_failure_count=0,
            inventory_shortage=40, safety_severity="LOW",
            production_load_pct=70, quality_fail_rate=0,
        ),
    },
    "quality_crisis": {
        "name": "Quality Crisis",
        "params": SimulationInput(
            scenario_id="quality_crisis",
            downtime_min=20, machine_failure_count=1,
            inventory_shortage=5, safety_severity="LOW",
            production_load_pct=90, quality_fail_rate=8,
        ),
    },
    "safety_incident": {
        "name": "Safety Incident",
        "params": SimulationInput(
            scenario_id="safety_incident",
            downtime_min=30, machine_failure_count=1,
            inventory_shortage=0, safety_severity="CRITICAL",
            production_load_pct=80, quality_fail_rate=0,
        ),
    },
    "peak_demand": {
        "name": "Peak Production Demand",
        "params": SimulationInput(
            scenario_id="peak_demand",
            downtime_min=5, machine_failure_count=0,
            inventory_shortage=15, safety_severity="LOW",
            production_load_pct=140, quality_fail_rate=2,
        ),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# IMPACT CASCADE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def compute_impact_cascade(
    loss_pct: float, machine_failures: int,
    inventory_shortage: int, quality_fail_rate: int
) -> ImpactCascade:
    """
    Chain effects: machine failure -> production drop -> inventory delay
    -> delivery risk -> customer impact.
    """
    prod_factor = loss_pct / 100.0
    inv_delay = prod_factor * 24 + machine_failures * 3 + inventory_shortage * 0.2
    inv_delay = round(min(inv_delay, 72), 1)

    del_score = prod_factor * 80 + machine_failures * 10 + inventory_shortage * 0.5
    if del_score >= 50:
        delivery_risk = "CRITICAL"
    elif del_score >= 30:
        delivery_risk = "HIGH"
    elif del_score >= 15:
        delivery_risk = "MEDIUM"
    else:
        delivery_risk = "LOW"

    cust_score = del_score + quality_fail_rate * 3
    if cust_score >= 60:
        customer_impact = "Major customer contracts at risk — expedite recovery"
    elif cust_score >= 35:
        customer_impact = "Potential delivery delays — notify key clients"
    elif cust_score >= 15:
        customer_impact = "Minor customer impact expected — monitor closely"
    else:
        customer_impact = "Minimal customer impact expected"

    cascade_parts = []
    if loss_pct > 5:
        cascade_parts.append(f"Production drops {loss_pct:.1f}% causing inventory depletion")
    if inv_delay > 4:
        cascade_parts.append(f"Inventory replenishment delayed by {inv_delay} hrs")
    if delivery_risk in ("HIGH", "CRITICAL"):
        cascade_parts.append(f"Delivery risk at {delivery_risk} — customer fulfillment threatened")

    return ImpactCascade(
        production_drop_pct=loss_pct,
        inventory_delay_hrs=inv_delay,
        delivery_risk=delivery_risk,
        customer_impact=customer_impact,
        cascade_summary=" -> ".join(cascade_parts) if cascade_parts else "Stable - no cascade effects",
    )


# ─────────────────────────────────────────────────────────────────────────────
# COST IMPACT CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────
def compute_financial_loss(
    downtime_min: float, machine_failures: int,
    loss_units: int, cost_per_minute: int
) -> int:
    """Calculate total financial impact in ₹."""
    dt_cost = downtime_min * cost_per_minute
    fail_cost = machine_failures * cost_per_minute * 20
    unit_cost = loss_units * 150  # ₹150 per unit
    return dt_cost + fail_cost + unit_cost


# ─────────────────────────────────────────────────────────────────────────────
# RECOVERY SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────
def estimate_recovery(
    downtime_min: float, machine_failures: int,
    loss_units: int, financial_loss: int
) -> RecoveryEstimate:
    """Predict recovery time, team size, and cost."""
    base_hrs = downtime_min / 60.0
    recovery_hrs = base_hrs + machine_failures * 2.5
    recovery_hrs = round(max(recovery_hrs, 0.5), 1)

    engineers = max(1, int(np.ceil(machine_failures * 1.5 + downtime_min / 30)))
    units_lost = int(loss_units * (recovery_hrs / 8))
    recovery_cost = int(financial_loss * 0.15)

    if machine_failures >= 2 or downtime_min >= 45:
        rec = f"Activate emergency maintenance protocol. Deploy {engineers} engineers for {recovery_hrs}h recovery operation."
    elif machine_failures >= 1 or downtime_min >= 20:
        rec = f"Schedule {engineers} engineer(s) for {recovery_hrs}h repair. Prepare backup equipment."
    else:
        rec = f"Standard maintenance team ({engineers} engineer(s)) can handle in {recovery_hrs}h."

    return RecoveryEstimate(
        recovery_hours=recovery_hrs,
        engineers_required=engineers,
        units_lost_during=units_lost,
        cost_of_recovery=recovery_cost,
        recommendation=rec,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LINE RISK HEATMAP
# ─────────────────────────────────────────────────────────────────────────────
def compute_line_risks(
    downtime_min: float, machine_failures: int,
    inventory_shortage: int, safety_severity: str,
    quality_fail_rate: int
) -> List[LineRisk]:
    """Generate per-line risk scores for the heatmap."""
    lines = ["Line-1", "Line-2", "Line-3", "Line-4"]
    sev_scores = {"LOW": 5, "MEDIUM": 25, "HIGH": 55, "CRITICAL": 80}

    # Simulate differential impact per line
    base = downtime_min * 0.6 + machine_failures * 10 + sev_scores.get(safety_severity, 0) * 0.3
    results = []
    for i, line in enumerate(lines):
        offset = [0, -5, 15, -8][i]
        score = base + offset + quality_fail_rate * 2 + max(0, inventory_shortage - 10 * (i + 1)) * 0.2
        score = min(max(score, 0), 100)

        if score >= 65:
            risk = "CRITICAL"
        elif score >= 45:
            risk = "HIGH"
        elif score >= 20:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        results.append(LineRisk(line, risk, round(score, 1)))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# FACTORY RESILIENCE SCORE
# ─────────────────────────────────────────────────────────────────────────────
def compute_resilience_score(
    loss_pct: float, risk_level: str, maint_pressure: str,
    safety_esc: str, quality_change: float, health_impact: float
) -> float:
    """
    Calculate 0–100 Factory Resilience Score from multiple dimensions.
    Higher = more resilient.
    """
    sev_penalty = {"CRITICAL": 35, "HIGH": 22, "MEDIUM": 10, "LOW": 3, "OK": 0}
    prod_score = max(0, 100 - loss_pct * 1.2)
    risk_penalty = sev_penalty.get(risk_level, 10)
    maint_penalty = sev_penalty.get(maint_pressure, 5)
    safety_penalty = sev_penalty.get(safety_esc, 5)
    qual_score = max(0, 100 + quality_change * 1.5)
    health_score = health_impact

    score = (
        prod_score * 0.25
        + (100 - risk_penalty) * 0.20
        + (100 - maint_penalty) * 0.15
        + (100 - safety_penalty) * 0.15
        + qual_score * 0.10
        + health_score * 0.15
    )
    return round(min(max(score, 0), 100), 1)


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTIVE RECOMMENDATION
# ─────────────────────────────────────────────────────────────────────────────
def generate_executive_action(
    risk_level: str, loss_pct: float, machine_failures: int,
    safety_esc: str, downtime_min: float, financial_loss: int
) -> tuple:
    """
    Generate recommended executive action and confidence score.
    Returns (action, confidence).
    """
    if risk_level == "CRITICAL":
        if safety_esc in ("CRITICAL", "HIGH"):
            action = "STOP ALL AFFECTED LINES. Initiate emergency safety protocol. Escalate to plant director."
        elif machine_failures >= 2:
            action = "Activate backup production lines. Deploy emergency maintenance team. Notify supply chain."
        else:
            action = "Halt affected operations. Mobilise cross-functional response team within 30 min."
        conf = 92 if downtime_min > 30 else 85
    elif risk_level == "HIGH":
        action = "Schedule corrective maintenance within 2h. Redistribute load to stable lines. Alert operations manager."
        conf = 78
    elif risk_level == "MEDIUM":
        action = "Increase monitoring frequency. Prepare contingency resources. Brief shift supervisor."
        conf = 65
    else:
        action = "Continue normal operations. Monitor key metrics as per standard schedule."
        conf = 55

    if loss_pct > 30:
        action += " | Financial exposure significant — engage finance team."
    elif financial_loss > 500000:
        action += " | Financial impact flagged for management review."

    return (action, conf)


# ─────────────────────────────────────────────────────────────────────────────
# GENERATE STRATEGY CONTEXT FOR GEMINI
# ─────────────────────────────────────────────────────────────────────────────
def build_strategy_context(result: SimulationResult, scenario_name: str) -> str:
    """Build structured context string for Gemini strategy analysis."""
    return f"""
FACTORY SCENARIO ANALYSIS REQUEST

Scenario: {scenario_name}

Simulation Results:
- Production Impact: {result.production_impact_pct}% ({result.production_loss_units:,} units)
- Operational Risk Level: {result.risk_level}
- Maintenance Pressure: {result.maintenance_pressure}
- Safety Escalation: {result.safety_escalation}
- Quality Impact: {result.quality_impact_pct} points
- Fleet Health Impact: {result.health_impact}/100
- Financial Impact: ₹{result.financial_loss:,}
- Resilience Score: {result.resilience_score}/100

Impact Cascade:
- Inventory Delay: {result.cascade.inventory_delay_hrs if result.cascade else 'N/A'} hrs
- Delivery Risk: {result.cascade.delivery_risk if result.cascade else 'N/A'}
- Customer Impact: {result.cascade.customer_impact if result.cascade else 'N/A'}

Recovery Estimate:
- Recovery Time: {result.recovery.recovery_hours if result.recovery else 'N/A'} hrs
- Engineers Required: {result.recovery.engineers_required if result.recovery else 'N/A'}
- Units Lost During Recovery: {result.recovery.units_lost_during if result.recovery else 'N/A'}

Provide:
1. Strategic operational assessment
2. Recommended mitigation strategy
3. Resource allocation plan
4. Timeline for恢复正常 operations
5. Risk mitigation measures
"""


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SIMULATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def simulate_factory_conditions(
    params: SimulationInput,
    base_health: float = 85.0,
    base_quality: float = 85.0,
    base_target: int = 6000
) -> SimulationResult:
    """
    Full digital twin simulation: calculates operational, financial, cascade,
    recovery, heatmap, resilience, and executive recommendation.
    """
    # ── Production impact ─────────────────────────────────────────────────
    dt_factor = params.downtime_min / 60.0
    fail_factor = params.machine_failure_count * 0.08
    load_factor = abs(params.production_load_pct - 100) / 100.0
    load_penalty = load_factor * 0.15 if params.production_load_pct > 100 else -load_factor * 0.05
    loss_pct = min(dt_factor * 0.4 + fail_factor + load_penalty, 0.85)
    loss_pct = max(loss_pct, -0.05)
    loss_units = int(base_target * loss_pct)
    loss_pct = round(loss_pct * 100, 1)

    # ── Risk escalation ──────────────────────────────────────────────────
    risk_score = 25.0 + params.downtime_min * 0.8 + params.machine_failure_count * 12 + params.quality_fail_rate * 3
    risk_score = min(risk_score, 100)
    risk_level = "CRITICAL" if risk_score >= 75 else "HIGH" if risk_score >= 50 else "MEDIUM" if risk_score >= 25 else "LOW"

    # ── Maintenance pressure ──────────────────────────────────────────────
    maint_score = params.machine_failure_count * 20 + params.downtime_min * 1.2
    maint_pressure = "CRITICAL" if maint_score >= 70 else "HIGH" if maint_score >= 45 else "MEDIUM" if maint_score >= 20 else "LOW"

    # ── Quality impact ────────────────────────────────────────────────────
    qual_impact = params.downtime_min * 0.15 + params.machine_failure_count * 4.0 + params.quality_fail_rate * 3
    if params.production_load_pct > 110:
        qual_impact += (params.production_load_pct - 110) * 0.5
    new_quality = max(base_quality - qual_impact, 15)
    new_quality = min(new_quality, 100)
    quality_change = round(new_quality - base_quality, 1)

    # ── Safety escalation ─────────────────────────────────────────────────
    sev_scores = {"LOW": 0, "MEDIUM": 20, "HIGH": 50, "CRITICAL": 80}
    saf_score = sev_scores.get(params.safety_severity.upper(), 0) + params.machine_failure_count * 8
    saf_score += max(0, params.downtime_min - 20) * 1.5
    safety_esc = "CRITICAL" if saf_score >= 70 else "HIGH" if saf_score >= 40 else "MEDIUM" if saf_score >= 15 else "LOW"

    # ── Health impact ─────────────────────────────────────────────────────
    health_impact = max(base_health - params.downtime_min * 0.3 - params.machine_failure_count * 5, 10)
    health_impact = round(min(health_impact, 100), 1)

    # ── Financial impact ──────────────────────────────────────────────────
    financial_loss = compute_financial_loss(
        params.downtime_min, params.machine_failure_count, loss_units, params.cost_per_minute
    )

    # ── Impact cascade ────────────────────────────────────────────────────
    cascade = compute_impact_cascade(loss_pct, params.machine_failure_count,
                                     params.inventory_shortage, params.quality_fail_rate)

    # ── Recovery estimate ─────────────────────────────────────────────────
    recovery = estimate_recovery(params.downtime_min, params.machine_failure_count, loss_units, financial_loss)

    # ── Line risk heatmap ─────────────────────────────────────────────────
    line_risks = compute_line_risks(
        params.downtime_min, params.machine_failure_count,
        params.inventory_shortage, params.safety_severity, params.quality_fail_rate
    )

    # ── Resilience score ──────────────────────────────────────────────────
    resilience = compute_resilience_score(
        loss_pct, risk_level, maint_pressure, safety_esc, quality_change, health_impact
    )

    # ── Executive recommendation ──────────────────────────────────────────
    action, confidence = generate_executive_action(
        risk_level, loss_pct, params.machine_failure_count, safety_esc,
        params.downtime_min, financial_loss
    )

    # ── Scenario name ─────────────────────────────────────────────────────
    scenario_name = SCENARIOS.get(params.scenario_id, {}).get("name", "Custom Scenario")

    # ── Summary ────────────────────────────────────────────────────────────
    parts = []
    if loss_pct > 5:
        parts.append(f"Production drops {loss_pct:.1f}% ({loss_units:,} units/day)")
    if risk_level in ("HIGH", "CRITICAL"):
        parts.append(f"Risk at {risk_level}")
    if maint_pressure in ("HIGH", "CRITICAL"):
        parts.append(f"Maintenance at {maint_pressure}")
    if safety_esc in ("HIGH", "CRITICAL"):
        parts.append(f"Safety at {safety_esc}")
    if quality_change < -3:
        parts.append(f"Quality -{abs(quality_change):.1f}pts")
    summary = " | ".join(parts) if parts else "Minimal operational impact expected"

    # ── Details ───────────────────────────────────────────────────────────
    details = [
        f"Downtime {params.downtime_min} min → production impact {loss_pct}%",
        f"{params.machine_failure_count} machine failure(s) → risk score {risk_score}",
        f"Quality estimate: {new_quality}/100 ({quality_change:+.1f} change)",
        f"Maintenance pressure: {maint_pressure}",
        f"Safety escalation: {safety_esc}",
        f"Fleet health: {health_impact}/100",
        f"Financial loss: ₹{financial_loss:,}",
        f"Resilience score: {resilience}/100",
        f"Recovery: {recovery.recovery_hours}h with {recovery.engineers_required} engineers",
        f"Production load: {params.production_load_pct}% of capacity",
    ]

    return SimulationResult(
        production_impact_pct=loss_pct,
        production_loss_units=loss_units,
        risk_level=risk_level,
        maintenance_pressure=maint_pressure,
        quality_impact_pct=quality_change,
        safety_escalation=safety_esc,
        health_impact=health_impact,
        financial_loss=financial_loss,
        resilience_score=resilience,
        recovery=recovery,
        cascade=cascade,
        line_risks=line_risks,
        recommended_action=action,
        confidence=confidence,
        scenario_name=scenario_name,
        summary=summary,
        details=details,
    )
