import streamlit as st
import pandas as pd
import io
import json
import re
import base64
from datetime import datetime

from PIL import Image
from google import genai
from google.genai import types
from supabase import create_client, Client


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="SEED Lab | Multimodal Data QC Studio",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DARK GREEN / BLACK UI
# =========================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #07110D;
    --sidebar: #0A1711;
    --card: #0E2017;
    --card2: #10271B;
    --border: #1D3A2B;
    --green: #22C55E;
    --green2: #4ADE80;
    --text: #F1F5F3;
    --muted: #8FA69A;
    --orange: #F59E0B;
    --red: #EF4444;
}

html, body, [class*="css"] {
    font-family: "Inter", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 80% 0%, rgba(34,197,94,0.08), transparent 28%),
        radial-gradient(circle at 0% 80%, rgba(34,197,94,0.04), transparent 25%),
        var(--bg);
    color: var(--text);
}

.main .block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* ---------------------------------------------------------
SIDEBAR
--------------------------------------------------------- */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A1711 0%, #07110D 100%);
    border-right: 1px solid #173024;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.3rem;
}

[data-testid="stSidebar"] .block-container {
    padding: 1.2rem 1rem;
}

.brand-box {
    padding: 8px 8px 22px 8px;
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 11px;
}

.brand-logo {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #4ADE80;
    font-size: 21px;
    font-weight: 800;
}

.brand-name {
    font-size: 15px;
    font-weight: 800;
    color: #F1F5F3;
    letter-spacing: 0.2px;
}

