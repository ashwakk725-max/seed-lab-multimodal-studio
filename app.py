import io
import json
import os
import re
import sqlite3
import time
import hashlib
import hmac
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
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

DATA_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)


# ============================================================
# GREEN THEME
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #f3faf7;
        color: #17352d;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #d8ebe3;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #174d3b !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: #3f5f55 !important;
    }

    h1 {
        color: #174d3b !important;
        font-weight: 750 !important;
    }

    h2 {
        color: #1c5843 !important;
    }

    h3 {
        color: #24634d !important;
    }

    p {
        color: #3f5f55;
    }

    [data-testid="stCaptionContainer"] {
        color: #6b837a !important;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #d7ebe2;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 3px 12px rgba(28, 91, 67, 0.06);
    }

    [data-testid="stMetricLabel"] {
        color: #668078 !important;
    }

    [data-testid="stMetricValue"] {
        color: #174d3b !important;
    }

    [data-testid="stFileUploader"] {
        background: #ffffff;
        border: 1px dashed #82b9a3;
        border-radius: 14px;
        padding: 10px;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: #f8fcfa;
        border-radius: 12px;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 650;
        background: #ffffff;
        color: #1b5944 !important;
        border: 1px solid #9cc8b5;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #249568;
        color: #18734f !important;
        background: #f2fbf6;
    }

    .stButton > button[kind="primary"] {
        background: #19a66b !important;
        color: #ffffff !important;
        border: 1px solid #15945f !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #148d59 !important;
        color: #ffffff !important;
    }

    input,
    textarea {
        background: #ffffff !important;
        color: #183c31 !important;
    }

    textarea {
        border: 1px solid #cfe4da !important;
        border-radius: 10px !important;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background: #ffffff !important;
        color: #183c31 !important;
        border-color: #cfe4da !important;
    }

    [data-baseweb="select"] > div {
        background: #ffffff !important;
        border-color: #cfe4da !important;
        color: #183c31 !important;
    }

    [data-testid="stRadio"] label {
        color: #24483d !important;
    }

    button[data-baseweb="tab"] {
        color: #5a7169 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #168457 !important;
        font-weight: 700;
    }

    [data-testid="stDataFrame"] {
        background: #ffffff;
        border: 1px solid #d7ebe2;
        border-radius: 12px;
    }

    [data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #d7ebe2;
        border-radius: 12px;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    hr {
        border-color: #d7ebe2 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_database():

    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            profile_picture TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


init_database()


# ============================================================
# PASSWORD SECURITY
# ============================================================

def hash_password(password):

    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120000,
    )

    return (
        base64.b64encode(password_hash).decode(),
        base64.b64encode(salt).decode(),
    )


def verify_password(
    password,
    stored_hash,
    stored_salt,
):

    try:

        salt = base64.b64decode(
            stored_salt
        )

        expected_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            120000,
        )

        expected_hash = base64.b64encode(
            expected_hash
        ).decode()

        return hmac.compare_digest(
            expected_hash,
            stored_hash,
        )

    except Exception:

        return False


# ============================================================
# USER DATABASE FUNCTIONS
# ============================================================

def create_user(
    name,
    email,
    password,
    profile_picture=None,
):

    conn = get_connection()

    try:

        password_hash, salt = hash_password(
            password
        )

        created_at = time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor = conn.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash,
                salt,
                profile_picture,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                email.strip().lower(),
                password_hash,
                salt,
                profile_picture,
                created_at,
            ),
        )

        conn.commit()

        user_id = cursor.lastrowid

        return user_id, None

    except sqlite3.IntegrityError:

        return None, "An account with this email already exists."

    except Exception as error:

        return None, str(error)

    finally:

        conn.close()


def authenticate_user(
    email,
    password,
):

    conn = get_connection()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (
            email.strip().lower(),
        ),
    ).fetchone()

    conn.close()

    if not user:

        return None

    if verify_password(
        password,
        user["password_hash"],
        user["salt"],
    ):

        return dict(user)

    return None


