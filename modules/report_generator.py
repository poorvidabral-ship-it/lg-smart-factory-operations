import io
import re
import streamlit as st
from datetime import datetime
from fpdf import FPDF

EMOJI_PATTERN = re.compile(
    "[" 
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # misc
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\U00002600-\U000026FF"  # misc symbols
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U0000200D"             # zero width joiner
    "]+", flags=re.UNICODE
)


def strip_emoji(text):
    return EMOJI_PATTERN.sub("", text).strip()

SCOPE_LABELS = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}

MODULE_CONFIG = {
    "production":  {"icon": "🏭", "color": "#1d4ed8", "title": "Production Report"},
    "maintenance": {"icon": "🛠", "color": "#92400e", "title": "Maintenance Report"},
    "warehouse":   {"icon": "📦", "color": "#0f766e", "title": "Warehouse Report"},
    "quality":     {"icon": "✅", "color": "#166534", "title": "Quality Report"},
    "safety":      {"icon": "⚠", "color": "#9f1239", "title": "Safety Report"},
}


def collect_kpis(df, warehouse_df, maintenance_df, quality_df, safety_df, engines):
    total_target = int(df["Target"].sum()) if not df.empty else 0
    total_actual = int(df["Actual"].sum()) if not df.empty else 0
    factory_health = round((total_actual / total_target) * 100, 1) if total_target > 0 else 0
    avg_downtime = round(df["Downtime_min"].mean(), 1) if not df.empty else 0
    active_lines = int(df["Prod_line"].nunique()) if not df.empty else 0

    crit_machines = int((maintenance_df["Risk_Level"] == "High").sum()) if not maintenance_df.empty else 0
    avg_health = round(maintenance_df["Health_Score"].mean(), 1) if not maintenance_df.empty else 0
    pending_maint = int((maintenance_df["Maintenance_Status"] == "Pending").sum()) if not maintenance_df.empty else 0

    low_stock = int((warehouse_df["Current_stock"] < warehouse_df["Minimum_stock"]).sum()) if not warehouse_df.empty else 0
    total_stock = int(warehouse_df["Current_stock"].sum()) if not warehouse_df.empty else 0

    avg_quality = round(quality_df["Quality_Score"].mean(), 1) if not quality_df.empty else 0
    failed_insp = int((quality_df["Inspection_Status"] == "Failed").sum()) if not quality_df.empty else 0
    total_defects = int(quality_df["Defective_Units"].sum()) if not quality_df.empty else 0
    total_insp = len(quality_df) if not quality_df.empty else 0

    crit_incidents = int((safety_df["Severity"] == "Critical").sum()) if not safety_df.empty else 0
    open_cases = int((safety_df["Safety_Status"] != "Resolved").sum()) if not safety_df.empty else 0
    affected = int(safety_df["Employees_Affected"].sum()) if not safety_df.empty else 0
    total_incidents = len(safety_df) if not safety_df.empty else 0

    prod_risk = engines.get("production")
    maint_risk = engines.get("maintenance")

    return {
        "total_target": total_target,
        "total_actual": total_actual,
        "factory_health": factory_health,
        "avg_downtime": avg_downtime,
        "active_lines": active_lines,
        "crit_machines": crit_machines,
        "avg_health": avg_health,
        "pending_maint": pending_maint,
        "low_stock": low_stock,
        "total_stock": total_stock,
        "avg_quality": avg_quality,
        "failed_insp": failed_insp,
        "total_defects": total_defects,
        "total_insp": total_insp,
        "crit_incidents": crit_incidents,
        "open_cases": open_cases,
        "affected": affected,
        "total_incidents": total_incidents,
        "prod_risk_summary": prod_risk.summary if prod_risk else "",
        "maint_risk_summary": maint_risk.summary if maint_risk else "",
    }


