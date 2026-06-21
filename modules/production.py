import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from modules.theme import page_header, kpi_card, alert_row, ai_card, panel_title, stat_strip, divider
from modules.ai_engine import detect_production_risk, render_engine_alerts, status_badge_html

# ── Shared chart theme ────────────────────────────────────────────────────────
LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#475569", size=12),
    title_font=dict(color="#7a0026", size=14, family="Inter, sans-serif"),
    margin=dict(l=8, r=8, t=44, b=8),
    legend=dict(bgcolor="rgba(255,255,255,0.55)", borderwidth=0, font=dict(size=11)),
)
GRID = dict(showgrid=True, gridcolor="rgba(0,0,0,0.045)", zeroline=False)
NO_GRID = dict(showgrid=False, zeroline=False)

LG_RED   = "#a50034"
LG_DARK  = "#7a0026"
LG_PINK  = "#d90452"
CLR_OK   = "#22c55e"
CLR_WARN = "#f59e0b"
CLR_CRIT = "#ef4444"

def _eff_color(val):
    if val >= 95:  return CLR_OK
    if val >= 80:  return CLR_WARN
    return CLR_CRIT

def _dt_color(val):
    if val <= 15:  return CLR_OK
    if val <= 25:  return CLR_WARN
    return CLR_CRIT

