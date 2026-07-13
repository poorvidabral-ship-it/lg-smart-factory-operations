# LG Smart Factory — AI-Powered Operational Intelligence Platform

## Project Overview

An enterprise-grade **Smart Factory operational intelligence platform** built for LG manufacturing environments. Integrates AI copilot, predictive maintenance, incident reporting, vision analysis, digital twin simulation, agentic AI, live cloud database, role-based access control, and AI executive reporting — all powered by **Google Gemini**.

---

## Architecture

### Frontend
- **Streamlit** — Single-page application with role-scoped sidebar navigation, auth wall, warm cream LG-branded UI (#a50034 red accent)

### Backend / AI
- **Google Gemini 2.0 Flash** — Copilot chat, vision analysis, report generation, breakdown alert actions
- **Rule-based engines** — Risk detection (SEV levels), predictive maintenance scoring, agentic AI agents

### Database
- **Supabase** (PostgreSQL cloud) — 7 tables (production, warehouse, maintenance, quality, safety, incident_log, users)

### Deployment
- **Streamlit Community Cloud** — Connected to GitHub repo, auto-deploys on push

---

## Modules

### 1. Dashboard
- KPI cards per department, live auto-refresh (30s), task queue, AI recommendations, critical alerts panel, breakdown risk detection

### 2. AI Factory Copilot (Phase 3.1)
- `modules/llm_engine.py` — Gemini 2.5 Flash chat with 5 domain analysis functions

### 3. Predictive Maintenance (Phase 3.2)
- `modules/predictive_engine.py` — Risk scoring (temperature, vibration, runtime, pressure), trend alerts

### 4. Visual Incident Reporting (Phase 3.3)
- `modules/incident_reporting.py` — Upload images, JSON-based storage, severity tagging

### 5. Gemini Vision Analysis (Phase 3.4)
- `modules/vision_engine.py` — Gemini 2.0 Flash analyzes incident images for cause/severity

### 6. Agentic AI Operations (Phase 4.1)
- `modules/agents.py` — 5 domain agents (production, warehouse, maintenance, quality, safety) + coordinator, all rule-based

### 7. Digital Twin Simulator (Phase 4.2)
- `modules/simulator.py` — What-if scenarios, cost impact, cascade analysis, recovery simulation, resilience scoring, AI strategy generation

### 8. Supabase Cloud Database (Phase 5.1)
- `modules/database.py` — load_table, insert_record, column casing fix
- `scripts/seed_supabase.py` — Seeded 500 Excel records across 5 tables
- `scripts/seed_users.py` — 7 default users with hashed passwords

### 9. Authentication & Roles (Phase 5.2)
- `modules/auth.py` — SHA-256 password auth, session management, warm cream login page
- `modules/roles.py` — 7 roles with scoped page access, badges, task queue, recommendations
- **Roles:** Admin, Factory Manager, Production, Warehouse, Maintenance, Quality, Safety

### 10. Executive Reports (Phase 5.3)
- `modules/report_generator.py` — Daily/Weekly/Monthly consolidated + individual PDF reports via fpdf2, Gemini-generated analysis, fallback when quota exhausted

### 11. Breakdown Alerts
- `modules/breakdown_alerts.py` — Detects "Breakdown Risk" machine status, Gemini action steps, fallback actions

---

## File Structure

```
lg-smart-factory-operations/
├── app1.py                      # Main dashboard — auth, routing, data entry, pages
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata (uv fallback)
├── .gitignore
├── .python-version              # Python 3.12
├── .streamlit/
│   └── secrets.toml             # API keys (GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY)
├── modules/
│   ├── theme.py                 # UI components (kpi_card, panel_title, inject_css, LG brand)
│   ├── auth.py                  # Login page, session management, Supabase auth
│   ├── roles.py                 # Role definitions, page access, task queue, recommendations
│   ├── database.py              # Supabase client, load_table, insert_record
│   ├── llm_engine.py            # Gemini copilot with 5 factory analysis functions
│   ├── ai_engine.py             # Rule-based risk detection (SEV levels)
│   ├── predictive_engine.py     # Predictive maintenance scoring
│   ├── agents.py                # 5 domain agents + coordinator
│   ├── simulator.py             # Digital twin simulator
│   ├── incident_reporting.py    # Legacy JSON-based incident reporting
│   ├── vision_engine.py         # Gemini Vision incident image analysis
│   ├── report_generator.py      # Executive report + PDF export (fpdf2)
│   ├── breakdown_alerts.py      # Breakdown detection + AI actions
│   ├── production.py            # Production page module
│   ├── warehouse.py             # Warehouse page module
│   ├── maintenance.py           # Maintenance page module
│   ├── quality.py               # Quality page module
│   └── safety.py                # Safety page module
├── datalg2/                     # Excel data files (production, warehouse, maintenance, quality, safety)
├── scripts/
│   ├── seed_supabase.py         # Batch seed 500 Excel records to Supabase
│   └── seed_users.py            # Seed 7 default users
├── data/
│   └── incidents.json           # Incident records
│   └── incident_images/         # Uploaded incident images
├── live_Simulator.py            # Standalone script — modifies production CSV every 5s
└── test.py
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | UI framework |
| streamlit-autorefresh | Live dashboard refresh |
| google-generativeai | Gemini AI (copilot, vision, reports, alerts) |
| supabase | Cloud PostgreSQL database |
| fpdf2 | PDF report export |
| pandas | Data processing |
| numpy | Numerical operations |
| Pillow | Image handling |
| openpyxl | Excel file parsing |
| plotly | Charts and graphs |

---

## User Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin@2024 |
| Factory Manager | manager | factory@2024 |
| Production | production | prod@2024 |
| Maintenance | maintenance | maint@2024 |
| Warehouse | warehouse | wh@2024 |
| Quality | quality | qual@2024 |
| Safety | safety | safety@2024 |

---

## Key Technical Decisions

- **Gemini only** (no OpenAI/GPT) — uses `gemini-2.0-flash` and `gemini-2.5-flash`
- **Fallback generators** active when Gemini daily quota (429 errors) exhausted
- **fpdf2** for PDF — Helvetica font, emoji stripped before export
- **SHA-256** password hashing for Supabase user auth
- **Single `st.markdown(..., unsafe_allow_html=True)`** per dashboard panel to avoid orphaned `</div>` rendering as text
- **Warm cream palette** (#faf6f0, #f3ede4) unified across login and main app with LG red (#a50034)

---

## How to Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set up secrets in .streamlit/secrets.toml:
# GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY

# Run
py -m streamlit run app1.py
```

## Live Demo

Deployed at: [lg-smart-factory-operations.streamlit.app](https://lg-smart-factory-operations.streamlit.app)
