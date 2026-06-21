import os
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from modules.theme import (
    inject_css, kpi_card, alert_row, ai_card,
    panel_title, stat_strip, divider
)
from modules.ai_engine import detect_factory_risk, render_engine_alerts, status_badge_html, SEV
from modules.roles import (
    ROLES, PRIORITY_STYLE, P,
    build_task_queue, get_role_recommendations
)
from modules.llm_engine import (
    generate_factory_ai_response,
    generate_production_analysis,
    generate_maintenance_analysis,
    generate_safety_analysis,
    render_copilot_panel
)
from modules import production, warehouse, maintenance, quality, safety
from modules.predictive_engine import run_predictive_analysis, generate_predictive_alerts
from modules.incident_reporting import (
    upload_incident, render_incident_feed, render_incident_stats,
    DEPARTMENTS, SEVERITIES
)
from modules.vision_engine import (
    analyze_incident_image, render_vision_analysis
)
from modules.agents import agent_coordinator
from modules.simulator import simulate_factory_conditions, SimulationInput, SCENARIOS
from modules.simulator import build_strategy_context
from modules.database import load_table, get_available_dates, insert_record, get_supabase
from modules.auth import login_required, logout, get_current_user, get_current_role
from modules.report_generator import render_report_page
from modules.breakdown_alerts import check_breakdowns, render_breakdown_alerts
from modules.roles import AUTH_TO_ROLE_KEY
from datetime import datetime

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LG Smart Factory",
    page_icon="https://i.pinimg.com/736x/08/75/36/087536c5fd0ee3ddf9f2eb48afc03620.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)

st_autorefresh(interval=30000, key="factory_live_refresh")
inject_css()

# ── EXTRA CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.role-banner {
    background: linear-gradient(135deg, #7a0026, #a50034);
    border-radius: 16px; padding: 18px 24px; margin-bottom: 22px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 6px 24px rgba(122,0,38,0.22);
}
.role-banner-name  { color:white; font-size:22px; font-weight:800; margin-bottom:3px; }
.role-banner-desc  { color:rgba(255,255,255,0.62); font-size:13px; }
.role-banner-badge {
    background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.25);
    color:white; padding:6px 16px; border-radius:30px; font-size:12px; font-weight:700;
}
.task-card {
    border-radius:12px; padding:16px 18px; margin-bottom:10px;
    border-left:4px solid transparent; transition:transform 0.2s ease;
}
.task-card:hover { transform:translateX(4px); }
.task-priority { font-size:10px; font-weight:800; letter-spacing:1.2px;
                 text-transform:uppercase; margin-bottom:5px;
                 display:flex; align-items:center; gap:6px; }
.task-title  { font-size:14px; font-weight:700; margin-bottom:4px; }
.task-detail { font-size:12px; opacity:0.78; margin-bottom:6px; }
.task-action { font-size:12px; font-weight:600; }
.task-module { font-size:10px; font-weight:600; background:rgba(0,0,0,0.06);
               padding:2px 8px; border-radius:20px; display:inline-block; margin-left:auto; }