def get_user(user_id):

    conn = get_connection()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()

    conn.close()

    if user:

        return dict(user)

    return None


def update_user(
    user_id,
    name,
    profile_picture=None,
):

    conn = get_connection()

    if profile_picture is not None:

        conn.execute(
            """
            UPDATE users
            SET name = ?,
                profile_picture = ?
            WHERE id = ?
            """,
            (
                name.strip(),
                profile_picture,
                user_id,
            ),
        )

    else:

        conn.execute(
            """
            UPDATE users
            SET name = ?
            WHERE id = ?
            """,
            (
                name.strip(),
                user_id,
            ),
        )

    conn.commit()
    conn.close()


def change_password(
    user_id,
    new_password,
):

    password_hash, salt = hash_password(
        new_password
    )

    conn = get_connection()

    conn.execute(
        """
        UPDATE users
        SET password_hash = ?,
            salt = ?
        WHERE id = ?
        """,
        (
            password_hash,
            salt,
            user_id,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "auth_page" not in st.session_state:
    st.session_state.auth_page = "Login"

if "image_result" not in st.session_state:
    st.session_state.image_result = None

if "audio_result" not in st.session_state:
    st.session_state.audio_result = None

if "manifest" not in st.session_state:
    st.session_state.manifest = []

if "app_mode" not in st.session_state:
    st.session_state.app_mode = "Image Data Studio"

if "settings_open" not in st.session_state:
    st.session_state.settings_open = False


# ============================================================
# AUTHENTICATION SCREEN
# ============================================================

def authentication_screen():

    st.markdown(
        "",
        unsafe_allow_html=True,
    )

    st.title(
        "🌿 SEED Lab"
    )

    st.subheader(
        "Multimodal Data QC Studio"
    )

    st.caption(
        "Secure workspace for multimodal data annotation and quality control."
    )

    st.divider()

    login_tab, register_tab = st.tabs(
        [
            "Login",
            "Create Account",
        ]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        st.subheader(
            "Welcome back"
        )

        email = st.text_input(
            "Email",
            placeholder="you@example.com",
            key="login_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password",
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
        ):

            if not email or not password:

                st.warning(
                    "Please enter your email and password."
                )

            else:

                user = authenticate_user(
                    email,
                    password,
                )

                if user:

                    st.session_state.logged_in = True
                    st.session_state.user_id = user["id"]
                    st.session_state.auth_page = "Login"

                    st.success(
                        "Login successful."
                    )

                    time.sleep(0.5)

                    st.rerun()

                else:

                    st.error(
                        "Invalid email or password."
                    )

    # ========================================================
    # REGISTER
    # ========================================================

    with register_tab:

        st.subheader(
            "Create your SEED Lab account"
        )

        name = st.text_input(
            "Full name",
            placeholder="Enter your name",
            key="register_name",
        )

        email = st.text_input(
            "Email address",
            placeholder="you@example.com",
            key="register_email",
        )

        password = st.text_input(
            "Create password",
            type="password",
            placeholder="Create a secure password",
            key="register_password",
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            placeholder="Re-enter your password",
            key="register_confirm_password",
        )

        profile_picture = st.file_uploader(
            "Profile picture (optional)",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
            key="register_profile_picture",
        )

        if profile_picture:

            st.image(
                profile_picture,
                width=140,
            )

        if st.button(
            "Create Account",
            type="primary",
            use_container_width=True,
        ):

            if not name.strip():

                st.warning(
                    "Please enter your name."
                )

            elif not email.strip():

                st.warning(
                    "Please enter your email."
                )

            elif "@" not in email:

                st.warning(
                    "Please enter a valid email address."
                )

            elif len(password) < 8:

                st.warning(
                    "Password must contain at least 8 characters."
                )

            elif password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                saved_picture = None

                if profile_picture:

                    extension = (
                        Path(
                            profile_picture.name
                        ).suffix.lower()
                    )

                    filename = (
                        f"pending_{int(time.time())}{extension}"
                    )

                    picture_path = (
                        PROFILE_DIR / filename
                    )

                    with open(
                        picture_path,
                        "wb",
                    ) as file:

                        file.write(
                            profile_picture.getvalue()
                        )

                    saved_picture = str(
                        picture_path
                    )

                user_id, error = create_user(
                    name,
                    email,
                    password,
                    saved_picture,
                )

                if error:

                    if saved_picture:

                        try:
                            os.remove(
                                saved_picture
                            )
                        except Exception:
                            pass

                    st.error(error)

                else:

                    st.success(
                        "Account created successfully. You can now log in."
                    )


# ============================================================
# SHOW LOGIN IF NOT AUTHENTICATED
# ============================================================

if not st.session_state.logged_in:

    authentication_screen()

    st.stop()


# ============================================================
# CURRENT USER
# ============================================================

current_user = get_user(
    st.session_state.user_id
)

if not current_user:

    st.session_state.logged_in = False
    st.session_state.user_id = None

    st.rerun()


# ============================================================
# PROFILE IMAGE HELPER
# ============================================================

def display_profile_picture(
    user,
    width=80,
):

    picture = user.get(
        "profile_picture"
    )

    if picture and os.path.exists(
        picture
    ):

        try:

            st.image(
                picture,
                width=width,
            )

            return

        except Exception:
            pass

    st.write("👤")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "🌿 SEED Lab"
    )

    st.caption(
        "Multimodal Data QC Studio"
    )

    st.divider()

    display_profile_picture(
        current_user,
        width=75,
    )

    st.write(
        f"**{current_user['name']}**"
    )

    st.caption(
        current_user["email"]
    )

    st.divider()

    st.subheader(
        "Studio"
    )

    selected_mode = st.radio(
        "Workspace",
        [
            "Image Data Studio",
            "Audio Data Studio",
            "Auditor Console",
        ],
        index=[
            "Image Data Studio",
            "Audio Data Studio",
            "Auditor Console",
        ].index(
            st.session_state.app_mode
        ),
        label_visibility="collapsed",
    )

    st.session_state.app_mode = selected_mode

    st.divider()

    # ========================================================
    # SETTINGS AT BOTTOM LEFT
    # ========================================================

    st.subheader(
        "⚙️ Settings"
    )

    settings_choice = st.radio(
        "Settings",
        [
            "Profile",
            "Account",
        ],
        label_visibility="collapsed",
    )

    if settings_choice == "Profile":

        if st.button(
            "Open Profile",
            use_container_width=True,
        ):

            st.session_state.settings_open = True

    if settings_choice == "Account":

        if st.button(
            "Logout",
            use_container_width=True,
        ):

            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.image_result = None
            st.session_state.audio_result = None
            st.session_state.manifest = []

            st.rerun()

    st.divider()

    st.caption(
        "SEED Lab Multimodal Studio"
    )

    st.caption(
        "Secure user workspace"
    )


# ============================================================
# PROFILE / SETTINGS PAGE
# ============================================================

if st.session_state.settings_open:

    st.title(
        "Profile & Settings"
    )

    st.caption(
        "Manage your personal profile and account settings."
    )

    if st.button(
        "← Back to Dashboard"
    ):

        st.session_state.settings_open = False

        st.rerun()

    st.divider()

    profile_tab, account_tab = st.tabs(
        [
            "Profile",
            "Account Security",
        ]
    )

    # ========================================================
    # PROFILE
    # ========================================================

    with profile_tab:

        st.subheader(
            "Your Profile"
        )

        left, right = st.columns(
            [1, 2]
        )

        with left:

            display_profile_picture(
                current_user,
                width=180,
            )

        with right:

            st.write(
                f"**Email:** {current_user['email']}"
            )

            st.write(
                f"**Account created:** {current_user['created_at']}"
            )

        st.divider()

        new_name = st.text_input(
            "Name",
            value=current_user["name"],
        )

        new_picture = st.file_uploader(
            "Change profile picture",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
        )

        if new_picture:

            st.image(
                new_picture,
                width=180,
            )

        if st.button(
            "Save Profile",
            type="primary",
        ):

            picture_path = None

            if new_picture:

                extension = (
                    Path(
                        new_picture.name
                    ).suffix.lower()
                )

                filename = (
                    f"user_{current_user['id']}_{int(time.time())}{extension}"
                )

                picture_path = (
                    PROFILE_DIR / filename
                )

                with open(
                    picture_path,
                    "wb",
                ) as file:

                    file.write(
                        new_picture.getvalue()
                    )

                picture_path = str(
                    picture_path
                )

            update_user(
                current_user["id"],
                new_name,
                picture_path,
            )

            st.success(
                "Profile updated successfully."
            )

            time.sleep(0.5)

            st.rerun()

    # ========================================================
    # ACCOUNT SECURITY
    # ========================================================

    with account_tab:

        st.subheader(
            "Change Password"
        )

        new_password = st.text_input(
            "New password",
            type="password",
        )

        confirm_new_password = st.text_input(
            "Confirm new password",
            type="password",
        )

        if st.button(
            "Change Password",
            type="primary",
        ):

            if len(new_password) < 8:

                st.warning(
                    "Password must contain at least 8 characters."
                )

            elif new_password != confirm_new_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                change_password(
                    current_user["id"],
                    new_password,
                )

                st.success(
                    "Password changed successfully."
                )

    st.stop()


# ============================================================
# GEMINI CONFIG
# ============================================================

API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    "",
)

if API_KEY:

    client = genai.Client(
        api_key=API_KEY
    )

else:

    client = None


PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]


