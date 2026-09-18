
import os
import io
import re
import csv
import hmac
import time
import sqlite3
import hashlib
import secrets
from datetime import datetime
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
    page_title="SEED Lab • Multimodal Data QC Studio",
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
# PROFESSIONAL UI CSS
# IMPORTANT: HTML is used ONLY inside this CSS block.
# All visible UI is built with native Streamlit components.
# ============================================================

st.markdown(
    """
    <style>
        /* ---------- Global ---------- */
        :root {
            --seed-green: #22c55e;
            --seed-green-dark: #15803d;
            --seed-green-soft: #12351f;
            --seed-bg: #07110d;
            --seed-card: #0e2017;
            --seed-border: #1d3a2b;
            --seed-text: #f1f5f3;
            --seed-muted: #8fa69a;
            --seed-danger: #b42318;
            --seed-warning: #9a6700;
        }

        .stApp {
            background: var(--seed-bg);
            color: var(--seed-text);
        }

        .main .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* ---------- Sidebar ---------- */
        [data-testid="stSidebar"] {
            background: #10231c;
            border-right: 1px solid #20372e;
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.25rem;
        }

        [data-testid="stSidebar"] * {
            color: #eef7f2;
        }

        [data-testid="stSidebar"] .stCaption {
            color: #9fb3a9 !important;
        }

        [data-testid="stSidebar"] .stRadio label {
            border-radius: 10px;
            padding: 8px 10px;
        }

        [data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(255,255,255,0.07);
        }

        [data-testid="stSidebar"] .stButton button {
            background: transparent;
            border: 1px solid #2b493d;
            color: #eef7f2;
        }

        [data-testid="stSidebar"] .stButton button:hover {
            border-color: #67c59c;
            color: white;
        }

        /* ---------- Typography ---------- */
        h1, h2, h3 {
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.25rem !important;
            margin-bottom: 0.35rem !important;
        }

        h2 {
            font-size: 1.55rem !important;
        }

        h3 {
            font-size: 1.15rem !important;
        }

        .seed-eyebrow {
            color: var(--seed-green);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .seed-muted {
            color: var(--seed-muted);
        }

        /* ---------- Cards ---------- */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--seed-border) !important;
            border-radius: 16px !important;
            background: var(--seed-card); color: var(--seed-text);
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1;
            margin: 0.25rem 0;
        }

        .metric-label {
            color: var(--seed-muted);
            font-size: 0.85rem;
            font-weight: 600;
        }

        .metric-icon {
            font-size: 1.35rem;
        }

        .status-pass {
            color: #137333;
            font-weight: 800;
        }

        .status-review {
            color: #9a6700;
            font-weight: 800;
        }

        .status-fail {
            color: #b42318;
            font-weight: 800;
        }

        /* ---------- Buttons ---------- */
        .stButton button,
        .stDownloadButton button {
            border-radius: 10px;
            font-weight: 700;
            min-height: 42px;
        }

        /* ---------- Upload ---------- */
        [data-testid="stFileUploader"] {
            border-radius: 14px;
        }

        /* ---------- Dataframe ---------- */
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
        }

        /* ---------- Hide Streamlit chrome ---------- */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* ---------- Auth page ---------- */
        .auth-title {
            font-size: 2.2rem;
            font-weight: 850;
            letter-spacing: -0.03em;
        }

        .auth-subtitle {
            color: var(--seed-muted);
            margin-bottom: 1.25rem;
        }

        /* ---------- Small screens ---------- */
        @media (max-width: 900px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
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

def hash_password(password: str, salt_hex: str | None = None):
    """
    Create a PBKDF2-SHA256 password hash.

    A new 16-byte salt is generated when salt_hex is not supplied.
    Existing salts are validated before being decoded so a damaged
    database row cannot crash the whole Streamlit app.
    """
    if salt_hex is None or str(salt_hex).strip() == "":
        salt = secrets.token_bytes(16)
    else:
        salt_hex = str(salt_hex).strip()

        # A valid 16-byte salt is exactly 32 hexadecimal characters.
        if len(salt_hex) != 32:
            raise ValueError("Invalid stored password salt.")

        try:
            salt = bytes.fromhex(salt_hex)
        except (TypeError, ValueError):
            raise ValueError("Invalid stored password salt.")

        if len(salt) != 16:
            raise ValueError("Invalid stored password salt.")

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        180_000,
    )
    return hashed.hex(), salt.hex()


def verify_password(password: str, stored_hash: str, salt_hex: str):
    """
    Verify a password without allowing a corrupted user record
    to crash the application.
    """
    if not password or not stored_hash or not salt_hex:
        return False

    try:
        calculated, _ = hash_password(password, salt_hex)
        return hmac.compare_digest(
            str(calculated),
            str(stored_hash).strip(),
        )
    except (TypeError, ValueError):
        # The account's stored credentials are malformed.
        # Treat the login as invalid instead of exposing a traceback.
        return False


# ============================================================
# USER FUNCTIONS
# ============================================================

def create_user(name, email, password):
    email = email.strip().lower()

    password_hash, salt = hash_password(password)

    conn = db()
    try:
        cur = conn.execute(
            """
            INSERT INTO users
            (name, email, password_hash, salt, profile_image, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                email,
                password_hash,
                salt,
                "",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return cur.lastrowid, None
    except sqlite3.IntegrityError:
        return None, "An account with this email already exists."
    finally:
        conn.close()


def get_user_by_email(email):
    conn = db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    conn.close()
    return row


def get_user(user_id):
    conn = db()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return row


def update_profile(user_id, name, image_path=None):
    conn = db()

    if image_path is None:
        conn.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (name.strip(), user_id),
        )
    else:
        conn.execute(
            "UPDATE users SET name = ?, profile_image = ? WHERE id = ?",
            (name.strip(), str(image_path), user_id),
        )

    conn.commit()
    conn.close()


def change_password(user_id, new_password):
    password_hash, salt = hash_password(new_password)

    conn = db()
    conn.execute(
        """
        UPDATE users
        SET password_hash = ?, salt = ?
        WHERE id = ?
        """,
        (password_hash, salt, user_id),
    )
    conn.commit()
    conn.close()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "logged_in": False,
    "user_id": None,
    "page": "Overview",
    "settings_open": False,
    "image_result": None,
    "audio_result": None,
    "manifest": [],
    "processing": False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GEMINI
# ============================================================

def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")


def get_client():
    api_key = get_api_key()
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        return None
    return genai.Client(api_key=api_key)


MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]


