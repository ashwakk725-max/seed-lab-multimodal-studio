# ============================================================
# SEED LAB MULTIMODAL STUDIO
# Complete Streamlit App
# Login • Register • Profile • Settings
# Image QC • Audio QC • Auditor Console
# ============================================================

import os
import re
import csv
import io
import json
import time
import hmac
import hashlib
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
from PIL import Image

from google import genai
from google.genai import types


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SEED Lab Multimodal Studio",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "seed_lab_data"
PROFILE_DIR = DATA_DIR / "profiles"
DB_PATH = DATA_DIR / "users.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: "Inter", sans-serif;
}

.stApp {
    background: #f5f7f6;
    color: #17201b;
}

/* Hide Streamlit branding */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #10251b;
    border-right: 1px solid #183c2b;
}

section[data-testid="stSidebar"] * {
    color: #eef8f1 !important;
}

section[data-testid="stSidebar"] .stButton button {
    background: transparent;
    border: 1px solid transparent;
    color: #dcebe1 !important;
    text-align: left;
    border-radius: 10px;
}

section[data-testid="stSidebar"] .stButton button:hover {
    background: #183a29;
    border-color: #24543b;
}

section[data-testid="stSidebar"] hr {
    border-color: #28523b;
}

/* Main content */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

/* Headings */
h1 {
    font-weight: 800 !important;
    letter-spacing: -0.04em;
}

h2 {
    font-weight: 750 !important;
    letter-spacing: -0.025em;
}

h3 {
    font-weight: 700 !important;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
    border: 1px solid #d9e2dc;
    background: white;
    color: #173323;
}

.stButton > button:hover {
    border-color: #24864e;
    color: #16733f;
}

/* Primary buttons */
button[kind="primary"] {
    background: #16834a !important;
    border-color: #16834a !important;
    color: white !important;
}

button[kind="primary"]:hover {
    background: #116a3b !important;
}

/* Inputs */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] {
    border-radius: 10px !important;
}

/* Upload */
[data-testid="stFileUploader"] {
    background: white;
    border: 1px dashed #a9bbb0;
    border-radius: 14px;
    padding: 12px;
}

