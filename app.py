import streamlit as st
import pandas as pd
from PIL import Image
from google import genai
from google.genai import types
import json
import io
import time
import re
import html


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SEED Lab Multimodal Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROFESSIONAL FUTURISTIC UI
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
        radial-gradient(circle at 75% 5%, rgba(40, 100, 255, 0.18), transparent 25%),
        radial-gradient(circle at 10% 70%, rgba(85, 35, 180, 0.12), transparent 30%),
        linear-gradient(135deg, #020817 0%, #03142b 45%, #020617 100%);
    color: #eaf2ff;
}

/* Background grid */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: 0.14;
    background-image:
        linear-gradient(rgba(55, 130, 255, 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(55, 130, 255, 0.08) 1px, transparent 1px);
    background-size: 42px 42px;
    z-index: 0;
}

/* Glow orbs */
.bg-orb {
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    pointer-events: none;
    z-index: 0;
    opacity: 0.20;
}

.orb-one {
    width: 350px;
    height: 350px;
    background: #1769ff;
    top: 5%;
    right: 5%;
    animation: floatOne 10s ease-in-out infinite;
}

.orb-two {
    width: 280px;
    height: 280px;
    background: #6d28d9;
    bottom: 5%;
    left: 8%;
    animation: floatTwo 13s ease-in-out infinite;
}

@keyframes floatOne {
    0%,100% { transform: translate(0,0); }
    50% { transform: translate(-35px,30px); }
}

@keyframes floatTwo {
    0%,100% { transform: translate(0,0); }
    50% { transform: translate(30px,-25px); }
}


/* Main content */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
    position: relative;
    z-index: 1;
}


/* Sidebar */
section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #03152f 0%, #020b1b 100%);
    border-right: 1px solid rgba(65, 140, 255, 0.25);
}

section[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}

.sidebar-brand {
    padding: 18px 12px 25px 12px;
    border-bottom: 1px solid rgba(80, 140, 255, 0.18);
    margin-bottom: 20px;
}

.sidebar-logo {
    font-size: 29px;
    font-weight: 800;
    letter-spacing: -1px;
    color: #ffffff;
}

.sidebar-logo span {
    color: #3ea0ff;
}

.sidebar-subtitle {
    color: #83bfff;
    font-size: 13px;
    margin-top: 3px;
}

.sidebar-section {
    color: #607da5;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.6px;
    margin: 20px 12px 10px;
}


/* Hero */
.hero {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(45, 139, 255, 0.55);
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 22px;

    background:
        radial-gradient(circle at 85% 50%, rgba(36, 109, 255, 0.35), transparent 35%),
        linear-gradient(110deg, rgba(5, 30, 66, 0.96), rgba(4, 19, 43, 0.90));

    box-shadow:
        0 20px 60px rgba(0,0,0,0.35),
        inset 0 1px 0 rgba(255,255,255,0.05);
}

.hero::after {
    content: "";
    position: absolute;
    width: 420px;
    height: 420px;
    right: -130px;
    top: -190px;
    border-radius: 50%;
    border: 1px solid rgba(70,150,255,0.25);
    box-shadow:
        0 0 60px rgba(40,130,255,0.20),
        inset 0 0 50px rgba(50,130,255,0.15);
}

.hero-small {
    color: #78baff;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 9px;
}

.hero-title {
    font-size: 34px;
    line-height: 1.15;
    font-weight: 800;
    margin: 0;
    color: #f7fbff;
}

.hero-title span {
    color: #3d9cff;
    text-shadow: 0 0 30px rgba(50,140,255,0.35);
}

.hero-description {
    margin-top: 12px;
    max-width: 720px;
    color: #a9c1df;
    font-size: 14px;
    line-height: 1.65;
}


/* Top header */
.top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
}

.brand-area {
    display: flex;
    align-items: center;
    gap: 15px;
}

.brand-icon {
    width: 48px;
    height: 48px;
    border-radius: 15px;

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 24px;

    background: linear-gradient(135deg, #1769ff, #6738ef);
    box-shadow: 0 0 35px rgba(43,120,255,0.32);
}

.brand-title {
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
}

.brand-title span {
    color: #55aaff;
}

.brand-tagline {
    color: #7697bd;
    font-size: 11px;
    margin-top: 3px;
}

.connection-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;

    padding: 9px 15px;
    border-radius: 999px;

    border: 1px solid rgba(38, 132, 255, 0.6);
    background: rgba(5, 33, 72, 0.72);

    color: #8fd0ff;
    font-size: 12px;
    font-weight: 600;
}

.connection-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #28df65;
    box-shadow: 0 0 12px #28df65;
}