# ============================================================
# GEMINI HELPERS
# ============================================================

def retryable(error):

    message = str(error).lower()

    words = [
        "503",
        "unavailable",
        "high demand",
        "overloaded",
        "429",
        "rate limit",
        "resource exhausted",
        "temporarily",
        "timeout",
    ]

    return any(
        word in message
        for word in words
    )


def response_text(response):

    if response is None:
        return ""

    try:

        text = getattr(
            response,
            "text",
            None,
        )

        if text:
            return str(text).strip()

    except Exception:
        pass

    try:

        candidates = getattr(
            response,
            "candidates",
            [],
        )

        if candidates:

            content = getattr(
                candidates[0],
                "content",
                None,
            )

            if content:

                parts = getattr(
                    content,
                    "parts",
                    [],
                )

                output = []

                for part in parts:

                    text_part = getattr(
                        part,
                        "text",
                        None,
                    )

                    if text_part:

                        output.append(
                            str(text_part)
                        )

                return "\n".join(
                    output
                ).strip()

    except Exception:
        pass

    return ""


def parse_json(text):

    if not text:
        return None

    cleaned = text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    try:

        return json.loads(
            cleaned
        )

    except Exception:
        pass

    start = cleaned.find(
        "{"
    )

    end = cleaned.rfind(
        "}"
    )

    if start != -1 and end != -1:

        try:

            return json.loads(
                cleaned[
                    start:end + 1
                ]
            )

        except Exception:
            pass

    return None


