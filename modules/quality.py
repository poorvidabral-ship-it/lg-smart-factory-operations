import streamlit as st
import plotly.graph_objects as go
from modules.theme import page_header, kpi_card, alert_row, ai_card, panel_title, stat_strip, divider
from modules.ai_engine import detect_quality_risk, render_engine_alerts, status_badge_html

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

def _score_color(v):
    if v >= 85: return CLR_OK
    if v >= 70: return CLR_WARN
    return CLR_CRIT

def show(df):
    result = detect_quality_risk(df)
    page_header("✅", "Quality Intelligence",
                subtitle="Inspection results · Defect tracking · Quality scoring",
                badge=result.status_label)

    if len(df) == 0:
        st.markdown(alert_row("⚠ No quality data available for this date.", "warning"), unsafe_allow_html=True)
        return

    total_insp  = len(df)
    defective   = int(df["Defective_Units"].sum())
    avg_quality = round(df["Quality_Score"].mean(), 1)
    failed      = len(df[df["Inspection_Status"] == "Failed"])
    pass_rate   = round(((total_insp - failed) / total_insp) * 100, 1) if total_insp > 0 else 0

    st.markdown(stat_strip([
        ("Inspections", str(total_insp)),
        ("Pass Rate",   f"{pass_rate}%"),
        ("Failed",      str(failed)),
        ("Defective",   f"{defective:,}"),
        ("Avg Score",   str(avg_quality)),
    ]), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("🔍", "Inspections", str(total_insp), unit="records today"), unsafe_allow_html=True)
    with c2:
        qb = "EXCELLENT" if avg_quality >= 90 else ("GOOD" if avg_quality >= 75 else "POOR")
        st.markdown(kpi_card("⭐", "Avg Quality Score", str(avg_quality), unit="out of 100", badge=qb), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("❌", "Defective Units", f"{defective:,}", unit="units rejected"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("📋", "Failed Inspections", str(failed),
                              badge="ACTION NEEDED" if failed > 0 else "CLEAR"), unsafe_allow_html=True)

    divider()

    # ── Gauges row ────────────────────────────────────────────────────────
    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("⭐", "Quality Score Gauge"), unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_quality,
            number={"suffix": "/100", "font": {"size": 28, "color": "#0f172a"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar":  {"color": _score_color(avg_quality), "thickness": 0.28},
                "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
                "steps": [
                    {"range": [0,  65], "color": "rgba(239,68,68,0.1)"},
                    {"range": [65, 80], "color": "rgba(245,158,11,0.1)"},
                    {"range": [80,100], "color": "rgba(34,197,94,0.1)"},
                ],
                "threshold": {"line": {"color": "#a50034", "width": 3},
                              "thickness": 0.85, "value": 80},
            },
            title={"text": "Avg Quality Score", "font": {"size": 12, "color": "#7a0026"}},
        ))
        fig_gauge.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=16, r=16, t=40, b=8))
        st.plotly_chart(fig_gauge, use_container_width=True, key="qual_gauge")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("📋", "Pass vs Fail"), unsafe_allow_html=True)
        fig_pf = go.Figure(go.Pie(
            labels=["Passed", "Failed"],
            values=[total_insp - failed, failed],
            hole=0.55,
            marker=dict(colors=[CLR_OK, CLR_CRIT], line=dict(color="white", width=2)),
            textinfo="label+percent", textfont=dict(size=12)
        ))
        fig_pf.update_layout(**_layout(
            title="Inspection Pass/Fail Split",
            annotations=[dict(text=f"{pass_rate:.0f}%<br>pass", x=0.5, y=0.5,
                              font_size=16, showarrow=False, font_color="#0f172a")],
            height=220, margin=dict(l=8, r=8, t=40, b=8)
        ))
        st.plotly_chart(fig_pf, use_container_width=True, key="qual_pf")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g3:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("🔴", "Defects by Product"), unsafe_allow_html=True)
        def_df = df.groupby("Product")["Defective_Units"].sum().reset_index().sort_values("Defective_Units", ascending=False)
        fig_def = go.Figure(go.Bar(
            x=def_df["Product"], y=def_df["Defective_Units"],
            marker=dict(color="#a50034", line=dict(width=0)),
            text=def_df["Defective_Units"], textposition="outside",
            hovertemplate="<b>%{x}</b><br>Defective: %{y}<extra></extra>"
        ))
        fig_def.update_layout(title="Defective Units per Product",
                              xaxis=dict(showgrid=False),
                              yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)"),
                              height=220, **LAYOUT)
        st.plotly_chart(fig_def, use_container_width=True, key="qual_def")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Quality score + failed table ──────────────────────────────────────
    col4, col5 = st.columns(2)
    with col4:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("📊", "Quality Score by Product"), unsafe_allow_html=True)
        q_df = df.groupby("Product")["Quality_Score"].mean().reset_index().sort_values("Quality_Score")
        fig = go.Figure(go.Bar(
            x=q_df["Quality_Score"], y=q_df["Product"], orientation="h",
            marker=dict(color=q_df["Quality_Score"].apply(_score_color), line=dict(width=0)),
            text=q_df["Quality_Score"].apply(lambda x: f"{x:.1f}"), textposition="outside",
            hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>"
        ))
        fig.add_vline(x=80, line_dash="dash", line_color="#a50034",
                      annotation_text="Target 80", annotation_font_color="#a50034",
                      annotation_font_size=10)
        fig.update_layout(title="Avg Quality Score per Product",
                          xaxis=dict(range=[0, 105], showgrid=True,
                                     gridcolor="rgba(0,0,0,0.04)"),
                          yaxis=dict(showgrid=False), height=280, **LAYOUT)
        st.plotly_chart(fig, use_container_width=True, key="qual_bar")
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("⚠", "Failed Inspections"), unsafe_allow_html=True)
        fail_df = df[df["Inspection_Status"] == "Failed"].reset_index(drop=True)
        if len(fail_df) == 0:
            st.markdown(alert_row("✅ No failed inspections today", "success"), unsafe_allow_html=True)
        else:
            st.dataframe(fail_df, use_container_width=True, hide_index=True)
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
        st.markdown(panel_title("📈", "Quality Intelligence"), unsafe_allow_html=True)
        st.markdown(ai_card("Pass Rate",     f"{pass_rate}%",         f"{total_insp - failed} of {total_insp} passed"), unsafe_allow_html=True)
        st.markdown(ai_card("Quality Index", f"{avg_quality}/100",    "Avg score across all products"), unsafe_allow_html=True)
        st.markdown(ai_card("Defect Count",  f"{defective:,} units",  "Root cause review recommended"), unsafe_allow_html=True)
        st.markdown(alert_row("⚠ Smart TV panels elevated defect rates", "warning"), unsafe_allow_html=True)
        st.markdown(alert_row("🚨 Line-2 failures exceeded threshold",
                               "danger" if failed > 2 else "warning"), unsafe_allow_html=True)
        st.markdown(alert_row("✅ Quality monitoring systems active", "success"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)