def clean_text(text):
    if not text:
        return ""

    text = str(text).replace("\r", "").strip()

    # Remove accidental markdown fences.
    text = re.sub(r"^```(?:text|json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)

    return text.strip()


def split_lines(text, count):
    text = clean_text(text)

    lines = []
    for raw in text.splitlines():
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", raw).strip()
        if line:
            lines.append(line)

    if not lines and text:
        lines = [text]

    return lines[:count]


def generate_with_fallback(contents, temperature=0.2):
    client = get_client()

    if client is None:
        return None, "Gemini API key is missing."

    last_error = None

    for model_name in MODEL_CANDIDATES:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                    ),
                )
                text = getattr(response, "text", None)

                if text and text.strip():
                    return text.strip(), None

                last_error = f"{model_name} returned an empty response."

            except Exception as exc:
                last_error = str(exc)
                time.sleep(1.2 * (attempt + 1))

    return None, last_error or "Gemini request failed."


def image_analysis(uploaded_file, lines_required):
    try:
        image = Image.open(uploaded_file).convert("RGB")

        prompt = f"""
You are a professional multimodal data annotation assistant.

Analyze the supplied image and return EXACTLY these sections:

OCR:
Write the important visible text. If there is no readable text, write NONE.

TRANSLATION:
Translate the visible text into English. If no text is present, write NONE.

DESCRIPTION:
Write exactly {lines_required} concise numbered lines describing the image.
Do not invent facts. Mention only visually supported information.

QC:
Return PASS if the image is clear enough for annotation and the requested
fields can be reasonably produced. Otherwise return REVIEW.

CONFIDENCE:
Return one number from 0 to 100.

Use this exact structure:

OCR:
...

TRANSLATION:
...

DESCRIPTION:
1. ...
2. ...

QC:
PASS

CONFIDENCE:
95
"""

        text, error = generate_with_fallback(
            [
                prompt,
                image,
            ],
            temperature=0.15,
        )

        if error:
            return {"error": error}

        text = clean_text(text)

        def section(name, next_names):
            pattern = rf"{name}\s*:\s*(.*?)(?=\n(?:{'|'.join(next_names)})\s*:|\Z)"
            match = re.search(pattern, text, flags=re.I | re.S)
            return match.group(1).strip() if match else ""

        ocr = section("OCR", ["TRANSLATION", "DESCRIPTION", "QC", "CONFIDENCE"])
        translation = section(
            "TRANSLATION",
            ["DESCRIPTION", "QC", "CONFIDENCE"],
        )
        description_raw = section(
            "DESCRIPTION",
            ["QC", "CONFIDENCE"],
        )
        qc = section("QC", ["CONFIDENCE"])
        confidence_raw = section("CONFIDENCE", [])

        description_lines = split_lines(description_raw, lines_required)

        if len(description_lines) < lines_required:
            # A second, smaller request can fill missing lines.
            extra_prompt = f"""
The following image analysis produced fewer than {lines_required}
description lines.

Existing description:
{chr(10).join(description_lines)}

Provide exactly {lines_required - len(description_lines)} additional
short visual description lines. Do not invent facts.
"""
            extra_text, _ = generate_with_fallback(
                [extra_prompt, image],
                temperature=0.15,
            )
            if extra_text:
                description_lines.extend(
                    split_lines(extra_text, lines_required - len(description_lines))
                )

        try:
            confidence = float(
                re.search(r"\d+(?:\.\d+)?", confidence_raw).group()
            )
        except Exception:
            confidence = 0.0

        qc_upper = qc.upper()
        status = (
            "PASS"
            if "PASS" in qc_upper and "REVIEW" not in qc_upper
            else "REVIEW"
        )

        return {
            "ocr": ocr or "NONE",
            "translation": translation or "NONE",
            "description": description_lines,
            "qc": status,
            "confidence": max(0.0, min(100.0, confidence)),
            "raw": text,
        }

    except Exception as exc:
        return {"error": str(exc)}