/* Metrics */
div[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e0e7e2;
    border-radius: 14px;
    padding: 18px;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* Cards */
.seed-card {
    background: white;
    border: 1px solid #e1e8e3;
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 18px;
}

.seed-card:hover {
    border-color: #c7d9cd;
}

.seed-card-title {
    font-size: 18px;
    font-weight: 750;
    margin-bottom: 6px;
}

.seed-card-subtitle {
    color: #66756d;
    font-size: 14px;
}

.status-pass {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: #e8f7ee;
    color: #13733d;
    font-size: 12px;
    font-weight: 700;
}

.status-review {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: #fff4dc;
    color: #966500;
    font-size: 12px;
    font-weight: 700;
}

.hero {
    background:
        radial-gradient(circle at 90% 10%, rgba(40,160,91,0.12), transparent 30%),
        linear-gradient(135deg, #ffffff 0%, #f4faf6 100%);
    border: 1px solid #dfe9e2;
    border-radius: 22px;
    padding: 34px;
    margin-bottom: 24px;
}

.hero-small {
    color: #617168;
    font-size: 15px;
    line-height: 1.7;
}

.big-number {
    font-size: 30px;
    font-weight: 800;
    color: #173323;
}

.muted {
    color: #6b7871;
}

.profile-box {
    background: #183a29;
    border: 1px solid #28563d;
    border-radius: 14px;
    padding: 14px;
    margin: 10px 0 18px 0;
}

.sidebar-label {
    color: #91b39d !important;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
}

.auth-wrap {
    max-width: 500px;
    margin: 7vh auto 0 auto;
}

.auth-brand {
    text-align: center;
    margin-bottom: 28px;
}

.auth-logo {
    font-size: 42px;
}

.auth-title {
    font-size: 32px;
    font-weight: 800;
    color: #173323;
}

.auth-subtitle {
    color: #68766e;
    margin-top: 6px;
}

.result-box {
    background: #ffffff;
    border: 1px solid #e1e8e3;
    border-radius: 14px;
    padding: 18px;
    margin-top: 12px;
}

.result-label {
    color: #6a776f;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 7px;
}

.result-text {
    color: #1d2922;
    line-height: 1.7;
}

.footer {
    text-align: center;
    color: #89958e;
    font-size: 12px;
    padding: 30px 0 10px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "logged_in": False,
    "user_id": None,
    "page": "overview",
    "settings_open": False,
    "image_result": None,
    "audio_result": None,
    "manifest": [],
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            profile_image TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# PASSWORD SECURITY
# ============================================================

HASH_ITERATIONS = 180_000


def hash_password(password, salt_hex=None):
    """
    Create a PBKDF2 password hash.

    Important:
    - New passwords always receive a valid random salt.
    - Old/corrupted salts do NOT crash the app.
    """

    if salt_hex:
        try:
            salt = bytes.fromhex(str(salt_hex))

            # Reject suspicious/invalid salt sizes.
            if len(salt) < 16:
                raise ValueError("Invalid salt length")

        except (ValueError, TypeError):
            salt = secrets.token_bytes(16)
    else:
        salt = secrets.token_bytes(16)

    password_bytes = str(password).encode("utf-8")

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        HASH_ITERATIONS,
    )

    return hashed.hex(), salt.hex()


def verify_password(password, stored_hash, salt_hex):
    """
    Safely verify an existing password.

    Invalid/corrupted database data returns False
    instead of crashing the application.
    """

    try:
        if not stored_hash or not salt_hex:
            return False

        salt_text = str(salt_hex).strip()

        # A valid 16-byte hex salt is 32 hex characters.
        if len(salt_text) != 32:
            return False

        if not re.fullmatch(r"[0-9a-fA-F]{32}", salt_text):
            return False

        calculated_hash, _ = hash_password(
            password,
            salt_text,
        )

        return hmac.compare_digest(
            str(calculated_hash),
            str(stored_hash),
        )

    except Exception:
        return False


# ============================================================
# USER FUNCTIONS
# ============================================================

def get_user_by_email(email):
    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE LOWER(email)=LOWER(?)",
        (email.strip(),),
    ).fetchone()

    conn.close()

    return user


def get_user_by_id(user_id):
    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,),
    ).fetchone()

    conn.close()

    return user


