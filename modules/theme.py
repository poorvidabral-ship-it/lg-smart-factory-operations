import streamlit as st

LG_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── BASE ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
}
.stApp {
    background: linear-gradient(160deg, #faf6f0 0%, #f3ede4 35%, #f0e8dc 65%, #faf6f0 100%) !important;
}
#MainMenu, footer, header { display: none !important; }
.block-container {
    padding: 1.2rem 2rem 2.5rem 2rem !important;
    max-width: 100% !important;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    min-width: 264px !important;
    max-width: 264px !important;
    background: linear-gradient(180deg, #3d0015 0%, #5c001e 20%, #7a0026 45%, #8f002d 70%, #a50034 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
    box-shadow: 4px 0 32px rgba(0,0,0,0.18) !important;
    z-index: 99 !important;
}
section[data-testid="stSidebar"] > div {
    padding: 0.75rem 0.75rem 1rem 0.75rem !important;
}
section[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.88) !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
}
section[data-testid="stSidebar"] hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent) !important;
    margin: 10px 0 !important;
}

/* ── Sidebar radio nav ── */
section[data-testid="stSidebar"] .stRadio > div {
    gap: 3px !important;
}
section[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    margin-bottom: 1px !important;
    display: block !important;
    cursor: pointer !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.08) !important;
}
section[data-testid="stSidebar"] .stRb {
    display: none !important;
}
section[data-testid="stSidebar"] .stRadio label span:first-child {
    display: inline-block !important;
    color: rgba(255,255,255,0.35) !important;
    margin-right: 8px !important;
    font-size: 14px !important;
}

/* ── Sidebar select / date ── */
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
    padding: 2px 4px !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div:hover {
    border-color: rgba(255,255,255,0.18) !important;
}
section[data-testid="stSidebar"] .stSelectbox svg {
    fill: rgba(255,255,255,0.4) !important;
}

/* ── Sidebar button (logout) ── */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
    color: rgba(255,255,255,0.6) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 7px 12px !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,77,125,0.12) !important;
    border-color: rgba(255,77,125,0.2) !important;
    color: #ff6b8a !important;
}

/* ── HEADINGS ── */
h1, h2, h3 {
    color: #7a0026 !important;
    font-weight: 700 !important;
    letter-spacing: -0.3px !important;
}
h1 { font-size: 1.6rem !important; }
h2 { font-size: 1.3rem !important; }
h3 { font-size: 1.1rem !important; }

/* ── KPI CARD ── */
.kpi-card {
    background: #ffffff;
    border: 1px solid #e8e2d8;
    border-radius: 16px;
    padding: 22px 22px 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #a50034, #d90452);
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(165,0,52,0.10);
}
.kpi-icon { font-size: 20px; margin-bottom: 10px; display: block; }
.kpi-label {
    color: #78716c;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.kpi-value {
    color: #1c1917;
    font-size: 34px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -1px;
}
.kpi-unit {
    color: #a8a29e;
    font-size: 12px;
    font-weight: 500;
    margin-top: 4px;
}
.kpi-badge {
    display: inline-block;
    background: rgba(165,0,52,0.07);
    color: #a50034;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    margin-top: 6px;
    letter-spacing: 0.3px;
}