def audio_analysis(uploaded_file, lines_required):
    client = get_client()

    if client is None:
        return {"error": "Gemini API key is missing."}

    suffix = Path(uploaded_file.name).suffix or ".mp3"
    temp_path = BASE_DIR / f"_audio_{secrets.token_hex(8)}{suffix}"

    try:
        temp_path.write_bytes(uploaded_file.getvalue())

        prompt = f"""
You are a professional multimodal audio annotation assistant.

Analyze the uploaded audio.

Return EXACTLY these sections:

TRANSCRIPT:
Provide the spoken content as accurately as possible.
If speech is not understandable, write NONE.

TRANSLATION:
Translate the spoken content into English.
If there is no understandable speech, write NONE.

DESCRIPTION:
Write exactly {lines_required} concise lines describing the audible
content, environment, speakers, sounds, mood, or events that are
actually supported by the audio. Do not invent facts.

QC:
Return PASS if the audio is reasonably usable for annotation.
Otherwise return REVIEW.

CONFIDENCE:
Return one number from 0 to 100.

Use this exact structure:

TRANSCRIPT:
...

TRANSLATION:
...

DESCRIPTION:
1. ...
2. ...

QC:
PASS

CONFIDENCE:
95
"""

        uploaded = client.files.upload(file=str(temp_path))

        last_error = None
        response_text = None

        for model_name in MODEL_CANDIDATES:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[uploaded, prompt],
                        config=types.GenerateContentConfig(
                            temperature=0.15,
                        ),
                    )
                    response_text = getattr(response, "text", None)

                    if response_text and response_text.strip():
                        break

                except Exception as exc:
                    last_error = str(exc)
                    time.sleep(1.2 * (attempt + 1))

            if response_text:
                break

        if not response_text:
            return {
                "error": last_error or "Audio analysis returned no result."
            }

        text = clean_text(response_text)

        def section(name, next_names):
            pattern = rf"{name}\s*:\s*(.*?)(?=\n(?:{'|'.join(next_names)})\s*:|\Z)"
            match = re.search(pattern, text, flags=re.I | re.S)
            return match.group(1).strip() if match else ""

        transcript = section(
            "TRANSCRIPT",
            ["TRANSLATION", "DESCRIPTION", "QC", "CONFIDENCE"],
        )
        translation = section(
            "TRANSLATION",
            ["DESCRIPTION", "QC", "CONFIDENCE"],
        )
        description_raw = section(
            "DESCRIPTION",
            ["QC", "CONFIDENCE"],
        )
        qc = section("QC", ["CONFIDENCE"])
        confidence_raw = section("CONFIDENCE", [])

        description_lines = split_lines(description_raw, lines_required)

        try:
            confidence = float(
                re.search(r"\d+(?:\.\d+)?", confidence_raw).group()
            )
        except Exception:
            confidence = 0.0

        status = (
            "PASS"
            if "PASS" in qc.upper() and "REVIEW" not in qc.upper()
            else "REVIEW"
        )

        return {
            "transcript": transcript or "NONE",
            "translation": translation or "NONE",
            "description": description_lines,
            "qc": status,
            "confidence": max(0.0, min(100.0, confidence)),
            "raw": text,
        }

    except Exception as exc:
        return {"error": str(exc)}

    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


