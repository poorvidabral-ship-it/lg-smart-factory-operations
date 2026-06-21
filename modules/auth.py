"""
LG Smart Factory — Authentication Layer (Phase 5.2)
=====================================================
Login page, session management, role-based access control.
Users stored in Supabase `users` table.
"""

import hashlib
import streamlit as st
from modules.database import get_supabase


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username: str, password: str):
    """Validate credentials against Supabase users table. Returns user dict or None."""
    supabase = get_supabase()
    pw_hash = _hash_password(password)
    resp = supabase.table("users").select("*") \
        .eq("username", username.lower()) \
        .eq("password", pw_hash) \
        .execute()
    users = resp.data or []
    if users:
        u = users[0]
        return {"username": u["username"], "role": u["role"],
                "display_name": u["display_name"]}
    return None


def login_required():
    """Render login page if not authenticated. Returns True once authenticated."""
    if st.session_state.get("authenticated", False):
        return True

    inject_login_css()

    # ── Background layer ──
    st.markdown("""
    <div class="login-bg">
        <div class="login-glow"></div>
        <div class="login-grid"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Card header (self-contained) ──
    st.markdown("""
    <div class="login-card">
        <div class="login-card-bar"></div>
        <div class="login-card-header">
            <img src="https://i.pinimg.com/736x/08/75/36/087536c5fd0ee3ddf9f2eb48afc03620.jpg" style="width:68px;height:68px;border-radius:20px;object-fit:cover;display:block;margin:0 auto 14px;box-shadow:0 4px 16px rgba(165,0,52,0.25);">
            <div class="login-title">Smart Factory</div>
            <div class="login-sub">Operational Intelligence Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        st.markdown('<div class="login-form-label">Account Login</div>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter your username",
                                 label_visibility="collapsed")
        password = st.text_input("Password", type="password",
                                 placeholder="Enter your password",
                                 label_visibility="collapsed")
        st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    st.markdown("""
    <div class="login-footer">
        <span>LG Smart Factory v5.2</span>
        <span class="login-dot">·</span>
        <span>Supabase Cloud</span>
        <span class="login-dot">·</span>
        <span>RBAC</span>
    </div>
    """, unsafe_allow_html=True)

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            try:
                user = authenticate(username, password)
            except Exception as e:
                st.error(f"Connection error: {e}")
                user = None
            if user:
                st.session_state["authenticated"] = True
                st.session_state["user"] = user
                st.rerun()
            else:
                if user is None:
                    st.error("Invalid username or password.")

    st.stop()
    return False


def inject_login_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        * { font-family: 'Inter', -apple-system, sans-serif !important; }

        /* ── Page background (matches theme.py warm palette) ── */
        .stApp {
            background: linear-gradient(160deg, #faf6f0 0%, #f3ede4 35%, #f0e8dc 65%, #faf6f0 100%) !important;
        }
        .block-container {
            max-width: 420px !important;
            padding: 0 20px !important;
            margin: 0 auto !important;
            padding-top: 3rem !important;
        }

        /* ── Hide chrome ── */
        section[data-testid="stSidebar"] { display: none !important; }
        #MainMenu, footer, header, .stDecoration, .stToolbar { display: none !important; }
        .stApp > header { display: none !important; }

        /* ── Background layer ── */
        .login-bg {
            position: fixed; inset: 0;
            pointer-events: none;
            z-index: 0;
        }
        .login-glow {
            position: absolute; inset: 0;
            background:
                radial-gradient(ellipse at 20% 20%, rgba(165,0,52,0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(165,0,52,0.04) 0%, transparent 40%);
        }
        .login-grid {
            position: absolute; inset: 0;
            background-image:
                linear-gradient(rgba(165,0,52,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(165,0,52,0.03) 1px, transparent 1px);
            background-size: 56px 56px;
            mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
            -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
        }

        /* ── Card (white with warm shadow, matches theme.py panels) ── */
        .login-card {
            background: #ffffff;
            border: 1px solid #e8e2d8;
            border-radius: 28px 28px 0 0;
            padding: 48px 36px 20px;
            box-shadow: 0 12px 48px rgba(0,0,0,0.06);
            position: relative;
            overflow: hidden;
        }
        .login-card-bar {
            position: absolute; top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent 5%, #a50034 20%, #d90452 50%, #a50034 80%, transparent 95%);
        }
        .login-card-header { text-align: center; }
        .login-logo {
            width: 68px; height: 68px; margin: 0 auto 14px;
            background: linear-gradient(135deg, #a50034, #7a0026);
            border-radius: 20px;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px; font-weight: 900; color: white;
            letter-spacing: 1px;
            box-shadow: 0 4px 16px rgba(165,0,52,0.25);
        }
        .login-title {
            color: #7a0026; font-size: 26px;
            font-weight: 800; letter-spacing: -0.5px;
            line-height: 1.2;
        }
        .login-sub {
            color: #a8a29e;
            font-size: 12px; margin-top: 5px;
            font-weight: 400; letter-spacing: 0.4px;
        }

        /* ── Form container (white, matches card) ── */
        form[data-testid="stForm"] {
            background: #ffffff !important;
            border: 1px solid #e8e2d8 !important;
            border-top: none !important;
            border-radius: 0 0 28px 28px !important;
            padding: 8px 36px 32px !important;
            margin-bottom: 16px !important;
            box-shadow: 0 12px 48px rgba(0,0,0,0.06) !important;
        }
        .login-form-label {
            color: #7a0026;
            font-size: 10px; font-weight: 700;
            letter-spacing: 1.8px;
            text-transform: uppercase;
            margin-bottom: 14px;
        }

        /* ── Inputs ── */
        .stTextInput { margin-bottom: 4px !important; }
        .stTextInput > div > div > input {
            background: #faf6f0 !important;
            border: 1px solid #e8e2d8 !important;
            border-radius: 14px !important;
            color: #1c1917 !important;
            padding: 15px 18px !important;
            font-size: 14px !important;
            font-weight: 400 !important;
            transition: all 0.25s ease !important;
            height: 52px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #a50034 !important;
            box-shadow: 0 0 0 4px rgba(165,0,52,0.10) !important;
            background: #ffffff !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #a8a29e !important;
            font-weight: 300 !important;
        }

        /* ── Button (LG red gradient) ── */
        .stButton > button {
            background: linear-gradient(135deg, #a50034 0%, #8a002b 55%, #7a0026 100%) !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 15px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            color: white !important;
            letter-spacing: 0.5px !important;
            transition: all 0.3s cubic-bezier(0.34,1.56,0.64,1) !important;
            cursor: pointer !important;
            height: 52px !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 12px 32px rgba(165,0,52,0.25) !important;
        }
        .stButton > button:active {
            transform: translateY(0) !important;
            box-shadow: 0 4px 12px rgba(165,0,52,0.15) !important;
        }

        /* ── Footer ── */
        .login-footer {
            text-align: center; margin-top: 4px; margin-bottom: 24px;
            color: #a8a29e;
            font-size: 11px; letter-spacing: 0.2px;
        }
        .login-dot { margin: 0 6px; color: #d6d0c8; }

        /* ── Alerts ── */
        .stAlert {
            border-radius: 14px !important;
            font-size: 13px !important;
            border: 1px solid #fecdd3 !important;
            background: #fff1f2 !important;
            color: #9f1239 !important;
            padding: 12px 16px !important;
            margin-top: 8px !important;
        }
        div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
        .row-widget.stButton { margin-top: 0 !important; }

        /* ── Animations ── */
        @keyframes loginFade {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .login-card { animation: loginFade 0.5s ease-out; }
        form[data-testid="stForm"] { animation: loginFade 0.5s ease-out 0.1s both; }
        .login-footer { animation: loginFade 0.5s ease-out 0.2s both; }
    </style>
    """, unsafe_allow_html=True)


def logout():
    """Clear session and redirect to login."""
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()


def get_current_user():
    """Return current user dict or None."""
    return st.session_state.get("user")


def get_current_role():
    """Return current role string or None."""
    user = get_current_user()
    return user["role"] if user else None