/* ── PANEL ── */
.panel {
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(8px);
    border: 1px solid #e8e2d8;
    border-radius: 16px;
    padding: 22px 22px;
    margin-bottom: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.panel-title {
    color: #7a0026;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.panel-title-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(165,0,52,0.15), transparent);
    margin-left: 6px;
}

/* ── PAGE HEADER ── */
.page-header {
    background: linear-gradient(135deg, #7a0026 0%, #a50034 60%, #c0003d 100%);
    border-radius: 16px;
    padding: 22px 26px;
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 6px 24px rgba(122,0,38,0.22);
    position: relative;
    overflow: hidden;
}
.page-header::after {
    content: "";
    position: absolute;
    right: -30px; top: -30px;
    width: 140px; height: 140px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.page-header-title {
    color: white;
    font-size: 20px;
    font-weight: 700;
}
.page-header-sub {
    color: rgba(255,255,255,0.55);
    font-size: 12px;
    margin-top: 3px;
}
.page-header-badge {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.18);
    color: white;
    padding: 5px 14px;
    border-radius: 30px;
    font-size: 11px;
    font-weight: 600;
}

/* ── ALERT ROW ── */
.alert-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 11px 14px;
    border-radius: 10px;
    margin-bottom: 7px;
    font-size: 13px;
    font-weight: 500;
    border: 1px solid transparent;
    transition: transform 0.15s ease;
}
.alert-row:hover { transform: translateX(2px); }
.alert-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}
.alert-success { background:#f0fdf4; border-color:#bbf7d0; color:#166534; }
.alert-success .alert-dot { background:#22c55e; }
.alert-warning  { background:#fffbeb; border-color:#fde68a; color:#92400e; }
.alert-warning .alert-dot  { background:#f59e0b; }
.alert-info     { background:#eff6ff; border-color:#bfdbfe; color:#1e40af; }
.alert-info .alert-dot     { background:#3b82f6; }
.alert-danger   { background:#fff1f2; border-color:#fecdd3; color:#9f1239; }
.alert-danger .alert-dot   { background:#f43f5e; }

/* ── AI CARD ── */
.ai-card {
    background: #ffffff;
    border: 1px solid rgba(165,0,52,0.10);
    border-left: 3px solid #a50034;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 9px;
    transition: transform 0.2s ease;
}
.ai-card:hover { transform: translateY(-2px); }
.ai-card-label {
    color: #a50034;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.ai-card-value { color: #1c1917; font-size: 14px; font-weight: 700; }
.ai-card-sub   { color: #78716c; font-size: 12px; margin-top: 2px; }

/* ── STAT STRIP ── */
.stat-strip {
    display: flex;
    background: #ffffff;
    border: 1px solid #e8e2d8;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 18px;
}
.stat-strip-item {
    flex: 1;
    padding: 14px 16px;
    border-right: 1px solid #f0ece6;
    text-align: center;
}
.stat-strip-item:last-child { border-right: none; }
.stat-strip-label {
    color: #a8a29e;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.stat-strip-value { color: #1c1917; font-size: 18px; font-weight: 800; }

/* ── HERO ── */
.hero-wrap {
    position: relative;
    border-radius: 18px;
    overflow: hidden;
    margin-bottom: 22px;
    height: 44vh;
    min-height: 280px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
}
.hero-wrap img {
    width: 100%; height: 100%;
    object-fit: cover;
    filter: brightness(0.40) saturate(0.8);
}
.hero-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(105deg, rgba(60,0,18,0.90) 0%, rgba(122,0,38,0.50) 40%, rgba(0,0,0,0.05) 100%);
}
.hero-body {
    position: absolute;
    top: 50%; left: 5%;
    transform: translateY(-50%);
    max-width: 520px;
}
.hero-eyebrow {
    color: rgba(255,255,255,0.45);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.hero-title {
    color: white;
    font-size: 44px;
    font-weight: 900;
    line-height: 1.05;
    letter-spacing: -1.2px;
    margin-bottom: 12px;
}
.hero-title span { color: #ff6b8a; }
.hero-sub {
    color: rgba(255,255,255,0.65);
    font-size: 15px;
    line-height: 1.6;
    margin-bottom: 20px;
}
.hero-cta {
    display: inline-block;
    background: white;
    color: #a50034 !important;
    padding: 10px 22px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 700;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    transition: 0.2s ease;
    cursor: pointer;
}
.hero-cta:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(0,0,0,0.22); }
.hero-stats {
    position: absolute;
    bottom: 18px; right: 22px;
    display: flex; gap: 10px;
}
.hero-stat {
    background: rgba(255,255,255,0.10);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px;
    padding: 10px 14px;
    text-align: center;
}
.hero-stat-val { color: white; font-size: 18px; font-weight: 800; line-height: 1; }
.hero-stat-lbl { color: rgba(255,255,255,0.50); font-size: 9px; font-weight: 600; margin-top: 2px; }

/* ── DIVIDER ── */
.lg-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(165,0,52,0.12), transparent);
    margin: 20px 0;
    border: none;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #e8e2d8 !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-thumb { background: rgba(165,0,52,0.25); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #a50034; }

/* ── COLUMN GAUGE ── */
div[data-testid="column"] {
    gap: 0 !important;
}

/* ── TABS ── */
button[data-testid="stTab"] {
    font-size: 13px !important;
    font-weight: 600 !important;
}

/* ── BUTTONS ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    transition: all 0.2s ease !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #7a0026 !important;
}
</style>
"""

def inject_css():
    st.markdown(LG_CSS, unsafe_allow_html=True)

def divider():
    st.markdown('<div class="lg-divider"></div>', unsafe_allow_html=True)

def page_header(icon, title, subtitle="", badge="● LIVE"):
    st.markdown(f"""
    <div class="page-header">
        <div>
            <div class="page-header-title">{icon}&nbsp; {title}</div>
            <div class="page-header-sub">{subtitle}</div>
        </div>
        <div class="page-header-badge">{badge}</div>
    </div>""", unsafe_allow_html=True)

def kpi_card(icon, label, value, unit="", badge=""):
    badge_html = f'<div class="kpi-badge">{badge}</div>' if badge else ""
    unit_html  = f'<div class="kpi-unit">{unit}</div>'  if unit  else ""
    return f"""
    <div class="kpi-card">
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {unit_html}{badge_html}
    </div>"""

def alert_row(msg, kind="info"):
    return f"""
    <div class="alert-row alert-{kind}">
        <div class="alert-dot"></div>
        <span>{msg}</span>
    </div>"""

def ai_card(label, value, sub=""):
    sub_html = f'<div class="ai-card-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="ai-card">
        <div class="ai-card-label">AI Insight · {label}</div>
        <div class="ai-card-value">{value}</div>
        {sub_html}
    </div>"""

def panel_title(icon, title):
    return f"""
    <div class="panel-title">
        {icon}&nbsp;{title}
        <div class="panel-title-line"></div>
    </div>"""

def stat_strip(items):
    inner = "".join(f"""
        <div class="stat-strip-item">
            <div class="stat-strip-label">{lbl}</div>
            <div class="stat-strip-value">{val}</div>
        </div>""" for lbl, val in items)
    return f'<div class="stat-strip">{inner}</div>'
