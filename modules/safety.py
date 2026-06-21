import streamlit as st
import plotly.graph_objects as go
from modules.theme import page_header, kpi_card, alert_row, ai_card, panel_title, stat_strip, divider
from modules.ai_engine import detect_safety_risk, render_engine_alerts, status_badge_html

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#475569", size=12),
    title_font=dict(color="#7a0026", size=14),
    margin=dict(l=8, r=8, t=44, b=8),
)
def _layout(**extra):
    d = {k: v for k, v in LAYOUT.items()}
    d.update(extra)
    return d
CLR_OK   = "#22c55e"
CLR_WARN = "#f59e0b"
CLR_CRIT = "#ef4444"

def show(df):
    result = detect_safety_risk(df)
    page_header("⚠", "Safety Intelligence",
                subtitle="Incident tracking · Severity analysis · Employee protection",
                badge=result.status_label)

    if len(df) == 0:
        st.markdown(alert_row("⚠ No safety data available for this date.", "warning"), unsafe_allow_html=True)
        return

    total_incidents = len(df)
    critical        = len(df[df["Severity"] == "Critical"])
    affected        = int(df["Employees_Affected"].sum())
    unresolved      = len(df[df["Safety_Status"] != "Resolved"])
    resolved        = total_incidents - unresolved
    resolution_rate = round((resolved / total_incidents) * 100, 1) if total_incidents > 0 else 0

    st.markdown(stat_strip([
        ("Incidents",       str(total_incidents)),
        ("Critical",        str(critical)),
        ("Affected",        str(affected)),
        ("Unresolved",      str(unresolved)),
        ("Resolution Rate", f"{resolution_rate}%"),
    ]), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("📋", "Total Incidents", str(total_incidents), unit="recorded today"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("🚨", "Critical Incidents", str(critical),
                              badge="URGENT" if critical > 0 else "CLEAR"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("👷", "Employees Affected", str(affected), unit="workers impacted"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("🔓", "Unresolved Cases", str(unresolved),
                              badge="OPEN" if unresolved > 0 else "ALL CLEAR"), unsafe_allow_html=True)

    divider()

    # ── Severity gauge + donut + resolution ──────────────────────────────
    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("🚨", "Safety Risk Level"), unsafe_allow_html=True)
        risk_val = (critical * 40 + unresolved * 20 + (affected / max(affected, 1)) * 20)
        risk_val = min(risk_val, 100)
        risk_color = CLR_CRIT if risk_val > 60 else CLR_WARN if risk_val > 30 else CLR_OK
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_val,
            number={"suffix": " risk", "font": {"size": 24, "color": "#0f172a"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar":  {"color": risk_color, "thickness": 0.28},
                "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
                "steps": [
                    {"range": [0,  30], "color": "rgba(34,197,94,0.1)"},
                    {"range": [30, 60], "color": "rgba(245,158,11,0.1)"},
                    {"range": [60,100], "color": "rgba(239,68,68,0.1)"},
                ],
            },
            title={"text": "Composite Risk Score", "font": {"size": 12, "color": "#7a0026"}},
        ))
        fig_gauge.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=16, r=16, t=40, b=8))
        st.plotly_chart(fig_gauge, use_container_width=True, key="safety_gauge")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("🥧", "Severity Breakdown"), unsafe_allow_html=True)
        sev_df = df["Severity"].value_counts().reset_index()
        sev_df.columns = ["Severity", "Count"]
        cmap = {"Critical": CLR_CRIT, "High": "#f97316", "Medium": CLR_WARN, "Low": CLR_OK}
        fig2 = go.Figure(go.Pie(
            labels=sev_df["Severity"], values=sev_df["Count"], hole=0.5,
            marker=dict(colors=[cmap.get(s, "#94a3b8") for s in sev_df["Severity"]],
                        line=dict(color="white", width=2)),
            textinfo="label+percent", textfont=dict(size=12)
        ))
        fig2.update_layout(title="Incident Severity Split",
                           height=220, **_layout(margin=dict(l=8, r=8, t=40, b=8)))
        st.plotly_chart(fig2, use_container_width=True, key="safety_sev")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g3:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("✅", "Resolution Status"), unsafe_allow_html=True)
        fig_res = go.Figure(go.Pie(
            labels=["Resolved", "Unresolved"],
            values=[resolved, unresolved],
            hole=0.55,
            marker=dict(colors=[CLR_OK, CLR_CRIT], line=dict(color="white", width=2)),
            textinfo="label+percent", textfont=dict(size=12)
        ))
        fig_res.update_layout(
            title="Case Resolution Rate",
            annotations=[dict(text=f"{resolution_rate:.0f}%", x=0.5, y=0.5,
                              font_size=20, showarrow=False, font_color="#0f172a")],
            height=220, **_layout(margin=dict(l=8, r=8, t=40, b=8))
        )
        st.plotly_chart(fig_res, use_container_width=True, key="safety_res")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Incidents by line + affected heatmap ─────────────────────────────
    col4, col5 = st.columns(2)
    with col4:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("📊", "Incidents by Production Line"), unsafe_allow_html=True)
        inc_df = df.groupby("Prod_line")["Employees_Affected"].sum().reset_index().sort_values("Employees_Affected", ascending=False)
        inc_colors = [CLR_CRIT if v > 5 else CLR_WARN if v > 2 else CLR_OK for v in inc_df["Employees_Affected"]]
        fig = go.Figure(go.Bar(
            x=inc_df["Prod_line"], y=inc_df["Employees_Affected"],
            marker=dict(color=inc_colors, line=dict(width=0)),
            text=inc_df["Employees_Affected"], textposition="outside",
            hovertemplate="<b>Line %{x}</b><br>Affected: %{y}<extra></extra>"
        ))
        fig.update_layout(title="Employees Affected per Line",
                          xaxis=dict(showgrid=False),
                          yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)"),
                          height=280, **LAYOUT)
        st.plotly_chart(fig, use_container_width=True, key="safety_bar")
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("🚨", "Critical Incidents Table"), unsafe_allow_html=True)
        crit_df = df[df["Severity"] == "Critical"].reset_index(drop=True)
        if len(crit_df) == 0:
            st.markdown(alert_row("✅ No critical incidents recorded today", "success"), unsafe_allow_html=True)
        else:
            st.dataframe(crit_df, use_container_width=True, hide_index=True)
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
        st.markdown(panel_title("🛡", "Safety Intelligence"), unsafe_allow_html=True)
        st.markdown(ai_card("Resolution Rate", f"{resolution_rate}%",       f"{resolved} of {total_incidents} cases closed"), unsafe_allow_html=True)
        st.markdown(ai_card("Critical Risk",   f"{critical} incidents",      "Immediate intervention required"), unsafe_allow_html=True)
        st.markdown(ai_card("People at Risk",  f"{affected} employees",      "Affected across all lines"), unsafe_allow_html=True)
        st.markdown(alert_row("⚠ Line-3 overheating incidents recurring", "warning"), unsafe_allow_html=True)
        st.markdown(alert_row("🚨 Critical violations in Line-2",
                               "danger" if critical > 0 else "success"), unsafe_allow_html=True)
        st.markdown(alert_row("🔌 Electrical systems — immediate inspection", "info"), unsafe_allow_html=True)
        st.markdown(alert_row("✅ Safety monitoring active", "success"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)