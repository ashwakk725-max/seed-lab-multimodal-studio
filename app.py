import streamlit as st
import pandas as pd
import io
import json
import re
import base64
import os
from datetime import datetime

from PIL import Image
from google import genai
from google.genai import types
from supabase import create_client, Client


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SEED Lab | Multimodal Data QC Studio",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #f6f8f7;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    h1, h2, h3, h4 {
        color: #16251e;
    }

    p, span, label {
        color: #34443c;
    }

    /* ---------- SIDEBAR ---------- */

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e3e9e5;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }

    /* ---------- BRAND ---------- */

    .brand-box {
        padding: 12px 8px 22px 8px;
        border-bottom: 1px solid #e8edea;
        margin-bottom: 18px;
    }

    .brand-title {
        font-size: 22px;
        font-weight: 800;
        color: #163c2a;
        margin-bottom: 2px;
    }

    .brand-subtitle {
        font-size: 12px;
        color: #738078;
    }

    /* ---------- USER CARD ---------- */

    .user-card {
        background: #f4f8f5;
        border: 1px solid #e1ebe4;
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 18px;
    }

    .user-name {
        font-weight: 700;
        color: #183c2b;
        font-size: 14px;
    }

    .user-email {
        font-size: 11px;
        color: #738078;
        word-break: break-word;
    }

    /* ---------- AUTH ---------- */

    .auth-shell {
        max-width: 470px;
        margin: 5vh auto 0 auto;
    }

    .auth-card {
        background: white;
        border: 1px solid #e1e8e3;
        border-radius: 22px;
        padding: 35px;
        box-shadow: 0 10px 35px rgba(25, 55, 39, 0.07);
    }

    .auth-logo {
        text-align: center;
        font-size: 42px;
        margin-bottom: 5px;
    }

    .auth-title {
        text-align: center;
        color: #173e2b;
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .auth-subtitle {
        text-align: center;
        color: #78847e;
        font-size: 14px;
        margin-bottom: 25px;
    }

    /* ---------- METRICS ---------- */

    .metric-card {
        background: white;
        border: 1px solid #e1e8e3;
        border-radius: 16px;
        padding: 20px;
        min-height: 125px;
        box-shadow: 0 5px 18px rgba(25, 55, 39, 0.04);
    }

    .metric-label {
        font-size: 13px;
        color: #758179;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 31px;
        font-weight: 800;
        color: #183d2c;
    }

    /* ---------- HERO ---------- */

    .hero {
        background: linear-gradient(
            135deg,
            #e9f6ed 0%,
            #f8fbf8 55%,
            #eef7f1 100%
        );
        border: 1px solid #dbe9df;
        border-radius: 22px;
        padding: 28px;
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 31px;
        font-weight: 850;
        color: #153c29;
        margin-bottom: 7px;
    }

    .hero-text {
        color: #5d6d64;
        font-size: 15px;
        max-width: 850px;
        line-height: 1.6;
    }

    /* ---------- CARDS ---------- */

    .feature-card {
        background: white;
        border: 1px solid #e1e8e3;
        border-radius: 18px;
        padding: 22px;
        min-height: 175px;
        box-shadow: 0 5px 18px rgba(25, 55, 39, 0.04);
    }

    .feature-icon {
        font-size: 28px;
        margin-bottom: 12px;
    }

    .feature-title {
        font-weight: 750;
        font-size: 17px;
        color: #1b3e2d;
        margin-bottom: 7px;
    }

    .feature-text {
        color: #718078;
        font-size: 13px;
        line-height: 1.5;
    }

    /* ---------- STATUS ---------- */

    .status-pass {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 999px;
        background: #e7f7ed;
        color: #18753d;
        font-weight: 700;
        font-size: 12px;
    }

    .status-review {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 999px;
        background: #fff5df;
        color: #9a6800;
        font-weight: 700;
        font-size: 12px;
    }

    /* ---------- SECTION ---------- */

    .section-title {
        font-size: 22px;
        font-weight: 800;
        color: #183d2c;
        margin-top: 15px;
        margin-bottom: 4px;
    }

    .section-subtitle {
        color: #7a867f;
        font-size: 13px;
        margin-bottom: 18px;
    }

    /* ---------- RESULT ---------- */

    .result-box {
        background: white;
        border: 1px solid #e1e8e3;
        border-radius: 16px;
        padding: 20px;
        margin-top: 15px;
    }

    .confidence-number {
        font-size: 34px;
        font-weight: 850;
        color: #183d2c;
    }

    /* ---------- PROFILE ---------- */

    .profile-card {
        background: white;
        border: 1px solid #e1e8e3;
        border-radius: 20px;
        padding: 25px;
    }

    /* ---------- BUTTONS ---------- */

    .stButton > button {
        border-radius: 10px;
        font-weight: 650;
        border: 1px solid #d8e4dc;
    }

    /* ---------- DIVIDER ---------- */

    .soft-divider {
        height: 1px;
        background: #e6ece8;
        margin: 25px 0;
    }

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_SESSION = {
    "authenticated": False,
    "user": None,
    "page": "Overview",
    "manifest": [],
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# SECRETS
# ============================================================

def get_secret(name, default=""):
    """
    Safely read a value from Streamlit secrets first,
    then environment variables.
    """

    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass

    return os.getenv(name, default)


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

GEMINI_MODEL = get_secret(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def get_supabase() -> Client:

    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        return create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )
    except Exception:
        return None


supabase = get_supabase()


# ============================================================
# GEMINI
# ============================================================

@st.cache_resource
def get_gemini_client():

    if not GEMINI_API_KEY:
        return None

    try:
        return genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception:
        return None


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clean_email(email):
    return email.strip().lower()


def valid_email(email):

    return bool(
        re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            email.strip()
        )
    )


def password_strength(password):

    if len(password) < 6:
        return "Password must contain at least 6 characters."

    return ""


def image_to_data_url(uploaded_file):

    if uploaded_file is None:
        return None

    try:

        image = Image.open(uploaded_file)

        # Resize large images
        max_size = 600

        image.thumbnail(
            (max_size, max_size)
        )

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=82
        )

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        return f"data:image/jpeg;base64,{encoded}"

    except Exception:

        return None