# ============================================================
# MANIFEST
# ============================================================

def add_manifest(filename, media_type, result):
    if not result or result.get("error"):
        return

    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file": filename,
        "type": media_type,
        "status": result.get("qc", "REVIEW"),
        "confidence": result.get("confidence", 0),
    }

    st.session_state.manifest.insert(0, row)


def stats():
    rows = st.session_state.manifest

    processed = len(rows)
    passed = sum(1 for r in rows if r["status"] == "PASS")
    review = sum(1 for r in rows if r["status"] != "PASS")

    return processed, passed, review


# ============================================================
# AUTH PAGE
# ============================================================

def auth_page():
    left, center, right = st.columns([1, 1.35, 1])

    with center:
        st.write("")
        st.write("")

        st.caption("🌿 SEED LAB")
        st.title("Multimodal Data QC Studio")
        st.caption("Secure workspace for annotation, AI processing and quality control.")

        login_tab, register_tab = st.tabs(["Sign in", "Create account"])

        with login_tab:
            with st.container(border=True):
                st.subheader("Welcome back")

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
                    "Sign in",
                    type="primary",
                    use_container_width=True,
                    key="login_button",
                ):
                    user = get_user_by_email(email)

                    if user and verify_password(
                        password,
                        user["password_hash"],
                        user["salt"],
                    ):
                        st.session_state.logged_in = True
                        st.session_state.user_id = user["id"]
                        st.session_state.page = "Overview"
                        st.rerun()
                    else:
                        st.error("Incorrect email or password.")

        with register_tab:
            with st.container(border=True):
                st.subheader("Create your workspace")

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

                if st.button(
                    "Create account",
                    type="primary",
                    use_container_width=True,
                    key="register_button",
                ):
                    if not name.strip() or not email.strip() or not password:
                        st.error("Please complete all fields.")
                    elif len(password) < 8:
                        st.error("Password must contain at least 8 characters.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        user_id, error = create_user(
                            name,
                            email,
                            password,
                        )

                        if error:
                            st.error(error)
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.page = "Overview"
                            st.success("Account created.")
                            st.rerun()

        st.caption("Your account information is stored in the app workspace.")


# ============================================================
# SIDEBAR
# ============================================================