/* Cards */
.glass-card {
    background:
        linear-gradient(
            145deg,
            rgba(8, 31, 63, 0.88),
            rgba(3, 18, 40, 0.90)
        );

    border: 1px solid rgba(54, 129, 220, 0.35);
    border-radius: 18px;

    padding: 20px;

    box-shadow:
        0 18px 45px rgba(0,0,0,0.24),
        inset 0 1px 0 rgba(255,255,255,0.035);

    margin-bottom: 18px;
}

.glass-card:hover {
    border-color: rgba(63, 151, 255, 0.55);
    box-shadow:
        0 20px 55px rgba(0,0,0,0.30),
        0 0 35px rgba(30,100,255,0.08);
}

.card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 15px;
}

.card-icon {
    width: 42px;
    height: 42px;
    border-radius: 13px;

    display: flex;
    align-items: center;
    justify-content: center;

    background:
        linear-gradient(
            135deg,
            rgba(28,116,255,0.9),
            rgba(88,52,220,0.9)
        );

    box-shadow: 0 0 25px rgba(37,119,255,0.25);

    font-size: 19px;
}

.card-title {
    color: #f3f8ff;
    font-weight: 700;
    font-size: 17px;
}

.card-subtitle {
    color: #6f91b8;
    font-size: 11px;
    margin-top: 2px;
}


/* Section title */
.section-title {
    display: flex;
    align-items: center;
    justify-content: space-between;

    color: #eef6ff;
    font-size: 19px;
    font-weight: 750;

    margin: 25px 0 14px;
}

.section-line {
    height: 1px;
    flex: 1;
    margin-left: 18px;
    background: linear-gradient(
        90deg,
        rgba(50,140,255,0.35),
        transparent
    );
}