def get_current_user():

    if not supabase:
        return None

    try:

        response = supabase.auth.get_user()

        if response and response.user:
            return response.user

    except Exception:
        pass

    return None


# ============================================================
# SUPABASE PROFILE FUNCTIONS
# ============================================================

def get_profile(user_id):

    if not supabase or not user_id:
        return None

    try:

        response = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

    except Exception:
        pass

    return None


def create_or_update_profile(
    user_id,
    name,
    profile_image=None
):

    if not supabase or not user_id:
        return False

    try:

        existing = get_profile(user_id)

        data = {
            "id": user_id,
            "name": name.strip(),
        }

        if profile_image is not None:
            data["profile_image"] = profile_image

        if existing:

            (
                supabase
                .table("profiles")
                .update(data)
                .eq("id", user_id)
                .execute()
            )

        else:

            (
                supabase
                .table("profiles")
                .insert(data)
                .execute()
            )

        return True

    except Exception as e:

        st.error(
            f"Unable to save profile: {e}"
        )

        return False


# ============================================================
# AUTHENTICATION
# ============================================================

def login_user(email, password):

    if not supabase:

        return False, (
            "Supabase is not configured. "
            "Check your Streamlit Secrets."
        )

    try:

        response = supabase.auth.sign_in_with_password(
            {
                "email": clean_email(email),
                "password": password,
            }
        )

        if response and response.user:

            user = response.user

            profile = get_profile(
                str(user.id)
            )

            st.session_state.authenticated = True
            st.session_state.user = user
            st.session_state.profile = profile
            st.session_state.page = "Overview"

            return True, "Login successful."

        return False, "Invalid email or password."

    except Exception as e:

        error = str(e)

        if "Email not confirmed" in error:
            return False, (
                "Please confirm your email before signing in."
            )

        if "Invalid login credentials" in error:
            return False, "Invalid email or password."

        return False, error