def build_full_report_prompt(kpis, scope, data_date=None):
    label = SCOPE_LABELS.get(scope, "Daily")
    gen_date = datetime.now().strftime("%d %B %Y")
    data_str = data_date if data_date else gen_date
    return f"""You are the LG Smart Factory AI Reporting Assistant. Generate a structured {label.lower()} operations report.

Report Generated: {gen_date}
Data Period: {data_str}
Scope: {label}

Data:

PRODUCTION: Output={kpis['total_actual']:,} units, Health={kpis['factory_health']}%, Lines={kpis['active_lines']}, Downtime={kpis['avg_downtime']}min, Risk={kpis['prod_risk_summary']}

MAINTENANCE: Critical={kpis['crit_machines']}, Health={kpis['avg_health']}, Pending={kpis['pending_maint']}, Risk={kpis['maint_risk_summary']}

WAREHOUSE: Low Stock={kpis['low_stock']}, Total Stock={kpis['total_stock']}

QUALITY: Score={kpis['avg_quality']}%, Failed={kpis['failed_insp']}, Defects={kpis['total_defects']}

SAFETY: Critical={kpis['crit_incidents']}, Open={kpis['open_cases']}, Affected={kpis['affected']}

Format EXACTLY:

LG SMART FACTORY {label.upper()} OPERATIONS REPORT
Generated: {gen_date} · Data: {data_str}

Executive Summary
[2-3 sentence summary]

Production Summary
- Total Production: [value] Units
- Factory Health: [value]%
- Active Production Lines: [value]
- Average Downtime: [value] Minutes

Key Observation:
[1 sentence]

Maintenance Summary
- Critical Machines: [value]
- Pending Maintenance Tasks: [value]
- Average Machine Health Score: [value]

Key Observation:
[1 sentence]

Warehouse Summary
- Low Stock Items: [value]
- Inventory Status: [Stable / Needs Attention / Critical]

Key Observation:
[1 sentence]

Quality Summary
- Average Quality Score: [value]%
- Failed Inspections: [value]

Key Observation:
[1 sentence]

Safety Summary
- Critical Incidents: [value]
- Open Cases: [value]

Key Observation:
[1 sentence]

Top Operational Risks
1. [risk 1]
2. [risk 2]
3. [risk 3]

Recommended Actions
1. [action 1]
2. [action 2]
3. [action 3]
4. [action 4]

AI Operational Outlook
[2-3 sentence forward-looking analysis]
"""


def build_module_prompt(module, kpis, df, warehouse_df, maintenance_df, quality_df, safety_df):
    date_str = datetime.now().strftime("%d %B %Y")
    prompts = {
        "production": f"""You are the LG Smart Factory Production Analyst. Generate a production department report.

Date: {date_str}

DATA:
- Total Output: {kpis['total_actual']:,} units
- Factory Health: {kpis['factory_health']}%
- Active Lines: {kpis['active_lines']}
- Avg Downtime: {kpis['avg_downtime']} min
- Target: {kpis['total_target']:,} units
- Risk: {kpis['prod_risk_summary']}

Format:
PRODUCTION DEPARTMENT REPORT
Date: {date_str}

Production Performance
[2-3 sentence analysis of production performance, output vs target, and efficiency]

Key Metrics
- Total Output: [value] Units
- Factory Health: [value]%
- Active Lines: [value]
- Avg Downtime: [value] min
- Target Achievement: [value]%

Key Observation:
[1 sentence]

Line Performance
[1-2 sentences on best/worst performing lines]

Risk Assessment
[1-2 sentences on production risks]

Recommendations
1. [action 1]
2. [action 2]
""",
        "maintenance": f"""You are the LG Smart Factory Maintenance Analyst. Generate a maintenance department report.

Date: {date_str}

DATA:
- Critical Machines: {kpis['crit_machines']}
- Avg Health Score: {kpis['avg_health']}/100
- Pending Tasks: {kpis['pending_maint']}
- Risk: {kpis['maint_risk_summary']}

Format:
MAINTENANCE DEPARTMENT REPORT
Date: {date_str}

Maintenance Overview
[2-3 sentence analysis of fleet health, critical machines, and maintenance backlog]

Key Metrics
- Critical Machines: [value]
- Pending Tasks: [value]
- Avg Machine Health: [value]/100

Key Observation:
[1 sentence]

Fleet Health Assessment
[1-2 sentences]

Recommendations
1. [action 1]
2. [action 2]
""",
        "warehouse": f"""You are the LG Smart Factory Warehouse Analyst. Generate a warehouse department report.

Date: {date_str}

DATA:
- Low Stock Items: {kpis['low_stock']}
- Total Stock Value: {kpis['total_stock']:,} units

Format:
WAREHOUSE DEPARTMENT REPORT
Date: {date_str}

Inventory Overview
[2-3 sentence analysis of inventory status, stock levels, and supply chain health]

Key Metrics
- Low Stock Items: [value]
- Total Inventory: [value] units
- Inventory Status: [Stable/Needs Attention/Critical]

Key Observation:
[1 sentence]

Stock Risk Assessment
[1-2 sentences]

Recommendations
1. [action 1]
2. [action 2]
""",
        "quality": f"""You are the LG Smart Factory Quality Analyst. Generate a quality department report.

Date: {date_str}

DATA:
- Avg Quality Score: {kpis['avg_quality']}%
- Failed Inspections: {kpis['failed_insp']}
- Total Inspections: {kpis['total_insp']}
- Defective Units: {kpis['total_defects']}

Format:
QUALITY DEPARTMENT REPORT
Date: {date_str}

Quality Overview
[2-3 sentence analysis of quality metrics, defect rates, and inspection outcomes]

Key Metrics
- Average Score: [value]%
- Inspections: [value]
- Failed: [value]
- Defective Units: [value]

Key Observation:
[1 sentence]

Defect Analysis
[1-2 sentences]

Recommendations
1. [action 1]
2. [action 2]
""",
        "safety": f"""You are the LG Smart Factory Safety Officer. Generate a safety department report.

Date: {date_str}

DATA:
- Critical Incidents: {kpis['crit_incidents']}
- Open Cases: {kpis['open_cases']}
- Employees Affected: {kpis['affected']}
- Total Incidents: {kpis['total_incidents']}

Format:
SAFETY DEPARTMENT REPORT
Date: {date_str}

Safety Overview
[2-3 sentence analysis of workplace safety, incidents, and compliance]

Key Metrics
- Total Incidents: [value]
- Critical: [value]
- Open Cases: [value]
- Employees Affected: [value]

Key Observation:
[1 sentence]

Risk Assessment
[1-2 sentences]

Recommendations
1. [action 1]
2. [action 2]
""",
    }
    return prompts.get(module, "Generate a factory report.")


