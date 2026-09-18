import os
import re
import csv
import json
import time
import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image

from google import genai
from google.genai import types


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SEED Lab | Multimodal Data QC",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path("seed_lab_data")
PROFILE_DIR = BASE_DIR / "profiles"
DB_PATH = BASE_DIR / "users.db"

BASE_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)


# ============================================================
# PROFESSIONAL UI
# ============================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 80% 0%, rgba(33, 150, 83, 0.08), transparent 25%),
        #f6f8f7;
}

/* ---------- SIDEBAR ---------- */

section[data-testid="stSidebar"] {
    background: #10251b;
    border-right: 1px solid rgba(255,255,255,0.06);
}

section[data-testid="stSidebar"] * {
    color: #eaf4ee !important;
}

section[data-testid="stSidebar"] .stButton button {
    background: transparent;
    border: 1px solid transparent;
    color: #dce9e1 !important;
    text-align: left;
    border-radius: 10px;
    transition: all .2s ease;
}

section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,.08);
    border-color: rgba(255,255,255,.08);
}

.sidebar-brand {
    padding: 8px 4px 22px 4px;
}

.sidebar-logo {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: #37a866;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 23px;
    margin-bottom: 12px;
}

.sidebar-title {
    font-size: 18px;
    font-weight: 800;
    color: white;
}

.sidebar-subtitle {
    color: #9fb5a7;
    font-size: 12px;
    margin-top: 3px;
}

.sidebar-section {
    color: #71917d;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin: 24px 0 8px 4px;
}

.user-card {
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 14px;
    padding: 12px;
    margin: 10px 0 20px 0;
}

.user-name {
    font-size: 13px;
    font-weight: 700;
    color: white;
}

.user-email {
    font-size: 11px;
    color: #9fb5a7;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ---------- MAIN ---------- */

.page-title {
    font-size: 34px;
    font-weight: 800;
    color: #14231b;
    margin-bottom: 4px;
}

.page-subtitle {
    color: #6c7d73;
    font-size: 14px;
    margin-bottom: 30px;
}

.eyebrow {
    color: #299452;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.8px;
    margin-bottom: 8px;
}

.hero {
    background: linear-gradient(135deg, #ffffff 0%, #eef8f1 100%);
    border: 1px solid #dce8df;
    border-radius: 22px;
    padding: 30px;
    margin-bottom: 24px;
    box-shadow: 0 8px 30px rgba(21, 54, 35, .05);
}

.hero-title {
    font-size: 29px;
    font-weight: 800;
    color: #13271c;
}

.hero-text {
    color: #687a70;
    font-size: 14px;
    margin-top: 8px;
}

/* ---------- CARDS ---------- */

.metric-card {
    background: white;
    border: 1px solid #e0e9e3;
    border-radius: 16px;
    padding: 19px;
    min-height: 110px;
    box-shadow: 0 5px 20px rgba(30,55,40,.035);
}

.metric-label {
    color: #718078;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .8px;
}

.metric-value {
    color: #15271d;
    font-size: 29px;
    font-weight: 800;
    margin-top: 8px;
}

.metric-green {
    color: #269653;
}

/* ---------- STUDIO CARDS ---------- */

.studio-card {
    background: white;
    border: 1px solid #dfe8e2;
    border-radius: 20px;
    padding: 24px;
    min-height: 245px;
    box-shadow: 0 7px 25px rgba(30,55,40,.045);
}

.studio-icon {
    width: 48px;
    height: 48px;
    border-radius: 13px;
    background: #eaf7ee;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    margin-bottom: 17px;
}

.studio-title {
    font-size: 19px;
    font-weight: 800;
    color: #16281e;
}

.studio-description {
    color: #718078;
    font-size: 13px;
    line-height: 1.6;
    margin: 8px 0 20px;
}

/* ---------- BUTTONS ---------- */

.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 700;
    border: 1px solid #d5e1d9;
    background: white;
    color: #203128;
    transition: all .18s ease;
}

.stButton > button:hover {
    border-color: #39a963;
    color: #20834a;
    transform: translateY(-1px);
}

.primary-btn .stButton > button {
    background: #238b4c;
    color: white !important;
    border-color: #238b4c;
}

/* ---------- UPLOAD ---------- */

.upload-panel {
    background: white;
    border: 1px dashed #b8cdbd;
    border-radius: 18px;
    padding: 30px;
    text-align: center;
}

/* ---------- RESULTS ---------- */

.result-card {
    background: white;
    border: 1px solid #dfe8e2;
    border-radius: 17px;
    padding: 20px;
    margin-bottom: 16px;
}

.result-heading {
    color: #1a2b21;
    font-size: 14px;
    font-weight: 800;
    margin-bottom: 10px;
}

.result-text {
    color: #5f7067;
    font-size: 13px;
    line-height: 1.7;
}

.status-pass {
    background: #e8f7ed;
    color: #237b43;
    border: 1px solid #c9e9d3;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 800;
    text-align: center;
}

.status-review {
    background: #fff6df;
    color: #9b6a13;
    border: 1px solid #f0dfad;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 800;
    text-align: center;
}

/* ---------- PROFILE ---------- */

.profile-card {
    background: white;
    border: 1px solid #dfe8e2;
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 7px 25px rgba(30,55,40,.04);
}

/* ---------- DIVIDER ---------- */

hr {
    border-color: #e0e8e2 !important;
}

/* ---------- HIDE STREAMLIT BRANDING ---------- */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            profile_picture TEXT,
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

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        120000,
    ).hex()

    return password_hash, salt