def text_value(
    data,
    key,
    default="",
):

    if not isinstance(
        data,
        dict,
    ):

        return default

    value = data.get(
        key,
        default,
    )

    if value is None:
        return default

    return str(value).strip()


def description_lines(data):

    if not isinstance(
        data,
        dict,
    ):

        return []

    value = data.get(
        "description_lines",
        [],
    )

    if isinstance(
        value,
        list,
    ):

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(
        value,
        str,
    ):

        return [
            line.strip()
            for line in value.splitlines()
            if line.strip()
        ]

    return []


def confidence(data):

    if not isinstance(
        data,
        dict,
    ):

        return None

    value = data.get(
        "confidence"
    )

    if value is None:
        return None

    try:

        number = float(value)

        if number <= 1:
            number *= 100

        return max(
            0,
            min(100, number),
        )

    except Exception:

        return None


def json_config():

    return types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    )


def generate_with_fallback(
    contents
):

    if client is None:

        return (
            None,
            None,
            "GEMINI_API_KEY is not configured.",
        )

    models = [
        PRIMARY_MODEL
    ] + FALLBACK_MODELS

    last_error = None

    for model_index, model in enumerate(
        models
    ):

        for attempt in range(2):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=json_config(),
                )

                if response_text(
                    response
                ):

                    return (
                        response,
                        model,
                        None,
                    )

                last_error = (
                    "Gemini returned an empty response."
                )

            except Exception as error:

                last_error = str(error)

                if not retryable(error):
                    break

                if attempt == 0:
                    time.sleep(2)

        if model_index < len(models) - 1:
            time.sleep(1)

    return (
        None,
        None,
        last_error or "Gemini request failed.",
    )


