import streamlit as st
import plotly.graph_objects as go
from modules.theme import page_header, kpi_card, alert_row, ai_card, panel_title, stat_strip, divider
from modules.ai_engine import detect_maintenance_risk, render_engine_alerts, status_badge_html
from modules.predictive_engine import run_predictive_analysis, generate_predictive_alerts

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#475569", size=12),
    title_font=dict(color="#7a0026", size=14),
    margin=dict(l=8, r=8, t=44, b=8),
)
def _layout(**extra):
    """Return LAYOUT with margin overridden if supplied."""   
    d = {k: v for k, v in LAYOUT.items()}
    d.update(extra)
    return d
CLR_OK   = "#22c55e"
CLR_WARN = "#f59e0b"
CLR_CRIT = "#ef4444"

def _health_color(v):
    if v >= 80: return CLR_OK
    if v >= 60: return CLR_WARN
    return CLR_CRIT

def show(df):
    result = detect_maintenance_risk(df)
    page_header("🛠", "Maintenance Intelligence",
                subtitle="Machine health · Risk levels · Predictive scheduling",
                badge=result.status_label)

    if len(df) == 0:
        st.markdown(alert_row("⚠ No maintenance data available for this date.", "warning"), unsafe_allow_html=True)
        return

    total_machines = df["Machine_ID"].nunique()
    critical       = len(df[df["Risk_Level"] == "High"])
    avg_health     = round(df["Health_Score"].mean(), 1)
    pending        = len(df[df["Maintenance_Status"] == "Pending"])
    completed      = len(df[df["Maintenance_Status"] == "Completed"]) if "Completed" in df["Maintenance_Status"].values else 0

    st.markdown(stat_strip([
        ("Machines",    str(total_machines)),
        ("Critical",    str(critical)),
        ("Avg Health",  str(avg_health)),
        ("Pending",     str(pending)),
        ("Completed",   str(completed)),
    ]), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("⚙", "Total Machines", str(total_machines), unit="tracked assets"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("🔴", "Critical Machines", str(critical),
                              badge="URGENT" if critical > 0 else "CLEAR"), unsafe_allow_html=True)
    with c3:
        hb = "GOOD" if avg_health >= 80 else ("FAIR" if avg_health >= 60 else "POOR")
        st.markdown(kpi_card("💚", "Avg Health Score", str(avg_health), unit="out of 100", badge=hb), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("🔧", "Pending Tasks", str(pending), unit="awaiting service"), unsafe_allow_html=True)

    divider()

    dt_col = next((c for c in ["Downtime_Min","Downtime_min","Downtime","Downtime Min"] if c in df.columns), None)

    # ── Gauge + Health histogram ──────────────────────────────────────────
    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("💚", "Fleet Health Score"), unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_health,
            number={"suffix": "/100", "font": {"size": 28, "color": "#0f172a"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar":  {"color": _health_color(avg_health), "thickness": 0.28},
                "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
                "steps": [
                    {"range": [0,  40], "color": "rgba(239,68,68,0.1)"},
                    {"range": [40, 60], "color": "rgba(245,158,11,0.1)"},
                    {"range": [60, 80], "color": "rgba(245,158,11,0.07)"},
                    {"range": [80,100], "color": "rgba(34,197,94,0.1)"},
                ],
                "threshold": {"line": {"color": "#a50034", "width": 3},
                              "thickness": 0.85, "value": 80},
            },
            title={"text": "Avg Machine Health", "font": {"size": 12, "color": "#7a0026"}},
        ))
        fig_gauge.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=16, r=16, t=40, b=8))
        st.plotly_chart(fig_gauge, use_container_width=True, key="maint_gauge")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("📊", "Health Distribution"), unsafe_allow_html=True)
        fig_hist = go.Figure(go.Histogram(
            x=df["Health_Score"], nbinsx=10,
            marker=dict(
                color=df["Health_Score"].apply(_health_color),
                line=dict(color="white", width=1)
            )
        ))
        fig_hist.add_vline(x=40, line_dash="dash", line_color=CLR_CRIT, line_width=1.5,
                           annotation_text="Critical", annotation_font_color=CLR_CRIT,
                           annotation_font_size=10)
        fig_hist.add_vline(x=60, line_dash="dash", line_color=CLR_WARN, line_width=1.5,
                           annotation_text="Warning", annotation_font_color=CLR_WARN,
                           annotation_font_size=10)
        fig_hist.update_layout(title="Health Score Spread",
                               xaxis=dict(title="Score", showgrid=False),
                               yaxis=dict(title="Machines", showgrid=True,
                                          gridcolor="rgba(0,0,0,0.04)"),
                               height=220, **LAYOUT)
        st.plotly_chart(fig_hist, use_container_width=True, key="maint_hist")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g3:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("🔴", "Risk Distribution"), unsafe_allow_html=True)
        risk_counts = df["Risk_Level"].value_counts().reset_index()
        risk_counts.columns = ["Risk", "Count"]
        risk_cmap = {"High": CLR_CRIT, "Medium": CLR_WARN, "Low": CLR_OK}
        fig_risk = go.Figure(go.Pie(
            labels=risk_counts["Risk"], values=risk_counts["Count"], hole=0.52,
            marker=dict(colors=[risk_cmap.get(r, "#94a3b8") for r in risk_counts["Risk"]],
                        line=dict(color="white", width=2)),
            textinfo="label+percent", textfont=dict(size=11)
        ))
        fig_risk.update_layout(**_layout(title="Machine Risk Levels", height=220, margin=dict(l=8, r=8, t=40, b=8)))
        st.plotly_chart(fig_risk, use_container_width=True, key="maint_risk_pie")
        st.markdown('</div>', unsafe_allow_html=True)

    divider()

    # ── PREDICTIVE MAINTENANCE INTELLIGENCE ────────────────────────────────
    st.markdown("## 🔮 Predictive Maintenance Intelligence")

    pred_report = run_predictive_analysis(df)

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        risk_badge = "CRITICAL" if pred_report.fleet_avg_risk >= 70 else ("HIGH" if pred_report.fleet_avg_risk >= 50 else "LOW")
        st.markdown(kpi_card("📊", "Fleet Risk Score", f"{pred_report.fleet_avg_risk}%", badge=risk_badge), unsafe_allow_html=True)
    with p2:
        st.markdown(kpi_card("🔴", "Critical Risk", str(pred_report.critical_count), badge="IMMINENT" if pred_report.critical_count > 0 else "NONE"), unsafe_allow_html=True)
    with p3:
        st.markdown(kpi_card("🟠", "High Risk", str(pred_report.high_count), badge="URGENT" if pred_report.high_count > 0 else "CLEAR"), unsafe_allow_html=True)
    with p4:
        st.markdown(kpi_card("📦", "Impact Estimate", f"{pred_report.total_impact_units:,}", unit="units/day"), unsafe_allow_html=True)

    # Predictive alerts
    pred_alerts = generate_predictive_alerts(pred_report.predictions)
    for a in pred_alerts:
        kind = "danger" if "CRITICAL" in a else "warning" if "HIGH" in a else "success"
        st.markdown(alert_row(a, kind), unsafe_allow_html=True)

    # Per-machine breakdown
    if pred_report.predictions:
        st.markdown(panel_title("🔮", "Machine Risk Breakdown — Predictive Ranking"), unsafe_allow_html=True)
        pred_rows = []
        for p in pred_report.predictions[:10]:
            urgency_color = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#f59e0b", "LOW": "#22c55e"}
            bar_pct = min(p.risk_score, 100)
            bar_color = urgency_color.get(p.urgency, "#94a3b8")
            pred_rows.append(f"""
            <div style="background:white;border-radius:12px;padding:14px 18px;margin-bottom:8px;
                        border-left:4px solid {bar_color};box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                    <div>
                        <strong style="font-size:15px;color:#0f172a;">{p.machine_id}</strong>
                        <span style="font-size:11px;color:#94a3b8;margin-left:8px;">Health: {p.health_score}/100</span>
                    </div>
                    <div style="background:{bar_color}15;color:{bar_color};font-size:11px;font-weight:700;
                                padding:3px 12px;border-radius:20px;">{p.urgency}</div>
                </div>
                <div style="display:flex;gap:20px;font-size:12px;color:#475569;margin-bottom:8px;flex-wrap:wrap;">
                    <span>🎯 Risk: <strong>{p.risk_score}%</strong></span>
                    <span>💥 Failure: <strong>{p.breakdown_prob}%</strong></span>
                    <span>📦 {p.impact_label}</span>
                    <span>🔧 <strong>{p.status}</strong></span>
                </div>
                <div style="width:100%;height:6px;background:#f1f5f9;border-radius:10px;overflow:hidden;">
                    <div style="width:{bar_pct}%;height:100%;background:{bar_color};border-radius:10px;
                                transition:width 0.4s ease;"></div>
                </div>
                <div style="font-size:11px;color:#64748b;margin-top:6px;">💡 {p.recommendation}</div>
            </div>
            """)
        st.markdown("".join(pred_rows), unsafe_allow_html=True)

    # ── Downtime + health per line ────────────────────────────────────────
    col4, col5 = st.columns(2)
    with col4:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("📊", "Downtime by Line"), unsafe_allow_html=True)
        has_line = "Prod_line" in df.columns
        if dt_col and has_line:
            dt_df = df.groupby("Prod_line")[dt_col].sum().reset_index().sort_values(dt_col, ascending=False)
            dt_colors = [CLR_CRIT if v > 30 else CLR_WARN if v > 15 else CLR_OK for v in dt_df[dt_col]]
            fig = go.Figure(go.Bar(
                x=dt_df["Prod_line"], y=dt_df[dt_col],
                marker=dict(color=dt_colors, line=dict(width=0)),
                text=dt_df[dt_col].apply(lambda x: f"{x:.0f}m"), textposition="outside",
                hovertemplate="<b>Line %{x}</b><br>Downtime: %{y:.0f} min<extra></extra>"
            ))
            fig.add_hline(y=30, line_dash="dash", line_color=CLR_CRIT, line_width=1.5,
                          annotation_text="Critical 30m", annotation_font_color=CLR_CRIT,
                          annotation_font_size=10)
            fig.update_layout(title="Total Downtime per Line (min)",
                              xaxis=dict(showgrid=False),
                              yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)"),
                              height=280, **LAYOUT)
            st.plotly_chart(fig, use_container_width=True, key="maint_dt")
        else:
            msg = "Prod_line or downtime column not found." if not has_line else "Downtime column not found."
            st.markdown(alert_row(msg, "warning"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("💚", "Health Score per Machine"), unsafe_allow_html=True)
        health_df = df[["Machine_ID", "Health_Score", "Risk_Level"]].sort_values("Health_Score")
        fig2 = go.Figure(go.Bar(
            x=health_df["Health_Score"],
            y=health_df["Machine_ID"].astype(str),
            orientation="h",
            marker=dict(color=health_df["Health_Score"].apply(_health_color),
                        line=dict(width=0)),
            text=health_df["Health_Score"].apply(lambda x: f"{x:.0f}"),
            textposition="outside",
            hovertemplate="<b>Machine %{y}</b><br>Health: %{x}<extra></extra>"
        ))
        fig2.add_vline(x=40, line_dash="dash", line_color=CLR_CRIT, line_width=1.5)
        fig2.add_vline(x=60, line_dash="dash", line_color=CLR_WARN, line_width=1.5)
        fig2.update_layout(title="Individual Machine Health Scores",
                           xaxis=dict(range=[0, 120], showgrid=True,
                                      gridcolor="rgba(0,0,0,0.04)"),
                           yaxis=dict(showgrid=False),
                           height=280, **LAYOUT)
        st.plotly_chart(fig2, use_container_width=True, key="maint_health_bar")
        st.markdown('</div>', unsafe_allow_html=True)

    divider()

    # ── AI Engine ─────────────────────────────────────────────────────────
    col_ai, col_intel = st.columns([3, 2])
    with col_ai:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("🤖", f"AI Decision Engine — {result.status_label}"), unsafe_allow_html=True)
        st.markdown(f'<div style="color:#64748b;font-size:12px;margin-bottom:14px;">{result.summary}</div>',
                    unsafe_allow_html=True)
        render_engine_alerts(result, st)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_intel:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("🔧", "Maintenance Intelligence"), unsafe_allow_html=True)
        st.markdown(ai_card("Fleet Health",  f"{avg_health}/100",        "Overall machine health index"), unsafe_allow_html=True)
        st.markdown(ai_card("Critical Risk", f"{critical} machines",     "High risk — immediate inspection"), unsafe_allow_html=True)
        st.markdown(ai_card("Pending Queue", f"{pending} tasks",         "Awaiting execution"), unsafe_allow_html=True)
        st.markdown(alert_row("⚠ Line-3 machines show downtime spikes", "warning"), unsafe_allow_html=True)
        st.markdown(alert_row("🚨 Critical machines need immediate check",
                               "danger" if critical > 0 else "success"), unsafe_allow_html=True)
        st.markdown(alert_row("🛠 Preventive maintenance due in 3 days", "info"), unsafe_allow_html=True)
        st.markdown(alert_row("✅ Monitoring system active", "success"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Critical machines table ───────────────────────────────────────────
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(panel_title("⚠", "Critical Machines — High Risk"), unsafe_allow_html=True)
    crit_df = df[df["Risk_Level"] == "High"].reset_index(drop=True)
    if len(crit_df) == 0:
        st.markdown(alert_row("✅ No critical machines detected today", "success"), unsafe_allow_html=True)
    else:
        st.dataframe(crit_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)