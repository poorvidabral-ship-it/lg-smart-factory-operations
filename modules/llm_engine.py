"""
LG Smart Factory — Enterprise Gemini AI Copilot
Phase 3.1
"""

import streamlit as st

# ─────────────────────────────────────────────
# SAFE GEMINI IMPORT
# ─────────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ─────────────────────────────────────────────
# ENTERPRISE SYSTEM PROMPT
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a senior enterprise industrial AI operations copilot
for LG Smart Factory.

Your responsibilities:
- Analyze manufacturing KPIs
- Detect operational risks
- Explain root causes
- Recommend corrective actions
- Suggest preventive strategies
- Predict operational impact
- Identify escalation severity

You are NOT a chatbot.

You behave like:
- senior manufacturing consultant
- industrial operations strategist
- factory intelligence analyst

Always provide:
- detailed operational reasoning
- realistic industrial recommendations
- enterprise-focused analysis

Use this EXACT format:

🏭 FACTORY STATUS:
Provide 2-3 lines summarizing overall operational condition.

🔍 ROOT CAUSE ANALYSIS:
Provide detailed reasoning explaining likely causes
behind operational issues.

⚡ IMMEDIATE ACTIONS:
1. Action one
2. Action two
3. Action three

🛡 PREVENTION STRATEGY:
Provide detailed long-term prevention strategies.

📊 RISK OUTLOOK:
Explain future operational impact if issues remain unresolved.

Rules:
- Be professional
- Be operationally realistic
- Be concise but detailed
- Use enterprise language
- Minimum response length: 180 words
- Maximum response length: 400 words
"""

# ─────────────────────────────────────────────
# GET API KEY
# ─────────────────────────────────────────────
def _get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None

# ─────────────────────────────────────────────
# LOAD GEMINI MODEL
# ─────────────────────────────────────────────
def _get_client():
    if not GEMINI_AVAILABLE:
        return None, (
            "⚠ Gemini SDK not installed.\n\n"
            "Run: pip install google-generativeai"
        )

    api_key = _get_api_key()
    if not api_key:
        return None, (
            "⚠ Gemini API key missing.\n\n"
            "Create file: .streamlit/secrets.toml\n"
            'Add line:  GEMINI_API_KEY = "AIzaSy...your-key..."'
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1200,
                top_p=0.95,
            )
        )
        return model, None
    except Exception as e:
        return None, f"⚠ Gemini initialization failed: {str(e)}"

# ─────────────────────────────────────────────
# MAIN FACTORY AI ANALYSIS
# ─────────────────────────────────────────────
def generate_factory_ai_response(
    factory_health,
    avg_downtime,
    critical_machines,
    failed_inspections,
    critical_incidents,
    low_stock_items=0,
    breakdown_risk=0,
    avg_quality_score=0,
    best_shift="",
    worst_line="",
):
    model, err = _get_client()
    if err:
        return err

    # Severity classification
    if factory_health < 75 or critical_incidents > 0 or critical_machines > 2:
        severity = "CRITICAL"
    elif factory_health < 90 or avg_downtime > 25 or failed_inspections > 3:
        severity = "HIGH"
    elif factory_health < 95 or avg_downtime > 15:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    context = f"""
LG SMART FACTORY OPERATIONAL ANALYSIS
Overall Severity Level: {severity}

═══════════════════════════════════
PRODUCTION OPERATIONS
═══════════════════════════════════
• Factory Health Index: {factory_health}%
• Average Downtime: {avg_downtime} minutes
• Machines at Breakdown Risk: {breakdown_risk}
• Highest Downtime Line: {worst_line if worst_line else 'N/A'}
• Best Performing Shift: {best_shift if best_shift else 'N/A'}

═══════════════════════════════════
MAINTENANCE OPERATIONS
═══════════════════════════════════
• Critical High-Risk Machines: {critical_machines}

═══════════════════════════════════
QUALITY OPERATIONS
═══════════════════════════════════
• Failed Inspections: {failed_inspections}
• Average Quality Score: {avg_quality_score}/100

═══════════════════════════════════
WAREHOUSE OPERATIONS
═══════════════════════════════════
• Low Stock Inventory Items: {low_stock_items}

