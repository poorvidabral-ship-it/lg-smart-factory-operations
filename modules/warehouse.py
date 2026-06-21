import streamlit as st
import plotly.graph_objects as go
from modules.theme import page_header, kpi_card, alert_row, ai_card, panel_title, stat_strip, divider
from modules.ai_engine import detect_warehouse_risk, render_engine_alerts, status_badge_html

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#475569", size=12),
    title_font=dict(color="#7a0026", size=14),
    margin=dict(l=8, r=8, t=44, b=8),
)
COLORS = ["#a50034","#d90452","#7a0026","#f43f75","#ff8fab","#c0003d"]
CLR_OK   = "#22c55e"
CLR_WARN = "#f59e0b"
CLR_CRIT = "#ef4444"

def show(df):
    result = detect_warehouse_risk(df)
    page_header("📦", "Warehouse Intelligence",
                subtitle="Inventory levels · Supplier tracking · Stock alerts",
                badge=result.status_label)

    if len(df) == 0:
        st.markdown(alert_row("⚠ No warehouse data available for this date.", "warning"), unsafe_allow_html=True)
        return

    total_stock     = int(df["Current_stock"].sum())
    low_stock_items = int((df["Current_stock"] < df["Minimum_stock"]).sum())
    suppliers       = int(df["Supplier"].nunique())
    inv_value       = float((df["Current_stock"] * df["Unit_Cost"]).sum())
    healthy_items   = len(df) - low_stock_items
    stock_health    = round((healthy_items / len(df)) * 100, 1) if len(df) > 0 else 0

    st.markdown(stat_strip([
        ("Total SKUs",      str(len(df))),
        ("Total Stock",     f"{total_stock:,}"),
        ("Low Stock",       str(low_stock_items)),
        ("Stock Health",    f"{stock_health}%"),
        ("Inventory Value", f"₹{inv_value:,.0f}"),
    ]), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("📦", "Total Stock", f"{total_stock:,}", unit="units on hand"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("⚠", "Low Stock Items", str(low_stock_items),
                              badge="REORDER" if low_stock_items > 0 else "OK"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("🤝", "Active Suppliers", str(suppliers), unit="vendors"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("💰", "Inventory Value", f"₹{inv_value/100000:.1f}L", unit="lakh rupees"), unsafe_allow_html=True)

    divider()

    # ── Charts ────────────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("📊", "Stock by Category"), unsafe_allow_html=True)
        group_col = "Category" if "Category" in df.columns else "material"
        cat_df = df.groupby(group_col)["Current_stock"].sum().reset_index().sort_values("Current_stock")
        bar_colors = [CLR_OK if v > df["Minimum_stock"].mean() else CLR_WARN for v in cat_df["Current_stock"]]
        fig = go.Figure(go.Bar(
            x=cat_df["Current_stock"], y=cat_df[group_col], orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=cat_df["Current_stock"].apply(lambda x: f"{x:,}"), textposition="outside",
            hovertemplate="<b>%{y}</b><br>Stock: %{x:,}<extra></extra>"
        ))
        fig.update_layout(title=f"Stock per {group_col}",
                          xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)"),
                          yaxis=dict(showgrid=False), **LAYOUT)
        st.plotly_chart(fig, use_container_width=True, key="wh_bar")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("🍩", "Value Distribution"), unsafe_allow_html=True)
        vg = "Category" if "Category" in df.columns else "material"
        val_df = df.groupby(vg).apply(
            lambda x: (x["Current_stock"] * x["Unit_Cost"]).sum()
        ).reset_index()
        val_df.columns = [vg, "Value"]
        fig2 = go.Figure(go.Pie(
            labels=val_df[vg], values=val_df["Value"], hole=0.5,
            marker=dict(colors=COLORS, line=dict(color="white", width=2)),
            textinfo="label+percent", textfont=dict(size=11)
        ))
        fig2.update_layout(title=f"Value by {vg}", **LAYOUT)
        st.plotly_chart(fig2, use_container_width=True, key="wh_pie")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Stock health gauge + low stock table ─────────────────────────────
    col3, col4 = st.columns([1, 2])
    with col3:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("💚", "Stock Health"), unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=stock_health,
            number={"suffix": "%", "font": {"size": 30, "color": "#0f172a"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar":  {"color": CLR_OK if stock_health >= 85 else CLR_WARN if stock_health >= 70 else CLR_CRIT,
                         "thickness": 0.28},
                "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
                "steps": [
                    {"range": [0,  70],  "color": "rgba(239,68,68,0.1)"},
                    {"range": [70, 85],  "color": "rgba(245,158,11,0.1)"},
                    {"range": [85, 100], "color": "rgba(34,197,94,0.1)"},
                ],
                "threshold": {"line": {"color": "#a50034", "width": 3},
                              "thickness": 0.85, "value": 85},
            },
            title={"text": "Inventory Health", "font": {"size": 13, "color": "#7a0026"}},
        ))
        fig_gauge.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=16, r=16, t=40, b=8))
        st.plotly_chart(fig_gauge, use_container_width=True, key="wh_gauge")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(panel_title("⚠", "Low Stock — Reorder Required"), unsafe_allow_html=True)
        low_df = df[df["Current_stock"] < df["Minimum_stock"]].reset_index(drop=True)
        if len(low_df) == 0:
            st.markdown(alert_row("✅ All items above minimum stock level", "success"), unsafe_allow_html=True)
        else:
            st.dataframe(low_df, use_container_width=True, hide_index=True)
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
        st.markdown(panel_title("📈", "Warehouse Intelligence"), unsafe_allow_html=True)
        top_grp = "Category" if "Category" in df.columns else "material"
        top_cat = df.groupby(top_grp)["Current_stock"].sum().idxmax()
        st.markdown(ai_card("Stock Health",    f"{stock_health}% Healthy",   f"{healthy_items} of {len(df)} SKUs above minimum"), unsafe_allow_html=True)
        st.markdown(ai_card(f"Top {top_grp}",  top_cat,                       "Highest stock volume — review for overstock"), unsafe_allow_html=True)
        st.markdown(ai_card("Inventory Value", f"₹{inv_value:,.0f}",         f"Across {suppliers} active suppliers"), unsafe_allow_html=True)
        st.markdown(alert_row(f"⚠ {low_stock_items} items need reorder",
                               "warning" if low_stock_items > 0 else "success"), unsafe_allow_html=True)
        st.markdown(alert_row("✅ Warehouse monitoring active", "success"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)