def register_user(name, email, password):

    if not supabase:
        return False, "Supabase is not configured."

    name = name.strip()
    email = clean_email(email)

    # Check name
    if not name:
        return False, "Please enter your name."

    # Check email
    if not valid_email(email):
        return False, "Please enter a valid email address."

    # Check password
    password_error = password_strength(password)

    if password_error:
        return False, password_error

    try:

        # Create account in Supabase Authentication
        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name
                    }
                }
            }
        )

        user = response.user
        session = response.session

        # Make sure user was created
        if not user:
            return False, "Account creation failed."

        # --------------------------------------------------
        # EMAIL CONFIRMATION OFF
        # --------------------------------------------------
        # If email confirmation is disabled in Supabase,
        # a session will be returned immediately.
        # Then we can safely create the profile.
        # --------------------------------------------------

        if session:

            profile_saved = create_or_update_profile(
                str(user.id),
                name
            )

            if not profile_saved:

                return False, (
                    "Account was created, but your profile "
                    "could not be saved."
                )

            # Save login information in Streamlit session
            st.session_state.authenticated = True

            st.session_state.user = user

            st.session_state.profile = get_profile(
                str(user.id)
            )

            st.session_state.page = "Overview"

            return True, "Account created successfully."

        # --------------------------------------------------
        # EMAIL CONFIRMATION ON
        # --------------------------------------------------
        # No authenticated session exists yet, so DON'T try
        # to insert into profiles here.
        # The user must confirm email and then sign in.
        # --------------------------------------------------

        return True, (
            "Account created successfully. "
            "Please check your email and confirm your account. "
            "Then return here and sign in."
        )

    except Exception as e:

        error = str(e)

        # Existing account
        if "already registered" in error.lower():

            return False, (
                "This email is already registered. "
                "Please sign in."
            )

        # Other Supabase error
        return False, error

def logout_user():

    try:

        if supabase:
            supabase.auth.sign_out()

    except Exception:
        pass

    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.page = "Overview"
    st.session_state.manifest = []


def change_user_password(new_password):

    if not supabase:
        return False, "Supabase is not configured."

    password_error = password_strength(
        new_password
    )

    if password_error:
        return False, password_error

    try:

        response = supabase.auth.update_user(
            {
                "password": new_password
            }
        )

        if response and response.user:
            return True, (
                "Password updated successfully."
            )

        return False, "Password update failed."

    except Exception as e:

        return False, str(e)


def send_password_reset(email):

    if not supabase:
        return False, "Supabase is not configured."

    try:

        supabase.auth.reset_password_for_email(
            clean_email(email)
        )

        return True, (
            "If the email exists, a password reset "
            "message has been sent."
        )

    except Exception as e:

        return False, str(e)


# ============================================================
# GEMINI FUNCTIONS
# ============================================================

def generate_gemini_text(
    prompt,
    contents=None
):

    client = get_gemini_client()

    if not client:
        return None, (
            "Gemini API key is missing."
        )

    try:

        if contents is None:
            contents = prompt
        else:
            contents = [
                prompt,
                *contents
            ]

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents
        )

        if response and response.text:
            return response.text.strip(), None

        return None, "Gemini returned an empty response."

    except Exception as e:

        return None, str(e)


def extract_json(text):

    if not text:
        return None

    text = text.strip()

    # Remove markdown JSON fences
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

    # Try finding first JSON object
    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if match:

        try:
            return json.loads(
                match.group(0)
            )
        except Exception:
            pass

    return None


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def analyze_image(
    uploaded_file,
    line_count=3
):

    try:

        image_bytes = uploaded_file.getvalue()

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        prompt = f"""
You are a professional multimodal data quality
control assistant.

Analyze the supplied image.

Return ONLY valid JSON in exactly this structure:

{{
  "ocr": "all useful visible text",
  "english_translation": "English translation if text is not English, otherwise empty string",
  "description": [
      "short description line 1",
      "short description line 2",
      "short description line 3"
  ],
  "confidence": 0
}}

Rules:

1. OCR must contain readable visible text.
2. If there is no readable text, use an empty string.
3. Translation should translate detected non-English text.
4. Description must contain exactly {line_count} short lines.
5. Confidence must be a number from 0 to 100.
6. Do not add markdown.
7. Do not add explanations outside JSON.
"""

        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=(
                uploaded_file.type
                or "image/jpeg"
            )
        )

        text, error = generate_gemini_text(
            prompt,
            [image_part]
        )

        if error:
            return None, error

        result = extract_json(text)

        if not result:
            return None, (
                "Gemini returned an invalid response."
            )

        return result, None

    except Exception as e:

        return None, str(e)