def add_manifest(
    mode,
    filename,
    requested_lines,
    actual_lines,
    model,
):

    st.session_state.manifest.append(
        {
            "Timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "User": current_user["email"],
            "Mode": mode,
            "File": filename,
            "Requested Lines": requested_lines,
            "Actual Lines": actual_lines,
            "QC": (
                "PASS"
                if requested_lines == actual_lines
                else "FAIL"
            ),
            "Model": model or "Unknown",
        }
    )


# ============================================================
# MAIN DASHBOARD HEADER
# ============================================================

st.title(
    "SEED Lab Multimodal Studio"
)

st.caption(
    f"Welcome, {current_user['name']} • Unified multimodal data annotation and quality-control workspace"
)

st.divider()


# ============================================================
# API WARNING
# ============================================================

if not API_KEY:

    st.warning(
        "GEMINI_API_KEY is not configured. "
        "Add it to Streamlit Secrets before running AI analysis."
    )


# ============================================================
# IMAGE DATA STUDIO
# ============================================================

if st.session_state.app_mode == "Image Data Studio":

    st.header(
        "Image Data Studio"
    )

    st.caption(
        "OCR • Translation • Visual Description • Quality Control"
    )

    upload_col, lines_col = st.columns(
        [2, 1]
    )

    with upload_col:

        image_file = st.file_uploader(
            "Upload image",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
                "bmp",
            ],
            key="image_uploader",
        )

    with lines_col:

        image_description_count = st.number_input(
            "Description lines required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
            key="image_description_count",
        )

    if image_file:

        image_bytes = image_file.getvalue()

        try:

            image = Image.open(
                io.BytesIO(
                    image_bytes
                )
            )

        except Exception as error:

            st.error(
                f"Could not open image: {error}"
            )

            image = None

        if image:

            st.divider()

            preview_col, info_col = st.columns(
                [1.4, 1]
            )

            with preview_col:

                st.subheader(
                    "Image Preview"
                )

                st.image(
                    image,
                    use_container_width=True,
                )

            with info_col:

                st.subheader(
                    "File Information"
                )

                st.metric(
                    "File size",
                    f"{len(image_bytes) / 1024:.1f} KB",
                )

                st.metric(
                    "Resolution",
                    f"{image.width} × {image.height}",
                )

                st.metric(
                    "Description lines",
                    image_description_count,
                )

            st.divider()

            if st.button(
                "Analyze Image",
                type="primary",
                use_container_width=True,
            ):

                if not API_KEY:

                    st.error(
                        "Gemini API key is missing."
                    )

                else:

                    prompt = f"""
You are a professional multimodal data annotation and quality-control assistant.

Analyze the uploaded image.

Return ONLY valid JSON:

{{
  "ocr_text": "all clearly readable text",
  "translation": "English translation of readable text",
  "description_lines": [
    "line 1",
    "line 2"
  ],
  "confidence": 0.0
}}

Rules:

1. description_lines MUST contain exactly {image_description_count} separate lines.
2. Every line must contain useful visual information.
3. Do not number the lines.
4. Do not combine multiple lines.
5. Extract readable text accurately.
6. If no readable text exists, use an empty string.
7. Translate extracted text into English.
8. If translation is not applicable, use an empty string.
9. confidence must be a number from 0 to 1.
10. Return JSON only.
"""

                    with st.spinner(
                        "Analyzing image..."
                    ):

                        response, model_used, error = (
                            generate_with_fallback(
                                [
                                    prompt,
                                    image,
                                ]
                            )
                        )

                    if error:

                        st.error(
                            f"Image analysis failed: {error}"
                        )

                    else:

                        raw = response_text(
                            response
                        )

                        result = parse_json(
                            raw
                        )

                        if result is None:

                            st.error(
                                "Gemini response could not be parsed."
                            )

                            with st.expander(
                                "Developer Response"
                            ):

                                st.code(
                                    raw or "EMPTY RESPONSE"
                                )

                        else:

                            st.session_state.image_result = {
                                "data": result,
                                "model": model_used,
                                "filename": image_file.name,
                            }

                            add_manifest(
                                "Image",
                                image_file.name,
                                image_description_count,
                                len(
                                    description_lines(
                                        result
                                    )
                                ),
                                model_used,
                            )

                            st.success(
                                "Image analysis completed."
                            )

            # =================================================
            # IMAGE RESULTS
            # =================================================

            if st.session_state.image_result:

                result = (
                    st.session_state.image_result
                    .get(
                        "data",
                        {},
                    )
                )

                ocr = text_value(
                    result,
                    "ocr_text",
                )

                translation = text_value(
                    result,
                    "translation",
                )

                lines = description_lines(
                    result
                )

                conf = confidence(
                    result
                )

                st.divider()

                st.header(
                    "Image Analysis Results"
                )

                c1, c2, c3 = st.columns(3)

                with c1:

                    st.metric(
                        "OCR",
                        (
                            "Available"
                            if ocr
                            else "No text"
                        ),
                    )

                with c2:

                    st.metric(
                        "Translation",
                        (
                            "Available"
                            if translation
                            else "N/A"
                        ),
                    )

                with c3:

                    st.metric(
                        "Confidence",
                        (
                            f"{conf:.1f}%"
                            if conf is not None
                            else "Not supplied"
                        ),
                    )

                left, right = st.columns(2)

                with left:

                    st.subheader(
                        "OCR Text"
                    )

                    st.text_area(
                        "OCR",
                        value=(
                            ocr
                            if ocr
                            else "No readable text detected."
                        ),
                        height=220,
                        disabled=True,
                        label_visibility="collapsed",
                    )

                with right:

                    st.subheader(
                        "Translation"
                    )

                    st.text_area(
                        "Translation",
                        value=(
                            translation
                            if translation
                            else "No translation available."
                        ),
                        height=220,
                        disabled=True,
                        label_visibility="collapsed",
                    )

                st.divider()

                st.subheader(
                    f"AI Visual Description ({image_description_count} lines requested)"
                )

                for index, line in enumerate(
                    lines,
                    start=1,
                ):

                    st.write(
                        f"**{index}.** {line}"
                    )

                st.divider()

                st.subheader(
                    "Quality Control"
                )

                actual_count = len(
                    lines
                )

                q1, q2, q3 = st.columns(3)

                with q1:

                    if (
                        actual_count
                        == image_description_count
                    ):

                        st.success(
                            f"Description count: PASS ({actual_count})"
                        )

                    else:

                        st.error(
                            f"Description count: FAIL ({actual_count}/{image_description_count})"
                        )

                with q2:

                    if ocr:
                        st.success(
                            "OCR: PASS"
                        )
                    else:
                        st.info(
                            "OCR: No readable text"
                        )

                with q3:

                    if translation:
                        st.success(
                            "Translation: PASS"
                        )
                    else:
                        st.info(
                            "Translation: N/A"
                        )


