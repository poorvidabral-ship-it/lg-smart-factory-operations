"""
LG Smart Factory
Gemini Vision Incident Analysis Engine
Phase 3.4
"""

import streamlit as st
from PIL import Image

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────

VISION_PROMPT = """

You are an industrial AI visual inspection expert
for LG Smart Factory.

Analyze the uploaded industrial image carefully.

Your responsibilities:

- identify visible operational issues
- detect possible machine faults
- identify safety hazards
- analyze warehouse damage
- detect quality defects
- estimate operational severity
- recommend immediate actions

Use this EXACT format:

🏭 INCIDENT SUMMARY:
[Brief issue summary]

🔍 VISUAL ANALYSIS:
[Detailed explanation of visible issue]

⚠ RISK LEVEL:
LOW / MEDIUM / HIGH / CRITICAL

⚡ IMMEDIATE ACTION:
[Immediate operational recommendation]

🛠 RECOMMENDED RESPONSE:
[Maintenance or operational response]

📊 OPERATIONAL IMPACT:
[Possible impact if unresolved]

Rules:
- Be industrially realistic
- Be concise but detailed
- Focus only on visible evidence
- Sound like senior factory inspector

"""

# ─────────────────────────────────────────────
# LOAD GEMINI MODEL
# ─────────────────────────────────────────────

def load_vision_model():

    if not GEMINI_AVAILABLE:
        return None, (
            "⚠ Gemini SDK not installed.\n"
            "Run: pip install google-generativeai"
        )

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None, (
            "⚠ Gemini API key missing.\n"
            "Configure secrets.toml"
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        return model, None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────
# ANALYZE INCIDENT IMAGE
# ─────────────────────────────────────────────

def analyze_incident_image(uploaded_file):

    model, err = load_vision_model()

    if err:
        return err

    try:
        image = Image.open(uploaded_file)
        response = model.generate_content([
            VISION_PROMPT,
            image
        ])
        return response.text
    except Exception as e:
        return f"⚠ Vision Analysis Error: {str(e)}"


# ─────────────────────────────────────────────
# RENDER VISION PANEL
# ─────────────────────────────────────────────

def render_vision_analysis(st_obj, analysis):

    st_obj.markdown(f"""

    <div style="
        background:
            linear-gradient(
                135deg,
                rgba(255,255,255,0.96),
                rgba(255,255,255,0.88)
            );

        border-radius:24px;

        padding:32px;

        margin-top:20px;

        border-left:8px solid #a50034;

        box-shadow:
            0 10px 35px rgba(0,0,0,0.08);
    ">

        <div style="
            display:flex;
            align-items:center;
            gap:14px;
            margin-bottom:24px;
        ">

            <div style="
                background:
                    linear-gradient(
                        135deg,
                        #7a0026,
                        #a50034
                    );

                color:white;

                padding:10px 14px;

                border-radius:12px;

                font-size:24px;
            ">
                👁
            </div>

            <div>

                <div style="
                    color:#7a0026;
                    font-size:26px;
                    font-weight:800;
                ">
                    AI Visual Incident Analysis
                </div>

                <div style="
                    color:#94a3b8;
                    font-size:13px;
                    margin-top:4px;
                ">
                    Powered by Gemini Vision
                </div>

            </div>

        </div>

        <div style="
            color:#374151;
            font-size:16px;
            line-height:1.9;
            white-space:pre-wrap;
        ">
            {analysis}
        </div>

    </div>

    """, unsafe_allow_html=True)