# ============================================================
# AUDIO ANALYSIS
# ============================================================

def analyze_audio(
    uploaded_file,
    line_count=3
):

    try:

        audio_bytes = uploaded_file.getvalue()

        mime_type = (
            uploaded_file.type
            or "audio/mpeg"
        )

        prompt = f"""
You are a professional multimodal data quality
control assistant.

Analyze the supplied audio.

Return ONLY valid JSON in exactly this structure:

{{
  "transcript": "complete useful transcript",
  "translation": "English translation if the spoken language is not English, otherwise empty string",
  "description": [
      "short description line 1",
      "short description line 2",
      "short description line 3"
  ],
  "confidence": 0
}}

Rules:

1. Transcribe the spoken content as accurately as possible.
2. If the language is not English, translate it into English.
3. Description must contain exactly {line_count} short lines.
4. Confidence must be a number from 0 to 100.
5. Do not add markdown.
6. Do not add explanations outside JSON.
"""

        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type
        )

        text, error = generate_gemini_text(
            prompt,
            [audio_part]
        )

        if error:
            return None, error

        result = extract_json(text)

        if not result:
            return None, (
                "Gemini returned an invalid response."
            )

        return result, None

    except Exception as e:

        return None, str(e)


# ============================================================
# QC
# ============================================================