.brand-sub {
    font-size: 10px;
    color: #71887C;
    margin-top: 2px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

.user-card {
    background: #0E2017;
    border: 1px solid #1B3528;
    border-radius: 14px;
    padding: 12px;
    margin: 4px 0 22px 0;
}

.user-name {
    color: #F1F5F3;
    font-size: 13px;
    font-weight: 700;
}

.user-email {
    color: #71887C;
    font-size: 10px;
    margin-top: 3px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.sidebar-label {
    color: #60786B;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.3px;
    margin: 18px 8px 8px 8px;
}

[data-testid="stSidebar"] .stButton {
    margin-bottom: 5px;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    min-height: 43px;
    border-radius: 10px;
    border: 1px solid transparent;
    background: transparent;
    color: #8FA69A;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
    transition: all 0.15s ease;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #10271B;
    border-color: #1D3A2B;
    color: #F1F5F3;
}

[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #173A26;
    border: 1px solid #245B38;
    color: #4ADE80;
}

[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: #1B472D;
}

[data-testid="stSidebar"] .stExpander {
    border: 1px solid transparent;
    background: transparent;
}

[data-testid="stSidebar"] .stExpander summary {
    color: #8FA69A;
    font-size: 13px;
}

.logout-btn button {
    color: #F87171 !important;
}

/* ---------------------------------------------------------
HEADERS
--------------------------------------------------------- */

.page-kicker {
    color: #4ADE80;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    margin-bottom: 7px;
}

.page-title {
    color: #F1F5F3;
    font-size: 31px;
    font-weight: 800;
    letter-spacing: -0.8px;
    margin: 0;
}

.page-subtitle {
    color: #81988C;
    font-size: 13px;
    margin-top: 7px;
    margin-bottom: 25px;
}

/* ---------------------------------------------------------
HERO
--------------------------------------------------------- */

.hero {
    position: relative;
    overflow: hidden;
    border-radius: 20px;
    padding: 31px 34px;
    margin-bottom: 23px;
    background:
        linear-gradient(135deg, #102A1C 0%, #0B1C14 48%, #0A1711 100%);
    border: 1px solid #214532;
    box-shadow: 0 15px 50px rgba(0,0,0,0.18);
}

.hero:after {
    content: "";
    position: absolute;
    width: 230px;
    height: 230px;
    right: -70px;
    top: -100px;
    border-radius: 50%;
    background: rgba(34,197,94,0.09);
}

.hero-title {
    position: relative;
    z-index: 1;
    color: #F1F5F3;
    font-size: 27px;
    font-weight: 800;
    margin-bottom: 9px;
}

.hero-text {
    position: relative;
    z-index: 1;
    color: #91A99B;
    font-size: 13px;
    max-width: 650px;
    line-height: 1.7;
}

/* ---------------------------------------------------------
METRICS
--------------------------------------------------------- */

.metric-card {
    background: #0E2017;
    border: 1px solid #1D3A2B;
    border-radius: 15px;
    padding: 19px;
    min-height: 116px;
}

.metric-label {
    color: #71887C;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .6px;
    text-transform: uppercase;
}

.metric-value {
    color: #F1F5F3;
    font-size: 28px;
    font-weight: 800;
    margin-top: 8px;
}

.metric-green {
    color: #4ADE80;
}

.metric-orange {
    color: #FBBF24;
}

/* ---------------------------------------------------------
FEATURE CARDS
--------------------------------------------------------- */

.feature-card {
    background: #0E2017;
    border: 1px solid #1D3A2B;
    border-radius: 17px;
    padding: 23px;
    min-height: 188px;
    transition: border 0.2s ease, transform 0.2s ease;
}

.feature-card:hover {
    border-color: #2B6040;
    transform: translateY(-2px);
}

.feature-icon {
    width: 43px;
    height: 43px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: #173A26;
    color: #4ADE80;
    font-size: 20px;
    margin-bottom: 17px;
}

.feature-title {
    color: #F1F5F3;
    font-size: 15px;
    font-weight: 750;
    margin-bottom: 7px;
}

.feature-text {
    color: #788F83;
    font-size: 12px;
    line-height: 1.65;
}

/* ---------------------------------------------------------
BUTTONS
--------------------------------------------------------- */

.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 650;
}

.stButton > button[kind="primary"] {
    background: #22C55E;
    border-color: #22C55E;
    color: #06100B;
}

.stButton > button[kind="primary"]:hover {
    background: #4ADE80;
    border-color: #4ADE80;
    color: #06100B;
}

.stButton > button[kind="secondary"] {
    background: #10231A;
    border-color: #244332;
    color: #D7E5DE;
}

.stButton > button[kind="secondary"]:hover {
    background: #173A26;
    border-color: #2B6040;
}

/* ---------------------------------------------------------
INPUTS
--------------------------------------------------------- */

.stTextInput label,
.stTextArea label,
.stNumberInput label,
.stSelectbox label,
.stFileUploader label {
    color: #9BAFA5 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stSelectbox > div > div {
    background: #0B1913 !important;
    color: #F1F5F3 !important;
    border: 1px solid #234332 !important;
    border-radius: 10px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #22C55E !important;
    box-shadow: 0 0 0 1px #22C55E !important;
}

[data-testid="stFileUploader"] {
    background: #0B1913;
    border: 1px dashed #31543F;
    border-radius: 13px;
    padding: 7px;
}

[data-testid="stFileUploader"] section {
    background: transparent !important;
}

/* ---------------------------------------------------------
RESULT CARDS
--------------------------------------------------------- */

.result-card {
    background: #0B1913;
    border: 1px solid #1D3A2B;
    border-radius: 15px;
    padding: 20px;
}

.result-title {
    color: #F1F5F3;
    font-size: 14px;
    font-weight: 750;
    margin-bottom: 12px;
}

.result-label {
    color: #71887C;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .8px;
    font-weight: 700;
    margin-top: 14px;
    margin-bottom: 5px;
}

.result-value {
    color: #D9E6DF;
    font-size: 13px;
    line-height: 1.65;
}

.status-pass {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    background: rgba(34,197,94,.12);
    border: 1px solid rgba(34,197,94,.28);
    color: #4ADE80;
    font-size: 11px;
    font-weight: 800;
}

.status-review {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    background: rgba(245,158,11,.10);
    border: 1px solid rgba(245,158,11,.28);
    color: #FBBF24;
    font-size: 11px;
    font-weight: 800;
}

/* ---------------------------------------------------------
AUTH
--------------------------------------------------------- */

.auth-shell {
    max-width: 460px;
    margin: 7vh auto 0 auto;
}

.auth-brand {
    text-align: center;
    margin-bottom: 24px;
}

.auth-logo {
    width: 56px;
    height: 56px;
    border-radius: 17px;
    margin: auto;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #173A26;
    border: 1px solid #2B6040;
    color: #4ADE80;
    font-size: 27px;
}

.auth-title {
    margin-top: 14px;
    color: #F1F5F3;
    font-size: 25px;
    font-weight: 800;
}

.auth-subtitle {
    color: #71887C;
    font-size: 12px;
    margin-top: 5px;
}

.auth-card {
    background: #0E2017;
    border: 1px solid #1D3A2B;
    border-radius: 19px;
    padding: 27px;
}

/* ---------------------------------------------------------
PROFILE
--------------------------------------------------------- */

.profile-card {
    background: #0E2017;
    border: 1px solid #1D3A2B;
    border-radius: 17px;
    padding: 24px;
}

.profile-avatar {
    width: 105px;
    height: 105px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #2B6040;
}

/* ---------------------------------------------------------
DATAFRAME
--------------------------------------------------------- */

[data-testid="stDataFrame"] {
    border: 1px solid #1D3A2B;
    border-radius: 12px;
}

/* ---------------------------------------------------------
DIVIDER
--------------------------------------------------------- */

hr {
    border-color: #1D3A2B !important;
}

/* ---------------------------------------------------------
SUCCESS / ERROR
--------------------------------------------------------- */

.stAlert {
    border-radius: 11px;
}

/* ---------------------------------------------------------
HIDE STREAMLIT DEFAULT ELEMENTS
--------------------------------------------------------- */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULT_SESSION = {
    "authenticated": False,
    "user": None,
    "page": "Overview",
    "manifest": [],
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# SECRETS
# =========================================================

def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GEMINI_MODEL = get_secret("GEMINI_MODEL", "gemini-2.5-flash")


# =========================================================
# SUPABASE
# =========================================================

@st.cache_resource
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


supabase = get_supabase()


# =========================================================
# GEMINI
# =========================================================

@st.cache_resource
def get_gemini_client():
    if not GEMINI_API_KEY:
        return None

    try:
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        return None


gemini_client = get_gemini_client()


# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def clean_email(email):
    return email.strip().lower()


def valid_email(email):
    return bool(
        re.match(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
            email
        )
    )


def password_strength(password):
    score = 0

    if len(password) >= 8:
        score += 1

    if re.search(r"[A-Z]", password):
        score += 1

    if re.search(r"[a-z]", password):
        score += 1

    if re.search(r"[0-9]", password):
        score += 1

    return score


def image_to_data_url(uploaded_file):
    try:
        image = Image.open(uploaded_file).convert("RGB")

        image.thumbnail((600, 600))

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=88)

        encoded = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/jpeg;base64,{encoded}"

    except Exception:
        return None


def get_current_user():
    if supabase is None:
        return None

    try:
        response = supabase.auth.get_user()

        if response and response.user:
            return response.user

    except Exception:
        pass

    return None


# =========================================================
# PROFILE FUNCTIONS
# =========================================================

def get_profile(user_id):

    if supabase is None:
        return None

    try:
        response = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )

        return response.data

    except Exception:
        return None


def create_or_update_profile(user_id, name, profile_image=None):

    if supabase is None:
        return False

    data = {
        "id": user_id,
        "name": name,
        "updated_at": datetime.utcnow().isoformat(),
    }

    if profile_image:
        data["profile_image"] = profile_image

    try:
        supabase.table("profiles").upsert(data).execute()
        return True

    except Exception:
        return False


# =========================================================
# AUTHENTICATION
# =========================================================

def login_user(email, password):

    if supabase is None:
        return False, "Supabase is not configured."

    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

        if response.user:

            profile = get_profile(response.user.id)

            st.session_state.authenticated = True
            st.session_state.user = response.user

            if profile:
                st.session_state.user_name = profile.get(
                    "name",
                    response.user.email.split("@")[0]
                )
                st.session_state.profile_image = profile.get(
                    "profile_image"
                )
            else:
                st.session_state.user_name = (
                    response.user.email.split("@")[0]
                )
                st.session_state.profile_image = None

            return True, "Login successful."

        return False, "Unable to login."

    except Exception as e:
        return False, str(e)


def register_user(name, email, password):

    if supabase is None:
        return False, "Supabase is not configured."

    try:

        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )

        if response.user:

            # If email confirmation is disabled,
            # a session will be returned immediately.
            if response.session:

                create_or_update_profile(
                    response.user.id,
                    name
                )

                st.session_state.authenticated = True
                st.session_state.user = response.user
                st.session_state.user_name = name
                st.session_state.profile_image = None

                return True, "Account created successfully."

            return (
                True,
                "Account created. Please check your email and confirm your account before signing in."
            )

        return False, "Registration failed."

    except Exception as e:

        message = str(e)

        if "already registered" in message.lower():
            return False, "This email is already registered."

        return False, message