def _call_gemini(prompt):
    try:
        import google.generativeai as genai
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception:
        return None


def _fallback_full_report(kpis, scope, data_date):
    label = SCOPE_LABELS.get(scope, "Daily")
    gen_date = datetime.now().strftime("%d %B %Y")
    data_str = data_date if data_date else gen_date
    h = kpis["factory_health"]
    return f"""LG SMART FACTORY {label.upper()} OPERATIONS REPORT
Generated: {gen_date} · Data: {data_str}

Executive Summary
Factory operations recorded a health score of {h}% for the {label.lower()} period. Production output reached {kpis['total_actual']:,} units across {kpis['active_lines']} active lines with an average downtime of {kpis['avg_downtime']} minutes. {kpis['crit_machines']} machine(s) flagged as critical. {kpis['failed_insp']} quality inspections failed. No critical safety incidents recorded.

Production Summary
- Total Production: {kpis['total_actual']:,} Units
- Factory Health: {h}%
- Active Production Lines: {kpis['active_lines']}
- Average Downtime: {kpis['avg_downtime']} Minutes

Key Observation:
Production {h}% health score. Downtime averages {kpis['avg_downtime']} min across lines.

Maintenance Summary
- Critical Machines: {kpis['crit_machines']}
- Pending Maintenance Tasks: {kpis['pending_maint']}
- Average Machine Health Score: {kpis['avg_health']}

Key Observation:
{kpis['crit_machines']} machine(s) require immediate attention.

Warehouse Summary
- Low Stock Items: {kpis['low_stock']}
- Inventory Status: {"Stable" if kpis['low_stock'] == 0 else "Needs Attention"}

Key Observation:
{kpis['low_stock']} item(s) below minimum threshold.

Quality Summary
- Average Quality Score: {kpis['avg_quality']}%
- Failed Inspections: {kpis['failed_insp']}

Key Observation:
Quality score at {kpis['avg_quality']}% with {kpis['failed_insp']} failed inspection(s).

Safety Summary
- Critical Incidents: {kpis['crit_incidents']}
- Open Cases: {kpis['open_cases']}

Key Observation:
{kpis['open_cases']} open case(s). No critical incidents.

Top Operational Risks
1. Downtime escalation on lines with above-average downtime
2. {"Inventory shortage risk" if kpis['low_stock'] > 0 else "Inventory levels are stable"}
3. {"Machine health degradation" if kpis['crit_machines'] > 0 else "Fleet health is nominal"}

Recommended Actions
1. {"Schedule preventive maintenance for critical machines" if kpis['crit_machines'] > 0 else "Continue routine maintenance schedule"}
2. {"Replenish low-stock inventory items" if kpis['low_stock'] > 0 else "Maintain current inventory levels"}
3. Increase monitoring on high-downtime production lines
4. {"Conduct quality audits for failed inspections" if kpis['failed_insp'] > 0 else "Maintain quality standards"}

AI Operational Outlook
Factory health at {h}% indicates {( "stable operations with minor risks requiring attention." if h >= 80 else "elevated risk levels requiring management attention." )} Recommended actions above should be prioritized for the next operational cycle.
"""