def get_confidence(result):

    try:

        value = result.get(
            "confidence",
            0
        )

        return float(value)

    except Exception:

        return 0.0


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

    item = {
        "File": filename,
        "Type": data_type,
        "Confidence": round(
            float(confidence),
            1
        ),
        "QC Status": status,
        "Processed At": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    st.session_state.manifest.append(
        item
    )


# ============================================================
# AUTH PAGE
# ============================================================

def auth_page():

    st.markdown(
        '<div class="auth-shell">',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="auth-card">
            <div class="auth-logo">🌿</div>
            <div class="auth-title">
                SEED Lab Studio
            </div>
            <div class="auth-subtitle">
                Unified Multimodal Data QC Studio
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_login, tab_register = st.tabs(
        ["Sign In", "Create Account"]
    )

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    with tab_login:

        st.markdown("### Welcome back")

        login_email = st.text_input(
            "Email",
            placeholder="you@example.com",
            key="login_email"
        )

        login_password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        if st.button(
            "Sign In",
            use_container_width=True,
            type="primary"
        ):

            if not login_email or not login_password:

                st.warning(
                    "Please enter both email and password."
                )

            else:

                success, message = login_user(
                    login_email,
                    login_password
                )

                if success:

                    if st.session_state.authenticated:

                        st.success(message)

                        st.rerun()

                    else:

                        st.info(message)

                else:

                    st.error(message)

        st.markdown(
            '<div class="soft-divider"></div>',
            unsafe_allow_html=True
        )

        st.caption(
            "Forgot your password?"
        )

        reset_email = st.text_input(
            "Reset email",
            placeholder="Enter your account email",
            key="reset_email"
        )

        if st.button(
            "Send Password Reset",
            use_container_width=True
        ):

            if not valid_email(reset_email):

                st.warning(
                    "Enter a valid email address."
                )

            else:

                success, message = send_password_reset(
                    reset_email
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    with tab_register:

        st.markdown("### Create your account")

        register_name = st.text_input(
            "Full name",
            placeholder="Your name",
            key="register_name"
        )

        register_email = st.text_input(
            "Email",
            placeholder="you@example.com",
            key="register_email"
        )

        register_password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 6 characters",
            key="register_password"
        )

        register_confirm = st.text_input(
            "Confirm password",
            type="password",
            placeholder="Re-enter password",
            key="register_confirm"
        )

        if st.button(
            "Create Account",
            use_container_width=True,
            type="primary"
        ):

            if register_password != register_confirm:

                st.error(
                    "Passwords do not match."
                )

            else:

                success, message = register_user(
                    register_name,
                    register_email,
                    register_password
                )

                if success:

                    if st.session_state.authenticated:
                        st.success(message)
                        st.rerun()
                    else:
                        st.success(message)
                        st.info(
                            "If email confirmation is enabled "
                            "in Supabase, confirm your email "
                            "and then sign in."
                        )

                else:

                    st.error(message)

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    user = st.session_state.user
    profile = st.session_state.get(
        "profile"
    ) or {}

    display_name = (
        profile.get("name")
        if profile
        else None
    )

    if not display_name and user:
        display_name = (
            user.user_metadata.get("name")
            if user.user_metadata
            else None
        )

    if not display_name:
        display_name = (
            user.email.split("@")[0]
            if user and user.email
            else "User"
        )

    email = (
        user.email
        if user
        else ""
    )

    with st.sidebar:

        st.markdown(
            """
            <div class="brand-box">
                <div class="brand-title">
                    🌿 SEED LAB
                </div>
                <div class="brand-subtitle">
                    Multimodal Data QC Studio
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="user-card">
                <div class="user-name">
                    {display_name}
                </div>
                <div class="user-email">
                    {email}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            "**WORKSPACE**"
        )

        pages = [
            (
                "Overview",
                "⌂"
            ),
            (
                "Image Data Studio",
                "▧"
            ),
            (
                "Audio Data Studio",
                "◉"
            ),
            (
                "Auditor Console",
                "✓"
            ),
        ]

        for page_name, icon in pages:

            if st.button(
                f"{icon}  {page_name}",
                key=f"nav_{page_name}",
                use_container_width=True
            ):

                st.session_state.page = page_name
                st.rerun()

        st.markdown("")

        with st.expander(
            "⚙ Settings",
            expanded=False
        ):

            if st.button(
                "Profile",
                use_container_width=True
            ):

                st.session_state.page = "Profile"
                st.rerun()

            if st.button(
                "Account",
                use_container_width=True
            ):

                st.session_state.page = "Account"
                st.rerun()

        st.markdown(
            '<div style="height:25px;"></div>',
            unsafe_allow_html=True
        )

        if st.button(
            "Sign Out",
            use_container_width=True
        ):

            logout_user()
            st.rerun()


# ============================================================
# PAGE HEADER
# ============================================================

def page_header(
    title,
    subtitle
):

    st.markdown(
        f"""
        <div class="section-title">
            {title}
        </div>

        <div class="section-subtitle">
            {subtitle}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# OVERVIEW
# ============================================================

def overview_page():

    manifest = st.session_state.manifest

    total = len(manifest)

    passed = sum(
        1
        for x in manifest
        if x.get("QC Status") == "PASS"
    )

    review = sum(
        1
        for x in manifest
        if x.get("QC Status") == "REVIEW"
    )

    st.markdown(
    """
    <div class="hero-text">
        Process image and audio datasets with AI-powered
        OCR, transcription, translation, descriptions,
        confidence scoring and quality-control review.
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
                <div class="metric-value">
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
                <div class="metric-value">
                    {review}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="section-title">
            Workspace
        </div>
        <div class="section-subtitle">
            Choose a data workflow to begin processing.
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🖼️</div>
                <div class="feature-title">
                    Image Data Studio
                </div>
                <div class="feature-text">
                    Upload images and extract OCR,
                    translation, AI descriptions and
                    automated QC confidence.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Open Image Studio",
            use_container_width=True
        ):

            st.session_state.page = (
                "Image Data Studio"
            )
            st.rerun()

    with c2:

        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🎧</div>
                <div class="feature-title">
                    Audio Data Studio
                </div>
                <div class="feature-text">
                    Process speech recordings with
                    transcription, translation,
                    descriptions and confidence scoring.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Open Audio Studio",
            use_container_width=True
        ):

            st.session_state.page = (
                "Audio Data Studio"
            )
            st.rerun()

    with c3:

        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📋</div>
                <div class="feature-title">
                    Auditor Console
                </div>
                <div class="feature-text">
                    Review processed files, QC status,
                    confidence scores and export the
                    processing manifest.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Open Auditor Console",
            use_container_width=True
        ):

            st.session_state.page = (
                "Auditor Console"
            )
            st.rerun()


# ============================================================
# IMAGE STUDIO
# ============================================================

def image_studio_page():

    page_header(
        "Image Data Studio",
        "AI-powered image understanding and quality control."
    )

    left, right = st.columns(
        [1, 1.25],
        gap="large"
    )

    with left:

        st.markdown("### Upload image")

        uploaded = st.file_uploader(
            "Choose an image",
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
            max_value=8,
            value=3,
            step=1
        )

        if uploaded:

            try:

                image = Image.open(
                    uploaded
                )

                st.image(
                    image,
                    use_container_width=True
                )

            except Exception:

                st.error(
                    "Unable to display this image."
                )

        analyze_button = st.button(
            "Analyze Image",
            type="primary",
            use_container_width=True
        )

    with right:

        st.markdown("### Analysis")

        if analyze_button:

            if not uploaded:

                st.warning(
                    "Please upload an image first."
                )

            else:

                with st.spinner(
                    "Gemini is analyzing the image..."
                ):

                    result, error = analyze_image(
                        uploaded,
                        line_count
                    )

                if error:

                    st.error(
                        f"Analysis failed: {error}"
                    )

                else:

                    confidence = get_confidence(
                        result
                    )

                    status = qc_status(
                        confidence
                    )

                    add_manifest_item(
                        uploaded.name,
                        "Image",
                        confidence,
                        status
                    )

                    st.session_state[
                        "last_image_result"
                    ] = result

                    st.session_state[
                        "last_image_status"
                    ] = status

        result = st.session_state.get(
            "last_image_result"
        )

        if result:

            confidence = get_confidence(
                result
            )

            status = st.session_state.get(
                "last_image_status",
                qc_status(confidence)
            )

            st.markdown(
                '<div class="result-box">',
                unsafe_allow_html=True
            )

            st.markdown("#### OCR")

            ocr = result.get(
                "ocr",
                ""
            )

            if ocr:
                st.text_area(
                    "Detected text",
                    ocr,
                    height=130,
                    disabled=True,
                    label_visibility="collapsed"
                )
            else:
                st.info(
                    "No readable text detected."
                )

            st.markdown("#### English Translation")

            translation = result.get(
                "english_translation",
                ""
            )

            if translation:
                st.write(translation)
            else:
                st.caption(
                    "No translation required."
                )

            st.markdown("#### AI Description")

            descriptions = result.get(
                "description",
                []
            )

            if isinstance(
                descriptions,
                list
            ):

                for line in descriptions:
                    st.write(
                        f"• {line}"
                    )

            else:

                st.write(
                    descriptions
                )

            st.markdown("#### QC Confidence")

            st.markdown(
                f"""
                <div class="confidence-number">
                    {confidence:.0f}%
                </div>
                """,
                unsafe_allow_html=True
            )

            if status == "PASS":

                st.markdown(
                    '<span class="status-pass">✓ PASS</span>',
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    '<span class="status-review">⚠ REVIEW</span>',
                    unsafe_allow_html=True
                )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )


# ============================================================
# AUDIO STUDIO
# ============================================================

def audio_studio_page():

    page_header(
        "Audio Data Studio",
        "Transcribe, translate and quality-check audio datasets."
    )

    left, right = st.columns(
        [1, 1.25],
        gap="large"
    )

    with left:

        st.markdown("### Upload audio")

        uploaded = st.file_uploader(
            "Choose an audio file",
            type=[
                "mp3",
                "wav",
                "m4a",
                "aac",
                "ogg",
                "flac"
            ],
            key="audio_upload"
        )

        line_count = st.number_input(
            "Description lines",
            min_value=1,
            max_value=8,
            value=3,
            step=1,
            key="audio_line_count"
        )

        if uploaded:

            st.audio(
                uploaded
            )

            st.caption(
                f"{uploaded.name} · "
                f"{uploaded.size / 1024:.1f} KB"
            )

        analyze_button = st.button(
            "Analyze Audio",
            type="primary",
            use_container_width=True
        )

    with right:

        st.markdown("### Analysis")

        if analyze_button:

            if not uploaded:

                st.warning(
                    "Please upload an audio file first."
                )

            else:

                with st.spinner(
                    "Gemini is analyzing the audio..."
                ):

                    result, error = analyze_audio(
                        uploaded,
                        line_count
                    )

                if error:

                    st.error(
                        f"Analysis failed: {error}"
                    )

                else:

                    confidence = get_confidence(
                        result
                    )

                    status = qc_status(
                        confidence
                    )

                    add_manifest_item(
                        uploaded.name,
                        "Audio",
                        confidence,
                        status
                    )

                    st.session_state[
                        "last_audio_result"
                    ] = result

                    st.session_state[
                        "last_audio_status"
                    ] = status

        result = st.session_state.get(
            "last_audio_result"
        )

        if result:

            confidence = get_confidence(
                result
            )

            status = st.session_state.get(
                "last_audio_status",
                qc_status(confidence)
            )

            st.markdown(
                '<div class="result-box">',
                unsafe_allow_html=True
            )

            st.markdown("#### Transcript")

            transcript = result.get(
                "transcript",
                ""
            )

            if transcript:

                st.text_area(
                    "Transcript",
                    transcript,
                    height=180,
                    disabled=True,
                    label_visibility="collapsed"
                )

            else:

                st.info(
                    "No transcript detected."
                )

            st.markdown("#### English Translation")

            translation = result.get(
                "translation",
                ""
            )

            if translation:
                st.write(
                    translation
                )
            else:
                st.caption(
                    "No translation required."
                )

            st.markdown("#### AI Audio Description")

            descriptions = result.get(
                "description",
                []
            )

            if isinstance(
                descriptions,
                list
            ):

                for line in descriptions:
                    st.write(
                        f"• {line}"
                    )

            else:

                st.write(
                    descriptions
                )

            st.markdown("#### QC Confidence")

            st.markdown(
                f"""
                <div class="confidence-number">
                    {confidence:.0f}%
                </div>
                """,
                unsafe_allow_html=True
            )

            if status == "PASS":

                st.markdown(
                    '<span class="status-pass">✓ PASS</span>',
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    '<span class="status-review">⚠ REVIEW</span>',
                    unsafe_allow_html=True
                )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )


# ============================================================
# AUDITOR CONSOLE
# ============================================================

def auditor_page():

    page_header(
        "Auditor Console",
        "Review the current processing manifest and QC results."
    )

    manifest = st.session_state.manifest

    total = len(manifest)

    passed = sum(
        1
        for item in manifest
        if item.get("QC Status") == "PASS"
    )

    review = sum(
        1
        for item in manifest
        if item.get("QC Status") == "REVIEW"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Total Files",
            total
        )

    with c2:

        st.metric(
            "Passed",
            passed
        )

    with c3:

        st.metric(
            "Needs Review",
            review
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if not manifest:

        st.info(
            "No files have been processed yet."
        )

        return

    df = pd.DataFrame(
        manifest
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    csv_data = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download CSV Manifest",
        data=csv_data,
        file_name=(
            "seed_lab_qc_manifest.csv"
        ),
        mime="text/csv",
        use_container_width=True
    )

    if st.button(
        "Clear Session Manifest",
        use_container_width=True
    ):

        st.session_state.manifest = []

        st.success(
            "Manifest cleared."
        )

        st.rerun()


# ============================================================
# PROFILE
# ============================================================

def profile_page():

    page_header(
        "Profile",
        "Manage your SEED Lab Studio profile."
    )

    user = st.session_state.user

    if not user:
        return

    profile = (
        st.session_state.get("profile")
        or get_profile(str(user.id))
        or {}
    )

    current_name = profile.get(
        "name",
        ""
    )

    current_image = profile.get(
        "profile_image"
    )

    c1, c2 = st.columns(
        [1, 2],
        gap="large"
    )

    with c1:

        st.markdown(
            '<div class="profile-card">',
            unsafe_allow_html=True
        )

        if current_image:

            st.image(
                current_image,
                width=170
            )

        else:

            st.markdown(
                """
                <div style="
                    width:170px;
                    height:170px;
                    border-radius:50%;
                    background:#e9f3ec;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:65px;
                    margin:auto;
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

    with c2:

        st.markdown("### Profile details")

        name = st.text_input(
            "Name",
            value=current_name
        )

        st.text_input(
            "Email",
            value=user.email or "",
            disabled=True
        )

        profile_picture = st.file_uploader(
            "Profile picture",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ],
            key="profile_picture"
        )

        new_image = None

        if profile_picture:

            new_image = image_to_data_url(
                profile_picture
            )

            if new_image:

                st.image(
                    new_image,
                    width=150
                )

            else:

                st.error(
                    "Could not process profile image."
                )

        if st.button(
            "Save Profile",
            type="primary",
            use_container_width=True
        ):

            if not name.strip():

                st.error(
                    "Name cannot be empty."
                )

            else:

                if new_image is None:
                    new_image = current_image

                success = create_or_update_profile(
                    str(user.id),
                    name,
                    new_image
                )

                if success:

                    st.session_state.profile = (
                        get_profile(
                            str(user.id)
                        )
                    )

                    st.success(
                        "Profile updated successfully."
                    )

                    st.rerun()


# ============================================================
# ACCOUNT
# ============================================================

def account_page():

    page_header(
        "Account",
        "Security and account controls."
    )

    user = st.session_state.user

    if not user:
        return

    st.markdown(
        "### Account information"
    )

    st.text_input(
        "Email",
        value=user.email or "",
        disabled=True
    )

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    st.markdown(
        "### Change password"
    )

    new_password = st.text_input(
        "New password",
        type="password",
        placeholder="Minimum 6 characters",
        key="new_password"
    )

    confirm_password = st.text_input(
        "Confirm new password",
        type="password",
        placeholder="Re-enter new password",
        key="confirm_new_password"
    )

    if st.button(
        "Update Password",
        type="primary",
        use_container_width=True
    ):

        if new_password != confirm_password:

            st.error(
                "Passwords do not match."
            )

        else:

            success, message = (
                change_user_password(
                    new_password
                )
            )

            if success:
                st.success(message)
            else:
                st.error(message)

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    st.markdown(
        "### Sign out"
    )

    if st.button(
        "Sign Out",
        use_container_width=True
    ):

        logout_user()
        st.rerun()


# ============================================================
# CONFIGURATION CHECK
# ============================================================

def configuration_check():

    missing = []

    if not SUPABASE_URL:
        missing.append(
            "SUPABASE_URL"
        )

    if not SUPABASE_KEY:
        missing.append(
            "SUPABASE_KEY"
        )

    if not GEMINI_API_KEY:
        missing.append(
            "GEMINI_API_KEY"
        )

    if missing:

        st.error(
            "Missing Streamlit Secrets: "
            + ", ".join(missing)
        )

        st.info(
            "Open Streamlit → Manage app → Settings → "
            "Secrets and add the required values."
        )

        st.stop()


# ============================================================
# MAIN APP
# ============================================================

def main():

    configuration_check()

    # Try restoring current Supabase user
    if not st.session_state.authenticated:

        current_user = get_current_user()

        if current_user:

            st.session_state.authenticated = True
            st.session_state.user = current_user
            st.session_state.profile = (
                get_profile(
                    str(current_user.id)
                )
            )

    # Login screen
    if not st.session_state.authenticated:

        auth_page()
        return

    # Sidebar
    sidebar()

    # Current page
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


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()