def logout_user():

    if supabase:
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.page = "Overview"


def change_user_password(new_password):

    if supabase is None:
        return False, "Supabase is not configured."

    try:

        supabase.auth.update_user(
            {
                "password": new_password
            }
        )

        return True, "Password updated successfully."

    except Exception as e:
        return False, str(e)


def send_password_reset(email):

    if supabase is None:
        return False, "Supabase is not configured."

    try:

        supabase.auth.reset_password_email(email)

        return True, "Password reset email sent."

    except Exception as e:
        return False, str(e)


# =========================================================
# GEMINI
# =========================================================

def generate_gemini_text(prompt, contents=None):

    if gemini_client is None:
        return None

    try:

        if contents is None:
            contents = [prompt]

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
        )

        return response.text

    except Exception as e:
        st.error(f"Gemini error: {e}")
        return None


def extract_json(text):

    if not text:
        return {}

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:

        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {}


# =========================================================
# IMAGE ANALYSIS
# =========================================================

def analyze_image(uploaded_file, line_count=3):

    image_bytes = uploaded_file.getvalue()

    prompt = f"""
You are a professional multimodal data quality control assistant.

Analyze the provided image.

Return ONLY valid JSON.

Required JSON structure:

{{
    "ocr": "all readable text from the image",
    "english_translation": "English translation of visible text if needed",
    "description": [
        "short description line 1",
        "short description line 2",
        "short description line 3"
    ],
    "confidence": 0
}}

Requirements:

1. OCR should contain readable text.
2. If the text is already English, keep the English translation appropriate.
3. Description must contain exactly {line_count} concise lines.
4. Confidence must be a number from 0 to 100.
5. Do not add Markdown.
6. Do not add explanations outside JSON.
"""

    contents = [
        types.Part.from_bytes(
            data=image_bytes,
            mime_type=uploaded_file.type
        ),
        prompt,
    ]

    text = generate_gemini_text(
        prompt,
        contents
    )

    result = extract_json(text)

    if not result:
        return {
            "ocr": "",
            "english_translation": "",
            "description": [],
            "confidence": 0,
        }

    return result