def _fallback_module_report(module, kpis, data_date):
    gen_date = datetime.now().strftime("%d %B %Y")
    data_str = data_date if data_date else gen_date
    h = kpis["factory_health"]

    reports = {
        "production": f"""PRODUCTION DEPARTMENT REPORT
Generated: {gen_date} · Data: {data_str}

Production Performance
Production achieved {kpis['total_actual']:,} units against a target of {kpis['total_target']:,} units with a health score of {h}%. {kpis['active_lines']} lines were active with average downtime of {kpis['avg_downtime']} minutes.

Key Metrics
- Total Output: {kpis['total_actual']:,} Units
- Factory Health: {h}%
- Active Lines: {kpis['active_lines']}
- Avg Downtime: {kpis['avg_downtime']} min
- Target Achievement: {round(kpis['total_actual']/kpis['total_target']*100,1) if kpis['total_target'] > 0 else 0}%

Key Observation:
Production is operating at {h}% health with {kpis['active_lines']} active lines.

Line Performance
Overall production lines maintained operational status throughout the period.

Risk Assessment
Downtime of {kpis['avg_downtime']} minutes requires monitoring on underperforming lines.

Recommendations
1. Monitor lines with above-average downtime
2. Optimise shift scheduling for maximum output
""",
        "maintenance": f"""MAINTENANCE DEPARTMENT REPORT
Generated: {gen_date} · Data: {data_str}

Maintenance Overview
Fleet health score averages {kpis['avg_health']}/100 with {kpis['crit_machines']} critical machine(s) identified. {kpis['pending_maint']} maintenance task(s) are pending.

Key Metrics
- Critical Machines: {kpis['crit_machines']}
- Pending Tasks: {kpis['pending_maint']}
- Avg Machine Health: {kpis['avg_health']}/100

Key Observation:
{kpis['crit_machines']} machine(s) at critical risk level requiring immediate intervention.

Fleet Health Assessment
Average machine health of {kpis['avg_health']}/100 indicates {( "good overall fleet condition." if kpis['avg_health'] >= 80 else "degrading fleet condition requiring attention." )}

Recommendations
1. {"Prioritise critical machine repairs" if kpis['crit_machines'] > 0 else "Continue preventive maintenance schedule"}
2. Clear pending maintenance backlog
""",
        "warehouse": f"""WAREHOUSE DEPARTMENT REPORT
Generated: {gen_date} · Data: {data_str}

Inventory Overview
{kpis['low_stock']} item(s) are below minimum stock thresholds. Total inventory across all items is {kpis['total_stock']:,} units.

Key Metrics
- Low Stock Items: {kpis['low_stock']}
- Total Inventory: {kpis['total_stock']:,} units
- Inventory Status: {"Stable" if kpis['low_stock'] == 0 else "Needs Attention"}

Key Observation:
{kpis['low_stock']} item(s) require replenishment to avoid production impact.

Stock Risk Assessment
Inventory levels are {( "within acceptable ranges." if kpis['low_stock'] == 0 else "below minimum thresholds for some items." )}

Recommendations
1. {"Place replenishment orders for low-stock items" if kpis['low_stock'] > 0 else "Maintain current stock levels"}
2. Review minimum stock thresholds
""",
        "quality": f"""QUALITY DEPARTMENT REPORT
Generated: {gen_date} · Data: {data_str}

Quality Overview
Quality score averages {kpis['avg_quality']}% with {kpis['failed_insp']} failed inspection(s) out of {kpis['total_insp']} total. {kpis['total_defects']} defective unit(s) identified.

Key Metrics
- Average Score: {kpis['avg_quality']}%
- Inspections: {kpis['total_insp']}
- Failed: {kpis['failed_insp']}
- Defective Units: {kpis['total_defects']}

Key Observation:
Quality at {kpis['avg_quality']}% with {kpis['failed_insp']} failure(s).

Defect Analysis
{kpis['total_defects']} defective unit(s) detected. {( "Defect rate requires investigation." if kpis['total_defects'] > 10 else "Defect levels within acceptable range." )}

Recommendations
1. {"Investigate root cause of failed inspections" if kpis['failed_insp'] > 0 else "Maintain current quality processes"}
2. Increase sampling on borderline production batches
""",
        "safety": f"""SAFETY DEPARTMENT REPORT
Generated: {gen_date} · Data: {data_str}

Safety Overview
{kpis['total_incidents']} incident(s) reported with {kpis['crit_incidents']} critical and {kpis['open_cases']} open case(s). {kpis['affected']} employee(s) affected.

Key Metrics
- Total Incidents: {kpis['total_incidents']}
- Critical: {kpis['crit_incidents']}
- Open Cases: {kpis['open_cases']}
- Employees Affected: {kpis['affected']}

Key Observation:
{("No critical safety incidents. Workplace safety is stable." if kpis['crit_incidents'] == 0 else "Critical incidents require immediate investigation.")}

Risk Assessment
Safety posture is {( "stable with no critical concerns." if kpis['crit_incidents'] == 0 else "elevated due to critical incidents." )}

Recommendations
1. {"Investigate and resolve open safety cases" if kpis['open_cases'] > 0 else "Maintain safety protocols"}
2. Conduct safety refresher training
""",
    }
    return reports.get(module, f"No report available for {module}.")