def verify_password(password, stored_hash, salt):
    password_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(password_hash, stored_hash)


# ============================================================
# USER FUNCTIONS
# ============================================================

def create_user(name, email, password, profile_picture=None):

    conn = get_db()

    try:
        password_hash, salt = hash_password(password)

        cursor = conn.execute(
            """
            INSERT INTO users
            (name, email, password_hash, salt, profile_picture, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email.lower().strip(),
                password_hash,
                salt,
                profile_picture,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        conn.commit()
        user_id = cursor.lastrowid

        return user_id

    except sqlite3.IntegrityError:
        return None

    finally:
        conn.close()


def authenticate_user(email, password):

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.lower().strip(),),
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

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

    conn.close()

    return dict(user) if user else None


def update_user(user_id, name, profile_picture):

    conn = get_db()

    conn.execute(
        """
        UPDATE users
        SET name = ?, profile_picture = ?
        WHERE id = ?
        """,
        (
            name,
            profile_picture,
            user_id,
        ),
    )

    conn.commit()
    conn.close()


def change_password(user_id, new_password):

    password_hash, salt = hash_password(new_password)

    conn = get_db()

    conn.execute(
        """
        UPDATE users
        SET password_hash = ?, salt = ?
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

DEFAULT_STATE = {
    "logged_in": False,
    "user_id": None,
    "page": "dashboard",
    "settings_open": False,
    "studio": "dashboard",
    "image_result": None,
    "audio_result": None,
    "manifest": [],
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# AUTHENTICATION PAGE
# ============================================================

def authentication_page():

    left, center, right = st.columns([1, 1.25, 1])

    with center:

        st.markdown(
            """
            <div style="
                text-align:center;
                padding:45px 0 20px;
            ">
                <div style="
                    font-size:48px;
                    margin-bottom:10px;
                ">🌿</div>

                <div style="
                    font-size:30px;
                    font-weight:800;
                    color:#15271d;
                ">
                    SEED Lab
                </div>

                <div style="
                    color:#718078;
                    margin-top:6px;
                    font-size:14px;
                ">
                    Multimodal Data Quality Studio
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(
            ["Sign In", "Create Account"]
        )

        # ====================================================
        # LOGIN
        # ====================================================

        with tab_login:

            st.markdown("### Welcome back")
            st.caption("Sign in to your SEED Lab workspace.")

            email = st.text_input(
                "Email",
                placeholder="you@example.com",
                key="login_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            if st.button(
                "Sign In →",
                use_container_width=True,
                type="primary",
            ):

                if not email or not password:
                    st.error("Please enter your email and password.")

                else:

                    user = authenticate_user(
                        email,
                        password,
                    )

                    if user:

                        st.session_state.logged_in = True
                        st.session_state.user_id = user["id"]
                        st.session_state.page = "dashboard"
                        st.session_state.settings_open = False

                        st.rerun()

                    else:
                        st.error("Incorrect email or password.")

        # ====================================================
        # REGISTER
        # ====================================================

        with tab_register:

            st.markdown("### Create your account")
            st.caption(
                "Create a secure workspace for your data-quality tasks."
            )

            name = st.text_input(
                "Full name",
                placeholder="Ashwak K",
                key="register_name",
            )

            email = st.text_input(
                "Email",
                placeholder="you@example.com",
                key="register_email",
            )

            password = st.text_input(
                "Create password",
                type="password",
                key="register_password",
            )

            confirm = st.text_input(
                "Confirm password",
                type="password",
                key="register_confirm",
            )

            profile = st.file_uploader(
                "Profile picture (optional)",
                type=["png", "jpg", "jpeg"],
                key="register_profile",
            )

            if st.button(
                "Create Account →",
                use_container_width=True,
                type="primary",
            ):

                if not name or not email or not password:
                    st.error("Please complete all required fields.")

                elif password != confirm:
                    st.error("Passwords do not match.")

                elif len(password) < 8:
                    st.error(
                        "Password must contain at least 8 characters."
                    )

                elif not re.match(
                    r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                    email,
                ):
                    st.error("Please enter a valid email address.")

                else:

                    picture_path = None

                    if profile:

                        extension = Path(
                            profile.name
                        ).suffix.lower()

                        filename = (
                            f"user_{secrets.token_hex(8)}"
                            f"{extension}"
                        )

                        picture_path = str(
                            PROFILE_DIR / filename
                        )

                        with open(
                            picture_path,
                            "wb",
                        ) as f:
                            f.write(profile.getbuffer())

                    user_id = create_user(
                        name.strip(),
                        email.strip(),
                        password,
                        picture_path,
                    )

                    if user_id:

                        st.success(
                            "Account created successfully. "
                            "Please sign in."
                        )

                    else:

                        if picture_path and os.path.exists(
                            picture_path
                        ):
                            os.remove(picture_path)

                        st.error(
                            "An account with this email already exists."
                        )


# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.page = "dashboard"
    st.session_state.settings_open = False
    st.session_state.image_result = None
    st.session_state.audio_result = None
    st.session_state.manifest = []

    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar(user):

    with st.sidebar:

        st.markdown(
            """
            <div class="sidebar-brand">

                <div class="sidebar-logo">🌿</div>

                <div class="sidebar-title">
                    SEED LAB
                </div>

                <div class="sidebar-subtitle">
                    Multimodal Data QC Studio
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # USER CARD

        picture = user.get("profile_picture")

        if picture and os.path.exists(picture):

            st.image(
                picture,
                width=54,
            )

        st.markdown(
            f"""
            <div class="user-card">

                <div class="user-name">
                    {user["name"]}
                </div>

                <div class="user-email">
                    {user["email"]}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # STUDIO

        st.markdown(
            '<div class="sidebar-section">WORKSPACE</div>',
            unsafe_allow_html=True,
        )

        if st.button(
            "▣  Overview",
            use_container_width=True,
        ):
            st.session_state.page = "dashboard"
            st.session_state.studio = "dashboard"
            st.rerun()

        if st.button(
            "◈  Image Data Studio",
            use_container_width=True,
        ):
            st.session_state.page = "studio"
            st.session_state.studio = "image"
            st.rerun()

        if st.button(
            "◉  Audio Data Studio",
            use_container_width=True,
        ):
            st.session_state.page = "studio"
            st.session_state.studio = "audio"
            st.rerun()

        if st.button(
            "◫  Auditor Console",
            use_container_width=True,
        ):
            st.session_state.page = "auditor"
            st.rerun()

        st.markdown("---")

        # ====================================================
        # SETTINGS
        # ====================================================

        if st.button(
            "⚙️  Settings",
            use_container_width=True,
        ):

            st.session_state.settings_open = (
                not st.session_state.settings_open
            )

            st.rerun()

        # ONLY SHOW AFTER SETTINGS IS CLICKED

        if st.session_state.settings_open:

            st.markdown(
                '<div class="sidebar-section">SETTINGS</div>',
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

        st.markdown("---")

        if st.button(
            "↪  Sign Out",
            use_container_width=True,
        ):
            logout()


# ============================================================
# GEMINI
# ============================================================

def get_gemini_client():

    api_key = None

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return genai.Client(
        api_key=api_key
    )


PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
]


def response_text(response):

    try:
        return response.text or ""
    except Exception:
        return ""


def clean_json(text):

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"```$",
            "",
            text,
        )

    return text.strip()


def parse_json(text):

    text = clean_json(text)

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if match:

        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {}


def generate_with_fallback(
    client,
    contents,
    config=None,
):

    models = [
        PRIMARY_MODEL,
        *FALLBACK_MODELS,
    ]

    errors = []

    for model in models:

        for attempt in range(2):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )

                text = response_text(response)

                if text.strip():
                    return text, model, None

            except Exception as e:

                errors.append(
                    f"{model}: {str(e)}"
                )

                time.sleep(
                    1.5 * (attempt + 1)
                )

    return "", None, " | ".join(errors[-4:])


# ============================================================
# DESCRIPTION LINES
# ============================================================

def normalize_description_lines(
    value,
    count,
):

    if isinstance(value, list):

        lines = [
            str(x).strip()
            for x in value
            if str(x).strip()
        ]

    else:

        lines = [
            x.strip(" -•0123456789.")
            for x in str(value).splitlines()
            if x.strip()
        ]

    lines = lines[:count]

    while len(lines) < count:
        lines.append("No additional description available.")

    return lines


# ============================================================
# MANIFEST
# ============================================================

def add_manifest(
    filename,
    media_type,
    status,
    confidence,
):

    st.session_state.manifest.append(
        {
            "Timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "User": get_user(
                st.session_state.user_id
            )["email"],
            "File": filename,
            "Type": media_type,
            "Status": status,
            "Confidence": confidence,
        }
    )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_page(user):

    st.markdown(
        '<div class="eyebrow">SEED LAB</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-title">'
        'Multimodal Data Quality Studio'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="page-subtitle">
            Welcome back, {user["name"]}.
            Your unified workspace for annotation and quality control.
        </div>
        """,
        unsafe_allow_html=True,
    )

    total = len(st.session_state.manifest)

    passed = len(
        [
            x for x in st.session_state.manifest
            if x["Status"] == "PASS"
        ]
    )

    review = total - passed

    # METRICS

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Files Processed</div>
                <div class="metric-value">{total}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">QC Passed</div>
                <div class="metric-value metric-green">
                    {passed}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Needs Review</div>
                <div class="metric-value">
                    {review}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # STUDIO CARDS

    st.markdown(
        """
        <div class="eyebrow">WORKSPACES</div>
        <div style="
            font-size:21px;
            font-weight:800;
            color:#17281f;
            margin-bottom:16px;
        ">
            Choose your studio
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="studio-card">

                <div class="studio-icon">🖼️</div>

                <div class="studio-title">
                    Image Data Studio
                </div>

                <div class="studio-description">
                    OCR, translation, visual description
                    and automated quality-control checks.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Image Studio →",
            use_container_width=True,
        ):

            st.session_state.page = "studio"
            st.session_state.studio = "image"
            st.rerun()

    with c2:

        st.markdown(
            """
            <div class="studio-card">

                <div class="studio-icon">🎧</div>

                <div class="studio-title">
                    Audio Data Studio
                </div>

                <div class="studio-description">
                    Transcription, translation, audio
                    description and automated QC.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Audio Studio →",
            use_container_width=True,
        ):

            st.session_state.page = "studio"
            st.session_state.studio = "audio"
            st.rerun()

    # RECENT ACTIVITY

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="eyebrow">ACTIVITY</div>
        <div style="
            font-size:21px;
            font-weight:800;
            color:#17281f;
            margin-bottom:14px;
        ">
            Recent processing
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.manifest:

        import pandas as pd

        df = pd.DataFrame(
            st.session_state.manifest
        )

        st.dataframe(
            df.tail(8),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No files have been processed yet."
        )


# ============================================================
# IMAGE STUDIO
# ============================================================

def image_studio():

    st.markdown(
        '<div class="eyebrow">IMAGE WORKSPACE</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-title">Image Data Studio</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-subtitle">
            OCR · Translation · Visual Description · Quality Control
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload image",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
            "bmp",
        ],
        label_visibility="collapsed",
    )

    lines = st.number_input(
        "Description lines required",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
    )

    if uploaded:

        left, right = st.columns([1, 1.2])

        with left:

            image = Image.open(uploaded)

            st.image(
                image,
                use_container_width=True,
            )

            st.caption(
                f"{uploaded.name} • "
                f"{uploaded.size / 1024:.1f} KB"
            )

        with right:

            if st.button(
                "Analyze Image →",
                type="primary",
                use_container_width=True,
            ):

                client = get_gemini_client()

                if not client:

                    st.error(
                        "GEMINI_API_KEY is not configured."
                    )

                else:

                    with st.spinner(
                        "Analyzing image..."
                    ):

                        prompt = f"""
Analyze this image for a multimodal
data-quality workflow.

Return ONLY valid JSON.

Required schema:

{{
  "ocr": "detected text",
  "translation": "English translation",
  "description_lines": [
    "line 1",
    "line 2"
  ],
  "confidence": 0
}}

IMPORTANT:
Return exactly {lines} description lines.

Describe only what is actually visible.
Do not invent details.
Confidence must be between 0 and 100.
"""

                        config = types.GenerateContentConfig(
                            temperature=0.2,
                            response_mime_type="application/json",
                        )

                        text, model, error = (
                            generate_with_fallback(
                                client,
                                [
                                    image,
                                    prompt,
                                ],
                                config,
                            )
                        )

                        if error:

                            st.error(
                                "Gemini analysis failed."
                            )

                            with st.expander(
                                "Technical details"
                            ):
                                st.code(error)

                        else:

                            result = parse_json(text)

                            description = (
                                normalize_description_lines(
                                    result.get(
                                        "description_lines",
                                        [],
                                    ),
                                    int(lines),
                                )
                            )

                            confidence = result.get(
                                "confidence",
                                0,
                            )

                            try:
                                confidence = float(
                                    confidence
                                )
                            except Exception:
                                confidence = 0

                            ocr = result.get(
                                "ocr",
                                "",
                            )

                            translation = result.get(
                                "translation",
                                "",
                            )

                            status = (
                                "PASS"
                                if confidence >= 80
                                and ocr
                                else "REVIEW"
                            )

                            st.session_state.image_result = {
                                "ocr": ocr,
                                "translation": translation,
                                "description": description,
                                "confidence": confidence,
                                "status": status,
                                "model": model,
                            }

                            add_manifest(
                                uploaded.name,
                                "Image",
                                status,
                                confidence,
                            )

                            st.rerun()

    # RESULTS

    result = st.session_state.image_result

    if result:

        st.divider()

        st.markdown(
            '<div class="eyebrow">ANALYSIS RESULT</div>',
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                """
                <div class="result-card">
                    <div class="result-heading">
                        OCR
                    </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(
                result["ocr"]
                or "No text detected."
            )

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(
                """
                <div class="result-card">
                    <div class="result-heading">
                        English Translation
                    </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(
                result["translation"]
                or "No translation available."
            )

            st.markdown("</div>", unsafe_allow_html=True)

        with c2:

            st.markdown(
                """
                <div class="result-card">
                    <div class="result-heading">
                        AI Description
                    </div>
                """,
                unsafe_allow_html=True,
            )

            for i, line in enumerate(
                result["description"],
                1,
            ):

                st.write(
                    f"**{i:02d}**  {line}"
                )

            st.markdown("</div>", unsafe_allow_html=True)

        status_class = (
            "status-pass"
            if result["status"] == "PASS"
            else "status-review"
        )

        st.markdown(
            f"""
            <div class="{status_class}">
                {"✓ QC PASSED" if result["status"] == "PASS"
                 else "⚠ NEEDS REVIEW"}
                &nbsp;&nbsp;|&nbsp;&nbsp;
                Confidence: {result["confidence"]:.0f}%
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# AUDIO STUDIO
# ============================================================

def audio_studio():

    st.markdown(
        '<div class="eyebrow">AUDIO WORKSPACE</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-title">Audio Data Studio</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-subtitle">
            Transcription · Translation · Audio Description · QC
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        label_visibility="collapsed",
    )

    lines = st.number_input(
        "Description lines required",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
    )

    if uploaded:

        st.audio(
            uploaded,
        )

        st.caption(
            f"{uploaded.name} • "
            f"{uploaded.size / (1024 * 1024):.2f} MB"
        )

        if st.button(
            "Analyze Audio →",
            type="primary",
            use_container_width=True,
        ):

            client = get_gemini_client()

            if not client:

                st.error(
                    "GEMINI_API_KEY is not configured."
                )

            else:

                with st.spinner(
                    "Analyzing audio..."
                ):

                    try:

                        audio_file = client.files.upload(
                            file=uploaded,
                            config=types.UploadFileConfig(
                                mime_type=uploaded.type
                            ),
                        )

                        prompt = f"""
Analyze this audio for a multimodal
data-quality workflow.

Return ONLY valid JSON.

Required schema:

{{
  "transcript": "full transcript",
  "translation": "English translation",
  "description_lines": [
    "line 1",
    "line 2"
  ],
  "confidence": 0
}}

IMPORTANT:
Return exactly {lines} description lines.

For the description, summarize the audible
content, speech, sounds, environment,
music or relevant audio events.

Do not invent sounds that cannot be supported.
Confidence must be between 0 and 100.
"""

                        config = types.GenerateContentConfig(
                            temperature=0.2,
                            response_mime_type="application/json",
                        )

                        text, model, error = (
                            generate_with_fallback(
                                client,
                                [
                                    audio_file,
                                    prompt,
                                ],
                                config,
                            )
                        )

                        if error:

                            st.error(
                                "Audio analysis failed."
                            )

                            with st.expander(
                                "Technical details"
                            ):
                                st.code(error)

                        else:

                            result = parse_json(text)

                            transcript = result.get(
                                "transcript",
                                "",
                            )

                            translation = result.get(
                                "translation",
                                "",
                            )

                            description = (
                                normalize_description_lines(
                                    result.get(
                                        "description_lines",
                                        [],
                                    ),
                                    int(lines),
                                )
                            )

                            confidence = result.get(
                                "confidence",
                                0,
                            )

                            try:
                                confidence = float(
                                    confidence
                                )
                            except Exception:
                                confidence = 0

                            status = (
                                "PASS"
                                if confidence >= 80
                                and transcript
                                else "REVIEW"
                            )

                            st.session_state.audio_result = {
                                "transcript": transcript,
                                "translation": translation,
                                "description": description,
                                "confidence": confidence,
                                "status": status,
                                "model": model,
                            }

                            add_manifest(
                                uploaded.name,
                                "Audio",
                                status,
                                confidence,
                            )

                            st.rerun()

                    except Exception as e:

                        st.error(
                            "Could not process the audio file."
                        )

                        with st.expander(
                            "Technical details"
                        ):
                            st.code(str(e))

    # RESULTS

    result = st.session_state.audio_result

    if result:

        st.divider()

        st.markdown(
            '<div class="eyebrow">ANALYSIS RESULT</div>',
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                """
                <div class="result-card">
                    <div class="result-heading">
                        Live Audio Transcript
                    </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(
                result["transcript"]
                or "No transcript detected."
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        with c2:

            st.markdown(
                """
                <div class="result-card">
                    <div class="result-heading">
                        English Translation
                    </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(
                result["translation"]
                or "No translation available."
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="result-card">
                <div class="result-heading">
                    AI Audio Description
                </div>
            """,
            unsafe_allow_html=True,
        )

        for i, line in enumerate(
            result["description"],
            1,
        ):

            st.write(
                f"**{i:02d}**  {line}"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        status_class = (
            "status-pass"
            if result["status"] == "PASS"
            else "status-review"
        )

        st.markdown(
            f"""
            <div class="{status_class}">
                {"✓ QC PASSED" if result["status"] == "PASS"
                 else "⚠ NEEDS REVIEW"}
                &nbsp;&nbsp;|&nbsp;&nbsp;
                Confidence: {result["confidence"]:.0f}%
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# PROFILE PAGE
# ============================================================

def profile_page(user):

    if st.button("← Back to Dashboard"):

        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown(
        '<div class="eyebrow">SETTINGS / PROFILE</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-title">Your Profile</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-subtitle">
            Manage your personal information and profile picture.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 2])

    with c1:

        if (
            user.get("profile_picture")
            and os.path.exists(user["profile_picture"])
        ):

            st.image(
                user["profile_picture"],
                width=150,
            )

        else:

            st.markdown(
                """
                <div style="
                    width:150px;
                    height:150px;
                    border-radius:50%;
                    background:#e7f4eb;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:55px;
                ">
                    👤
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c2:

        new_name = st.text_input(
            "Full name",
            value=user["name"],
        )

        st.text_input(
            "Email",
            value=user["email"],
            disabled=True,
        )

        new_picture = st.file_uploader(
            "Change profile picture",
            type=[
                "png",
                "jpg",
                "jpeg",
            ],
        )

        if st.button(
            "Save Profile",
            type="primary",
        ):

            picture_path = user.get(
                "profile_picture"
            )

            if new_picture:

                extension = Path(
                    new_picture.name
                ).suffix.lower()

                filename = (
                    f"user_{user['id']}_"
                    f"{secrets.token_hex(5)}"
                    f"{extension}"
                )

                picture_path = str(
                    PROFILE_DIR / filename
                )

                with open(
                    picture_path,
                    "wb",
                ) as f:
                    f.write(
                        new_picture.getbuffer()
                    )

            update_user(
                user["id"],
                new_name,
                picture_path,
            )

            st.success(
                "Profile updated successfully."
            )

            st.rerun()


# ============================================================
# ACCOUNT PAGE
# ============================================================

def account_page(user):

    if st.button("← Back to Dashboard"):

        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown(
        '<div class="eyebrow">SETTINGS / ACCOUNT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-title">Account & Security</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-subtitle">
            Manage your account and password security.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="profile-card">',
        unsafe_allow_html=True,
    )

    st.markdown("### Account information")

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

    st.markdown("### Change password")

    new_password = st.text_input(
        "New password",
        type="password",
    )

    confirm_password = st.text_input(
        "Confirm new password",
        type="password",
    )

    if st.button(
        "Update Password",
        type="primary",
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

            change_password(
                user["id"],
                new_password,
            )

            st.success(
                "Password updated successfully."
            )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "↪ Sign Out",
        use_container_width=True,
    ):

        logout()


# ============================================================
# AUDITOR
# ============================================================

def auditor_page():

    st.markdown(
        '<div class="eyebrow">QUALITY CONTROL</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-title">Auditor Console</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-subtitle">
            Review processing history and export QC records.
        </div>
        """,
        unsafe_allow_html=True,
    )

    total = len(
        st.session_state.manifest
    )

    passed = len(
        [
            x for x in st.session_state.manifest
            if x["Status"] == "PASS"
        ]
    )

    review = total - passed

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

    st.divider()

    if st.session_state.manifest:

        import pandas as pd

        df = pd.DataFrame(
            st.session_state.manifest
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "↓ Download CSV",
            data=csv_data,
            file_name="seed_lab_qc_manifest.csv",
            mime="text/csv",
            use_container_width=True,
        )

        if st.button(
            "Clear Current Manifest",
            use_container_width=True,
        ):

            st.session_state.manifest = []

            st.rerun()

    else:

        st.info(
            "No QC records are available yet."
        )


# ============================================================
# MAIN APPLICATION
# ============================================================

if not st.session_state.logged_in:

    authentication_page()
    st.stop()


# CURRENT USER

user = get_user(
    st.session_state.user_id
)

if not user:

    st.session_state.logged_in = False
    st.rerun()


# SIDEBAR

render_sidebar(user)


# ============================================================
# PAGE ROUTING
# ============================================================

if st.session_state.page == "profile":

    profile_page(user)

elif st.session_state.page == "account":

    account_page(user)

elif st.session_state.page == "auditor":

    auditor_page()

elif (
    st.session_state.page == "studio"
    and st.session_state.studio == "image"
):

    image_studio()

elif (
    st.session_state.page == "studio"
    and st.session_state.studio == "audio"
):

    audio_studio()

else:

    dashboard_page(user)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#8a9890;
        font-size:11px;
        padding:35px 0 10px;
    ">
        🌿 SEED Lab Multimodal Studio
        &nbsp;•&nbsp;
        Secure Multimodal Data Quality Control
    </div>
    """,
    unsafe_allow_html=True,
)