# =========================================================
# AUDIO ANALYSIS
# =========================================================

def analyze_audio(uploaded_file, line_count=3):

    audio_bytes = uploaded_file.getvalue()

    prompt = f"""
You are a professional multimodal data quality control assistant.

Analyze the provided audio.

Return ONLY valid JSON.

Required JSON structure:

{{
    "transcript": "accurate transcript",
    "translation": "English translation",
    "description": [
        "short description line 1",
        "short description line 2",
        "short description line 3"
    ],
    "confidence": 0
}}

Requirements:

1. Transcribe the spoken content.
2. Translate it into English where necessary.
3. Description must contain exactly {line_count} concise lines.
4. Confidence must be a number from 0 to 100.
5. Do not add Markdown.
6. Do not add explanations outside JSON.
"""

    contents = [
        types.Part.from_bytes(
            data=audio_bytes,
            mime_type=uploaded_file.type
        ),
        prompt,
    ]

    text = generate_gemini_text(
        prompt,
        contents
    )

    result = extract_json(text)

    if not result:
        return {
            "transcript": "",
            "translation": "",
            "description": [],
            "confidence": 0,
        }

    return result


# =========================================================
# QC
# =========================================================

def get_confidence(result):

    try:
        return int(float(result.get("confidence", 0)))
    except Exception:
        return 0


def qc_status(confidence):

    if confidence >= 80:
        return "PASS"

    return "REVIEW"