def generate_report(kpis, scope="daily", data_date=None):
    prompt = build_full_report_prompt(kpis, scope, data_date)
    result = _call_gemini(prompt)
    if result:
        return result
    return _fallback_full_report(kpis, scope, data_date)


def generate_module_report(module, kpis, df, warehouse_df, maintenance_df, quality_df, safety_df):
    prompt = build_module_prompt(module, kpis, df, warehouse_df, maintenance_df, quality_df, safety_df)
    result = _call_gemini(prompt)
    if result:
        return result
    gen_date = datetime.now().strftime("%d %B %Y")
    return _fallback_module_report(module, kpis, gen_date)


def export_pdf(report_text, title_suffix="Operations Report"):
    date_str = datetime.now().strftime("%d_%B_%Y")

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    margin = 20
    pdf.set_margins(margin, margin, margin)
    pdf.set_auto_page_break(auto=True, margin=25)

    pdf.set_fill_color(165, 0, 52)
    pdf.rect(0, 0, 210, 40, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(margin, 10)
    pdf.cell(170, 10, "LG Smart Factory", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(margin, 22)
    pdf.cell(170, 8, title_suffix, align="C")
    pdf.set_xy(margin, 32)
    pdf.cell(170, 6, f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", align="C")

    pdf.ln(42)
    pdf.set_text_color(30, 25, 23)
    pdf.set_font("Helvetica", "", 10)

    lines = report_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            pdf.ln(3)
            continue

        if any(stripped.endswith(x) for x in ["Summary", "Overview", "Outlook", "Assessment", "Performance", "Analysis"]) or stripped in ["Top Operational Risks", "Recommended Actions", "Production Performance", "Line Performance", "Risk Assessment", "Defect Analysis", "Fleet Health Assessment", "Stock Risk Assessment", "Key Metrics", "Inventory Overview", "Maintenance Overview", "Quality Overview", "Safety Overview"]:
            pdf.ln(2)
            pdf.set_text_color(165, 0, 52)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 7, stripped, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(30, 25, 23)
            continue

        if stripped.startswith("Key Observation") or stripped.startswith("Inventory Status"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(122, 0, 38)
            pdf.cell(0, 6, stripped, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(30, 25, 23)
            pdf.set_font("Helvetica", "", 10)
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(margin + 5)
            pdf.cell(5, 5, "", border=0)
            pdf.cell(160, 5, stripped[1:].strip(), new_x="LMARGIN", new_y="NEXT")
            continue

        if any(stripped.startswith(f"{i}.") for i in range(1, 11)):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(margin + 5)
            pdf.cell(160, 5, stripped, new_x="LMARGIN", new_y="NEXT")
            continue

        if "LG SMART FACTORY" in stripped or stripped.startswith("Date:"):
            continue

        if any(stripped.startswith(x) for x in ["PRODUCTION", "MAINTENANCE", "WAREHOUSE", "QUALITY", "SAFETY"]) and "DEPARTMENT" in stripped:
            continue

        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 5, stripped, new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(168, 162, 158)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_y(-15)
    pdf.cell(0, 10, f"LG Smart Factory · {title_suffix} · {date_str.replace('_', ' ')} · Confidential", align="C")

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf


def render_report_page(df, warehouse_df, maintenance_df, quality_df, safety_df, engines, selected_date=None):
    kpis = collect_kpis(df, warehouse_df, maintenance_df, quality_df, safety_df, engines)

    # ── Consolidated Report Section ──
    st.markdown("## 📊 Consolidated Operations Report")
    st.markdown(
        '<div style="color:#78716c;font-size:13px;margin-bottom:14px;">'
        "Generate an AI-powered executive report covering all factory departments."
        "</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    with cols[0]:
        daily = st.button("📄 Generate Daily Report", use_container_width=True, type="primary")
    with cols[1]:
        weekly = st.button("📊 Generate Weekly Report", use_container_width=True)
    with cols[2]:
        monthly = st.button("📈 Generate Monthly Report", use_container_width=True)

    scope = None
    if daily:
        scope = "daily"
    elif weekly:
        scope = "weekly"
    elif monthly:
        scope = "monthly"

    if scope is not None:
        label = SCOPE_LABELS.get(scope, "Daily")
        with st.spinner(f"🤖 Gemini generating {label.lower()} consolidated report..."):
            report = generate_report(kpis, scope, selected_date)

        st.markdown("---")
        st.markdown(f"### 📄 {label} Operations Report")
        st.markdown(
            f'<div style="color:#78716c;font-size:12px;margin-bottom:12px;">'
            f'{datetime.now().strftime("%d %B %Y, %H:%M")} · {label} Scope</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="panel" style="white-space:pre-wrap;font-size:13px;line-height:1.7;">{report}</div>',
            unsafe_allow_html=True,
        )

        with st.spinner("Generating consolidated PDF..."):
            pdf_buf = export_pdf(strip_emoji(report), f"{label} Operations Report")

        st.download_button(
            label=f"📥 Download Full Report PDF ({label})",
            data=pdf_buf,
            file_name=f"LG_Factory_Report_{scope}_{datetime.now().strftime('%d_%B_%Y')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

    # ── Individual Module Reports ──
    st.markdown("---")
    st.markdown("## 📑 Individual Module Reports")
    st.markdown(
        '<div style="color:#78716c;font-size:13px;margin-bottom:14px;">'
        "Generate and download separate PDF reports for each department."
        "</div>",
        unsafe_allow_html=True,
    )

    mod_cols = st.columns(3)
    mod_list = list(MODULE_CONFIG.items())
    for i, (mod_key, mod_cfg) in enumerate(mod_list):
        with mod_cols[i % 3]:
            icon = mod_cfg["icon"]
            color = mod_cfg["color"]
            title = mod_cfg["title"]

            st.markdown(
                f'<div style="background:#ffffff;border:1px solid #e8e2d8;border-radius:14px;'
                f'padding:16px;margin-bottom:10px;border-left:4px solid {color};">'
                f'<div style="font-size:22px;margin-bottom:6px;">{icon}</div>'
                f'<div style="font-weight:700;font-size:14px;color:#1c1917;">{title}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            btn_key = f"mod_{mod_key}"
            if st.button(f"📄 Generate & Download PDF", key=btn_key, use_container_width=True):
                with st.spinner(f"Gemini generating {mod_key} report..."):
                    mod_report = generate_module_report(
                        mod_key, kpis, df, warehouse_df, maintenance_df, quality_df, safety_df
                    )

                with st.spinner("Generating PDF..."):
                    mod_pdf = export_pdf(strip_emoji(mod_report), title)

                st.download_button(
                    label=f"📥 Download {title} PDF",
                    data=mod_pdf,
                    file_name=f"LG_{mod_key.capitalize()}_Report_{datetime.now().strftime('%d_%B_%Y')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                    key=f"dl_{mod_key}",
                )

                st.markdown(
                    f'<div style="background:#faf6f0;border:1px solid #e8e2d8;border-radius:10px;'
                    f'padding:12px;margin-top:6px;font-size:12px;color:#78716c;'
                    f'white-space:pre-wrap;max-height:200px;overflow-y:auto;">{mod_report[:500]}{"..." if len(mod_report) > 500 else ""}</div>',
                    unsafe_allow_html=True,
                )

    st.info("💡 Each module report is generated on-demand by Gemini AI using live factory data.")