.rec-card {
    background:linear-gradient(135deg,rgba(255,255,255,0.92),rgba(255,255,255,0.74));
    border:1px solid rgba(165,0,52,0.1); border-left:4px solid #a50034;
    border-radius:14px; padding:16px 18px; margin-bottom:10px;
    transition:transform 0.2s ease, box-shadow 0.2s ease;
}
.rec-card:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(165,0,52,0.1); }
.rec-title { color:#7a0026; font-size:13px; font-weight:700; margin-bottom:4px; }
.rec-body  { color:#475569; font-size:12px; line-height:1.5; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
</style>
""", unsafe_allow_html=True)

# ── AUTH WALL — must be authenticated to proceed ──────────────────────────────
login_required()

# Resolve role from auth session
user = get_current_user()
AUTH_ROLE = user["role"] if user else "Factory Manager"
_ROLE_KEY = AUTH_TO_ROLE_KEY.get(AUTH_ROLE, "🏭 Factory Manager")

# ── LOAD DATA (from Supabase cloud database) ─────────────────────────────────
def load_data():
    LIVE_CSV = "datalg2/production_live.csv"
    # Live simulator still writes to CSV; prefer live file over DB for production
    if os.path.exists(LIVE_CSV):
        pdf = pd.read_csv(LIVE_CSV)
        pdf.columns = pdf.columns.str.strip()
    else:
        pdf = load_table("production")

    wdf = load_table("warehouse")
    mdf = load_table("maintenance")
    qdf = load_table("quality")
    sdf = load_table("safety")

    for df_i, name in [(mdf, "mdf"), (qdf, "qdf"), (sdf, "sdf")]:
        if "Date" in df_i.columns:
            df_i["Date"] = pd.to_datetime(df_i["Date"], errors="coerce").dt.strftime("%d-%m-%Y")

    return pdf, wdf, mdf, qdf, sdf

df, warehouse_df, maintenance_df, quality_df, safety_df = load_data()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Brand header ──
    st.markdown("""
    <div style="display:flex;align-items:center;gap:14px;padding:8px 4px 4px 4px;">
        <img src="https://i.pinimg.com/736x/08/75/36/087536c5fd0ee3ddf9f2eb48afc03620.jpg"
             style="width:56px;opacity:0.9;">
        <div>
            <div style="color:white;font-size:18px;font-weight:800;letter-spacing:-0.3px;line-height:1.2;">
                Smart Factory
            </div>
            <div style="color:rgba(255,255,255,0.35);font-size:10px;font-weight:600;letter-spacing:0.5px;">
                OPERATIONS PLATFORM
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.08),transparent);margin:14px 0;"></div>', unsafe_allow_html=True)

    # ── User profile card ──
    role_cfg = ROLES[_ROLE_KEY]
    initial = user['username'][0].upper() if user['username'] else "U"
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);
                border-radius:14px;padding:14px 16px;margin-bottom:4px;
                backdrop-filter:blur(8px);">
        <div style="display:flex;align-items:center;gap:14px;">
            <div style="width:42px;height:42px;border-radius:12px;
                        background:linear-gradient(135deg,{role_cfg['color']},rgba(255,255,255,0.15));
                        display:flex;align-items:center;justify-content:center;
                        font-size:18px;font-weight:800;color:white;
                        border:1px solid rgba(255,255,255,0.1);">
                {initial}
            </div>
            <div style="flex:1;min-width:0;">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <span style="font-weight:700;font-size:13px;color:white;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {role_cfg['icon']}&nbsp;{AUTH_ROLE}
                    </span>
                    <span style="background:{role_cfg['color']}30;color:{role_cfg['color']};
                                font-size:9px;font-weight:700;padding:2px 10px;
                                border-radius:20px;border:1px solid {role_cfg['color']}30;
                                letter-spacing:0.3px;">{role_cfg['badge']}</span>
                </div>
                <div style="color:rgba(255,255,255,0.40);font-size:11px;margin-top:3px;">
                    @{user['username']} · {role_cfg['description'].split('·')[0].strip()}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.08),transparent);margin:14px 0;"></div>', unsafe_allow_html=True)

    # ── Navigation ──
    allowed_pages = role_cfg["modules"]
    page = st.radio("NAVIGATION", allowed_pages, label_visibility="visible")

    st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.06),transparent);margin:14px 0;"></div>', unsafe_allow_html=True)

    # ── Date selector ──
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <span style="color:rgba(255,255,255,0.40);font-size:16px;">📅</span>
        <span style="color:rgba(255,255,255,0.50);font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">Select Date</span>
    </div>
    """, unsafe_allow_html=True)
    selected_date = st.selectbox("Date", sorted(df["Date"].unique()),
                                 label_visibility="collapsed")

    st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.06),transparent);margin:14px 0;"></div>', unsafe_allow_html=True)

    # ── Live status ──
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(34,197,94,0.08),rgba(34,197,94,0.02));
                border:1px solid rgba(34,197,94,0.12);border-radius:12px;
                padding:12px 14px;margin-bottom:8px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">
            <div style="width:7px;height:7px;border-radius:50%;background:#22c55e;
                        box-shadow:0 0 10px #22c55e;animation:pulse 1.5s infinite;"></div>
            <div style="flex:1;">
                <span style="color:rgba(255,255,255,0.75);font-size:12px;font-weight:700;letter-spacing:0.3px;">
                    SYSTEM LIVE
                </span>
                <span style="color:rgba(255,255,255,0.30);font-size:10px;margin-left:8px;">
                    {role_cfg['badge']}
                </span>
            </div>
        </div>
        <div style="color:rgba(255,255,255,0.40);font-size:11px;margin-top:2px;">
            {role_cfg['description']}
        </div>
        <div style="display:flex;gap:6px;margin-top:6px;">
            <span style="background:rgba(255,255,255,0.06);border-radius:6px;padding:2px 8px;
                        font-size:10px;color:rgba(255,255,255,0.45);">🤖 Gemini</span>
            <span style="background:rgba(255,255,255,0.06);border-radius:6px;padding:2px 8px;
                        font-size:10px;color:rgba(255,255,255,0.45);">☁ Supabase</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer + Logout ──
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-top:6px;">
        <span style="color:rgba(255,255,255,0.20);font-size:10px;font-weight:500;">
            v5.2 · RBAC
        </span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚪  Sign Out", use_container_width=True, type="secondary"):
        logout()

# Backward-compat alias for downstream code
role = _ROLE_KEY

# ── FILTER DATA ───────────────────────────────────────────────────────────────
filtered_df           = df[df["Date"] == selected_date]
filtered_warehouse_df = warehouse_df[warehouse_df["Date"] == selected_date]
selected_date_str     = pd.to_datetime(selected_date).strftime("%d-%m-%Y")
filtered_maint_df     = maintenance_df[maintenance_df["Date"] == selected_date_str]
filtered_quality_df   = quality_df[quality_df["Date"] == selected_date_str]
filtered_safety_df    = safety_df[safety_df["Date"] == selected_date_str]

# ── AI ENGINES ────────────────────────────────────────────────────────────────
engines = detect_factory_risk(
    filtered_df, filtered_maint_df,
    filtered_warehouse_df, filtered_quality_df, filtered_safety_df
)

# ── DASHBOARD KPIs ────────────────────────────────────────────────────────────
total_target   = filtered_df["Target"].sum()
total_actual   = filtered_df["Actual"].sum()
avg_downtime   = round(filtered_df["Downtime_min"].mean(), 1)
factory_health = round((total_actual / total_target) * 100, 1) if total_target > 0 else 0
active_lines   = filtered_df["Prod_line"].nunique()

# ── HELPERS ───────────────────────────────────────────────────────────────────
def show_role_banner():
    st.markdown(f"""
    <div class="role-banner">
        <div>
            <div class="role-banner-name">{role_cfg['icon']} {AUTH_ROLE}</div>
            <div class="role-banner-desc">{role_cfg['description']} · {selected_date}</div>
        </div>
        <div class="role-banner-badge">● {role_cfg['badge']} ACCESS</div>
    </div>""", unsafe_allow_html=True)

def _task_card_html(task):
    s = PRIORITY_STYLE[task.priority]
    return f"""
    <div class="task-card" style="background:{s['bg']};border-left-color:{s['border']};">
        <div class="task-priority" style="color:{s['text']};">
            {s['icon']} {task.priority}
            <span class="task-module">{task.module}</span>
        </div>
        <div class="task-title" style="color:{s['text']};">{task.title}</div>
        <div class="task-detail">{task.detail}</div>
        <div class="task-action">⚡ {task.action}</div>
    </div>"""

def _rec_card_html(rec):
    dot = {"ok":"#22c55e","low":"#3b82f6","medium":"#f59e0b",
           "high":"#f97316","critical":"#ef4444"}.get(rec.get("status","low"),"#94a3b8")
    return f"""
    <div class="rec-card">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            <span style="font-size:18px;">{rec['icon']}</span>
            <div class="rec-title" style="flex:1;">{rec['title']}</div>
            <div style="width:8px;height:8px;border-radius:50%;background:{dot};flex-shrink:0;"></div>
        </div>
        <div class="rec-body">{rec['body']}</div>
    </div>"""

# ═════════════════════════════════════════════════════════════════════════════
# PAGES
# ═════════════════════════════════════════════════════════════════════════════
if page == "🏠  Dashboard":
    show_role_banner()

    # Hero — Admin / Manager only
    if role in ["👑 Admin", "🏭 Factory Manager"]:
        st.markdown(f"""
        <div class="hero-wrap">
            <img src="https://images.unsplash.com/photo-1565008447742-97f6f38c985c?q=80&w=1800&auto=format&fit=crop">
            <div class="hero-overlay"></div>
            <div class="hero-body">
                <div class="hero-eyebrow">LG Electronics · Smart Factory · {selected_date} · LIVE</div>
                <div class="hero-title">LG <span>Smart</span><br>Factory Ops</div>
                <div class="hero-sub">AI Copilot active — Gemini analyzing all operations.</div>
                <span class="hero-cta">Command Center Active →</span>
            </div>
            <div class="hero-stats">
                <div class="hero-stat"><div class="hero-stat-val">{factory_health}%</div>
                    <div class="hero-stat-lbl">Factory Health</div></div>
                <div class="hero-stat"><div class="hero-stat-val">{active_lines}</div>
                    <div class="hero-stat-lbl">Active Lines</div></div>
                <div class="hero-stat"><div class="hero-stat-val">{total_actual:,}</div>
                    <div class="hero-stat-lbl">Units Today</div></div>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Breakdown Alerts (AI-driven, shown at top for all roles) ──
    breakdown_alerts = check_breakdowns(filtered_df, filtered_maint_df)
    render_breakdown_alerts(breakdown_alerts)

    # ── Role KPIs ─────────────────────────────────────────────────────────
    if role in ["👑 Admin","🏭 Factory Manager","🏭 Production Supervisor"]:
        st.markdown("### 🏭 Production Overview")
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            b = "ON TARGET" if factory_health>=95 else ("WATCH" if factory_health>=80 else "AT RISK")
            st.markdown(kpi_card("⚡","Factory Health",f"{factory_health}%",badge=b),unsafe_allow_html=True)
        with c2:
            st.markdown(kpi_card("📦","Total Output",f"{total_actual:,}",unit="units"),unsafe_allow_html=True)
        with c3:
            st.markdown(kpi_card("⏱","Avg Downtime",str(avg_downtime),unit="minutes"),unsafe_allow_html=True)
        with c4:
            st.markdown(kpi_card("🔌","Active Lines",str(active_lines),unit="lines"),unsafe_allow_html=True)

    if role in ["👑 Admin","🛠 Maintenance Engineer"] and not filtered_maint_df.empty:
        st.markdown("### 🛠 Maintenance Overview")
        c1,c2,c3,c4 = st.columns(4)
        crit = len(filtered_maint_df[filtered_maint_df["Risk_Level"]=="High"])
        avg_h = round(filtered_maint_df["Health_Score"].mean(),1)
        pend  = len(filtered_maint_df[filtered_maint_df["Maintenance_Status"]=="Pending"])
        with c1: st.markdown(kpi_card("⚙","Machines",str(filtered_maint_df["Machine_ID"].nunique()),unit="tracked"),unsafe_allow_html=True)
        with c2: st.markdown(kpi_card("🔴","Critical",str(crit),badge="URGENT" if crit>0 else "CLEAR"),unsafe_allow_html=True)
        with c3: st.markdown(kpi_card("💚","Avg Health",str(avg_h),unit="out of 100"),unsafe_allow_html=True)
        with c4: st.markdown(kpi_card("🔧","Pending",str(pend),unit="tasks"),unsafe_allow_html=True)

        # ── Predictive Maintenance ────────────────────────────────────────
        st.markdown("### 🔮 Predictive Risk Assessment")
        pred_report = run_predictive_analysis(filtered_maint_df, filtered_df)
        p1,p2,p3,p4 = st.columns(4)
        risk_badge = "CRITICAL" if pred_report.fleet_avg_risk >= 70 else ("HIGH" if pred_report.fleet_avg_risk >= 50 else "LOW")
        with p1: st.markdown(kpi_card("📊","Fleet Risk",f"{pred_report.fleet_avg_risk}%",badge=risk_badge),unsafe_allow_html=True)
        with p2: st.markdown(kpi_card("🔴","Critical",str(pred_report.critical_count),badge="IMMINENT" if pred_report.critical_count>0 else "NONE"),unsafe_allow_html=True)
        with p3: st.markdown(kpi_card("🟠","High Risk",str(pred_report.high_count),badge="URGENT" if pred_report.high_count>0 else "CLEAR"),unsafe_allow_html=True)
        with p4: st.markdown(kpi_card("📦","Impact",f"{pred_report.total_impact_units:,}",unit="units/day"),unsafe_allow_html=True)

        pred_alerts = generate_predictive_alerts(pred_report.predictions)
        for a in pred_alerts:
            kind = "danger" if "CRITICAL" in a else "warning" if "HIGH" in a else "success"
            st.markdown(alert_row(a, kind), unsafe_allow_html=True)

    if role in ["👑 Admin","✅ Quality Inspector"] and not filtered_quality_df.empty:
        st.markdown("### ✅ Quality Overview")
        c1,c2,c3,c4 = st.columns(4)
        avg_q   = round(filtered_quality_df["Quality_Score"].mean(),1)
        defects = int(filtered_quality_df["Defective_Units"].sum())
        failed  = len(filtered_quality_df[filtered_quality_df["Inspection_Status"]=="Failed"])
        with c1: st.markdown(kpi_card("🔍","Inspections",str(len(filtered_quality_df)),unit="today"),unsafe_allow_html=True)
        with c2: st.markdown(kpi_card("⭐","Avg Score",str(avg_q),unit="out of 100"),unsafe_allow_html=True)
        with c3: st.markdown(kpi_card("❌","Defective",f"{defects:,}",unit="units"),unsafe_allow_html=True)
        with c4: st.markdown(kpi_card("📋","Failed",str(failed),badge="ACTION" if failed>0 else "CLEAR"),unsafe_allow_html=True)

    if role in ["👑 Admin","⚠ Safety Officer"] and not filtered_safety_df.empty:
        st.markdown("### ⚠ Safety Overview")
        c1,c2,c3,c4 = st.columns(4)
        crit_s   = len(filtered_safety_df[filtered_safety_df["Severity"]=="Critical"])
        affected = int(filtered_safety_df["Employees_Affected"].sum())
        unres    = len(filtered_safety_df[filtered_safety_df["Safety_Status"]!="Resolved"])
        with c1: st.markdown(kpi_card("📋","Incidents",str(len(filtered_safety_df)),unit="today"),unsafe_allow_html=True)
        with c2: st.markdown(kpi_card("🚨","Critical",str(crit_s),badge="URGENT" if crit_s>0 else "CLEAR"),unsafe_allow_html=True)
        with c3: st.markdown(kpi_card("👷","Affected",str(affected),unit="employees"),unsafe_allow_html=True)
        with c4: st.markdown(kpi_card("🔓","Unresolved",str(unres),badge="OPEN" if unres>0 else "CLEAR"),unsafe_allow_html=True)

    divider()

    # ── AI Engine Status ──────────────────────────────────────────────────
    st.markdown("### 🤖 AI Engine Status")
    visible_keys = {
        "👑 Admin":                 ["production","warehouse","maintenance","quality","safety"],
        "🏭 Factory Manager":       ["production","warehouse","maintenance","quality","safety"],
        "🏭 Production Supervisor": ["production","maintenance"],
        "🛠 Maintenance Engineer":  ["maintenance","production"],
        "✅ Quality Inspector":     ["quality","warehouse"],
        "⚠ Safety Officer":        ["safety","production"],
    }.get(role, ["production","maintenance","warehouse","quality","safety"])

    status_cols = st.columns(len(visible_keys))
    for col, key in zip(status_cols, visible_keys):
        with col:
            st.markdown(status_badge_html(engines[key]), unsafe_allow_html=True)

    divider()

    # ── Task Queue + Recommendations ──────────────────────────────────────
    col_tasks, col_recs = st.columns([3, 2])
    with col_tasks:
        html = '<div class="panel">'
        html += panel_title("📋", f"Live Task Queue — {role}")
        tasks = build_task_queue(engines, role)
        if not tasks:
            html += alert_row("✅ No active tasks for your role.", "success")
        else:
            counts = {p: sum(1 for t in tasks if t.priority==p) for p in [P.CRITICAL,P.HIGH,P.MEDIUM,P.LOW]}
            html += f"""<div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;">
            {"".join(f'<div style="background:{PRIORITY_STYLE[p]["bg"]};color:{PRIORITY_STYLE[p]["text"]};border:1px solid {PRIORITY_STYLE[p]["border"]}33;border-radius:8px;padding:5px 14px;font-size:12px;font-weight:700;">{PRIORITY_STYLE[p]["icon"]} {p}: {c}</div>' for p,c in counts.items() if c>0)}
            </div>"""
            for task in tasks[:8]:
                html += _task_card_html(task)
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    with col_recs:
        html = '<div class="panel">'
        html += panel_title("💡", "AI Recommendations")
        for rec in get_role_recommendations(engines, role):
            html += _rec_card_html(rec)
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    divider()

    # ══════════════════════════════════════════════════════════════════════
    # 🤖 AGENTIC AI OPERATIONS SYSTEM
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("## 🧠 Agentic AI Operations")

    coord = agent_coordinator(
        filtered_df, filtered_maint_df,
        filtered_warehouse_df, filtered_quality_df, filtered_safety_df
    )

    sev_color = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#f59e0b",
                 "LOW": "#3b82f6", "OK": "#22c55e"}
    sc = sev_color.get(coord.overall_severity, "#94a3b8")

    st.markdown(f"""
    <div style="background:{sc}10;border:1px solid {sc}44;border-left:6px solid {sc};
                border-radius:16px;padding:18px 22px;margin-bottom:18px;
                display:flex;align-items:center;justify-content:space-between;">
        <div>
            <div style="font-size:14px;font-weight:700;color:{sc};">
                {coord.summary}
            </div>
            <div style="font-size:12px;color:#64748b;margin-top:4px;">
                Priority Score: {coord.overall_priority}/100 · {len([d for d in coord.decisions if d.severity=="OK"])}/5 agents nominal
            </div>
        </div>
        <div style="font-size:28px;font-weight:800;color:{sc};">{coord.overall_priority}</div>
    </div>
    """, unsafe_allow_html=True)

    # Agent cards
    agent_cols = st.columns(5)
    for col, decision in zip(agent_cols, coord.decisions):
        with col:
            ac = sev_color.get(decision.severity, "#94a3b8")
            agent_icon = {"Production Agent": "🏭", "Maintenance Agent": "🛠",
                          "Warehouse Agent": "📦", "Quality Agent": "✅", "Safety Agent": "⚠"}
            st.markdown(f"""
            <div style="background:{ac}08;border:1px solid {ac}22;border-radius:12px;
                        padding:14px;text-align:center;">
                <div style="font-size:24px;">{agent_icon.get(decision.agent_name, "🤖")}</div>
                <div style="font-size:11px;font-weight:700;color:#0f172a;margin:6px 0 3px;">
                    {decision.agent_name.replace(" Agent", "")}
                </div>
                <div style="font-size:11px;font-weight:700;color:{ac};">{decision.severity}</div>
                <div style="font-size:10px;color:#64748b;margin-top:4px;">{decision.priority}/100</div>
                <div style="width:100%;height:4px;background:#f1f5f9;border-radius:4px;margin-top:6px;overflow:hidden;">
                    <div style="width:{min(decision.priority,100)}%;height:100%;background:{ac};
                                border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Cross-domain correlations (first 2)
    for corr in coord.cross_correlations[:2]:
        kind = "danger" if "crisis" in corr.lower() or "escalation" in corr.lower() else \
               "warning" if "correlation" in corr.lower() else "info"
        st.markdown(alert_row(corr, kind), unsafe_allow_html=True)

    # Detailed agent cards in expander
    with st.expander("📋 View detailed agent decisions"):
        for decision in coord.decisions:
            ac = sev_color.get(decision.severity, "#94a3b8")
            st.markdown(f"""
            <div style="background:{ac}06;border:1px solid {ac}22;border-radius:10px;
                        padding:12px 16px;margin-bottom:8px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <span style="font-size:16px;">{agent_icon.get(decision.agent_name, "🤖")}</span>
                    <span style="font-weight:700;font-size:13px;">{decision.agent_name}</span>
                    <span style="font-size:10px;background:{ac}18;color:{ac};padding:2px 10px;
                          border-radius:20px;font-weight:700;">{decision.severity}</span>
                    <span style="font-size:11px;color:#94a3b8;margin-left:auto;">Priority: {decision.priority}/100</span>
                </div>
                <div style="font-size:12px;color:#374151;font-weight:600;">{decision.issue}</div>
                <div style="font-size:11px;color:#64748b;">{decision.detail}</div>
                <div style="font-size:11px;color:#475569;margin-top:3px;">⚡ {decision.action}</div>
            </div>
            """, unsafe_allow_html=True)

    divider()

    # ══════════════════════════════════════════════════════════════════════
    # 🤖 AI FACTORY COPILOT — GEMINI SECTION
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("## 🤖 AI Factory Copilot")
    st.markdown(
        '<div style="color:#64748b;font-size:13px;margin-bottom:16px;">'
        'Real-time operational intelligence powered by Gemini. '
        'Analysis updates every refresh cycle based on live factory conditions.'
        '</div>',
        unsafe_allow_html=True
    )

    # Collect context values
    crit_machines  = len(filtered_maint_df[filtered_maint_df["Risk_Level"]=="High"]) if not filtered_maint_df.empty else 0
    fail_insp      = len(filtered_quality_df[filtered_quality_df["Inspection_Status"]=="Failed"]) if not filtered_quality_df.empty else 0
    crit_incidents = len(filtered_safety_df[filtered_safety_df["Severity"]=="Critical"]) if not filtered_safety_df.empty else 0
    low_stock      = int((filtered_warehouse_df["Current_stock"] < filtered_warehouse_df["Minimum_stock"]).sum()) if not filtered_warehouse_df.empty else 0
    breakdown_risk = len(filtered_df[filtered_df["Machine_Status"]=="Breakdown Risk"]) if not filtered_df.empty else 0
    avg_q_score    = round(filtered_quality_df["Quality_Score"].mean(),1) if not filtered_quality_df.empty else 0.0
    worst_line_dt  = str(filtered_df.groupby("Prod_line")["Downtime_min"].sum().idxmax()) if not filtered_df.empty else ""
    best_shift_str = str(filtered_df.groupby("shift")["Actual"].sum().idxmax()) if not filtered_df.empty else ""

    col_cop, col_btn = st.columns([5, 1])
    with col_btn:
        run_copilot = st.button("🤖 Analyze Now", use_container_width=True)

    if run_copilot or st.session_state.get("copilot_auto", False):
        with st.spinner("AI Copilot analyzing factory conditions..."):
            ai_response = generate_factory_ai_response(
                factory_health   = factory_health,
                avg_downtime     = avg_downtime,
                critical_machines= crit_machines,
                failed_inspections=fail_insp,
                critical_incidents=crit_incidents,
                low_stock_items  = low_stock,
                breakdown_risk   = breakdown_risk,
                avg_quality_score= avg_q_score,
                best_shift       = best_shift_str,
                worst_line       = worst_line_dt,
            )
        render_copilot_panel(st, ai_response, "Factory Operations Analysis")
        st.session_state["last_copilot_response"] = ai_response
    elif "last_copilot_response" in st.session_state:
        render_copilot_panel(st, st.session_state["last_copilot_response"],
                             "Factory Operations Analysis (Last Run)")

    # Admin overview panels
    if role in ["👑 Admin", "🏭 Factory Manager"]:
        divider()
        col_ov, col_al = st.columns(2)
        with col_ov:
            html = '<div class="panel">'
            html += panel_title("📊", "All Module Status")
            for key, label, icon in [("production","Production","🏭"),("maintenance","Maintenance","🛠"),
                                      ("warehouse","Warehouse","📦"),("quality","Quality","✅"),("safety","Safety","⚠")]:
                r = engines[key]
                kind = "success" if r.overall_status=="ok" else "warning" if r.overall_status in ["low","medium"] else "danger"
                html += alert_row(f"{icon} {label}: {r.status_label}", kind)
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

        with col_al:
            html = '<div class="panel">'
            html += panel_title("🚨", "Critical Alerts")
            found = False
            for key in ["production","maintenance","warehouse","quality","safety"]:
                r = engines[key]
                for a in r.alerts:
                    if a.severity in [SEV.CRITICAL,"high"]:
                        html += f"""
                        <div class="alert-row alert-danger" style="margin-bottom:8px;">
                            <div class="alert-dot"></div>
                            <div><strong style="font-size:13px;">[{r.module}] {a.title}</strong><br>
                            <span style="font-size:12px;opacity:0.8;">{a.action}</span></div>
                        </div>"""
                        found = True
            if not found:
                html += alert_row("✅ No critical alerts", "success")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    # ── Live Cloud Incident Feed ──────────────────────────────────────────
    st.markdown("### ☁ Live Incident Feed (Supabase)")
    supabase = get_supabase()
    cl_resp = supabase.table("incident_log").select("*").order("created_at", desc=True).limit(5).execute()
    cloud_incidents = cl_resp.data or []
    if cloud_incidents:
        for inc in cloud_incidents:
            sev = inc.get("severity", "LOW")
            sev_color_map = {"LOW":"#78716c", "MEDIUM":"#f59e0b", "HIGH":"#ef4444", "CRITICAL":"#dc2626"}
            sc = sev_color_map.get(sev, "#78716c")
            st.markdown(f"""
            <div style="background:#ffffff;border-left:4px solid {sc};border:1px solid #e8e2d8;
                        border-left-width:4px;border-radius:10px;padding:12px 14px;margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong style="color:#1c1917;font-size:13px;">{inc.get('title','')}</strong>
                    <span style="color:{sc};font-weight:700;font-size:11px;">{sev}</span>
                </div>
                <div style="color:#78716c;font-size:12px;margin-top:4px;">{inc.get('description','')}</div>
                <div style="color:#a8a29e;font-size:10px;margin-top:4px;">
                    {inc.get('department','')} · {inc.get('timestamp','')} · {inc.get('status','')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No cloud incidents reported yet.")

elif page == "🏭  Production":
    show_role_banner()
    production.show(filtered_df)
    with st.expander("➕ Add Production Record", expanded=False):
        with st.form("form_prod"):
            col1, col2 = st.columns(2)
            with col1:
                p_prod = st.text_input("Product", placeholder="e.g. Panel-X")
                p_line = st.text_input("Prod Line", placeholder="Line 1")
                p_target = st.number_input("Target", min_value=0, value=100)
            with col2:
                p_date = st.date_input("Date")
                p_shift = st.selectbox("Shift", ["Day", "Night"])
                p_actual = st.number_input("Actual Output", min_value=0, value=100)
            p_downtime = st.number_input("Downtime (min)", min_value=0, value=0)
            p_status = st.selectbox("Machine Status", ["Running", "Idle", "Breakdown Risk"])
            if st.form_submit_button("Submit", type="primary"):
                insert_record("production", {
                    "date": p_date.strftime("%Y-%m-%d"), "product": p_prod,
                    "prod_line": p_line, "shift": p_shift,
                    "target": p_target, "actual": p_actual,
                    "downtime_min": p_downtime, "machine_status": p_status,
                })
                st.success("Record saved to cloud!")
                st.rerun()
    # Module-level copilot for Production Supervisor
    if role in ["👑 Admin","🏭 Factory Manager","🏭 Production Supervisor"]:
        divider()
        st.markdown("### 🤖 Production AI Copilot")
        if st.button("🤖 Get Production Analysis", key="prod_copilot"):
            prod_sum = filtered_df.groupby("Product")["Actual"].sum()
            dt_sum   = filtered_df.groupby("Prod_line")["Downtime_min"].sum()
            with st.spinner("Analyzing production data..."):
                resp = generate_production_analysis(
                    factory_health = factory_health,
                    avg_downtime   = avg_downtime,
                    breakdown_risk = len(filtered_df[filtered_df["Machine_Status"]=="Breakdown Risk"]),
                    best_product   = str(prod_sum.idxmax()) if not filtered_df.empty else "",
                    worst_line     = str(dt_sum.idxmax()) if not filtered_df.empty else "",
                    total_gap      = int(total_target - total_actual),
                )
            render_copilot_panel(st, resp, "Production Intelligence Analysis")

elif page == "📦  Warehouse":
    show_role_banner()
    warehouse.show(filtered_warehouse_df)
    with st.expander("➕ Add Inventory Record", expanded=False):
        with st.form("form_wh"):
            col1, col2 = st.columns(2)
            with col1:
                w_material = st.text_input("Material", placeholder="e.g. Motor A")
                w_supplier = st.text_input("Supplier")
            with col2:
                w_date = st.date_input("Date")
                w_stock = st.number_input("Current Stock", min_value=0, value=100)
                w_min = st.number_input("Minimum Stock", min_value=0, value=10)
            w_cost = st.number_input("Unit Cost", min_value=0.0, value=0.0, step=0.01)
            if st.form_submit_button("Submit", type="primary"):
                insert_record("warehouse", {
                    "date": w_date.strftime("%Y-%m-%d"), "material": w_material,
                    "current_stock": w_stock, "minimum_stock": w_min,
                    "supplier": w_supplier, "unit_cost": w_cost,
                })
                st.success("Record saved to cloud!")
                st.rerun()

elif page == "🛠  Maintenance":
    show_role_banner()
    maintenance.show(filtered_maint_df)
    with st.expander("➕ Add Maintenance Record", expanded=False):
        with st.form("form_maint"):
            col1, col2 = st.columns(2)
            with col1:
                m_mid = st.text_input("Machine ID", placeholder="MAC-001")
                m_date = st.date_input("Date")
            with col2:
                m_health = st.slider("Health Score", 0, 100, 85)
                m_risk = st.selectbox("Risk Level", ["Low", "Medium", "High"])
            m_status = st.selectbox("Maintenance Status", ["Scheduled", "In Progress", "Completed", "Pending"])
            if st.form_submit_button("Submit", type="primary"):
                insert_record("maintenance", {
                    "date": m_date.strftime("%Y-%m-%d"), "machine_id": m_mid,
                    "health_score": m_health, "risk_level": m_risk,
                    "maintenance_status": m_status,
                })
                st.success("Record saved to cloud!")
                st.rerun()
    # Module-level copilot for Maintenance Engineer
    if role in ["👑 Admin","🛠 Maintenance Engineer"] and not filtered_maint_df.empty:
        divider()
        st.markdown("### 🤖 Maintenance AI Copilot")
        if st.button("🤖 Get Maintenance Analysis", key="maint_copilot"):
            crit_cnt = len(filtered_maint_df[filtered_maint_df["Risk_Level"]=="High"])
            pend_cnt = len(filtered_maint_df[filtered_maint_df["Maintenance_Status"]=="Pending"])
            worst_m  = str(filtered_maint_df.loc[filtered_maint_df["Health_Score"].idxmin(),"Machine_ID"]) if not filtered_maint_df.empty else ""
            with st.spinner("Analyzing maintenance data..."):
                resp = generate_maintenance_analysis(
                    avg_health    = round(filtered_maint_df["Health_Score"].mean(),1),
                    critical_count= crit_cnt,
                    pending_tasks = pend_cnt,
                    worst_machine = worst_m,
                )
            render_copilot_panel(st, resp, "Predictive Maintenance Analysis")

elif page == "✅  Quality":
    show_role_banner()
    quality.show(filtered_quality_df)
    with st.expander("➕ Add Quality Record", expanded=False):
        with st.form("form_qual"):
            col1, col2 = st.columns(2)
            with col1:
                q_prod = st.text_input("Product", placeholder="Panel-X")
                q_date = st.date_input("Date")
            with col2:
                q_defect = st.number_input("Defective Units", min_value=0, value=0)
                q_score = st.slider("Quality Score %", 0, 100, 95)
            q_status = st.selectbox("Inspection Status", ["Passed", "Failed", "Pending", "Rework"])
            if st.form_submit_button("Submit", type="primary"):
                insert_record("quality", {
                    "date": q_date.strftime("%Y-%m-%d"), "product": q_prod,
                    "quality_score": q_score, "inspection_status": q_status,
                    "defective_units": q_defect,
                })
                st.success("Record saved to cloud!")
                st.rerun()

elif page == "⚠  Safety":
    show_role_banner()
    safety.show(filtered_safety_df)
    with st.expander("➕ Add Safety Record", expanded=False):
        with st.form("form_safe"):
            col1, col2 = st.columns(2)
            with col1:
                s_line = st.text_input("Prod Line", placeholder="Line 1")
                s_date = st.date_input("Date")
            with col2:
                s_sev = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
                s_affected = st.number_input("Employees Affected", min_value=0, value=0)
            s_status = st.selectbox("Safety Status", ["Resolved", "Active", "Under Investigation", "Closed"])
            if st.form_submit_button("Submit", type="primary"):
                insert_record("safety", {
                    "date": s_date.strftime("%Y-%m-%d"), "prod_line": s_line,
                    "severity": s_sev, "employees_affected": s_affected,
                    "safety_status": s_status,
                })
                st.success("Record saved to cloud!")
                st.rerun()
    # Module-level copilot for Safety Officer
    if role in ["👑 Admin","⚠ Safety Officer"] and not filtered_safety_df.empty:
        divider()
        st.markdown("### 🤖 Safety AI Copilot")
        if st.button("🤖 Get Safety Analysis", key="safety_copilot"):
            crit_s   = len(filtered_safety_df[filtered_safety_df["Severity"]=="Critical"])
            unres    = len(filtered_safety_df[filtered_safety_df["Safety_Status"]!="Resolved"])
            affected = int(filtered_safety_df["Employees_Affected"].sum())
            worst_l  = str(filtered_safety_df.groupby("Prod_line")["Employees_Affected"].sum().idxmax()) if not filtered_safety_df.empty else ""
            with st.spinner("Analyzing safety data..."):
                resp = generate_safety_analysis(
                    critical_incidents  = crit_s,
                    unresolved          = unres,
                    affected_employees  = affected,
                    worst_line          = worst_l,
                )
            render_copilot_panel(st, resp, "Safety Risk Analysis")

elif page == "📸  Incidents":
    show_role_banner()

    tab1, tab2, tab3, tab4 = st.tabs(["📸 Report Incident", "☁ Cloud Incident", "👁 AI Vision Analysis", "📋 Incident Feed"])

    with tab1:
        upload_incident()

    with tab2:
        st.markdown("### ☁ Cloud-Based Incident Report")
        st.caption("Stored directly in Supabase cloud database")
        with st.form("form_incident_cloud"):
            ci_title = st.text_input("Incident Title", placeholder="e.g. Conveyor jam on Line 3")
            ci_desc = st.text_area("Description", placeholder="Describe what happened...")
            cola, colb = st.columns(2)
            with cola:
                ci_dept = st.selectbox("Department", ["Production", "Warehouse", "Maintenance", "Quality", "Safety"])
            with colb:
                ci_sev = st.selectbox("Severity", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            if st.form_submit_button("🚀 Submit to Cloud", type="primary"):
                supabase = get_supabase()
                supabase.table("incident_log").insert({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "title": ci_title, "description": ci_desc,
                    "department": ci_dept, "severity": ci_sev, "status": "Open",
                }).execute()
                st.success("Incident saved to Supabase cloud!")
                st.rerun()

    with tab3:
        st.markdown("## 👁 AI Visual Incident Intelligence")
        st.markdown("Upload a factory image for AI-powered visual analysis using Gemini Vision.")

        uploaded_image = st.file_uploader(
            "Upload Factory Incident Image",
            type=["png", "jpg", "jpeg"],
            key="vision_upload"
        )

        if uploaded_image:
            st.image(uploaded_image, use_container_width=True)
            with st.spinner("Analyzing incident using Gemini Vision..."):
                analysis = analyze_incident_image(uploaded_image)
            render_vision_analysis(st, analysis)

    with tab4:
        st.markdown("### ☁ Cloud Incident Feed (Supabase)")
        supabase = get_supabase()
        cl_resp = supabase.table("incident_log").select("*").order("created_at", desc=True).limit(50).execute()
        cloud_incidents = cl_resp.data or []
        if cloud_incidents:
            for inc in cloud_incidents:
                sev = inc.get("severity", "LOW")
                sev_color = {"LOW":"#78716c","MEDIUM":"#f59e0b","HIGH":"#ef4444","CRITICAL":"#dc2626"}.get(sev,"#78716c")
                st.markdown(f"""
                <div style="background:#ffffff;border-left:4px solid {sev_color};border:1px solid #e8e2d8;
                            border-left-width:4px;border-radius:10px;padding:12px 14px;margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;">
                        <strong style="color:#1c1917;font-size:13px;">{inc.get('title','')}</strong>
                        <span style="color:{sev_color};font-weight:700;font-size:11px;">{sev}</span>
                    </div>
                    <div style="color:#78716c;font-size:12px;margin-top:4px;">{inc.get('description','')}</div>
                    <div style="color:#a8a29e;font-size:10px;margin-top:4px;">
                        {inc.get('department','')} · {inc.get('timestamp','')} · {inc.get('status','')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No cloud incidents yet.")
        st.markdown("---")
        st.markdown("### 📋 Local Incident Feed (Legacy)")
        render_incident_stats()
        divider()
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            dept_filter = st.selectbox("Filter by Department", ["ALL"] + DEPARTMENTS, key="inc_dept_filter")
        with col_f2:
            sev_filter = st.selectbox("Filter by Severity", ["ALL"] + SEVERITIES, key="inc_sev_filter")
        render_incident_feed(
            department_filter=dept_filter if dept_filter != "ALL" else None,
            severity_filter=sev_filter if sev_filter != "ALL" else None,
        )

elif page == "🔮  Simulator":
    show_role_banner()
    st.markdown("## 🔮 Digital Twin — Operational Scenario Intelligence")
    st.markdown("Simulate real-world factory scenarios. Explore impact cascades, recovery costs, and AI-driven strategies.")

    # ── SCENARIO QUICK-SELECT ────────────────────────────────────────────────
    st.markdown(panel_title("📚", "Scenario Library — Quick Select"), unsafe_allow_html=True)
    sc_cols = st.columns(5)
    scenario_keys = list(SCENARIOS.keys())
    scenario_names = [SCENARIOS[k]["name"] for k in scenario_keys]
    scenario_icons = ["⚙", "📦", "✅", "⚠", "📈"]

    if "selected_scenario" not in st.session_state:
        st.session_state.selected_scenario = "custom"

    for i, (sk, sn, si) in enumerate(zip(scenario_keys, scenario_names, scenario_icons)):
        with sc_cols[i]:
            active = st.session_state.selected_scenario == sk
            btn_type = "primary" if active else "secondary"
            if st.button(f"{si} {sn}", key=f"sc_{sk}", use_container_width=True, type=btn_type):
                st.session_state.selected_scenario = sk
                st.rerun()

    if st.button("✏️ Custom Scenario", key="sc_custom", use_container_width=True,
                 type="primary" if st.session_state.selected_scenario == "custom" else "secondary"):
        st.session_state.selected_scenario = "custom"
        st.rerun()

    # ── PARAMETERS ──────────────────────────────────────────────────────────
    st.markdown(panel_title("🎛", "Simulation Parameters"), unsafe_allow_html=True)

    # Load scenario defaults if a preset is selected
    default_params = SimulationInput()
    if st.session_state.selected_scenario in SCENARIOS:
        default_params = SCENARIOS[st.session_state.selected_scenario]["params"]

    c1, c2 = st.columns(2)
    with c1:
        sim_dt = st.slider("⏱ Downtime (min per line)", 0, 120,
                           int(default_params.downtime_min), help="Average downtime per production line")
        sim_failures = st.slider("🔧 Machine Failures", 0, 10,
                                 default_params.machine_failure_count, help="Concurrent machine failures")
        sim_shortage = st.slider("📦 Inventory Shortage (SKUs)", 0, 100,
                                 default_params.inventory_shortage, help="Items below minimum stock")
        sim_quality_fail = st.slider("❌ Quality Fail Rate", 0, 20,
                                     default_params.quality_fail_rate, help="Defective rate per 100 units")
    with c2:
        sim_safety = st.select_slider("⚠ Safety Severity",
                                      ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                                      value=default_params.safety_severity,
                                      help="Worst-case safety incident severity")
        sim_load = st.slider("📊 Production Load (%)", 50, 160,
                             int(default_params.production_load_pct),
                             help="Production capacity utilisation")
        sim_cost = st.number_input("💰 Cost per Minute (₹)", min_value=1000, max_value=100000,
                                   value=default_params.cost_per_minute, step=1000,
                                   help="Financial impact rate per minute of downtime")

    run_sim = st.button("🚀 Run Simulation", use_container_width=True, type="primary")

    if run_sim:
        params = SimulationInput(
            scenario_id=st.session_state.selected_scenario,
            downtime_min=sim_dt,
            machine_failure_count=sim_failures,
            inventory_shortage=sim_shortage,
            safety_severity=sim_safety,
            production_load_pct=float(sim_load),
            quality_fail_rate=sim_quality_fail,
            cost_per_minute=sim_cost,
        )

        base_health = round(filtered_maint_df["Health_Score"].mean(), 1) if not filtered_maint_df.empty else 85.0
        base_quality = round(filtered_quality_df["Quality_Score"].mean(), 1) if not filtered_quality_df.empty else 85.0
        base_target = int(filtered_df["Target"].sum()) if not filtered_df.empty else 6000

        result = simulate_factory_conditions(params, base_health, base_quality, base_target)

        divider()
        st.markdown("## 📊 Digital Twin Simulation Results")

        sev_c = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#f59e0b", "LOW": "#22c55e"}
        rc = sev_c.get(result.risk_level, "#94a3b8")

        # ── RESILIENCE SCORE (hero) ───────────────────────────────────────
        rs_col1, rs_col2 = st.columns([1, 3])
        with rs_col1:
            res = result.resilience_score
            res_color = "#22c55e" if res >= 75 else "#f59e0b" if res >= 50 else "#ef4444"
            st.markdown(f"""
            <div style="background:white;border-radius:16px;padding:24px;text-align:center;
                        box-shadow:0 4px 16px rgba(0,0,0,0.06);">
                <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;
                            letter-spacing:1.2px;margin-bottom:8px;">Factory Resilience</div>
                <div style="position:relative;width:140px;height:140px;margin:0 auto 12px;">
                    <svg viewBox="0 0 120 120" style="transform:rotate(-90deg);width:140px;height:140px;">
                        <circle cx="60" cy="60" r="50" fill="none" stroke="#f1f5f9" stroke-width="10"/>
                        <circle cx="60" cy="60" r="50" fill="none" stroke="{res_color}" stroke-width="10"
                                stroke-dasharray="{res*3.14}" stroke-dashoffset="0"
                                stroke-linecap="round" style="transition:stroke-dasharray 0.8s ease;"/>
                    </svg>
                    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
                                font-size:36px;font-weight:800;color:{res_color};">{res}</div>
                </div>
                <div style="font-size:13px;font-weight:600;color:#0f172a;">{result.scenario_name}</div>
                <div style="font-size:11px;color:#64748b;margin-top:4px;">
                    {'🟢 Stable' if res >= 75 else '🟡 Watch' if res >= 50 else '🔴 Critical'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with rs_col2:
            # ── IMPACT SUMMARY ────────────────────────────────────────────
            st.markdown(f"""
            <div style="background:white;border-radius:16px;padding:20px 24px;margin-bottom:14px;
                        border-left:6px solid {rc};box-shadow:0 4px 16px rgba(0,0,0,0.06);">
                <div style="font-size:15px;font-weight:700;color:#0f172a;margin-bottom:8px;">
                    🧠 Operational Impact Summary — {result.scenario_name}</div>
                <div style="font-size:13px;color:#374151;line-height:1.7;">{result.summary}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── EXECUTIVE DECISION PANEL ──────────────────────────────────
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0f172a,#1e293b);border-radius:14px;
                        padding:16px 20px;margin-bottom:14px;">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                    <div style="color:white;font-size:13px;font-weight:700;">🏛 EXECUTIVE DECISION PANEL</div>
                    <div style="background:{rc}22;color:{rc};padding:3px 14px;border-radius:20px;
                                font-size:11px;font-weight:700;">{result.risk_level} RISK</div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;">
                    <div>
                        <div style="color:#94a3b8;font-size:10px;text-transform:uppercase;">Financial Impact</div>
                        <div style="color:white;font-size:18px;font-weight:800;">₹{result.financial_loss:,}</div>
                    </div>
                    <div>
                        <div style="color:#94a3b8;font-size:10px;text-transform:uppercase;">Confidence</div>
                        <div style="color:white;font-size:18px;font-weight:800;">{result.confidence}%</div>
                    </div>
                    <div>
                        <div style="color:#94a3b8;font-size:10px;text-transform:uppercase;">Recovery</div>
                        <div style="color:white;font-size:18px;font-weight:800;">{result.recovery.recovery_hours}h</div>
                    </div>
                    <div>
                        <div style="color:#94a3b8;font-size:10px;text-transform:uppercase;">Engineers</div>
                        <div style="color:white;font-size:18px;font-weight:800;">{result.recovery.engineers_required}</div>
                    </div>
                </div>
                <div style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.08);">
                    <div style="color:#94a3b8;font-size:10px;text-transform:uppercase;">Recommended Action</div>
                    <div style="color:white;font-size:13px;font-weight:600;margin-top:3px;">
                        {result.recommended_action}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── KPI ROW ───────────────────────────────────────────────────────
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            pct = abs(result.production_impact_pct)
            st.markdown(kpi_card("📉", "Production Impact", f"{pct:.1f}%",
                                  badge=result.risk_level, unit="change"), unsafe_allow_html=True)
        with r2:
            st.markdown(kpi_card("🎯", "Operational Risk", result.risk_level,
                                  badge=result.risk_level), unsafe_allow_html=True)
        with r3:
            st.markdown(kpi_card("🔧", "Maintenance", result.maintenance_pressure,
                                  badge=result.maintenance_pressure), unsafe_allow_html=True)
        with r4:
            st.markdown(kpi_card("⚠", "Safety Escalation", result.safety_escalation,
                                  badge=result.safety_escalation), unsafe_allow_html=True)

        # ── CASCADE · COST · RECOVERY · RESILIENCE ROW ────────────────────
        st.markdown("### 🔗 Impact Intelligence")
        ci1, ci2, ci3 = st.columns(3)
        with ci1:
            st.markdown(f"""
            <div style="background:white;border-radius:14px;padding:16px;
                        box-shadow:0 2px 12px rgba(0,0,0,0.05);height:100%;">
                <div style="font-size:13px;font-weight:700;color:#0f172a;margin-bottom:10px;">🌊 Impact Cascade</div>
                <div style="font-size:11px;color:#64748b;line-height:1.6;">{result.cascade.cascade_summary}</div>
                <div style="margin-top:10px;">
                    <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;">
                        <span style="color:#64748b;">Inventory Delay</span>
                        <span style="font-weight:600;">{result.cascade.inventory_delay_hrs}h</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;">
                        <span style="color:#64748b;">Delivery Risk</span>
                        <span style="font-weight:600;color:{sev_c.get(result.cascade.delivery_risk,'#64748b')};">{result.cascade.delivery_risk}</span>
                    </div>
                    <div style="font-size:11px;color:#475569;margin-top:6px;">
                        📋 {result.cascade.customer_impact}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with ci2:
            st.markdown(f"""
            <div style="background:white;border-radius:14px;padding:16px;
                        box-shadow:0 2px 12px rgba(0,0,0,0.05);height:100%;">
                <div style="font-size:13px;font-weight:700;color:#0f172a;margin-bottom:10px;">💰 Cost Impact</div>
                <div style="font-size:28px;font-weight:800;color:#0f172a;">₹{result.financial_loss:,}</div>
                <div style="font-size:11px;color:#64748b;margin-bottom:10px;">Total estimated financial loss</div>
                <div style="font-size:11px;color:#475569;">
                    Based on ₹{sim_cost:,}/min · {result.production_loss_units:,} units lost · {sim_failures} machine failure(s)
                </div>
            </div>
            """, unsafe_allow_html=True)

        with ci3:
            st.markdown(f"""
            <div style="background:white;border-radius:14px;padding:16px;
                        box-shadow:0 2px 12px rgba(0,0,0,0.05);height:100%;">
                <div style="font-size:13px;font-weight:700;color:#0f172a;margin-bottom:10px;">🔧 Recovery Simulator</div>
                <div style="display:flex;gap:16px;margin-bottom:8px;">
                    <div><span style="font-size:22px;font-weight:800;">{result.recovery.recovery_hours}</span>
                          <span style="font-size:11px;color:#64748b;"> hrs</span></div>
                    <div><span style="font-size:22px;font-weight:800;">{result.recovery.engineers_required}</span>
                          <span style="font-size:11px;color:#64748b;"> engineers</span></div>
                    <div><span style="font-size:22px;font-weight:800;color:#ef4444;">{result.recovery.units_lost_during:,}</span>
                          <span style="font-size:11px;color:#64748b;"> units lost</span></div>
                </div>
                <div style="font-size:11px;color:#475569;">{result.recovery.recommendation}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── RISK HEATMAP ───────────────────────────────────────────────────
        st.markdown("### 🗺 Line Risk Heatmap")
        heat_cols = st.columns(len(result.line_risks))
        for col, lr in zip(heat_cols, result.line_risks):
            hc = sev_c.get(lr.risk, "#94a3b8")
            with col:
                st.markdown(f"""
                <div style="background:white;border-radius:12px;padding:14px;text-align:center;
                            box-shadow:0 2px 10px rgba(0,0,0,0.05);">
                    <div style="font-size:14px;font-weight:700;color:#0f172a;margin-bottom:8px;">{lr.line_id}</div>
                    <div style="background:{hc}15;border-radius:50%;width:56px;height:56px;
                                display:flex;align-items:center;justify-content:center;margin:0 auto 8px;">
                        <span style="font-size:18px;font-weight:800;color:{hc};">{lr.score:.0f}</span>
                    </div>
                    <div style="width:100%;height:6px;background:#f1f5f9;border-radius:6px;overflow:hidden;">
                        <div style="width:{lr.score}%;height:100%;background:{hc};
                                    border-radius:6px;transition:width 0.6s ease;"></div>
                    </div>
                    <div style="font-size:11px;font-weight:700;color:{hc};margin-top:6px;">{lr.risk}</div>
                </div>
                """, unsafe_allow_html=True)

        # ── AI STRATEGY MODE ──────────────────────────────────────────────
        divider()
        st.markdown("### 🧠 AI Strategy Mode — Gemini Analysis")
        st.markdown("Let Gemini analyze this scenario and generate a strategic response.", unsafe_allow_html=True)

        if st.button("🤖 Run AI Strategy Analysis", key="sim_ai_strategy", use_container_width=True, type="primary"):
            with st.spinner("Gemini analyzing scenario and generating strategic response..."):
                ctx = build_strategy_context(result, result.scenario_name)
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    resp = model.generate_content(ctx)
                    strategy = resp.text
                except Exception as e:
                    strategy = f"⚠️ Gemini analysis unavailable: {e}"

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0f172a,#1e293b);border-radius:14px;
                        padding:20px 24px;margin-top:10px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                    <span style="font-size:18px;">🧠</span>
                    <div style="color:white;font-size:14px;font-weight:700;">Gemini Strategic Analysis</div>
                    <div style="background:rgba(255,255,255,0.1);color:#94a3b8;padding:2px 12px;
                                border-radius:20px;font-size:10px;margin-left:auto;">AI · {result.scenario_name}</div>
                </div>
                <div style="color:#cbd5e1;font-size:13px;line-height:1.7;
                            white-space:pre-wrap;">{strategy}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── DETAILED BREAKDOWN ─────────────────────────────────────────────
        with st.expander("📋 Full simulation breakdown"):
            for d in result.details:
                st.markdown(f"- {d}")
            st.metric("Production Loss Estimate", f"{result.production_loss_units:,} units/day")
            st.metric("Quality Score Estimate", f"{base_quality + result.quality_impact_pct:.1f}/100")
            st.metric("Fleet Health Estimate", f"{result.health_impact}/100")
            st.metric("Recovery Cost (₹)", f"₹{result.recovery.cost_of_recovery:,}")
            st.metric("Resilience Score", f"{result.resilience_score}/100")
    else:
        st.info("👆 Adjust parameters above and click **Run Simulation** to see predicted operational impacts.")

elif page == "📄  Executive Reports":
    show_role_banner()
    st.markdown("## 📄 Executive Report Generator")
    st.markdown(
        '<div style="color:#78716c;font-size:13px;margin-bottom:18px;">'
        "Generate AI-powered management reports with operational KPIs, risk analysis, "
        "and executive recommendations. Powered by Gemini AI."
        "</div>",
        unsafe_allow_html=True,
    )
    render_report_page(
        filtered_df, filtered_warehouse_df,
        filtered_maint_df, filtered_quality_df, filtered_safety_df, engines,
        selected_date=selected_date
    )