/* Metrics */
.metric-card {
    background:
        linear-gradient(
            145deg,
            rgba(9,35,72,0.90),
            rgba(4,19,41,0.92)
        );

    border: 1px solid rgba(57,128,214,0.30);
    border-radius: 15px;
    padding: 17px;
    min-height: 105px;

    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

.metric-label {
    color: #7595ba;
    font-size: 11px;
    font-weight: 600;
}

.metric-value {
    color: #f5f9ff;
    font-size: 26px;
    font-weight: 800;
    margin-top: 7px;
}

.metric-small {
    color: #4d8ccc;
    font-size: 10px;
    margin-top: 4px;
}


/* Status */
.status-active {
    display: inline-flex;
    align-items: center;
    gap: 6px;

    padding: 5px 9px;
    border-radius: 999px;

    color: #47ef87;
    background: rgba(20,160,75,0.12);
    border: 1px solid rgba(47,215,108,0.24);

    font-size: 10px;
    font-weight: 700;
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #35e976;
    box-shadow: 0 0 10px #35e976;
}


/* QC */
.qc-pass {
    display: flex;
    align-items: center;
    gap: 13px;

    background: rgba(15,125,75,0.10);
    border: 1px solid rgba(36,205,117,0.30);
    border-radius: 14px;
    padding: 15px;
}

.qc-icon {
    width: 38px;
    height: 38px;
    border-radius: 50%;

    display: flex;
    align-items: center;
    justify-content: center;

    background: rgba(26,202,111,0.16);
    color: #38ed88;
    font-size: 18px;
}

.qc-title {
    color: #48ee91;
    font-weight: 700;
    font-size: 14px;
}

.qc-text {
    color: #7594b4;
    font-size: 10px;
    margin-top: 3px;
}


/* Description lines */
.description-line {
    display: flex;
    gap: 12px;
    padding: 10px 0;

    border-bottom: 1px solid rgba(91,130,176,0.13);

    color: #d9e8fa;
    font-size: 12px;
    line-height: 1.5;
}

.description-line:last-child {
    border-bottom: none;
}

.line-number {
    flex-shrink: 0;

    width: 27px;
    height: 27px;
    border-radius: 9px;

    display: flex;
    align-items: center;
    justify-content: center;

    background: rgba(32,108,240,0.15);
    border: 1px solid rgba(45,126,255,0.32);

    color: #66adff;
    font-size: 10px;
    font-weight: 700;
}


/* Transcript */
.transcript-box {
    background: rgba(1,12,28,0.65);
    border: 1px solid rgba(55,120,190,0.25);
    border-radius: 13px;

    padding: 15px;

    color: #bcd2eb;
    font-size: 13px;
    line-height: 1.65;

    min-height: 120px;
}


/* Translation */
.translation-box {
    background:
        linear-gradient(
            145deg,
            rgba(13,47,91,0.70),
            rgba(7,26,55,0.75)
        );

    border: 1px solid rgba(61,137,235,0.32);
    border-radius: 13px;

    padding: 16px;

    color: #d9eaff;
    font-size: 14px;
    line-height: 1.8;
}


/* Upload */
.upload-info {
    text-align: center;

    border: 1px dashed rgba(64,148,255,0.55);
    border-radius: 14px;

    padding: 22px;

    background: rgba(20,83,160,0.06);

    color: #79a6d3;
    font-size: 12px;
}


/* Buttons */
.stButton > button {
    width: 100%;

    border: none !important;
    border-radius: 11px !important;

    background:
        linear-gradient(
            100deg,
            #116cff,
            #247eff,
            #673cf0
        ) !important;

    color: white !important;

    font-weight: 700 !important;
    min-height: 43px;

    box-shadow:
        0 8px 25px rgba(24,105,255,0.22);

    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow:
        0 12px 35px rgba(30,115,255,0.36);
}


/* Inputs */
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
.stNumberInput input {
    background: rgba(3,18,39,0.80) !important;
    color: #e9f4ff !important;
    border-color: rgba(65,132,213,0.35) !important;
    border-radius: 10px !important;
}

label {
    color: #8faecc !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}


/* File uploader */
section[data-testid="stFileUploader"] {
    background: rgba(4,21,45,0.55);
    border-radius: 14px;
}

section[data-testid="stFileUploader"] > div {
    border-color: rgba(54,135,235,0.42) !important;
    border-radius: 14px !important;
}


/* Audio player */
audio {
    width: 100%;
    border-radius: 12px;
}


/* Tabs */
button[data-baseweb="tab"] {
    color: #7598bf !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #4ba4ff !important;
}


/* Expanders */
details {
    background: rgba(4,19,41,0.55) !important;
    border: 1px solid rgba(58,121,195,0.22) !important;
    border-radius: 12px !important;
}


/* Divider */
hr {
    border-color: rgba(64,128,200,0.15) !important;
}


/* Footer */
.footer {
    margin-top: 35px;
    padding: 18px 5px;

    display: flex;
    justify-content: space-between;
    align-items: center;

    border-top: 1px solid rgba(68,125,194,0.18);

    color: #587797;
    font-size: 10px;
}

.footer strong {
    color: #3e9bff;
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


/* Mobile */
@media (max-width: 900px) {

    .hero-title {
        font-size: 27px;
    }

    .top-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }

    .footer {
        flex-direction: column;
        gap: 8px;
        align-items: flex-start;
    }
}

</style>

<div class="bg-orb orb-one"></div>
<div class="bg-orb orb-two"></div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# GEMINI CONFIG
# ============================================================

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not API_KEY:
    st.error("GEMINI_API_KEY is not configured in Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=API_KEY)

PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "image_result": None,
    "audio_result": None,
    "image_qc": [],
    "audio_qc": [],
    "image_manifest": [],
    "audio_manifest": [],
    "image_generation_id": 0,
    "audio_generation_id": 0,
    "last_image_name": "",
    "last_audio_name": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def is_retryable_error(error):
    text = str(error).upper()

    retry_words = [
        "503",
        "UNAVAILABLE",
        "RESOURCE_EXHAUSTED",
        "429",
        "OVERLOADED",
        "HIGH DEMAND",
        "TIMEOUT",
    ]

    return any(word in text for word in retry_words)


def generate_with_fallback(contents, config=None):
    models = [PRIMARY_MODEL] + [
        m for m in FALLBACK_MODELS if m != PRIMARY_MODEL
    ]

    errors = []

    for model in models:
        for attempt in range(2):
            try:
                if config:
                    response = client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config,
                    )
                else:
                    response = client.models.generate_content(
                        model=model,
                        contents=contents,
                    )

                return response, model, None

            except Exception as e:
                errors.append(f"{model}: {str(e)}")

                if not is_retryable_error(e):
                    break

                time.sleep(1.5 * (attempt + 1))

    return None, None, "\n".join(errors)


def get_response_text(response):
    if response is None:
        return ""

    try:
        return response.text or ""
    except Exception:
        pass

    try:
        if response.candidates:
            content = response.candidates[0].content

            if content and content.parts:
                return "\n".join(
                    getattr(part, "text", "")
                    for part in content.parts
                    if getattr(part, "text", None)
                )
    except Exception:
        pass

    return ""


def clean_json_response(text):
    if not text:
        return ""

    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()


def safe_json_loads(text):
    cleaned = clean_json_response(text)

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {}


def normalize_text(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return "\n".join(str(x) for x in value)

    return str(value).strip()


def get_description_lines(result):
    if not isinstance(result, dict):
        return []

    candidates = [
        result.get("description_lines"),
        result.get("description"),
        result.get("audio_description"),
        result.get("visual_description"),
    ]

    for candidate in candidates:

        if isinstance(candidate, list):
            return [
                str(x).strip()
                for x in candidate
                if str(x).strip()
            ]

        if isinstance(candidate, str) and candidate.strip():
            lines = [
                x.strip()
                for x in candidate.splitlines()
                if x.strip()
            ]

            return lines

    return []


def get_confidence(result):
    if not isinstance(result, dict):
        return None

    value = result.get("confidence")

    if value is None:
        return None

    try:
        value = float(value)

        if value <= 1:
            value *= 100

        return max(0, min(100, value))

    except Exception:
        return None


def description_to_text(lines):
    return "\n".join(lines)


def json_config():
    return types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    )


def escape(value):
    return html.escape(str(value))


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">
                ✦ SEED <span>Lab</span>
            </div>
            <div class="sidebar-subtitle">
                Multimodal Studio
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section">STUDIO</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Studio Mode",
        [
            "🎙️ Audio Studio",
            "🖼️ Image Studio",
        ],
        label_visibility="collapsed",
    )

    st.markdown(
        '<div class="sidebar-section">AI SETTINGS</div>',
        unsafe_allow_html=True,
    )

    translation_language = st.selectbox(
        "Target Translation Language",
        [
            "Hindi",
            "English",
            "Kannada",
            "Telugu",
            "Tamil",
            "Malayalam",
            "Spanish",
        ],
    )

    st.markdown(
        '<div class="sidebar-section">SYSTEM</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="connection-pill">
            <span class="connection-dot"></span>
            Gemini Cloud Engine Connected
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="
            margin-top:14px;
            color:#6484a8;
            font-size:10px;
            line-height:1.7;
        ">
            Primary Model<br>
            <span style="color:#8cb7e8;">{PRIMARY_MODEL}</span><br><br>
            Fallback Enabled<br>
            <span style="color:#8cb7e8;">{FALLBACK_MODELS[0]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            position:absolute;
            bottom:30px;
            left:22px;
            right:22px;
            color:#6686a8;
            font-size:10px;
            line-height:1.6;
        ">
            <span style="color:#2594ff;font-weight:700;font-size:15px;">
                SEED Lab
            </span><br>
            Innovating Multimodal AI<br>
            for a Smarter Tomorrow
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# TOP HEADER
# ============================================================

st.markdown(
    f"""
    <div class="top-header">

        <div class="brand-area">

            <div class="brand-icon">✦</div>

            <div>
                <div class="brand-title">
                    SEED <span>Lab</span> Multimodal Studio
                </div>

                <div class="brand-tagline">
                    AI-powered annotation · translation · quality control
                </div>
            </div>

        </div>

        <div class="connection-pill">
            <span class="connection-dot"></span>
            Gemini Connected
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-small">
            MULTIMODAL AI WORKSPACE
        </div>

        <h1 class="hero-title">
            Welcome to <span>SEED Lab Multimodal Studio</span>
        </h1>

        <div class="hero-description">
            Upload your audio or image and get AI-powered
            transcription, OCR, translation, descriptions
            and quality control — all in one professional workspace.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# AUDIO STUDIO
# ============================================================

if mode == "🎙️ Audio Studio":

    st.markdown(
        """
        <div class="section-title">
            Audio Workspace
            <div class="section-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.15, 0.85], gap="large")

    # --------------------------------------------------------
    # AUDIO INPUT
    # --------------------------------------------------------

    with left:

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">🎙</div>

                    <div>
                        <div class="card-title">
                            Audio Studio
                        </div>

                        <div class="card-subtitle">
                            Transcription · Translation · AI Description
                        </div>
                    </div>

                </div>
            """,
            unsafe_allow_html=True,
        )

        audio_file = st.file_uploader(
            "Upload audio",
            type=[
                "mp3",
                "wav",
                "m4a",
                "aac",
                "flac",
                "ogg",
                "webm",
            ],
            key="audio_uploader",
        )

        if not audio_file:

            st.markdown(
                """
                <div class="upload-info">
                    <div style="font-size:30px;margin-bottom:8px;">
                        ☁
                    </div>

                    <b style="color:#b7d8fa;">
                        Drop your audio file here
                    </b>

                    <br><br>

                    MP3 · WAV · M4A · AAC · FLAC · OGG · WEBM
                </div>
                """,
                unsafe_allow_html=True,
            )

        lines_required = st.number_input(
            "Description Lines Required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
        )

        generate_audio = st.button(
            "✦  Generate Audio Analysis",
            key="generate_audio",
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # AUDIO STATUS
    # --------------------------------------------------------

    with right:

        result = st.session_state.audio_result

        confidence = get_confidence(result)

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">◈</div>

                    <div style="flex:1;">
                        <div class="card-title">
                            Analysis Status
                        </div>

                        <div class="card-subtitle">
                            Gemini multimodal processing engine
                        </div>
                    </div>

                    <div class="status-active">
                        <span class="status-dot"></span>
                        ACTIVE
                    </div>

                </div>
            """,
            unsafe_allow_html=True,
        )

        model_display = (
            result.get("model", PRIMARY_MODEL)
            if isinstance(result, dict)
            else PRIMARY_MODEL
        )

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    AI MODEL
                </div>

                <div style="
                    color:#eaf4ff;
                    font-size:16px;
                    font-weight:700;
                    margin-top:7px;
                ">
                    ✦ {escape(model_display)}
                </div>

                <div class="metric-small">
                    Gemini cloud processing
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        confidence_text = (
            f"{confidence:.1f}%"
            if confidence is not None
            else "Not supplied"
        )

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    CONFIDENCE
                </div>

                <div class="metric-value">
                    {confidence_text}
                </div>

                <div class="metric-small">
                    Gemini-provided confidence
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)


    # --------------------------------------------------------
    # PROCESS AUDIO
    # --------------------------------------------------------

    if generate_audio:

        if not audio_file:

            st.warning("Please upload an audio file first.")

        else:

            with st.spinner("Analyzing audio with Gemini..."):

                try:

                    audio_bytes = audio_file.read()

                    uploaded_audio = client.files.upload(
                        file=io.BytesIO(audio_bytes),
                        config=types.UploadFileConfig(
                            mime_type=audio_file.type
                        ),
                    )

                    prompt = f"""
You are an expert multimodal data annotation and quality-control assistant.

Analyze the uploaded audio carefully.

Return ONLY valid JSON.

Required JSON structure:

{{
  "transcript": "complete speech transcript",
  "translation": "translation into {translation_language}",
  "description_lines": [
      "line 1",
      "line 2"
  ],
  "confidence": 0.0
}}

IMPORTANT:

1. Generate EXACTLY {int(lines_required)} description lines.
2. Each description line must be a complete sentence.
3. Describe the actual audio content, speech, environment,
   background sounds, speaker characteristics when relevant,
   recording quality, and notable acoustic events.
4. Do not invent events that cannot reasonably be heard.
5. Transcript should contain the spoken content.
6. Translation should translate the transcript into {translation_language}.
7. Confidence must be a number between 0 and 1.
8. Return valid JSON only.
"""

                    response, used_model, error = generate_with_fallback(
                        [
                            prompt,
                            uploaded_audio,
                        ],
                        config=json_config(),
                    )

                    if response:

                        raw_text = get_response_text(response)
                        parsed = safe_json_loads(raw_text)

                        parsed["model"] = used_model
                        parsed["_raw_response"] = raw_text

                        st.session_state.audio_result = parsed
                        st.session_state.audio_generation_id += 1
                        st.session_state.last_audio_name = audio_file.name

                        # QC
                        desc_lines = get_description_lines(parsed)

                        qc = []

                        qc.append({
                            "check": "Description line count",
                            "status": len(desc_lines) == int(lines_required),
                            "detail": f"{len(desc_lines)} / {int(lines_required)} lines",
                        })

                        transcript = normalize_text(
                            parsed.get("transcript")
                        )

                        qc.append({
                            "check": "Transcript generated",
                            "status": bool(transcript),
                            "detail": "Transcript available"
                            if transcript
                            else "Transcript is empty",
                        })

                        translation = normalize_text(
                            parsed.get("translation")
                        )

                        qc.append({
                            "check": "Translation generated",
                            "status": bool(translation),
                            "detail": "Translation available"
                            if translation
                            else "Translation is empty",
                        })

                        st.session_state.audio_qc = qc

                        st.session_state.audio_manifest.append({
                            "timestamp": time.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "file": audio_file.name,
                            "model": used_model,
                            "description_lines": len(desc_lines),
                            "requested_lines": int(lines_required),
                            "confidence": get_confidence(parsed),
                            "qc_passed": sum(
                                x["status"] for x in qc
                            ),
                            "qc_total": len(qc),
                        })

                        st.success("Audio analysis completed.")

                    else:

                        st.error(
                            "Gemini could not process the audio."
                        )

                        with st.expander("Technical Error"):
                            st.code(error or "Unknown error")

                except Exception as e:

                    st.error("Audio processing failed.")

                    with st.expander("Technical Error"):
                        st.code(str(e))


    # --------------------------------------------------------
    # AUDIO RESULTS
    # --------------------------------------------------------

    result = st.session_state.audio_result

    if result:

        st.markdown(
            """
            <div class="section-title">
                Analysis Results
                <div class="section-line"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Audio player
        if audio_file:

            st.markdown(
                '<div class="glass-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="card-header">

                    <div class="card-icon">♫</div>

                    <div>
                        <div class="card-title">
                            {escape(audio_file.name)}
                        </div>

                        <div class="card-subtitle">
                            Source audio
                        </div>
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            st.audio(
                audio_file.getvalue(),
                format=audio_file.type,
            )

            st.markdown("</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")

        # Transcript
        with col1:

            transcript = normalize_text(
                result.get("transcript")
            )

            st.markdown(
                f"""
                <div class="glass-card">

                    <div class="card-header">

                        <div class="card-icon">▤</div>

                        <div>
                            <div class="card-title">
                                Transcript
                            </div>

                            <div class="card-subtitle">
                                Detected speech
                            </div>
                        </div>

                    </div>

                    <div class="transcript-box">
                        {escape(transcript)
                        if transcript
                        else "No transcript was generated."}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        # Translation
        with col2:

            translation = normalize_text(
                result.get("translation")
            )

            st.markdown(
                f"""
                <div class="glass-card">

                    <div class="card-header">

                        <div class="card-icon">文</div>

                        <div style="flex:1;">
                            <div class="card-title">
                                Translation
                            </div>

                            <div class="card-subtitle">
                                Target language: {escape(translation_language)}
                            </div>
                        </div>

                    </div>

                    <div class="translation-box">
                        {escape(translation)
                        if translation
                        else "No translation was generated."}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        # Description
        description_lines = get_description_lines(result)

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">🔊</div>

                    <div style="flex:1;">
                        <div class="card-title">
                            AI Audio Description
                        </div>

                        <div class="card-subtitle">
                            Structured acoustic description
                        </div>
                    </div>

                </div>
            """,
            unsafe_allow_html=True,
        )

        if description_lines:

            for index, line in enumerate(description_lines, 1):

                st.markdown(
                    f"""
                    <div class="description-line">

                        <div class="line-number">
                            {index:02d}
                        </div>

                        <div>
                            {escape(line)}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                """
                <div class="transcript-box">
                    No audio description was generated.
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # QC
        st.markdown(
            """
            <div class="section-title">
                Quality Control
                <div class="section-line"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        qc = st.session_state.audio_qc

        passed = sum(x["status"] for x in qc)
        total = len(qc)

        if total and passed == total:

            st.markdown(
                f"""
                <div class="qc-pass">

                    <div class="qc-icon">✓</div>

                    <div>
                        <div class="qc-title">
                            QC PASS · {passed}/{total}
                        </div>

                        <div class="qc-text">
                            All quality-control checks passed successfully.
                        </div>
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.warning(
                f"QC result: {passed}/{total} checks passed."
            )

        with st.expander("View QC Details"):

            for item in qc:

                symbol = "✓" if item["status"] else "✕"

                st.write(
                    f"{symbol} **{item['check']}** — {item['detail']}"
                )

        with st.expander("Developer / Gemini Response"):

            st.code(
                result.get("_raw_response", ""),
                language="json",
            )


# ============================================================
# IMAGE STUDIO
# ============================================================

else:

    st.markdown(
        """
        <div class="section-title">
            Image Workspace
            <div class="section-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 0.95], gap="large")

    # --------------------------------------------------------
    # IMAGE INPUT
    # --------------------------------------------------------

    with left:

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">▧</div>

                    <div>
                        <div class="card-title">
                            Image Studio
                        </div>

                        <div class="card-subtitle">
                            OCR · Translation · Visual Description
                        </div>
                    </div>

                </div>
            """,
            unsafe_allow_html=True,
        )

        image_file = st.file_uploader(
            "Upload image",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key="image_uploader",
        )

        lines_required = st.number_input(
            "Description Lines Required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
            key="image_lines",
        )

        if image_file:

            try:

                image = Image.open(image_file)

                st.image(
                    image,
                    use_container_width=True,
                )

            except Exception:

                st.error("Could not read the uploaded image.")

        else:

            st.markdown(
                """
                <div class="upload-info">

                    <div style="font-size:30px;margin-bottom:8px;">
                        ◫
                    </div>

                    <b style="color:#b7d8fa;">
                        Upload an image for AI analysis
                    </b>

                    <br><br>

                    PNG · JPG · JPEG · WEBP

                </div>
                """,
                unsafe_allow_html=True,
            )

        generate_image = st.button(
            "✦  Generate Image Analysis",
            key="generate_image",
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # IMAGE STATUS
    # --------------------------------------------------------

    with right:

        result = st.session_state.image_result

        confidence = get_confidence(result)

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">◈</div>

                    <div style="flex:1;">
                        <div class="card-title">
                            Analysis Status
                        </div>

                        <div class="card-subtitle">
                            OCR and visual understanding engine
                        </div>
                    </div>

                    <div class="status-active">
                        <span class="status-dot"></span>
                        ACTIVE
                    </div>

                </div>
            """,
            unsafe_allow_html=True,
        )

        model_display = (
            result.get("model", PRIMARY_MODEL)
            if isinstance(result, dict)
            else PRIMARY_MODEL
        )

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    AI MODEL
                </div>

                <div style="
                    color:#eaf4ff;
                    font-size:16px;
                    font-weight:700;
                    margin-top:7px;
                ">
                    ✦ {escape(model_display)}
                </div>

                <div class="metric-small">
                    Gemini visual processing
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        confidence_text = (
            f"{confidence:.1f}%"
            if confidence is not None
            else "Not supplied"
        )

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    CONFIDENCE
                </div>

                <div class="metric-value">
                    {confidence_text}
                </div>

                <div class="metric-small">
                    Gemini-provided confidence
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)


    # --------------------------------------------------------
    # PROCESS IMAGE
    # --------------------------------------------------------

    if generate_image:

        if not image_file:

            st.warning("Please upload an image first.")

        else:

            with st.spinner("Analyzing image with Gemini..."):

                try:

                    image_bytes = image_file.getvalue()

                    image = Image.open(
                        io.BytesIO(image_bytes)
                    )

                    prompt = f"""
You are an expert multimodal data annotation and
quality-control assistant.

Analyze the uploaded image carefully.

Return ONLY valid JSON.

Required JSON:

{{
  "ocr_text": "all clearly readable text in the image",
  "translation": "translation of the OCR text into {translation_language}",
  "description_lines": [
      "line 1",
      "line 2"
  ],
  "confidence": 0.0
}}

IMPORTANT:

1. Generate EXACTLY {int(lines_required)} description lines.
2. Each description line must be a complete sentence.
3. Describe visible objects, people without identifying them,
   setting, layout, colors, actions, text, signs and relevant
   visual details.
4. Do not invent details.
5. OCR must contain only text actually visible.
6. Translation must translate the OCR text into {translation_language}.
7. Confidence must be a number between 0 and 1.
8. Return valid JSON only.
"""

                    response, used_model, error = generate_with_fallback(
                        [
                            prompt,
                            image,
                        ],
                        config=json_config(),
                    )

                    if response:

                        raw_text = get_response_text(response)

                        parsed = safe_json_loads(
                            raw_text
                        )

                        parsed["model"] = used_model
                        parsed["_raw_response"] = raw_text

                        st.session_state.image_result = parsed
                        st.session_state.image_generation_id += 1
                        st.session_state.last_image_name = image_file.name

                        desc_lines = get_description_lines(parsed)

                        qc = []

                        qc.append({
                            "check": "Description line count",
                            "status": len(desc_lines) == int(lines_required),
                            "detail": f"{len(desc_lines)} / {int(lines_required)} lines",
                        })

                        ocr = normalize_text(
                            parsed.get("ocr_text")
                        )

                        qc.append({
                            "check": "OCR generated",
                            "status": bool(ocr),
                            "detail": "OCR text detected"
                            if ocr
                            else "No OCR text detected",
                        })

                        translation = normalize_text(
                            parsed.get("translation")
                        )

                        qc.append({
                            "check": "Translation generated",
                            "status": bool(translation),
                            "detail": "Translation available"
                            if translation
                            else "Translation is empty",
                        })

                        st.session_state.image_qc = qc

                        st.session_state.image_manifest.append({
                            "timestamp": time.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "file": image_file.name,
                            "model": used_model,
                            "description_lines": len(desc_lines),
                            "requested_lines": int(lines_required),
                            "confidence": get_confidence(parsed),
                            "qc_passed": sum(
                                x["status"] for x in qc
                            ),
                            "qc_total": len(qc),
                        })

                        st.success("Image analysis completed.")

                    else:

                        st.error(
                            "Gemini could not process the image."
                        )

                        with st.expander("Technical Error"):
                            st.code(error or "Unknown error")

                except Exception as e:

                    st.error("Image processing failed.")

                    with st.expander("Technical Error"):
                        st.code(str(e))


    # --------------------------------------------------------
    # IMAGE RESULTS
    # --------------------------------------------------------

    result = st.session_state.image_result

    if result:

        st.markdown(
            """
            <div class="section-title">
                Analysis Results
                <div class="section-line"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2, gap="large")

        # OCR
        with col1:

            ocr = normalize_text(
                result.get("ocr_text")
            )

            st.markdown(
                f"""
                <div class="glass-card">

                    <div class="card-header">

                        <div class="card-icon">▤</div>

                        <div>
                            <div class="card-title">
                                OCR Text
                            </div>

                            <div class="card-subtitle">
                                Detected text from image
                            </div>
                        </div>

                    </div>

                    <div class="transcript-box">
                        {escape(ocr)
                        if ocr
                        else "No readable text detected."}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        # Translation
        with col2:

            translation = normalize_text(
                result.get("translation")
            )

            st.markdown(
                f"""
                <div class="glass-card">

                    <div class="card-header">

                        <div class="card-icon">文</div>

                        <div>
                            <div class="card-title">
                                Translation
                            </div>

                            <div class="card-subtitle">
                                {escape(translation_language)}
                            </div>
                        </div>

                    </div>

                    <div class="translation-box">
                        {escape(translation)
                        if translation
                        else "No translation generated."}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        # Description
        description_lines = get_description_lines(result)

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">✦</div>

                    <div>
                        <div class="card-title">
                            AI Visual Description
                        </div>

                        <div class="card-subtitle">
                            Structured image understanding
                        </div>
                    </div>

                </div>
            """,
            unsafe_allow_html=True,
        )

        if description_lines:

            for index, line in enumerate(description_lines, 1):

                st.markdown(
                    f"""
                    <div class="description-line">

                        <div class="line-number">
                            {index:02d}
                        </div>

                        <div>
                            {escape(line)}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                """
                <div class="transcript-box">
                    No visual description generated.
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # QC
        st.markdown(
            """
            <div class="section-title">
                Quality Control
                <div class="section-line"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        qc = st.session_state.image_qc

        passed = sum(x["status"] for x in qc)
        total = len(qc)

        if total and passed == total:

            st.markdown(
                f"""
                <div class="qc-pass">

                    <div class="qc-icon">✓</div>

                    <div>
                        <div class="qc-title">
                            QC PASS · {passed}/{total}
                        </div>

                        <div class="qc-text">
                            All quality-control checks passed successfully.
                        </div>
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.warning(
                f"QC result: {passed}/{total} checks passed."
            )

        with st.expander("View QC Details"):

            for item in qc:

                symbol = "✓" if item["status"] else "✕"

                st.write(
                    f"{symbol} **{item['check']}** — {item['detail']}"
                )

        with st.expander("Developer / Gemini Response"):

            st.code(
                result.get("_raw_response", ""),
                language="json",
            )


# ============================================================
# AUDITOR CONSOLE
# ============================================================

st.markdown(
    """
    <div class="section-title">
        Auditor Console
        <div class="section-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="glass-card">

        <div class="card-header">

            <div class="card-icon">✓</div>

            <div>
                <div class="card-title">
                    Quality Control & Audit Logs
                </div>

                <div class="card-subtitle">
                    Review processed multimodal data and export manifests
                </div>
            </div>

        </div>
    """,
    unsafe_allow_html=True,
)

image_df = pd.DataFrame(
    st.session_state.image_manifest
)

audio_df = pd.DataFrame(
    st.session_state.audio_manifest
)

tab1, tab2 = st.tabs(
    [
        "🎙️ Audio Manifest",
        "🖼️ Image Manifest",
    ]
)

with tab1:

    if not audio_df.empty:

        st.dataframe(
            audio_df,
            use_container_width=True,
            hide_index=True,
        )

        csv = audio_df.to_csv(index=False).encode(
            "utf-8"
        )

        st.download_button(
            "⬇ Download Audio CSV",
            csv,
            "audio_manifest.csv",
            "text/csv",
            key="download_audio",
        )

    else:

        st.info(
            "No audio audit records yet."
        )


with tab2:

    if not image_df.empty:

        st.dataframe(
            image_df,
            use_container_width=True,
            hide_index=True,
        )

        csv = image_df.to_csv(index=False).encode(
            "utf-8"
        )

        st.download_button(
            "⬇ Download Image CSV",
            csv,
            "image_manifest.csv",
            "text/csv",
            key="download_image",
        )

    else:

        st.info(
            "No image audit records yet."
        )

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

        <div>
            ✦ &nbsp;
            Powered by <strong>Google Gemini</strong>
            &nbsp; | &nbsp;
            SEED Lab Multimodal Studio
        </div>

        <div>
            Better Data → Better Models → A More Inclusive World
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)