def sidebar(user):
    with st.sidebar:
        st.caption("🌿 SEED LAB")

        st.markdown("### Multimodal Data QC Studio")
        st.caption("Annotation • AI • Quality Control")

        st.divider()

        # Profile
        with st.container():
            image_path = user["profile_image"]

            if image_path and Path(image_path).exists():
                st.image(image_path, width=54)
            else:
                st.subheader("👤")

            st.subheader(user["name"])
            st.caption(user["email"])

        st.divider()

        st.caption("WORKSPACE")

        pages = [
            "Overview",
            "Image Data Studio",
            "Audio Data Studio",
            "Auditor Console",
        ]

        current_index = pages.index(
            st.session_state.page
        ) if st.session_state.page in pages else 0

        selected = st.radio(
            "Workspace",
            pages,
            index=current_index,
            label_visibility="collapsed",
            key="workspace_navigation",
        )

        if selected != st.session_state.page:
            st.session_state.page = selected
            st.rerun()

        st.divider()

        if st.button(
            "⚙️  Settings",
            use_container_width=True,
            key="settings_toggle",
        ):
            st.session_state.settings_open = not st.session_state.settings_open
            st.rerun()

        if st.session_state.settings_open:
            setting = st.radio(
                "Settings",
                ["👤 Profile", "🔐 Account"],
                label_visibility="collapsed",
                key="settings_navigation",
            )

            if setting == "👤 Profile":
                if st.button(
                    "Open Profile",
                    use_container_width=True,
                    key="open_profile",
                ):
                    st.session_state.page = "Profile"
                    st.rerun()

            if setting == "🔐 Account":
                if st.button(
                    "Open Account",
                    use_container_width=True,
                    key="open_account",
                ):
                    st.session_state.page = "Account"
                    st.rerun()

        st.caption("Secure user workspace")
        st.caption("SEED Lab Multimodal Studio")


# ============================================================
# TOP BAR
# ============================================================

def page_header(eyebrow, title, subtitle=""):
    st.caption(f"🌿 {eyebrow}")
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.write("")


# ============================================================
# METRIC CARD
# ============================================================

def metric_card(icon, label, value):
    with st.container(border=True):
        st.subheader(f"{icon}  {value}")
        st.caption(label)


# ============================================================
# OVERVIEW
# ============================================================