def show(df):
    # ── AI Engine ─────────────────────────────────────────────────────────
    result = detect_production_risk(df)
    page_header("🏭", "Production Intelligence",
                subtitle="Live output · Operational analytics · Risk monitoring",
                badge=result.status_label)

    if df.empty:
        st.markdown(alert_row("⚠ No production data for this date.", "warning"), unsafe_allow_html=True)
        return

    # ── Core KPI calculations ─────────────────────────────────────────────
    total_target   = df["Target"].sum()
    total_actual   = df["Actual"].sum()
    avg_downtime   = round(df["Downtime_min"].mean(), 1)
    factory_health = round((total_actual / total_target) * 100, 1) if total_target > 0 else 0
    active_lines   = df["Prod_line"].nunique()
    total_gap      = int(total_target - total_actual)
    breakdown_risk = len(df[df["Machine_Status"] == "Breakdown Risk"])

    prod_sum              = df.groupby("Product")["Actual"].sum()
    best_product          = prod_sum.idxmax()
    best_product_val      = int(prod_sum.max())
    worst_product         = prod_sum.idxmin()
    shift_sum             = df.groupby("shift")["Actual"].sum()
    best_shift            = shift_sum.idxmax()
    downtime_sum          = df.groupby("Prod_line")["Downtime_min"].sum()
    highest_downtime_line = downtime_sum.idxmax()
    highest_downtime_val  = int(downtime_sum.max())
    high_risk             = df[df["Machine_Status"] == "Breakdown Risk"]

    # ── Stat strip ────────────────────────────────────────────────────────
    st.markdown(stat_strip([
        ("Target",        f"{total_target:,}"),
        ("Actual Output", f"{total_actual:,}"),
        ("Output Gap",    f"{total_gap:,}"),
        ("Active Lines",  str(active_lines)),
        ("Avg Downtime",  f"{avg_downtime} min"),
    ]), unsafe_allow_html=True)

    # ── KPI Cards ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        b = "ON TARGET" if factory_health >= 95 else ("WATCH" if factory_health >= 80 else "AT RISK")
        st.markdown(kpi_card("⚡", "Factory Health", f"{factory_health}%", badge=b), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("📦", "Total Output", f"{total_actual:,}", unit="units produced"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("⏱", "Avg Downtime", str(avg_downtime), unit="minutes per line"), unsafe_allow_html=True)
    with c4:
        br_badge = "⚠ AT RISK" if breakdown_risk > 0 else "CLEAR"
        st.markdown(kpi_card("🔴", "Breakdown Risk", str(breakdown_risk), unit="machines flagged", badge=br_badge), unsafe_allow_html=True)

    divider()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1 — EFFICIENCY GAUGE + PRODUCTION OVERVIEW
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(panel_title("⚡", "Factory Efficiency Command"), unsafe_allow_html=True)

    g1, g2, g3 = st.columns([1, 1, 1])

    # Gauge — Factory Efficiency
    with g1:
        needle_color = _eff_color(factory_health)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=factory_health,
            delta={"reference": 100, "valueformat": ".1f",
                   "increasing": {"color": CLR_OK},
                   "decreasing": {"color": CLR_CRIT}},
            number={"suffix": "%", "font": {"size": 32, "color": "#0f172a", "family": "Inter"}},
            gauge={
                "axis": {"range": [0, 120], "tickwidth": 1,
                         "tickcolor": "#94a3b8", "tickfont": {"size": 10}},
                "bar":  {"color": needle_color, "thickness": 0.28},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0,   75],  "color": "rgba(239,68,68,0.12)"},
                    {"range": [75,  90],  "color": "rgba(245,158,11,0.12)"},
                    {"range": [90,  100], "color": "rgba(34,197,94,0.12)"},
                    {"range": [100, 120], "color": "rgba(34,197,94,0.22)"},
                ],
                "threshold": {"line": {"color": LG_RED, "width": 3},
                              "thickness": 0.85, "value": 100},
            },
            title={"text": "Factory Efficiency", "font": {"size": 13, "color": "#7a0026"}},
        ))
        fig_gauge.update_layout(height=240, **{k: v for k, v in LAYOUT.items()
                                               if k not in ["margin"]},
                                margin=dict(l=16, r=16, t=40, b=8))
        st.plotly_chart(fig_gauge, use_container_width=True, key="gauge_eff")

    # Gauge — Avg Downtime
    with g2:
        dt_color = _dt_color(avg_downtime)
        fig_dt_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_downtime,
            number={"suffix": " min", "font": {"size": 28, "color": "#0f172a", "family": "Inter"}},
            gauge={
                "axis": {"range": [0, 60], "tickwidth": 1, "tickfont": {"size": 10}},
                "bar":  {"color": dt_color, "thickness": 0.28},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0,  15], "color": "rgba(34,197,94,0.12)"},
                    {"range": [15, 30], "color": "rgba(245,158,11,0.12)"},
                    {"range": [30, 60], "color": "rgba(239,68,68,0.12)"},
                ],
                "threshold": {"line": {"color": LG_RED, "width": 3},
                              "thickness": 0.85, "value": 20},
            },
            title={"text": "Avg Line Downtime", "font": {"size": 13, "color": "#7a0026"}},
        ))
        fig_dt_gauge.update_layout(height=240, **{k: v for k, v in LAYOUT.items()
                                                   if k not in ["margin"]},
                                   margin=dict(l=16, r=16, t=40, b=8))
        st.plotly_chart(fig_dt_gauge, use_container_width=True, key="gauge_dt")

    # Machine Status Donut
    with g3:
        status_counts = df["Machine_Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        status_color_map = {
            "Running":        CLR_OK,
            "Maintenance":    CLR_WARN,
            "Breakdown Risk": CLR_CRIT,
        }
        fig_status = go.Figure(go.Pie(
            labels=status_counts["Status"],
            values=status_counts["Count"],
            hole=0.58,
            marker=dict(
                colors=[status_color_map.get(s, "#94a3b8") for s in status_counts["Status"]],
                line=dict(color="white", width=2)
            ),
            textinfo="label+percent",
            textfont=dict(size=11),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>"
        ))
        running = int(status_counts[status_counts["Status"] == "Running"]["Count"].sum()) if "Running" in status_counts["Status"].values else 0
        fig_status.update_layout(
            title="Machine Status",
            annotations=[dict(text=f"{running}<br><span style='font-size:9px'>running</span>",
                              x=0.5, y=0.5, font_size=18, showarrow=False, font_color="#0f172a")],
            height=240, **{k: v for k, v in LAYOUT.items() if k not in ["margin"]},
            margin=dict(l=8, r=8, t=40, b=8)
        )
        st.plotly_chart(fig_status, use_container_width=True, key="status_donut")

    st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 2 — TARGET VS ACTUAL + SHIFT COMPARISON
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(panel_title("📊", "Production Analytics"), unsafe_allow_html=True)

    pa1, pa2 = st.columns([3, 2])

    with pa1:
        # Horizontal bar — products sorted by efficiency
        prod_df = df.groupby("Product").agg(
            Actual=("Actual", "sum"), Target=("Target", "sum")
        ).reset_index()
        prod_df["Efficiency"] = (prod_df["Actual"] / prod_df["Target"] * 100).round(1)
        prod_df = prod_df.sort_values("Actual")
        bar_colors = [_eff_color(e) for e in prod_df["Efficiency"]]

        fig_prod = go.Figure()
        fig_prod.add_trace(go.Bar(
            name="Target", x=prod_df["Target"], y=prod_df["Product"],
            orientation="h",
            marker=dict(color="rgba(165,0,52,0.12)", line=dict(width=0)),
            hovertemplate="<b>%{y}</b><br>Target: %{x:,}<extra></extra>"
        ))
        fig_prod.add_trace(go.Bar(
            name="Actual", x=prod_df["Actual"], y=prod_df["Product"],
            orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=prod_df["Efficiency"].apply(lambda x: f"{x:.0f}%"),
            textposition="outside",
            textfont=dict(size=11, color="#475569"),
            hovertemplate="<b>%{y}</b><br>Actual: %{x:,}<br>Efficiency: %{text}<extra></extra>"
        ))
        fig_prod.update_layout(
            title="Target vs Actual by Product",
            barmode="overlay",
            xaxis=dict(title="Units", **GRID),
            yaxis=NO_GRID,
            height=300, **LAYOUT
        )
        st.plotly_chart(fig_prod, use_container_width=True, key="prod_tva")

    with pa2:
        # Shift performance — radial / donut comparison
        shift_df = df.groupby("shift").agg(
            Actual=("Actual", "sum"), Target=("Target", "sum")
        ).reset_index()
        shift_df["Efficiency"] = (shift_df["Actual"] / shift_df["Target"] * 100).round(1)
        shift_colors = [_eff_color(e) for e in shift_df["Efficiency"]]

        fig_shift = go.Figure()
        fig_shift.add_trace(go.Bar(
            x=shift_df["shift"], y=shift_df["Actual"],
            name="Actual",
            marker=dict(color=shift_colors, line=dict(width=0)),
            text=shift_df["Efficiency"].apply(lambda x: f"{x:.0f}%"),
            textposition="outside",
            hovertemplate="<b>%{x} Shift</b><br>Output: %{y:,}<extra></extra>"
        ))
        fig_shift.add_trace(go.Bar(
            x=shift_df["shift"], y=shift_df["Target"],
            name="Target",
            marker=dict(color="rgba(165,0,52,0.14)", line=dict(width=0)),
            hovertemplate="<b>%{x} Shift</b><br>Target: %{y:,}<extra></extra>"
        ))
        fig_shift.update_layout(
            title="Shift Performance",
            barmode="group",
            xaxis=NO_GRID,
            yaxis=dict(title="Units", **GRID),
            height=300, **LAYOUT
        )
        st.plotly_chart(fig_shift, use_container_width=True, key="shift_bar")

    st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 3 — DOWNTIME HEATMAP + TREND
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(panel_title("🌡", "Downtime Intelligence"), unsafe_allow_html=True)

    dh1, dh2 = st.columns(2)

    with dh1:
        # Downtime per line — colour-coded bar
        dt_df = df.groupby("Prod_line")["Downtime_min"].agg(
            ["sum", "mean", "max"]
        ).reset_index()
        dt_df.columns = ["Line", "Total", "Avg", "Max"]
        dt_df = dt_df.sort_values("Total", ascending=False)
        dt_colors = [_dt_color(v) for v in dt_df["Avg"]]

        fig_dt = go.Figure()
        fig_dt.add_trace(go.Bar(
            x=dt_df["Line"], y=dt_df["Total"],
            name="Total Downtime",
            marker=dict(color=dt_colors, line=dict(width=0)),
            text=dt_df["Total"].apply(lambda x: f"{x:.0f}m"),
            textposition="outside",
            hovertemplate=(
                "<b>Line %{x}</b><br>"
                "Total: %{y:.0f} min<br>"
                "Avg per record: %{customdata[0]:.1f} min<br>"
                "Max single: %{customdata[1]:.0f} min"
                "<extra></extra>"
            ),
            customdata=dt_df[["Avg", "Max"]].values
        ))
        # Critical threshold line
        fig_dt.add_hline(y=30, line_dash="dash", line_color=CLR_CRIT, line_width=1.5,
                         annotation_text="⚠ Critical 30m", annotation_font_color=CLR_CRIT,
                         annotation_font_size=11)
        fig_dt.update_layout(
            title="Total Downtime per Line (min)",
            xaxis=dict(title="Production Line", **NO_GRID),
            yaxis=dict(title="Minutes", **GRID),
            height=300, **LAYOUT
        )
        st.plotly_chart(fig_dt, use_container_width=True, key="dt_bar")

    with dh2:
        # Downtime heatmap — line × product
        hm_df = df.pivot_table(
            index="Prod_line", columns="Product",
            values="Downtime_min", aggfunc="mean"
        ).fillna(0)

        fig_hm = go.Figure(go.Heatmap(
            z=hm_df.values,
            x=hm_df.columns.tolist(),
            y=hm_df.index.tolist(),
            colorscale=[
                [0.0,  "rgba(34,197,94,0.15)"],
                [0.35, "#fef9c3"],
                [0.65, "#f59e0b"],
                [1.0,  "#a50034"],
            ],
            showscale=True,
            colorbar=dict(title="Avg DT (min)", tickfont=dict(size=10)),
            hovertemplate="Line: <b>%{y}</b><br>Product: <b>%{x}</b><br>Avg DT: <b>%{z:.1f} min</b><extra></extra>",
            text=[[f"{v:.0f}m" for v in row] for row in hm_df.values],
            texttemplate="%{text}",
            textfont=dict(size=10, color="#0f172a")
        ))
        fig_hm.update_layout(
            title="Downtime Heatmap — Line × Product",
            xaxis=dict(title="Product", side="bottom", **NO_GRID),
            yaxis=dict(title="Line", **NO_GRID),
            height=300, **LAYOUT
        )
        st.plotly_chart(fig_hm, use_container_width=True, key="dt_heatmap")

    st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4 — LINE PERFORMANCE RADAR + EFFICIENCY SCATTER
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(panel_title("📡", "Line Performance Intelligence"), unsafe_allow_html=True)

    lp1, lp2 = st.columns(2)

    with lp1:
        # Radar chart — per-line scores
        line_df = df.groupby("Prod_line").agg(
            Efficiency=("Actual", "sum"),
            Target=("Target", "sum"),
            Downtime=("Downtime_min", "mean"),
        ).reset_index()
        line_df["Eff_score"]  = (line_df["Efficiency"] / line_df["Target"] * 100).clip(0, 120)
        line_df["DT_score"]   = (100 - (line_df["Downtime"] / 60 * 100)).clip(0, 100)

        categories = ["Efficiency", "Low Downtime", "Output Volume", "Reliability"]
        fig_radar = go.Figure()
        colors_radar = [LG_RED, LG_PINK, "#f43f75", "#7a0026", "#c0003d"]

        for i, row in line_df.iterrows():
            vol_score = min(100, row["Efficiency"] / line_df["Efficiency"].max() * 100)
            rel_score = 100 - (30 if row["Eff_score"] < 80 else 0)
            values = [row["Eff_score"], row["DT_score"], vol_score, rel_score]
            values += [values[0]]  # close the polygon

            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill="toself",
                name=f"Line {row['Prod_line']}",
                line=dict(color=colors_radar[i % len(colors_radar)], width=2),
                fillcolor=colors_radar[i % len(colors_radar)].replace("#", "rgba(").rstrip(")") if False else "rgba(165,0,52,0.06)",
                opacity=0.85,
                hovertemplate="<b>Line %{fullData.name}</b><br>%{theta}: %{r:.0f}<extra></extra>"
            ))

        fig_radar.update_layout(
            title="Line Performance Radar",
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 120],
                                gridcolor="rgba(0,0,0,0.07)", tickfont=dict(size=9)),
                angularaxis=dict(gridcolor="rgba(0,0,0,0.07)")
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#475569", size=11),
            title_font=dict(color="#7a0026", size=14),
            margin=dict(l=30, r=30, t=44, b=20),
            legend=dict(bgcolor="rgba(255,255,255,0.55)", borderwidth=0, font=dict(size=10)),
            height=320
        )
        st.plotly_chart(fig_radar, use_container_width=True, key="radar")

    with lp2:
        # Scatter — efficiency vs downtime bubble chart
        scatter_df = df.groupby("Prod_line").agg(
            Actual=("Actual", "sum"),
            Target=("Target", "sum"),
            Downtime=("Downtime_min", "mean"),
            Records=("Actual", "count")
        ).reset_index()
        scatter_df["Efficiency"] = (scatter_df["Actual"] / scatter_df["Target"] * 100).round(1)
        scatter_df["Color"] = scatter_df["Efficiency"].apply(_eff_color)

        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            x=scatter_df["Downtime"],
            y=scatter_df["Efficiency"],
            mode="markers+text",
            marker=dict(
                size=scatter_df["Actual"] / scatter_df["Actual"].max() * 40 + 14,
                color=scatter_df["Color"],
                line=dict(color="white", width=2),
                opacity=0.85
            ),
            text=scatter_df["Prod_line"].astype(str),
            textposition="top center",
            textfont=dict(size=11, color="#0f172a"),
            hovertemplate=(
                "<b>Line %{text}</b><br>"
                "Avg Downtime: %{x:.1f} min<br>"
                "Efficiency: %{y:.1f}%<br>"
                "<extra></extra>"
            )
        ))
        # Quadrant lines
        fig_scatter.add_hline(y=90,  line_dash="dot", line_color=CLR_OK,   line_width=1,
                               annotation_text="90% target", annotation_font_size=10)
        fig_scatter.add_vline(x=20,  line_dash="dot", line_color=CLR_WARN, line_width=1,
                               annotation_text="20min warn", annotation_font_size=10)
        fig_scatter.update_layout(
            title="Efficiency vs Downtime (bubble = output volume)",
            xaxis=dict(title="Avg Downtime (min)", **GRID),
            yaxis=dict(title="Efficiency %", **GRID, range=[0, 130]),
            height=320, **LAYOUT
        )
        st.plotly_chart(fig_scatter, use_container_width=True, key="scatter_eff")

    st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 5 — PRODUCTION TREND SIMULATION
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(panel_title("📈", "Production Trend Analysis"), unsafe_allow_html=True)

    # Simulate intra-day trend from existing data with small variance
    np.random.seed(42)
    n_points = 24
    hours = [f"{h:02d}:00" for h in range(n_points)]
    base_output = total_actual / n_points
    trend_actual = np.clip(
        base_output + np.random.normal(0, base_output * 0.12, n_points)
        + np.sin(np.linspace(0, 2 * np.pi, n_points)) * base_output * 0.08,
        0, None
    )
    trend_target = np.full(n_points, total_target / n_points)
    trend_dt     = np.clip(avg_downtime + np.random.normal(0, 5, n_points), 0, 60)
    cumulative   = np.cumsum(trend_actual)

    tr1, tr2 = st.columns(2)

    with tr1:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=hours, y=trend_target,
            name="Hourly Target",
            line=dict(color="rgba(165,0,52,0.3)", width=1.5, dash="dot"),
            hovertemplate="Hour %{x}<br>Target: %{y:.0f}<extra></extra>"
        ))
        fig_trend.add_trace(go.Scatter(
            x=hours, y=trend_actual,
            name="Actual Output",
            line=dict(color=LG_RED, width=2.5),
            fill="tonexty",
            fillcolor="rgba(165,0,52,0.06)",
            hovertemplate="Hour %{x}<br>Output: %{y:.0f}<extra></extra>"
        ))
        fig_trend.add_trace(go.Scatter(
            x=hours, y=cumulative,
            name="Cumulative",
            yaxis="y2",
            line=dict(color="#3b82f6", width=1.5, dash="dash"),
            hovertemplate="Hour %{x}<br>Cumulative: %{y:.0f}<extra></extra>"
        ))
        fig_trend.update_layout(
            title="Hourly Production Trend (Simulated)",
            xaxis=dict(title="Hour", **NO_GRID),
            yaxis=dict(title="Units / Hour", **GRID),
            yaxis2=dict(title="Cumulative", overlaying="y", side="right",
                        showgrid=False, zeroline=False),
            height=300, **LAYOUT
        )
        st.plotly_chart(fig_trend, use_container_width=True, key="trend_line")

    with tr2:
        fig_dt_trend = go.Figure()
        dt_colors_trend = [_dt_color(v) for v in trend_dt]
        fig_dt_trend.add_trace(go.Bar(
            x=hours, y=trend_dt,
            name="Downtime",
            marker=dict(color=dt_colors_trend, line=dict(width=0)),
            hovertemplate="Hour %{x}<br>Downtime: %{y:.1f} min<extra></extra>"
        ))
        fig_dt_trend.add_hline(y=20, line_dash="dash", line_color=CLR_WARN, line_width=1.5,
                                annotation_text="Warning 20m", annotation_font_color=CLR_WARN,
                                annotation_font_size=10)
        fig_dt_trend.add_hline(y=30, line_dash="dash", line_color=CLR_CRIT, line_width=1.5,
                                annotation_text="Critical 30m", annotation_font_color=CLR_CRIT,
                                annotation_font_size=10)
        fig_dt_trend.update_layout(
            title="Hourly Downtime Trend (Simulated)",
            xaxis=dict(title="Hour", **NO_GRID),
            yaxis=dict(title="Downtime (min)", **GRID),
            height=300, **LAYOUT
        )
        st.plotly_chart(fig_dt_trend, use_container_width=True, key="dt_trend")

    st.markdown('</div>', unsafe_allow_html=True)

    divider()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 6 — AI ENGINE + OPERATIONAL INTELLIGENCE
    # ══════════════════════════════════════════════════════════════════════
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
        st.markdown(panel_title("📈", "Operational Intelligence"), unsafe_allow_html=True)

        # Efficiency classification
        eff_class = ("🟢 Optimal" if factory_health >= 95
                     else "🟡 Suboptimal" if factory_health >= 80
                     else "🔴 Critical")
        st.markdown(ai_card("Efficiency Class",   eff_class,
                             f"{factory_health}% — {'Sustain current operations' if factory_health >= 95 else 'Intervention required'}"),
                    unsafe_allow_html=True)
        st.markdown(ai_card("Best Product",       best_product,
                             f"{best_product_val:,} units — highest output today"),
                    unsafe_allow_html=True)
        st.markdown(ai_card("Top Shift",          f"{best_shift} Shift",
                             "Highest cumulative output across all lines"),
                    unsafe_allow_html=True)
        st.markdown(ai_card("Bottleneck",         f"Line {highest_downtime_line}",
                             f"{highest_downtime_val} min downtime — primary constraint"),
                    unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # Risk severity colour indicators
        st.markdown(alert_row(f"Breakdown Risk: {breakdown_risk} machines",
                               "danger" if breakdown_risk > 0 else "success"), unsafe_allow_html=True)
        st.markdown(alert_row(f"Worst product: {worst_product}", "warning"), unsafe_allow_html=True)
        if len(high_risk) > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**⚠ Machines at Breakdown Risk:**")
            st.dataframe(high_risk[["Prod_line", "Product", "Machine_Status"]].reset_index(drop=True),
                         use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)