# ============================================================
# AUDIO DATA STUDIO
# ============================================================

elif st.session_state.app_mode == "Audio Data Studio":

    st.header(
        "Audio Data Studio"
    )

    st.caption(
        "Transcription • Translation • Audio Description • Quality Control"
    )

    upload_col, lines_col = st.columns(
        [2, 1]
    )

    with upload_col:

        audio_file = st.file_uploader(
            "Upload audio",
            type=[
                "mp3",
                "wav",
                "m4a",
                "aac",
                "ogg",
                "flac",
            ],
            key="audio_uploader",
        )

    with lines_col:

        audio_description_count = st.number_input(
            "Description lines required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
            key="audio_description_count",
        )

    if audio_file:

        audio_bytes = audio_file.getvalue()

        st.divider()

        a1, a2, a3 = st.columns(3)

        with a1:

            st.metric(
                "File size",
                f"{len(audio_bytes) / (1024 * 1024):.2f} MB",
            )

        with a2:

            st.metric(
                "Format",
                audio_file.type or "Unknown",
            )

        with a3:

            st.metric(
                "Description lines",
                audio_description_count,
            )

        st.subheader(
            "Audio Preview"
        )

        st.audio(
            audio_bytes,
            format=audio_file.type,
        )

        st.divider()

        if st.button(
            "Analyze Audio",
            type="primary",
            use_container_width=True,
        ):

            if not API_KEY:

                st.error(
                    "Gemini API key is missing."
                )

            else:

                uploaded_file = None

                with st.spinner(
                    "Uploading audio..."
                ):

                    try:

                        uploaded_file = client.files.upload(
                            file=io.BytesIO(
                                audio_bytes
                            ),
                            config=types.UploadFileConfig(
                                mime_type=audio_file.type
                            ),
                        )

                    except Exception as error:

                        st.error(
                            f"Audio upload failed: {error}"
                        )

                if uploaded_file:

                    prompt = f"""
You are a professional multimodal data annotation and quality-control assistant.

Analyze the uploaded audio.

Return ONLY valid JSON:

{{
  "transcript": "complete understandable speech transcription",
  "translation": "English translation of spoken content",
  "description_lines": [
    "line 1",
    "line 2"
  ],
  "confidence": 0.0
}}

Rules:

1. description_lines MUST contain exactly {audio_description_count} separate lines.
2. Every line must contain useful audio information.
3. Do not number the lines.
4. Do not combine lines.
5. Describe identifiable speech, sounds, environment, events or other useful audio information.
6. transcript should contain understandable speech.
7. If no understandable speech exists, use an empty string.
8. translation should be English.
9. If translation is not applicable, use an empty string.
10. confidence must be a number from 0 to 1.
11. Return JSON only.
"""

                    with st.spinner(
                        "Transcribing and analyzing audio..."
                    ):

                        response, model_used, error = (
                            generate_with_fallback(
                                [
                                    prompt,
                                    uploaded_file,
                                ]
                            )
                        )

                    if error:

                        st.error(
                            f"Audio analysis failed: {error}"
                        )

                    else:

                        raw = response_text(
                            response
                        )

                        result = parse_json(
                            raw
                        )

                        if result is None:

                            st.error(
                                "Gemini response could not be parsed."
                            )

                            with st.expander(
                                "Developer Response"
                            ):

                                st.code(
                                    raw or "EMPTY RESPONSE"
                                )

                        else:

                            st.session_state.audio_result = {
                                "data": result,
                                "model": model_used,
                                "filename": audio_file.name,
                            }

                            add_manifest(
                                "Audio",
                                audio_file.name,
                                audio_description_count,
                                len(
                                    description_lines(
                                        result
                                    )
                                ),
                                model_used,
                            )

                            st.success(
                                "Audio analysis completed."
                            )

    # ========================================================
    # AUDIO RESULTS
    # ========================================================

    if st.session_state.audio_result:

        result = (
            st.session_state.audio_result
            .get(
                "data",
                {},
            )
        )

        transcript = text_value(
            result,
            "transcript",
        )

        translation = text_value(
            result,
            "translation",
        )

        lines = description_lines(
            result
        )

        conf = confidence(
            result
        )

        st.divider()

        st.header(
            "Audio Analysis Results"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Transcript",
                (
                    "Available"
                    if transcript
                    else "No speech"
                ),
            )

        with c2:

            st.metric(
                "Translation",
                (
                    "Available"
                    if translation
                    else "N/A"
                ),
            )

        with c3:

            st.metric(
                "Confidence",
                (
                    f"{conf:.1f}%"
                    if conf is not None
                    else "Not supplied"
                ),
            )

        left, right = st.columns(2)

        with left:

            st.subheader(
                "Live Audio Transcript"
            )

            st.text_area(
                "Transcript",
                value=(
                    transcript
                    if transcript
                    else "No understandable speech detected."
                ),
                height=250,
                disabled=True,
                label_visibility="collapsed",
            )

        with right:

            st.subheader(
                "Translation"
            )

            st.text_area(
                "Translation",
                value=(
                    translation
                    if translation
                    else "No translation available."
                ),
                height=250,
                disabled=True,
                label_visibility="collapsed",
            )

        st.divider()

        st.subheader(
            f"AI Audio Description ({audio_description_count} lines requested)"
        )

        for index, line in enumerate(
            lines,
            start=1,
        ):

            st.write(
                f"**{index}.** {line}"
            )

        st.divider()

        st.subheader(
            "Quality Control"
        )

        actual_count = len(
            lines
        )

        q1, q2, q3 = st.columns(3)

        with q1:

            if (
                actual_count
                == audio_description_count
            ):

                st.success(
                    f"Description count: PASS ({actual_count})"
                )

            else:

                st.error(
                    f"Description count: FAIL ({actual_count}/{audio_description_count})"
                )

        with q2:

            if transcript:
                st.success(
                    "Transcript: PASS"
                )
            else:
                st.info(
                    "Transcript: No speech"
                )

        with q3:

            if translation:
                st.success(
                    "Translation: PASS"
                )
            else:
                st.info(
                    "Translation: N/A"
                )