def add_manifest_item(
    filename,
    data_type,
    confidence,
    status
):

    st.session_state.manifest.append(
        {
            "File": filename,
            "Type": data_type,
            "Confidence": confidence,
            "QC Status": status,
            "Processed At": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
    )


# =========================================================
# AUTH PAGE
# =========================================================

def auth_page():

    st.markdown(
        """
        <div class="auth-shell">

            <div class="auth-brand">

                <div class="auth-logo">
                    🌿
                </div>

                <div class="auth-title">
                    SEED Lab
                </div>

                <div class="auth-subtitle">
                    Multimodal Data QC Studio
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    _, center, _ = st.columns([1, 1.3, 1])

    with center:

        st.markdown('<div class="auth-card">', unsafe_allow_html=True)

        login_tab, register_tab = st.tabs(
            ["Sign In", "Create Account"]
        )

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        with login_tab:

            st.markdown("### Welcome back")

            st.caption(
                "Sign in to access your multimodal data workspace."
            )

            email = st.text_input(
                "Email",
                key="login_email",
                placeholder="you@example.com"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
                placeholder="Enter your password"
            )

            if st.button(
                "Sign In",
                type="primary",
                width="stretch",
                icon=":material/login:"
            ):

                email = clean_email(email)

                if not valid_email(email):

                    st.error("Enter a valid email address.")

                elif not password:

                    st.error("Enter your password.")

                else:

                    success, message = login_user(
                        email,
                        password
                    )

                    if success:

                        if "confirmation" in message.lower():

                            st.info(message)

                        else:

                            st.rerun()

                    else:

                        st.error(message)

            st.markdown("---")

            st.markdown("**Forgot your password?**")

            reset_email = st.text_input(
                "Reset email",
                key="reset_email",
                placeholder="Enter your registered email"
            )

            if st.button(
                "Send Reset Email",
                width="stretch",
                icon=":material/lock_reset:"
            ):

                reset_email = clean_email(reset_email)

                if not valid_email(reset_email):

                    st.error("Enter a valid email.")

                else:

                    success, message = send_password_reset(
                        reset_email
                    )

                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        # -------------------------------------------------
        # REGISTER
        # -------------------------------------------------

        with register_tab:

            st.markdown("### Create your account")

            st.caption(
                "Create a secure SEED Lab workspace account."
            )

            name = st.text_input(
                "Full Name",
                key="register_name",
                placeholder="Your name"
            )

            email = st.text_input(
                "Email",
                key="register_email",
                placeholder="you@example.com"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="register_password",
                placeholder="Minimum 8 characters"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="register_confirm",
                placeholder="Re-enter your password"
            )

            if password:

                strength = password_strength(password)

                if strength <= 2:
                    st.caption("Password strength: Weak")
                elif strength == 3:
                    st.caption("Password strength: Medium")
                else:
                    st.caption("Password strength: Strong")

            if st.button(
                "Create Account",
                type="primary",
                width="stretch",
                icon=":material/person_add:"
            ):

                email = clean_email(email)

                if not name.strip():
                    st.error("Enter your name.")

                elif not valid_email(email):
                    st.error("Enter a valid email.")

                elif len(password) < 8:
                    st.error(
                        "Password must contain at least 8 characters."
                    )

                elif password != confirm_password:
                    st.error("Passwords do not match.")

                else:

                    success, message = register_user(
                        name.strip(),
                        email,
                        password
                    )

                    if success:

                        if st.session_state.authenticated:
                            st.rerun()
                        else:
                            st.success(message)

                    else:
                        st.error(message)

        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

def sidebar():

    user = st.session_state.user

    name = st.session_state.get(
        "user_name",
        "SEED Lab User"
    )

    email = ""

    if user:
        email = getattr(
            user,
            "email",
            ""
        )

    st.sidebar.markdown(
        """
        <div class="brand-box">

            <div class="brand-row">

                <div class="brand-logo">
                    🌿
                </div>

                <div>
                    <div class="brand-name">
                        SEED LAB
                    </div>

                    <div class="brand-sub">
                        Multimodal Data QC Studio
                    </div>
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown(
        f"""
        <div class="user-card">

            <div class="user-name">
                {name}
            </div>

            <div class="user-email">
                {email}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown(
        '<div class="sidebar-label">WORKSPACE</div>',
        unsafe_allow_html=True
    )

    pages = [
        (
            "Overview",
            ":material/dashboard:"
        ),
        (
            "Image Data Studio",
            ":material/image:"
        ),
        (
            "Audio Data Studio",
            ":material/headphones:"
        ),
        (
            "Auditor Console",
            ":material/fact_check:"
        ),
    ]

    for page_name, icon in pages:

        active = (
            st.session_state.page == page_name
        )

        if st.sidebar.button(
            page_name,
            key=f"nav_{page_name.replace(' ', '_')}",
            icon=icon,
            type="primary" if active else "secondary",
            width="stretch",
        ):

            st.session_state.page = page_name
            st.rerun()

    st.sidebar.markdown(
        '<div class="sidebar-label">SETTINGS</div>',
        unsafe_allow_html=True
    )

    with st.sidebar.expander(
        "Settings",
        expanded=False,
        icon=":material/settings:"
    ):

        if st.button(
            "Profile",
            key="settings_profile",
            icon=":material/person:",
            width="stretch"
        ):

            st.session_state.page = "Profile"
            st.rerun()

        if st.button(
            "Account",
            key="settings_account",
            icon=":material/manage_accounts:",
            width="stretch"
        ):

            st.session_state.page = "Account"
            st.rerun()

    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    if st.sidebar.button(
        "Sign Out",
        key="sidebar_logout",
        icon=":material/logout:",
        width="stretch"
    ):

        logout_user()
        st.rerun()


# =========================================================
# PAGE HEADER
# =========================================================

def page_header(title, subtitle):

    st.markdown(
        f"""
        <div class="page-kicker">
            SEED LAB
        </div>

        <div class="page-title">
            {title}
        </div>

        <div class="page-subtitle">
            {subtitle}
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# OVERVIEW
# =========================================================

def overview_page():

    page_header(
        "Overview",
        "Unified workspace for multimodal data processing and quality control."
    )

    total = len(
        st.session_state.manifest
    )

    passed = sum(
        1
        for item in st.session_state.manifest
        if item["QC Status"] == "PASS"
    )

    review = sum(
        1
        for item in st.session_state.manifest
        if item["QC Status"] == "REVIEW"
    )

    st.markdown(
        """
        <div class="hero">

            <div class="hero-title">
                Process. Validate. Deliver.
            </div>

            <div class="hero-text">
                Process image and audio datasets with AI-powered
                OCR, transcription, translation, descriptions
                and quality control validation.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    Files Processed
                </div>

                <div class="metric-value">
                    {total}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    QC Passed
                </div>

                <div class="metric-value metric-green">
                    {passed}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    Needs Review
                </div>

                <div class="metric-value metric-orange">
                    {review}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="page-title"
             style="font-size:20px;">
            Workspace
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="page-subtitle">
            Choose a studio to begin processing your dataset.
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            """
            <div class="feature-card">

                <div class="feature-icon">
                    🖼️
                </div>

                <div class="feature-title">
                    Image Data Studio
                </div>

                <div class="feature-text">
                    Upload images and generate OCR,
                    English translation, AI descriptions
                    and confidence-based QC results.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Open Image Studio",
            key="overview_image",
            icon=":material/image:",
            width="stretch"
        ):

            st.session_state.page = "Image Data Studio"
            st.rerun()

    with c2:

        st.markdown(
            """
            <div class="feature-card">

                <div class="feature-icon">
                    🎧
                </div>

                <div class="feature-title">
                    Audio Data Studio
                </div>

                <div class="feature-text">
                    Analyze audio with transcription,
                    English translation, AI audio descriptions
                    and automated quality checks.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Open Audio Studio",
            key="overview_audio",
            icon=":material/headphones:",
            width="stretch"
        ):

            st.session_state.page = "Audio Data Studio"
            st.rerun()

    with c3:

        st.markdown(
            """
            <div class="feature-card">

                <div class="feature-icon">
                    📋
                </div>

                <div class="feature-title">
                    Auditor Console
                </div>

                <div class="feature-text">
                    Review processed files, QC status,
                    confidence scores and export the
                    complete processing manifest.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Open Auditor Console",
            key="overview_auditor",
            icon=":material/fact_check:",
            width="stretch"
        ):

            st.session_state.page = "Auditor Console"
            st.rerun()


# =========================================================
# IMAGE STUDIO
# =========================================================

def image_studio_page():

    page_header(
        "Image Data Studio",
        "Analyze image datasets with OCR, translation, description and QC."
    )

    left, right = st.columns(
        [0.95, 1.05],
        gap="large"
    )

    with left:

        st.markdown(
            """
            <div class="result-title">
                Image Input
            </div>
            """,
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "Upload image",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ],
            key="image_upload"
        )

        line_count = st.number_input(
            "Description lines",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            key="image_line_count"
        )

        if uploaded_file:

            try:

                image = Image.open(
                    uploaded_file
                )

                st.image(
                    image,
                    use_container_width=True
                )

            except Exception:

                st.error(
                    "Unable to display this image."
                )

        analyze = st.button(
            "Analyze Image",
            type="primary",
            width="stretch",
            icon=":material/auto_awesome:"
        )

        if analyze:

            if not uploaded_file:

                st.warning(
                    "Please upload an image first."
                )

            elif gemini_client is None:

                st.error(
                    "Gemini API is not configured."
                )

            else:

                with st.spinner(
                    "Analyzing image..."
                ):

                    result = analyze_image(
                        uploaded_file,
                        line_count
                    )

                st.session_state.image_result = result
                st.session_state.image_filename = (
                    uploaded_file.name
                )

                confidence = get_confidence(
                    result
                )

                status = qc_status(
                    confidence
                )

                add_manifest_item(
                    uploaded_file.name,
                    "Image",
                    confidence,
                    status
                )

                st.rerun()

    with right:

        result = st.session_state.get(
            "image_result"
        )

        if not result:

            st.markdown(
                """
                <div class="result-card">

                    <div class="result-title">
                        Analysis Result
                    </div>

                    <div class="result-value">
                        Upload an image and click
                        <b>Analyze Image</b> to begin.
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            confidence = get_confidence(
                result
            )

            status = qc_status(
                confidence
            )

            status_class = (
                "status-pass"
                if status == "PASS"
                else "status-review"
            )

            description = result.get(
                "description",
                []
            )

            if isinstance(description, list):
                description_text = "<br>".join(
                    str(x) for x in description
                )
            else:
                description_text = str(
                    description
                )

            st.markdown(
                f"""
                <div class="result-card">

                    <div class="result-title">
                        Analysis Result
                    </div>

                    <span class="{status_class}">
                        {status}
                    </span>

                    <div class="result-label">
                        Confidence
                    </div>

                    <div class="result-value">
                        {confidence}%
                    </div>

                    <div class="result-label">
                        OCR
                    </div>

                    <div class="result-value">
                        {result.get("ocr", "") or "No readable text detected."}
                    </div>

                    <div class="result-label">
                        English Translation
                    </div>

                    <div class="result-value">
                        {result.get("english_translation", "") or "No translation available."}
                    </div>

                    <div class="result-label">
                        AI Description
                    </div>

                    <div class="result-value">
                        {description_text}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# AUDIO STUDIO
# =========================================================

def audio_studio_page():

    page_header(
        "Audio Data Studio",
        "Analyze audio datasets with transcription, translation and QC."
    )

    left, right = st.columns(
        [0.95, 1.05],
        gap="large"
    )

    with left:

        st.markdown(
            """
            <div class="result-title">
                Audio Input
            </div>
            """,
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "Upload audio",
            type=[
                "mp3",
                "wav",
                "m4a",
                "ogg",
                "flac",
                "aac"
            ],
            key="audio_upload"
        )

        line_count = st.number_input(
            "Description lines",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            key="audio_line_count"
        )

        if uploaded_file:

            st.audio(
                uploaded_file
            )

        analyze = st.button(
            "Analyze Audio",
            type="primary",
            width="stretch",
            icon=":material/auto_awesome:"
        )

        if analyze:

            if not uploaded_file:

                st.warning(
                    "Please upload an audio file first."
                )

            elif gemini_client is None:

                st.error(
                    "Gemini API is not configured."
                )

            else:

                with st.spinner(
                    "Analyzing audio..."
                ):

                    result = analyze_audio(
                        uploaded_file,
                        line_count
                    )

                st.session_state.audio_result = result
                st.session_state.audio_filename = (
                    uploaded_file.name
                )

                confidence = get_confidence(
                    result
                )

                status = qc_status(
                    confidence
                )

                add_manifest_item(
                    uploaded_file.name,
                    "Audio",
                    confidence,
                    status
                )

                st.rerun()

    with right:

        result = st.session_state.get(
            "audio_result"
        )

        if not result:

            st.markdown(
                """
                <div class="result-card">

                    <div class="result-title">
                        Analysis Result
                    </div>

                    <div class="result-value">
                        Upload an audio file and click
                        <b>Analyze Audio</b> to begin.
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            confidence = get_confidence(
                result
            )

            status = qc_status(
                confidence
            )

            status_class = (
                "status-pass"
                if status == "PASS"
                else "status-review"
            )

            description = result.get(
                "description",
                []
            )

            if isinstance(description, list):
                description_text = "<br>".join(
                    str(x) for x in description
                )
            else:
                description_text = str(
                    description
                )

            st.markdown(
                f"""
                <div class="result-card">

                    <div class="result-title">
                        Analysis Result
                    </div>

                    <span class="{status_class}">
                        {status}
                    </span>

                    <div class="result-label">
                        Confidence
                    </div>

                    <div class="result-value">
                        {confidence}%
                    </div>

                    <div class="result-label">
                        Transcript
                    </div>

                    <div class="result-value">
                        {result.get("transcript", "") or "No transcript available."}
                    </div>

                    <div class="result-label">
                        English Translation
                    </div>

                    <div class="result-value">
                        {result.get("translation", "") or "No translation available."}
                    </div>

                    <div class="result-label">
                        AI Audio Description
                    </div>

                    <div class="result-value">
                        {description_text}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# AUDITOR CONSOLE
# =========================================================

def auditor_page():

    page_header(
        "Auditor Console",
        "Review processing history and quality-control results."
    )

    manifest = st.session_state.manifest

    total = len(manifest)

    passed = sum(
        1
        for item in manifest
        if item["QC Status"] == "PASS"
    )

    review = sum(
        1
        for item in manifest
        if item["QC Status"] == "REVIEW"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Total Files",
            total
        )

    with c2:
        st.metric(
            "QC Passed",
            passed
        )

    with c3:
        st.metric(
            "Needs Review",
            review
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if manifest:

        df = pd.DataFrame(
            manifest
        )

        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
        )

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Export CSV",
            data=csv,
            file_name="seed_lab_manifest.csv",
            mime="text/csv",
            icon=":material/download:"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Clear Session Manifest",
            icon=":material/delete_sweep:"
        ):

            st.session_state.manifest = []
            st.rerun()

    else:

        st.markdown(
            """
            <div class="result-card">

                <div class="result-title">
                    No processing records
                </div>

                <div class="result-value">
                    Process an image or audio file to
                    create your first QC record.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# PROFILE
# =========================================================

def profile_page():

    page_header(
        "Profile",
        "Manage your SEED Lab profile information."
    )

    user = st.session_state.user

    if not user:
        return

    current_name = st.session_state.get(
        "user_name",
        ""
    )

    current_image = st.session_state.get(
        "profile_image"
    )

    left, right = st.columns(
        [0.7, 1.3],
        gap="large"
    )

    with left:

        st.markdown(
            '<div class="profile-card">',
            unsafe_allow_html=True
        )

        if current_image:

            st.markdown(
                f"""
                <img
                    src="{current_image}"
                    class="profile-avatar"
                >
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                """
                <div class="profile-avatar"
                     style="
                     display:flex;
                     align-items:center;
                     justify-content:center;
                     background:#173A26;
                     color:#4ADE80;
                     font-size:35px;
                     ">
                    👤
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    with right:

        name = st.text_input(
            "Full Name",
            value=current_name
        )

        st.text_input(
            "Email",
            value=getattr(
                user,
                "email",
                ""
            ),
            disabled=True
        )

        uploaded = st.file_uploader(
            "Profile Picture",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ],
            key="profile_upload"
        )

        new_image = current_image

        if uploaded:

            new_image = image_to_data_url(
                uploaded
            )

            if new_image:

                st.image(
                    uploaded,
                    width=120
                )

        if st.button(
            "Save Profile",
            type="primary",
            icon=":material/save:",
            width="stretch"
        ):

            if not name.strip():

                st.error(
                    "Name cannot be empty."
                )

            else:

                success = create_or_update_profile(
                    user.id,
                    name.strip(),
                    new_image
                )

                if success:

                    st.session_state.user_name = (
                        name.strip()
                    )

                    st.session_state.profile_image = (
                        new_image
                    )

                    st.success(
                        "Profile updated successfully."
                    )

                else:

                    st.error(
                        "Unable to update profile."
                    )


# =========================================================
# ACCOUNT
# =========================================================

def account_page():

    page_header(
        "Account",
        "Manage account security and session settings."
    )

    user = st.session_state.user

    if not user:
        return

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True
    )

    st.markdown(
        "### Account Information"
    )

    st.text_input(
        "Email",
        value=getattr(
            user,
            "email",
            ""
        ),
        disabled=True
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True
    )

    st.markdown(
        "### Change Password"
    )

    new_password = st.text_input(
        "New Password",
        type="password",
        key="account_new_password"
    )

    confirm_password = st.text_input(
        "Confirm New Password",
        type="password",
        key="account_confirm_password"
    )

    if st.button(
        "Update Password",
        type="primary",
        icon=":material/lock:",
    ):

        if len(new_password) < 8:

            st.error(
                "Password must contain at least 8 characters."
            )

        elif new_password != confirm_password:

            st.error(
                "Passwords do not match."
            )

        else:

            success, message = change_user_password(
                new_password
            )

            if success:
                st.success(message)
            else:
                st.error(message)

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "Sign Out",
        icon=":material/logout:"
    ):

        logout_user()
        st.rerun()


# =========================================================
# CONFIGURATION CHECK
# =========================================================

def configuration_check():

    problems = []

    if not SUPABASE_URL:
        problems.append(
            "SUPABASE_URL"
        )

    if not SUPABASE_KEY:
        problems.append(
            "SUPABASE_KEY"
        )

    if not GEMINI_API_KEY:
        problems.append(
            "GEMINI_API_KEY"
        )

    if problems:

        st.warning(
            "Missing Streamlit secrets: "
            + ", ".join(problems)
        )


# =========================================================
# MAIN
# =========================================================

def main():

    # Try to restore Supabase session
    if not st.session_state.authenticated:

        current_user = get_current_user()

        if current_user:

            st.session_state.authenticated = True
            st.session_state.user = current_user

            profile = get_profile(
                current_user.id
            )

            if profile:

                st.session_state.user_name = (
                    profile.get(
                        "name",
                        current_user.email.split("@")[0]
                    )
                )

                st.session_state.profile_image = (
                    profile.get(
                        "profile_image"
                    )
                )

    # Login page
    if not st.session_state.authenticated:

        auth_page()
        return

    # Main app
    sidebar()

    page = st.session_state.page

    if page == "Overview":

        overview_page()

    elif page == "Image Data Studio":

        image_studio_page()

    elif page == "Audio Data Studio":

        audio_studio_page()

    elif page == "Auditor Console":

        auditor_page()

    elif page == "Profile":

        profile_page()

    elif page == "Account":

        account_page()

    else:

        overview_page()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()