def create_user(name, email, password):
    password_hash, salt = hash_password(password)

    conn = get_db()

    try:
        cursor = conn.execute(
            """
            INSERT INTO users
            (name, email, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                email.strip().lower(),
                password_hash,
                salt,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        conn.commit()

        user_id = cursor.lastrowid

        conn.close()

        return True, user_id

    except sqlite3.IntegrityError:
        conn.close()
        return False, None

    except Exception:
        conn.close()
        return False, None


def update_profile(user_id, name, image_path=None):
    conn = get_db()

    if image_path:
        conn.execute(
            """
            UPDATE users
            SET name=?, profile_image=?
            WHERE id=?
            """,
            (name.strip(), image_path, user_id),
        )
    else:
        conn.execute(
            """
            UPDATE users
            SET name=?
            WHERE id=?
            """,
            (name.strip(), user_id),
        )

    conn.commit()
    conn.close()


def change_password(user_id, new_password):
    new_hash, new_salt = hash_password(new_password)

    conn = get_db()

    conn.execute(
        """
        UPDATE users
        SET password_hash=?, salt=?
        WHERE id=?
        """,
        (
            new_hash,
            new_salt,
            user_id,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# AUTH PAGE
# ============================================================

def auth_page():

    st.markdown(
        '<div class="auth-wrap">',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="auth-brand">
            <div class="auth-logo">🌿</div>
            <div class="auth-title">SEED Lab</div>
            <div class="auth-subtitle">
                Multimodal Data Quality Control Studio
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(
        ["Sign in", "Create account"]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        st.markdown("### Welcome back")

        email = st.text_input(
            "Email",
            key="login_email",
            placeholder="you@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
            placeholder="Enter your password",
        )

        if st.button(
            "Sign in",
            type="primary",
            use_container_width=True,
        ):

            email_clean = email.strip().lower()

            if not email_clean or not password:
                st.error("Please enter your email and password.")

            else:

                user = get_user_by_email(email_clean)

                if not user:

                    st.error("Invalid email or password.")

                else:

                    valid = verify_password(
                        password,
                        user["password_hash"],
                        user["salt"],
                    )

                    if valid:

                        st.session_state.logged_in = True
                        st.session_state.user_id = user["id"]
                        st.session_state.page = "overview"
                        st.session_state.settings_open = False

                        st.rerun()

                    else:
                        st.error("Invalid email or password.")

    # ========================================================
    # REGISTER
    # ========================================================

    with register_tab:

        st.markdown("### Create your workspace")

        name = st.text_input(
            "Full name",
            key="register_name",
            placeholder="Your name",
        )

        email = st.text_input(
            "Email",
            key="register_email",
            placeholder="you@example.com",
        )

        password = st.text_input(
            "Create password",
            type="password",
            key="register_password",
            placeholder="Minimum 8 characters",
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="register_confirm",
        )

        if st.button(
            "Create account",
            type="primary",
            use_container_width=True,
        ):

            if not name.strip():
                st.error("Please enter your name.")

            elif not email.strip():
                st.error("Please enter your email.")

            elif "@" not in email:
                st.error("Please enter a valid email address.")

            elif len(password) < 8:
                st.error("Password must contain at least 8 characters.")

            elif password != confirm_password:
                st.error("Passwords do not match.")

            else:

                success, user_id = create_user(
                    name,
                    email,
                    password,
                )

                if success:

                    st.success(
                        "Account created successfully. You can now sign in."
                    )

                else:

                    st.error(
                        "An account with this email already exists."
                    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_api_key():

    # Streamlit secrets first
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass

    # Environment fallback
    return os.getenv("GEMINI_API_KEY", "").strip()


def get_gemini_client():

    api_key = get_api_key()

    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def get_model():

    try:
        model = st.secrets.get(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

        if model:
            return str(model)

    except Exception:
        pass

    return os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash",
    )


def get_fallback_models():

    primary = get_model()

    models = [
        primary,
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ]

    result = []

    for model in models:
        if model and model not in result:
            result.append(model)

    return result


# ============================================================
# GEMINI TEXT GENERATION
# ============================================================

def generate_text(prompt, contents=None):

    client = get_gemini_client()

    if client is None:
        return None, "Gemini API key is missing."

    models = get_fallback_models()

    last_error = ""

    for model in models:

        for attempt in range(2):

            try:

                if contents is None:

                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )

                else:

                    response = client.models.generate_content(
                        model=model,
                        contents=contents,
                    )

                text = getattr(response, "text", None)

                if text and text.strip():

                    return text.strip(), None

                last_error = (
                    f"{model} returned an empty response."
                )

            except Exception as exc:

                last_error = str(exc)

                # Small retry delay
                if attempt == 0:
                    time.sleep(1)

    return None, last_error


# ============================================================
# DESCRIPTION LINE NORMALIZATION
# ============================================================

def normalize_description(text, requested_lines):

    if not text:
        return ""

    text = text.strip()

    lines = []

    for line in text.splitlines():

        line = re.sub(
            r"^\s*(?:[-*•]|\d+[.)])\s*",
            "",
            line,
        ).strip()

        if line:
            lines.append(line)

    # If model returned a paragraph, split into sentences.
    if len(lines) <= 1:

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        sentences = [
            s.strip()
            for s in sentences
            if s.strip()
        ]

        if len(sentences) > 1:
            lines = sentences

    lines = lines[:requested_lines]

    while len(lines) < requested_lines:

        if lines:
            lines.append(lines[-1])
        else:
            break

    return "\n".join(
        f"{i + 1}. {line}"
        for i, line in enumerate(lines)
    )


# ============================================================
# IMAGE PROCESSING
# ============================================================

def analyze_image(image, description_lines):

    prompt = f"""
You are a professional multimodal data quality-control assistant.

Analyze the supplied image.

Return ONLY valid JSON with this exact structure:

{{
  "ocr": "all clearly readable text from the image",
  "english_translation": "English translation if the visible text is not English; otherwise write the original readable text",
  "description": [
    "description line 1",
    "description line 2"
  ],
  "confidence": 0.0
}}

Requirements:

1. Generate exactly {description_lines} useful description lines.
2. Do not invent details.
3. Mention only visually supported information.
4. OCR should contain readable text.
5. Confidence must be a number between 0 and 1.
6. Keep description concise.
7. Return JSON only.
"""

    client = get_gemini_client()

    if client is None:
        return None, "Gemini API key is missing."

    for model in get_fallback_models():

        try:

            response = client.models.generate_content(
                model=model,
                contents=[
                    prompt,
                    image,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            raw = getattr(response, "text", None)

            if not raw:
                continue

            data = json.loads(raw)

            description = data.get(
                "description",
                [],
            )

            if isinstance(description, list):

                description_text = "\n".join(
                    f"{i + 1}. {str(x).strip()}"
                    for i, x in enumerate(
                        description[:description_lines]
                    )
                    if str(x).strip()
                )

            else:
                description_text = normalize_description(
                    str(description),
                    description_lines,
                )

            confidence = data.get(
                "confidence",
                0,
            )

            try:
                confidence = float(confidence)

                if confidence <= 1:
                    confidence *= 100

            except Exception:
                confidence = 0

            result = {
                "ocr": str(
                    data.get("ocr", "")
                ).strip(),

                "translation": str(
                    data.get(
                        "english_translation",
                        "",
                    )
                ).strip(),

                "description": description_text,

                "confidence": round(
                    max(0, min(100, confidence)),
                    1,
                ),
            }

            return result, None

        except Exception as exc:

            last_error = str(exc)

    return None, last_error or "Image analysis failed."


# ============================================================
# AUDIO PROCESSING
# ============================================================

def analyze_audio(uploaded_file, description_lines):

    client = get_gemini_client()

    if client is None:
        return None, "Gemini API key is missing."

    try:

        audio_bytes = uploaded_file.getvalue()

        mime_type = uploaded_file.type or "audio/mpeg"

        prompt = f"""
You are a professional audio data quality-control assistant.

Analyze the supplied audio.

Return ONLY valid JSON with this exact structure:

{{
  "transcript": "full understandable transcript",
  "translation": "English translation of the transcript if necessary",
  "description": [
    "description line 1",
    "description line 2"
  ],
  "confidence": 0.0
}}

Requirements:

1. Generate exactly {description_lines} description lines.
2. Do not invent sounds or events.
3. Describe audible content only.
4. Transcript should contain the understandable spoken content.
5. If speech is not present, say that clearly.
6. Translation should be English where possible.
7. Confidence must be between 0 and 1.
8. Return JSON only.
"""

        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type,
        )

        for model in get_fallback_models():

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=[
                        prompt,
                        audio_part,
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )

                raw = getattr(response, "text", None)

                if not raw:
                    continue

                data = json.loads(raw)

                description = data.get(
                    "description",
                    [],
                )

                if isinstance(description, list):

                    description_text = "\n".join(
                        f"{i + 1}. {str(x).strip()}"
                        for i, x in enumerate(
                            description[:description_lines]
                        )
                        if str(x).strip()
                    )

                else:

                    description_text = normalize_description(
                        str(description),
                        description_lines,
                    )

                confidence = data.get(
                    "confidence",
                    0,
                )

                try:

                    confidence = float(confidence)

                    if confidence <= 1:
                        confidence *= 100

                except Exception:

                    confidence = 0

                result = {
                    "transcript": str(
                        data.get(
                            "transcript",
                            "",
                        )
                    ).strip(),

                    "translation": str(
                        data.get(
                            "translation",
                            "",
                        )
                    ).strip(),

                    "description": description_text,

                    "confidence": round(
                        max(
                            0,
                            min(
                                100,
                                confidence,
                            ),
                        ),
                        1,
                    ),
                }

                return result, None

            except Exception as exc:

                last_error = str(exc)

        return None, last_error or "Audio analysis failed."

    except Exception as exc:

        return None, str(exc)


# ============================================================
# QC
# ============================================================

def qc_status(confidence):

    try:
        confidence = float(confidence)
    except Exception:
        confidence = 0

    if confidence >= 80:
        return "PASS"

    return "REVIEW"


# ============================================================
# MANIFEST
# ============================================================

def add_manifest(
    file_name,
    media_type,
    confidence,
    status,
):

    st.session_state.manifest.append(
        {
            "Timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "File": file_name,
            "Type": media_type,
            "Confidence": confidence,
            "QC Status": status,
        }
    )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    user = get_user_by_id(
        st.session_state.user_id
    )

    if not user:
        return

    with st.sidebar:

        st.markdown(
            """
            <div style="
                font-size:25px;
                font-weight:800;
                margin-bottom:2px;
            ">
                🌿 SEED LAB
            </div>

            <div style="
                color:#9ab5a4;
                font-size:12px;
                margin-bottom:18px;
            ">
                Multimodal Data QC Studio
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Profile
        st.markdown(
            '<div class="profile-box">',
            unsafe_allow_html=True,
        )

        profile_path = user["profile_image"]

        if (
            profile_path
            and Path(profile_path).exists()
        ):

            st.image(
                profile_path,
                width=55,
            )

        st.markdown(
            f"""
            <div style="
                margin-top:7px;
                font-weight:700;
            ">
                {user["name"]}
            </div>

            <div style="
                color:#9ab5a4;
                font-size:11px;
                margin-top:2px;
            ">
                {user["email"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sidebar-label">WORKSPACE</div>',
            unsafe_allow_html=True,
        )

        if st.button(
            "▣  Overview",
            use_container_width=True,
        ):
            st.session_state.page = "overview"
            st.session_state.settings_open = False
            st.rerun()

        if st.button(
            "◈  Image Data Studio",
            use_container_width=True,
        ):
            st.session_state.page = "image"
            st.session_state.settings_open = False
            st.rerun()

        if st.button(
            "◉  Audio Data Studio",
            use_container_width=True,
        ):
            st.session_state.page = "audio"
            st.session_state.settings_open = False
            st.rerun()

        if st.button(
            "◫  Auditor Console",
            use_container_width=True,
        ):
            st.session_state.page = "auditor"
            st.session_state.settings_open = False
            st.rerun()

        st.divider()

        # Settings
        if st.button(
            "⚙  Settings",
            use_container_width=True,
        ):

            st.session_state.settings_open = (
                not st.session_state.settings_open
            )

            st.rerun()

        if st.session_state.settings_open:

            st.markdown(
                """
                <div style="
                    color:#9ab5a4;
                    font-size:11px;
                    margin:8px 0;
                ">
                    SETTINGS
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "👤  Profile",
                use_container_width=True,
            ):

                st.session_state.page = "profile"
                st.rerun()

            if st.button(
                "🔐  Account",
                use_container_width=True,
            ):

                st.session_state.page = "account"
                st.rerun()

        st.divider()

        st.caption(
            "SEED Lab Multimodal Studio"
        )

        st.caption(
            "Secure workspace"
        )


# ============================================================
# OVERVIEW
# ============================================================

def overview_page(user):

    st.markdown(
        """
        <div class="hero">

            <div style="
                color:#178348;
                font-size:12px;
                font-weight:800;
                letter-spacing:.08em;
                text-transform:uppercase;
            ">
                SEED LAB WORKSPACE
            </div>

            <h1 style="margin-bottom:5px;">
                Multimodal Data Quality Studio
            </h1>

            <div class="hero-small">
                Process images and audio, generate structured
                annotations, and perform quality control from
                one professional workspace.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    total = len(
        st.session_state.manifest
    )

    passed = sum(
        1
        for x in st.session_state.manifest
        if x.get("QC Status") == "PASS"
    )

    review = sum(
        1
        for x in st.session_state.manifest
        if x.get("QC Status") == "REVIEW"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Files Processed",
            total,
        )

    with c2:
        st.metric(
            "QC Passed",
            passed,
        )

    with c3:
        st.metric(
            "Needs Review",
            review,
        )

    st.markdown("## Workspaces")

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="seed-card">

                <div class="seed-card-title">
                    ◈ Image Data Studio
                </div>

                <div class="seed-card-subtitle">
                    OCR, translation, visual descriptions
                    and image quality control.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Image Studio →",
            key="open_image",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.page = "image"
            st.rerun()

    with c2:

        st.markdown(
            """
            <div class="seed-card">

                <div class="seed-card-title">
                    ◉ Audio Data Studio
                </div>

                <div class="seed-card-subtitle">
                    Transcription, translation, audio
                    descriptions and quality control.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Audio Studio →",
            key="open_audio",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.page = "audio"
            st.rerun()

    if st.session_state.manifest:

        st.markdown("## Recent Activity")

        df = pd.DataFrame(
            st.session_state.manifest
        )

        st.dataframe(
            df.tail(10),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# IMAGE STUDIO
# ============================================================

def image_page():

    st.title("Image Data Studio")

    st.caption(
        "OCR • Translation • Visual Description • Quality Control"
    )

    col1, col2 = st.columns(
        [1.35, 0.65],
        gap="large",
    )

    with col1:

        uploaded = st.file_uploader(
            "Upload image",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key="image_upload",
        )

        if uploaded:

            image = Image.open(uploaded)

            st.image(
                image,
                caption=uploaded.name,
                use_container_width=True,
            )

    with col2:

        description_lines = st.number_input(
            "Description lines required",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            key="image_description_lines",
        )

        st.caption(
            "The AI will generate the requested number "
            "of description lines."
        )

        analyze = st.button(
            "Analyze Image",
            type="primary",
            use_container_width=True,
            disabled=uploaded is None,
        )

    if analyze and uploaded:

        with st.spinner(
            "Analyzing image..."
        ):

            image = Image.open(
                uploaded
            ).convert("RGB")

            result, error = analyze_image(
                image,
                int(description_lines),
            )

        if result:

            st.session_state.image_result = result

            status = qc_status(
                result.get(
                    "confidence",
                    0,
                )
            )

            add_manifest(
                uploaded.name,
                "Image",
                result.get(
                    "confidence",
                    0,
                ),
                status,
            )

            st.success(
                "Image analysis completed."
            )

        else:

            st.error(
                "Image analysis failed."
            )

            if error:
                st.code(
                    error,
                    language=None,
                )

    result = st.session_state.image_result

    if result:

        st.markdown("---")

        confidence = result.get(
            "confidence",
            0,
        )

        status = qc_status(
            confidence
        )

        st.markdown("## Analysis Results")

        c1, c2 = st.columns(
            [1, 3]
        )

        with c1:

            st.metric(
                "Confidence",
                f"{confidence:.1f}%",
            )

        with c2:

            if status == "PASS":

                st.markdown(
                    '<span class="status-pass">✓ PASS</span>',
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    '<span class="status-review">! REVIEW</span>',
                    unsafe_allow_html=True,
                )

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                """
                <div class="result-box">
                    <div class="result-label">
                        OCR
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(
                result.get(
                    "ocr",
                    "",
                )
                or "No readable text detected."
            )

        with c2:

            st.markdown(
                """
                <div class="result-box">
                    <div class="result-label">
                        English Translation
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(
                result.get(
                    "translation",
                    "",
                )
                or "No translation required."
            )

        st.markdown(
            """
            <div class="result-box">
                <div class="result-label">
                    AI Image Description
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.text(
            result.get(
                "description",
                "",
            )
        )


# ============================================================
# AUDIO STUDIO
# ============================================================

def audio_page():

    st.title("Audio Data Studio")

    st.caption(
        "Transcription • Translation • Audio Description • Quality Control"
    )

    col1, col2 = st.columns(
        [1.35, 0.65],
        gap="large",
    )

    with col1:

        uploaded = st.file_uploader(
            "Upload audio",
            type=[
                "mp3",
                "wav",
                "m4a",
                "aac",
                "ogg",
                "flac",
            ],
            key="audio_upload",
        )

        if uploaded:

            st.audio(
                uploaded,
                format=uploaded.type,
            )

            size_mb = len(
                uploaded.getvalue()
            ) / (
                1024 * 1024
            )

            st.caption(
                f"{uploaded.name} • "
                f"{size_mb:.2f} MB"
            )

    with col2:

        description_lines = st.number_input(
            "Description lines required",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            key="audio_description_lines",
        )

        st.caption(
            "The AI will generate the requested number "
            "of audio description lines."
        )

        analyze = st.button(
            "Analyze Audio",
            type="primary",
            use_container_width=True,
            disabled=uploaded is None,
        )

    if analyze and uploaded:

        with st.spinner(
            "Processing audio..."
        ):

            result, error = analyze_audio(
                uploaded,
                int(description_lines),
            )

        if result:

            st.session_state.audio_result = result

            status = qc_status(
                result.get(
                    "confidence",
                    0,
                )
            )

            add_manifest(
                uploaded.name,
                "Audio",
                result.get(
                    "confidence",
                    0,
                ),
                status,
            )

            st.success(
                "Audio analysis completed."
            )

        else:

            st.error(
                "Audio analysis failed."
            )

            if error:
                st.code(
                    error,
                    language=None,
                )

    result = st.session_state.audio_result

    if result:

        st.markdown("---")

        confidence = result.get(
            "confidence",
            0,
        )

        status = qc_status(
            confidence
        )

        st.markdown("## Analysis Results")

        c1, c2 = st.columns(
            [1, 3]
        )

        with c1:

            st.metric(
                "Confidence",
                f"{confidence:.1f}%",
            )

        with c2:

            if status == "PASS":

                st.markdown(
                    '<span class="status-pass">✓ PASS</span>',
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    '<span class="status-review">! REVIEW</span>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            """
            <div class="result-box">
                <div class="result-label">
                    Live Audio Transcript
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.text(
            result.get(
                "transcript",
                "",
            )
            or "No speech detected."
        )

        st.markdown(
            """
            <div class="result-box">
                <div class="result-label">
                    English Translation
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.text(
            result.get(
                "translation",
                "",
            )
            or "No translation available."
        )

        st.markdown(
            """
            <div class="result-box">
                <div class="result-label">
                    AI Audio Description
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.text(
            result.get(
                "description",
                "",
            )
            or "No description generated."
        )


# ============================================================
# AUDITOR CONSOLE
# ============================================================

def auditor_page():

    st.title("Auditor Console")

    st.caption(
        "Review processed files and quality-control results."
    )

    if not st.session_state.manifest:

        st.info(
            "No processed files yet."
        )

        return

    df = pd.DataFrame(
        st.session_state.manifest
    )

    total = len(df)

    passed = len(
        df[
            df["QC Status"] == "PASS"
        ]
    )

    review = len(
        df[
            df["QC Status"] == "REVIEW"
        ]
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Total",
            total,
        )

    with c2:
        st.metric(
            "Passed",
            passed,
        )

    with c3:
        st.metric(
            "Review",
            review,
        )

    st.markdown("## Processing Manifest")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download CSV Manifest",
        data=csv_data,
        file_name="seed_lab_manifest.csv",
        mime="text/csv",
        type="primary",
    )


# ============================================================
# PROFILE
# ============================================================

def profile_page(user):

    st.title("Profile")

    st.caption(
        "Manage your SEED Lab workspace profile."
    )

    col1, col2 = st.columns(
        [0.35, 0.65],
        gap="large",
    )

    with col1:

        if (
            user["profile_image"]
            and Path(
                user["profile_image"]
            ).exists()
        ):

            st.image(
                user["profile_image"],
                width=180,
            )

        else:

            st.markdown(
                """
                <div style="
                    width:180px;
                    height:180px;
                    border-radius:50%;
                    background:#e8f2eb;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:65px;
                ">
                    👤
                </div>
                """,
                unsafe_allow_html=True,
            )

        uploaded = st.file_uploader(
            "Profile picture",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key="profile_picture",
        )

    with col2:

        name = st.text_input(
            "Full name",
            value=user["name"],
            key="profile_name",
        )

        st.text_input(
            "Email",
            value=user["email"],
            disabled=True,
        )

        st.text_input(
            "Account created",
            value=user["created_at"],
            disabled=True,
        )

        if st.button(
            "Save profile",
            type="primary",
        ):

            image_path = None

            if uploaded:

                extension = Path(
                    uploaded.name
                ).suffix.lower()

                image_path = str(
                    PROFILE_DIR
                    / f"user_{user['id']}{extension}"
                )

                with open(
                    image_path,
                    "wb",
                ) as file:

                    file.write(
                        uploaded.getvalue()
                    )

            update_profile(
                user["id"],
                name,
                image_path,
            )

            st.success(
                "Profile updated successfully."
            )

            st.rerun()


# ============================================================
# ACCOUNT
# ============================================================

def account_page(user):

    st.title("Account")

    st.caption(
        "Security and account controls."
    )

    st.markdown(
        '<div class="seed-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### Account information"
    )

    st.write(
        f"**Name:** {user['name']}"
    )

    st.write(
        f"**Email:** {user['email']}"
    )

    st.write(
        f"**Created:** {user['created_at']}"
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("## Change password")

    current_password = st.text_input(
        "Current password",
        type="password",
        key="current_password",
    )

    new_password = st.text_input(
        "New password",
        type="password",
        key="new_password",
    )

    confirm_password = st.text_input(
        "Confirm new password",
        type="password",
        key="confirm_new_password",
    )

    if st.button(
        "Update password",
        type="primary",
    ):

        valid = verify_password(
            current_password,
            user["password_hash"],
            user["salt"],
        )

        if not valid:

            st.error(
                "Current password is incorrect."
            )

        elif len(new_password) < 8:

            st.error(
                "New password must contain at least 8 characters."
            )

        elif new_password != confirm_password:

            st.error(
                "New passwords do not match."
            )

        else:

            change_password(
                user["id"],
                new_password,
            )

            st.success(
                "Password updated successfully."
            )

    st.markdown("---")

    st.markdown("## Session")

    if st.button(
        "Log out",
        use_container_width=True,
    ):

        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.page = "overview"
        st.session_state.settings_open = False
        st.session_state.image_result = None
        st.session_state.audio_result = None
        st.session_state.manifest = []

        st.rerun()


# ============================================================
# MAIN APP
# ============================================================

if not st.session_state.logged_in:

    auth_page()

    st.stop()


# ============================================================
# USER
# ============================================================

user = get_user_by_id(
    st.session_state.user_id
)

if not user:

    st.session_state.logged_in = False
    st.session_state.user_id = None

    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

sidebar()


# ============================================================
# ROUTING
# ============================================================

page = st.session_state.page

if page == "overview":

    overview_page(user)

elif page == "image":

    image_page()

elif page == "audio":

    audio_page()

elif page == "auditor":

    auditor_page()

elif page == "profile":

    profile_page(user)

elif page == "account":

    account_page(user)

else:

    st.session_state.page = "overview"

    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🌿 SEED Lab Multimodal Studio
        • Secure Multimodal Data Quality Control
    </div>
    """,
    unsafe_allow_html=True,
)