# ============================================================
# AUDITOR CONSOLE
# ============================================================

else:

    st.header(
        "Auditor Console"
    )

    st.caption(
        "Review annotation records and export the QC manifest."
    )

    manifest = st.session_state.manifest

    if not manifest:

        st.info(
            "No analysis records available yet."
        )

    else:

        df = pd.DataFrame(
            manifest
        )

        total = len(df)

        passed = int(
            (
                df["QC"] == "PASS"
            ).sum()
        )

        failed = total - passed

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Total records",
                total,
            )

        with c2:

            st.metric(
                "QC passed",
                passed,
            )

        with c3:

            st.metric(
                "QC failed",
                failed,
            )

        st.divider()

        tab1, tab2 = st.tabs(
            [
                "Manifest",
                "Statistics",
            ]
        )

        with tab1:

            st.subheader(
                "Annotation Manifest"
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            csv_data = df.to_csv(
                index=False
            ).encode(
                "utf-8"
            )

            st.download_button(
                "Download CSV Manifest",
                data=csv_data,
                file_name="seed_lab_manifest.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with tab2:

            st.subheader(
                "Records by Mode"
            )

            mode_counts = (
                df["Mode"]
                .value_counts()
                .rename_axis("Mode")
                .reset_index(
                    name="Records"
                )
            )

            st.dataframe(
                mode_counts,
                use_container_width=True,
                hide_index=True,
            )

            st.subheader(
                "QC Summary"
            )

            qc_counts = (
                df["QC"]
                .value_counts()
                .rename_axis("QC Status")
                .reset_index(
                    name="Records"
                )
            )

            st.dataframe(
                qc_counts,
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        if st.button(
            "Clear Auditor Manifest"
        ):

            st.session_state.manifest = []

            st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🌿 SEED Lab Multimodal Studio • Secure Multimodal Data Quality Control"
)