def overview_page(user):
    page_header(
        "SEED LAB",
        "Multimodal Data Quality Studio",
        f"Welcome back, {user['name']}. Your unified workspace for annotation and quality control.",
    )

    processed, passed, review = stats()

    a, b, c = st.columns(3)

    with a:
        metric_card("📁", "Files Processed", processed)

    with b:
        metric_card("✓", "QC Passed", passed)

    with c:
        metric_card("◌", "Needs Review", review)

    st.write("")
    st.subheader("Workspaces")
    st.caption("Choose a studio to start processing multimodal data.")

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("### 🖼️ Image Data Studio")
            st.caption(
                "OCR · Translation · Visual Description · Automated QC"
            )
            st.write(
                "Analyze images, extract visible text, translate content, "
                "generate structured descriptions and run quality checks."
            )

            if st.button(
                "Open Image Studio →",
                type="primary",
                use_container_width=True,
                key="overview_image",
            ):
                st.session_state.page = "Image Data Studio"
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown("### 🎧 Audio Data Studio")
            st.caption(
                "Transcription · Translation · Audio Description · Automated QC"
            )
            st.write(
                "Transcribe speech, translate spoken content, describe "
                "audible events and run annotation-quality checks."
            )

            if st.button(
                "Open Audio Studio →",
                type="primary",
                use_container_width=True,
                key="overview_audio",
            ):
                st.session_state.page = "Audio Data Studio"
                st.rerun()

    st.write("")
    st.subheader("Activity")
    st.caption("Recent processing")

    if not st.session_state.manifest:
        with st.container(border=True):
            st.markdown("### 🗂️ No processing activity yet")
            st.caption(
                "Upload your first image or audio file to begin "
                "quality-controlled annotation."
            )
    else:
        activity = pd.DataFrame(st.session_state.manifest[:8])
        st.dataframe(
            activity,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# IMAGE STUDIO
# ============================================================

def image_studio():
    page_header(
        "IMAGE WORKSPACE",
        "Image Data Studio",
        "OCR, translation, visual description and automated quality control.",
    )

    with st.container(border=True):
        st.subheader("Upload image")

        uploaded = st.file_uploader(
            "Choose an image",
            type=["png", "jpg", "jpeg", "webp", "bmp"],
            help="Upload a clear image for multimodal analysis.",
            key="image_upload",
        )

        lines_required = st.number_input(
            "Description lines required",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            key="image_lines",
        )

        if uploaded:
            left, right = st.columns([1.1, 1])

            with left:
                st.image(
                    uploaded,
                    caption=uploaded.name,
                    use_container_width=True,
                )

            with right:
                st.markdown("### Ready for analysis")
                st.caption(
                    f"{uploaded.name} • {lines_required} description lines"
                )

                analyze = st.button(
                    "Analyze Image",
                    type="primary",
                    use_container_width=True,
                    key="analyze_image",
                )

                if analyze:
                    with st.spinner("Analyzing image..."):
                        result = image_analysis(
                            uploaded,
                            int(lines_required),
                        )

                    if result.get("error"):
                        st.error(result["error"])
                        st.session_state.image_result = None
                    else:
                        st.session_state.image_result = result
                        add_manifest(
                            uploaded.name,
                            "Image",
                            result,
                        )
                        st.success("Image analysis completed.")

    result = st.session_state.image_result

    if result:
        st.write("")
        st.subheader("Analysis results")

        status = result.get("qc", "REVIEW")
        confidence = result.get("confidence", 0)

        r1, r2 = st.columns([2, 1])

        with r1:
            with st.container(border=True):
                st.markdown("### OCR")
                st.write(result.get("ocr", "NONE"))

        with r2:
            with st.container(border=True):
                st.markdown("### Quality Control")

                if status == "PASS":
                    st.success("✓ PASS")
                else:
                    st.warning("◌ REVIEW")

                st.metric("Confidence", f"{confidence:.0f}%")

        r3, r4 = st.columns(2)

        with r3:
            with st.container(border=True):
                st.markdown("### English Translation")
                st.write(result.get("translation", "NONE"))

        with r4:
            with st.container(border=True):
                st.markdown("### AI Visual Description")

                for i, line in enumerate(
                    result.get("description", []),
                    start=1,
                ):
                    st.write(f"**{i}.** {line}")


# ============================================================
# AUDIO STUDIO
# ============================================================

def audio_studio():
    page_header(
        "AUDIO WORKSPACE",
        "Audio Data Studio",
        "Transcription, translation, audio description and automated quality control.",
    )

    with st.container(border=True):
        st.subheader("Upload audio")

        uploaded = st.file_uploader(
            "Choose an audio file",
            type=["mp3", "wav", "m4a", "aac", "ogg", "flac"],
            help="Supported audio formats: MP3, WAV, M4A, AAC, OGG and FLAC.",
            key="audio_upload",
        )

        lines_required = st.number_input(
            "Description lines required",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            key="audio_lines",
        )

        if uploaded:
            st.audio(uploaded)

            st.caption(
                f"{uploaded.name} • "
                f"{uploaded.size / (1024 * 1024):.2f} MB • "
                f"{lines_required} description lines"
            )

            analyze = st.button(
                "Analyze Audio",
                type="primary",
                use_container_width=True,
                key="analyze_audio",
            )

            if analyze:
                with st.spinner(
                    "Uploading audio and generating annotation..."
                ):
                    result = audio_analysis(
                        uploaded,
                        int(lines_required),
                    )

                if result.get("error"):
                    st.error(result["error"])
                    st.session_state.audio_result = None
                else:
                    st.session_state.audio_result = result
                    add_manifest(
                        uploaded.name,
                        "Audio",
                        result,
                    )
                    st.success("Audio analysis completed.")

    result = st.session_state.audio_result

    if result:
        st.write("")
        st.subheader("Analysis results")

        status = result.get("qc", "REVIEW")
        confidence = result.get("confidence", 0)

        r1, r2 = st.columns([2, 1])

        with r1:
            with st.container(border=True):
                st.markdown("### Live Audio Transcript")
                st.write(result.get("transcript", "NONE"))

        with r2:
            with st.container(border=True):
                st.markdown("### Quality Control")

                if status == "PASS":
                    st.success("✓ PASS")
                else:
                    st.warning("◌ REVIEW")

                st.metric("Confidence", f"{confidence:.0f}%")

        r3, r4 = st.columns(2)

        with r3:
            with st.container(border=True):
                st.markdown("### English Translation")
                st.write(result.get("translation", "NONE"))

        with r4:
            with st.container(border=True):
                st.markdown("### AI Audio Description")

                for i, line in enumerate(
                    result.get("description", []),
                    start=1,
                ):
                    st.write(f"**{i}.** {line}")


# ============================================================
# AUDITOR CONSOLE
# ============================================================

def auditor_page():
    page_header(
        "QUALITY CONTROL",
        "Auditor Console",
        "Review processing history and export the current annotation manifest.",
    )

    processed, passed, review = stats()

    a, b, c = st.columns(3)

    with a:
        metric_card("📁", "Files Processed", processed)

    with b:
        metric_card("✓", "QC Passed", passed)

    with c:
        metric_card("◌", "Needs Review", review)

    st.write("")

    if not st.session_state.manifest:
        with st.container(border=True):
            st.markdown("### No audit records")
            st.caption(
                "Process an image or audio file to populate the audit table."
            )
        return

    df = pd.DataFrame(st.session_state.manifest)

    with st.container(border=True):
        st.subheader("Processing manifest")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download CSV Manifest",
            data=csv_data,
            file_name="seed_lab_manifest.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ============================================================
# PROFILE PAGE
# ============================================================

def profile_page(user):
    page_header(
        "SETTINGS",
        "Profile",
        "Manage your workspace identity and profile picture.",
    )

    left, right = st.columns([1, 1.8])

    with left:
        with st.container(border=True):
            st.subheader("Profile picture")

            image_path = user["profile_image"]

            if image_path and Path(image_path).exists():
                st.image(image_path, width=180)
            else:
                st.title("👤")
                st.caption("No profile picture uploaded.")

            new_image = st.file_uploader(
                "Upload new picture",
                type=["png", "jpg", "jpeg", "webp"],
                key="profile_picture",
            )

    with right:
        with st.container(border=True):
            st.subheader("Personal information")

            new_name = st.text_input(
                "Full name",
                value=user["name"],
                key="profile_name",
            )

            st.text_input(
                "Email",
                value=user["email"],
                disabled=True,
            )

            if st.button(
                "Save profile",
                type="primary",
                use_container_width=True,
                key="save_profile",
            ):
                saved_image = None

                if new_image:
                    suffix = Path(new_image.name).suffix.lower()
                    filename = f"user_{user['id']}{suffix}"
                    saved_path = PROFILE_DIR / filename
                    saved_path.write_bytes(new_image.getvalue())
                    saved_image = saved_path

                update_profile(
                    user["id"],
                    new_name,
                    saved_image,
                )

                st.success("Profile updated.")
                st.rerun()


# ============================================================
# ACCOUNT PAGE
# ============================================================

def account_page(user):
    page_header(
        "SETTINGS",
        "Account",
        "Manage your security settings and sign out.",
    )

    with st.container(border=True):
        st.subheader("Account information")

        c1, c2 = st.columns(2)

        with c1:
            st.text_input(
                "Email",
                value=user["email"],
                disabled=True,
            )

        with c2:
            st.text_input(
                "Created",
                value=user["created_at"],
                disabled=True,
            )

    st.write("")

    with st.container(border=True):
        st.subheader("Change password")

        old_password = st.text_input(
            "Current password",
            type="password",
            key="old_password",
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
            key="change_password",
        ):
            if not verify_password(
                old_password,
                user["password_hash"],
                user["salt"],
            ):
                st.error("Current password is incorrect.")
            elif len(new_password) < 8:
                st.error("New password must contain at least 8 characters.")
            elif new_password != confirm_password:
                st.error("New passwords do not match.")
            else:
                change_password(
                    user["id"],
                    new_password,
                )
                st.success("Password updated successfully.")

    st.write("")

    with st.container(border=True):
        st.subheader("Session")

        if st.button(
            "Sign out",
            use_container_width=True,
            key="logout_account",
        ):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.page = "Overview"
            st.session_state.image_result = None
            st.session_state.audio_result = None
            st.session_state.manifest = []
            st.rerun()


# ============================================================
# MAIN ROUTER
# ============================================================

if not st.session_state.logged_in:
    auth_page()
    st.stop()


user = get_user(st.session_state.user_id)

if not user:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.rerun()


sidebar(user)

page = st.session_state.page

if page == "Overview":
    overview_page(user)

elif page == "Image Data Studio":
    image_studio()

elif page == "Audio Data Studio":
    audio_studio()

elif page == "Auditor Console":
    auditor_page()

elif page == "Profile":
    profile_page(user)

elif page == "Account":
    account_page(user)

else:
    overview_page(user)


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption(
    "🌿 SEED Lab Multimodal Studio • Secure Multimodal Data Quality Control"
)