═══════════════════════════════════
SAFETY OPERATIONS
═══════════════════════════════════
• Critical Safety Incidents: {critical_incidents}

═══════════════════════════════════
Provide detailed enterprise operational analysis.
"""

    try:
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        return f"⚠ Gemini Copilot error: {str(e)}"

# ─────────────────────────────────────────────
# PRODUCTION ANALYSIS
# ─────────────────────────────────────────────
def generate_production_analysis(
    factory_health,
    avg_downtime,
    breakdown_risk,
    best_product,
    worst_line,
    total_gap,
):
    model, err = _get_client()
    if err:
        return err

    context = f"""
LG SMART FACTORY — PRODUCTION MODULE ANALYSIS

• Factory Health: {factory_health}%
• Average Downtime: {avg_downtime} min
• Machines at Breakdown Risk: {breakdown_risk}
• Best Performing Product: {best_product}
• Highest Downtime Line: {worst_line}
• Production Output Gap: {total_gap:,} units below target

Analyze production performance and provide operational recommendations.
"""
    try:
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        return f"⚠ Error: {str(e)}"

# ─────────────────────────────────────────────
# MAINTENANCE ANALYSIS
# ─────────────────────────────────────────────
def generate_maintenance_analysis(
    avg_health,
    critical_count,
    pending_tasks,
    worst_machine="",
):
    model, err = _get_client()
    if err:
        return err

    context = f"""
LG SMART FACTORY — MAINTENANCE MODULE ANALYSIS

• Average Machine Health Score: {avg_health}/100
• Critical High-Risk Machines: {critical_count}
• Pending Maintenance Tasks: {pending_tasks}
• Worst Performing Machine: {worst_machine if worst_machine else 'N/A'}

Provide predictive maintenance analysis and repair prioritization.
"""
    try:
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        return f"⚠ Error: {str(e)}"

# ─────────────────────────────────────────────
# SAFETY ANALYSIS
# ─────────────────────────────────────────────
def generate_safety_analysis(
    critical_incidents,
    unresolved,
    affected_employees,
    worst_line="",
):
    model, err = _get_client()
    if err:
        return err

    context = f"""
LG SMART FACTORY — SAFETY MODULE ANALYSIS

• Critical Safety Incidents: {critical_incidents}
• Unresolved Cases: {unresolved}
• Employees Affected: {affected_employees}
• Highest Incident Line: {worst_line if worst_line else 'N/A'}

Provide safety risk assessment and emergency response recommendations.
"""
    try:
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        return f"⚠ Error: {str(e)}"

# ─────────────────────────────────────────────
# PREMIUM UI PANEL
# ─────────────────────────────────────────────
def render_copilot_panel(
    st_obj,
    response,
    title="AI Operational Intelligence"
):
    st_obj.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(255,255,255,0.88));
        border-radius: 24px;
        padding: 34px;
        margin-top: 15px;
        border-left: 8px solid #a50034;
        box-shadow: 0 10px 35px rgba(0,0,0,0.08);
    ">
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:24px;">
            <div style="
                background: linear-gradient(135deg, #7a0026, #a50034);
                color: white;
                padding: 10px 14px;
                border-radius: 12px;
                font-size: 24px;
            ">🤖</div>
            <div>
                <div style="color:#7a0026;font-size:22px;font-weight:800;">{title}</div>
                <div style="color:#94a3b8;font-size:12px;margin-top:3px;">
                    Powered by Gemini 1.5 Flash · LG Smart Factory Copilot
                </div>
            </div>
            <div style="
                margin-left:auto;
                background:rgba(165,0,52,0.08);
                color:#a50034;
                font-size:10px;
                font-weight:700;
                padding:4px 12px;
                border-radius:20px;
                letter-spacing:0.5px;
            ">GEMINI AI</div>
        </div>
        <div style="
            color:#374151;
            font-size:15px;
            line-height:1.9;
            white-space:pre-wrap;
            font-family:'Inter',sans-serif;
        ">{response}</div>
    </div>
    """, unsafe_allow_html=True)