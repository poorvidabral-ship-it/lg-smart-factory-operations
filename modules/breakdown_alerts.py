import streamlit as st
from datetime import datetime


def _call_gemini_alert(prompt):
    try:
        import google.generativeai as genai
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception:
        return None


def _fallback_action(breakdown_count, lines_str, machines_str):
    return f"""**Immediate Actions Required:**

1. **Shutdown** — Halt production on affected line(s): {lines_str}
2. **Dispatch** — Send maintenance team to inspect {machines_str}
3. **Diagnose** — Run diagnostic checks to identify root cause
4. **Reroute** — Shift production load to operational lines
5. **Report** — Document incident and notify shift supervisor

**Estimated Resolution:** 30–60 minutes depending on fault complexity.
"""


def check_breakdowns(df, maintenance_df):
    alerts = []
    if df.empty:
        return alerts

    breakdowns = df[df["Machine_Status"] == "Breakdown Risk"]
    breakdown_count = len(breakdowns)

    if breakdown_count == 0:
        return alerts

    lines = breakdowns["Prod_line"].unique()
    lines_str = ", ".join(lines)

    machines = []
    for line in lines:
        matched = maintenance_df[maintenance_df["Machine_ID"].str.contains(line.split()[-1], na=False)]
        machines.extend(matched["Machine_ID"].tolist())
    machines_str = ", ".join(set(machines)) if machines else lines_str

    prompt = f"""You are the LG Smart Factory emergency response AI. A breakdown alert has been triggered.

Breakdown Details:
- Affected Lines: {lines_str}
- Affected Machines: {machines_str}
- Total Breakdown Risk Flags: {breakdown_count}
- Time: {datetime.now().strftime('%H:%M')}

Provide EXACTLY:
**Immediate Actions Required:** (4-5 numbered steps, each starting with a bold action word like Shutdown, Dispatch, Diagnose, Reroute, Report)
**Likely Cause:** (1 sentence)
**Estimated Resolution:** (time estimate)

Keep each step under 15 words. Be specific and actionable."""

    gemini_result = _call_gemini_alert(prompt)
    action_text = gemini_result if gemini_result else _fallback_action(breakdown_count, lines_str, machines_str)

    severity = "CRITICAL" if breakdown_count >= 3 else "HIGH"

    alerts.append({
        "count": breakdown_count,
        "lines": lines_str,
        "machines": machines_str,
        "severity": severity,
        "action": action_text,
        "time": datetime.now().strftime("%H:%M:%S"),
    })
    return alerts


def render_breakdown_alerts(alerts):
    if not alerts:
        return

    for alert in alerts:
        c = "#ef4444" if alert["severity"] == "CRITICAL" else "#f97316"

        box = st.error if alert["severity"] == "CRITICAL" else st.warning
        with box(f"🚨 BREAKDOWN ALERT · {alert['severity']} SEVERITY — {alert['count']} Risk Flag(s)"):
            g1, g2 = st.columns(2)
            g1.markdown(f"**Lines:** {alert['lines']}")
            g1.markdown(f"**Detected:** {alert['time']}")
            g2.markdown(f"**Machines:** {alert['machines']}")
            g2.markdown(f"**Status:** ACTIVE — AI Analyzing")

            st.divider()
            st.markdown(alert["action"])
