import streamlit as st
import pandas as pd
from PIL import Image
from google import genai
from google.genai import types
import io
import json
import re
import time
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
# PROFESSIONAL DARK UI
# ============================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    * {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 85% 5%,
                rgba(35, 110, 255, 0.20),
                transparent 28%
            ),
            radial-gradient(
                circle at 5% 80%,
                rgba(105, 40, 210, 0.13),
                transparent 28%
            ),
            linear-gradient(
                135deg,
                #020817 0%,
                #031329 50%,
                #020611 100%
            );

        color: #edf5ff;
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        opacity: 0.12;

        background-image:
            linear-gradient(
                rgba(70,140,255,0.08) 1px,
                transparent 1px
            ),
            linear-gradient(
                90deg,
                rgba(70,140,255,0.08) 1px,
                transparent 1px
            );

        background-size: 45px 45px;
        z-index: 0;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        position: relative;
        z-index: 1;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #03162f 0%,
                #020a18 100%
            );

        border-right: 1px solid rgba(56,135,235,0.25);
    }

    .sidebar-brand {
        padding: 12px 10px 24px;
        border-bottom: 1px solid rgba(75,135,210,0.17);
        margin-bottom: 20px;
    }

    .sidebar-logo {
        font-size: 27px;
        font-weight: 800;
        color: white;
    }

    .sidebar-logo span {
        color: #45a2ff;
    }

    .sidebar-subtitle {
        color: #7399c2;
        font-size: 12px;
        margin-top: 3px;
    }

    .sidebar-label {
        color: #58799e;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.6px;
        margin: 20px 10px 9px;
    }

    .system-box {
        margin-top: 14px;
        padding: 13px;
        border-radius: 12px;
        background: rgba(20,90,170,0.08);
        border: 1px solid rgba(58,135,225,0.22);
    }

    .system-title {
        color: #8cb8e5;
        font-size: 10px;
        font-weight: 700;
    }

    .system-value {
        color: #d9ebff;
        font-size: 11px;
        margin-top: 5px;
    }


    /* ========================================================
       TOP BRAND
       ======================================================== */

    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
    }

    .brand-area {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .brand-icon {
        width: 50px;
        height: 50px;

        border-radius: 15px;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 25px;

        background:
            linear-gradient(
                135deg,
                #1474ff,
                #7139e8
            );

        box-shadow:
            0 0 35px rgba(45,120,255,0.30);
    }

    .brand-title {
        color: #f5f9ff;
        font-size: 22px;
        font-weight: 800;
    }

    .brand-title span {
        color: #4aa7ff;
    }

    .brand-tagline {
        color: #6f91b7;
        font-size: 11px;
        margin-top: 3px;
    }

    .connection-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;

        padding: 9px 15px;

        border-radius: 999px;

        background: rgba(5,34,70,0.75);

        border: 1px solid rgba(48,139,255,0.45);

        color: #91caff;

        font-size: 11px;
        font-weight: 700;
    }

    .connection-dot {
        width: 8px;
        height: 8px;

        border-radius: 50%;

        background: #32e776;

        box-shadow:
            0 0 12px #32e776;
    }


    /* ========================================================
       HERO
       ======================================================== */

    .hero {
        position: relative;
        overflow: hidden;

        padding: 31px 34px;

        border-radius: 20px;

        border: 1px solid rgba(50,139,255,0.48);

        background:
            radial-gradient(
                circle at 88% 50%,
                rgba(38,110,255,0.28),
                transparent 35%
            ),
            linear-gradient(
                110deg,
                rgba(5,31,66,0.97),
                rgba(3,18,39,0.93)
            );

        box-shadow:
            0 20px 60px rgba(0,0,0,0.35),
            inset 0 1px 0 rgba(255,255,255,0.04);

        margin-bottom: 25px;
    }

    .hero-small {
        color: #55aaff;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.8px;
        margin-bottom: 9px;
    }

    .hero-title {
        color: #f5faff;
        font-size: 34px;
        line-height: 1.15;
        font-weight: 800;
        margin: 0;
    }

    .hero-title span {
        color: #4ca5ff;
        text-shadow:
            0 0 25px rgba(53,142,255,0.30);
    }

    .hero-description {
        color: #9eb8d5;
        font-size: 13px;
        line-height: 1.7;
        max-width: 730px;
        margin-top: 12px;
    }


    /* ========================================================
       SECTION HEADERS
       ======================================================== */

    .section-title {
        display: flex;
        align-items: center;
        gap: 16px;

        color: #edf5ff;

        font-size: 19px;
        font-weight: 800;

        margin: 26px 0 14px;
    }

    .section-line {
        height: 1px;
        flex: 1;

        background:
            linear-gradient(
                90deg,
                rgba(50,135,255,0.35),
                transparent
            );
    }


    /* ========================================================
       GLASS CARDS
       ======================================================== */

    .glass-card {
        background:
            linear-gradient(
                145deg,
                rgba(8,32,66,0.88),
                rgba(3,17,37,0.91)
            );

        border: 1px solid rgba(60,130,215,0.30);

        border-radius: 18px;

        padding: 20px;

        box-shadow:
            0 18px 50px rgba(0,0,0,0.25),
            inset 0 1px 0 rgba(255,255,255,0.035);

        margin-bottom: 18px;
    }

    .card-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 17px;
    }

    .card-icon {
        width: 42px;
        height: 42px;

        flex-shrink: 0;

        border-radius: 13px;

        display: flex;
        align-items: center;
        justify-content: center;

        background:
            linear-gradient(
                135deg,
                rgba(25,116,255,0.90),
                rgba(95,53,220,0.90)
            );

        box-shadow:
            0 0 25px rgba(36,120,255,0.20);

        font-size: 18px;
    }

    .card-title {
        color: #f1f7ff;
        font-size: 16px;
        font-weight: 750;
    }

    .card-subtitle {
        color: #6889ae;
        font-size: 10px;
        margin-top: 3px;
    }


    /* ========================================================
       METRICS
       ======================================================== */

    .metric-card {
        background:
            linear-gradient(
                145deg,
                rgba(10,39,78,0.88),
                rgba(4,20,43,0.91)
            );

        border: 1px solid rgba(61,132,219,0.27);

        border-radius: 14px;

        padding: 16px;

        min-height: 96px;
    }

    .metric-label {
        color: #7192b8;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    .metric-value {
        color: #f5f9ff;
        font-size: 25px;
        font-weight: 800;
        margin-top: 7px;
    }

    .metric-small {
        color: #4c8ac2;
        font-size: 9px;
        margin-top: 4px;
    }


    /* ========================================================
       STATUS
       ======================================================== */

    .status-active {
        display: inline-flex;
        align-items: center;
        gap: 6px;

        padding: 5px 9px;

        border-radius: 999px;

        color: #45eb88;

        background: rgba(22,170,85,0.10);

        border: 1px solid rgba(45,215,110,0.22);

        font-size: 9px;
        font-weight: 800;
    }

    .status-dot {
        width: 6px;
        height: 6px;

        border-radius: 50%;

        background: #36e979;

        box-shadow:
            0 0 10px #36e979;
    }


    /* ========================================================
       UPLOAD
       ======================================================== */

    .upload-info {
        text-align: center;

        padding: 23px;

        border-radius: 14px;

        border: 1px dashed rgba(58,145,255,0.48);

        background: rgba(25,95,175,0.05);

        color: #7097bf;

        font-size: 11px;
    }


    /* ========================================================
       DESCRIPTION
       ======================================================== */

    .description-line {
        display: flex;
        align-items: flex-start;
        gap: 12px;

        padding: 11px 0;

        border-bottom: 1px solid rgba(77,124,176,0.12);

        color: #d7e7f8;

        font-size: 12px;

        line-height: 1.55;
    }

    .description-line:last-child {
        border-bottom: none;
    }

    .line-number {
        width: 27px;
        height: 27px;

        flex-shrink: 0;

        border-radius: 9px;

        display: flex;
        align-items: center;
        justify-content: center;

        background: rgba(28,111,245,0.12);

        border: 1px solid rgba(52,135,255,0.30);

        color: #5eacff;

        font-size: 9px;
        font-weight: 800;
    }


    /* ========================================================
       TEXT BOXES
       ======================================================== */

    .transcript-box {
        min-height: 115px;

        padding: 15px;

        border-radius: 13px;

        background: rgba(1,12,28,0.62);

        border: 1px solid rgba(59,122,190,0.22);

        color: #bcd0e7;

        font-size: 12px;

        line-height: 1.65;
    }

    .translation-box {
        min-height: 115px;

        padding: 15px;

        border-radius: 13px;

        background:
            linear-gradient(
                145deg,
                rgba(12,49,94,0.65),
                rgba(6,26,53,0.70)
            );

        border: 1px solid rgba(60,138,235,0.25);

        color: #d7eaff;

        font-size: 13px;

        line-height: 1.7;
    }


    /* ========================================================
       QC
       ======================================================== */

    .qc-pass {
        display: flex;
        align-items: center;
        gap: 13px;

        padding: 16px;

        border-radius: 14px;

        background: rgba(15,130,76,0.09);

        border: 1px solid rgba(40,208,116,0.28);
    }

    .qc-icon {
        width: 38px;
        height: 38px;

        flex-shrink: 0;

        border-radius: 50%;

        display: flex;
        align-items: center;
        justify-content: center;

        background: rgba(37,205,112,0.14);

        color: #42ed8a;

        font-size: 18px;
    }

    .qc-title {
        color: #4bed90;
        font-size: 13px;
        font-weight: 800;
    }

    .qc-text {
        color: #6f95b8;
        font-size: 9px;
        margin-top: 3px;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        width: 100%;

        min-height: 43px;

        border: none !important;

        border-radius: 11px !important;

        color: white !important;

        font-weight: 700 !important;

        background:
            linear-gradient(
                100deg,
                #126cff,
                #267fff,
                #663ce8
            ) !important;

        box-shadow:
            0 9px 28px rgba(27,109,255,0.22);

        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);

        box-shadow:
            0 13px 35px rgba(30,115,255,0.35);
    }


    /* ========================================================
       INPUTS
       ======================================================== */

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        background: rgba(3,18,39,0.82) !important;
        color: #e8f4ff !important;

        border: 1px solid rgba(65,132,213,0.30) !important;

        border-radius: 10px !important;
    }

    label {
        color: #89a9c9 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
    }


    /* ========================================================
       FILE UPLOADER
       ======================================================== */

    section[data-testid="stFileUploader"] {
        background: rgba(3,20,42,0.45);
        border-radius: 14px;
    }

    section[data-testid="stFileUploader"] > div {
        border-color: rgba(57,136,230,0.38) !important;
        border-radius: 14px !important;
    }


    /* ========================================================
       AUDIO
       ======================================================== */

    audio {
        width: 100%;
        border-radius: 12px;
    }


    /* ========================================================
       TABS
       ======================================================== */

    button[data-baseweb="tab"] {
        color: #718eaf !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #4ca4ff !important;
    }


    /* ========================================================
       FOOTER
       ======================================================== */

    .footer {
        margin-top: 35px;

        padding: 18px 5px;

        border-top: 1px solid rgba(65,125,194,0.16);

        display: flex;
        justify-content: space-between;

        color: #577795;

        font-size: 9px;
    }

    .footer strong {
        color: #3f9eff;
    }


    /* ========================================================
       HIDE STREAMLIT UI
       ======================================================== */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }


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
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GEMINI
# ============================================================

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not API_KEY:
    st.error("GEMINI_API_KEY is not configured.")
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
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def retryable(error):
    text = str(error).upper()

    return any(
        x in text
        for x in [
            "503",
            "UNAVAILABLE",
            "429",
            "RESOURCE_EXHAUSTED",
            "OVERLOADED",
            "HIGH DEMAND",
            "TIMEOUT",
        ]
    )


def generate_with_fallback(contents, config=None):

    models = [PRIMARY_MODEL] + [
        x for x in FALLBACK_MODELS
        if x != PRIMARY_MODEL
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

                errors.append(
                    f"{model}: {str(e)}"
                )

                if not retryable(e):
                    break

                time.sleep(
                    1.5 * (attempt + 1)
                )

    return None, None, "\n".join(errors)


def response_text(response):

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
                    getattr(
                        part,
                        "text",
                        ""
                    )

                    for part in content.parts

                    if getattr(
                        part,
                        "text",
                        None
                    )
                )

    except Exception:
        pass

    return ""


def parse_json(text):

    if not text:
        return {}

    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
        flags=re.I,
    )

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
            return json.loads(
                match.group(0)
            )
        except Exception:
            pass

    return {}


def text_value(value):

    if value is None:
        return ""

    if isinstance(value, list):
        return "\n".join(
            str(x) for x in value
        )

    return str(value).strip()


def description_lines(result):

    if not isinstance(result, dict):
        return []

    for key in [
        "description_lines",
        "description",
        "audio_description",
        "visual_description",
    ]:

        value = result.get(key)

        if isinstance(value, list):

            return [
                str(x).strip()
                for x in value
                if str(x).strip()
            ]

        if isinstance(value, str) and value.strip():

            return [
                x.strip()
                for x in value.splitlines()
                if x.strip()
            ]

    return []


def confidence(result):

    if not isinstance(result, dict):
        return None

    value = result.get("confidence")

    if value is None:
        return None

    try:

        value = float(value)

        if value <= 1:
            value *= 100

        return max(
            0,
            min(100, value)
        )

    except Exception:
        return None


def esc(value):
    return html.escape(str(value))


def json_config():

    return types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    )


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
        '<div class="sidebar-label">STUDIO</div>',
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
        '<div class="sidebar-label">AI SETTINGS</div>',
        unsafe_allow_html=True,
    )

    language = st.selectbox(
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
        '<div class="sidebar-label">SYSTEM</div>',
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
        <div class="system-box">

            <div class="system-title">
                PRIMARY MODEL
            </div>

            <div class="system-value">
                {esc(PRIMARY_MODEL)}
            </div>

            <br>

            <div class="system-title">
                FALLBACK ENABLED
            </div>

            <div class="system-value">
                {esc(FALLBACK_MODELS[0])}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="top-header">

        <div class="brand-area">

            <div class="brand-icon">
                ✦
            </div>

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
            Welcome to
            <span>SEED Lab Multimodal Studio</span>
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

    left, right = st.columns(
        [1.15, 0.85],
        gap="large",
    )

    # --------------------------------------------------------
    # INPUT
    # --------------------------------------------------------

    with left:

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">
                        🎙
                    </div>

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

        audio = st.file_uploader(
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
            key="audio",
        )

        if not audio:

            st.markdown(
                """
                <div class="upload-info">

                    <div style="
                        font-size:32px;
                        margin-bottom:8px;
                    ">
                        ☁
                    </div>

                    <b style="color:#b7d8fa;">
                        Drop your audio file here
                    </b>

                    <br><br>

                    200MB per file ·
                    MP3 · WAV · M4A · AAC · FLAC · OGG · WEBM

                </div>
                """,
                unsafe_allow_html=True,
            )

        lines = st.number_input(
            "Description Lines Required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
            key="audio_lines",
        )

        analyze_audio = st.button(
            "✦  Generate Audio Analysis",
            key="audio_generate",
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    with right:

        result = st.session_state.audio_result

        conf = confidence(result)

        model = (
            result.get("model", PRIMARY_MODEL)
            if isinstance(result, dict)
            else PRIMARY_MODEL
        )

        conf_text = (
            f"{conf:.1f}%"
            if conf is not None
            else "Not supplied"
        )

        st.markdown(
            f"""
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">
                        ◈
                    </div>

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
                        ✦ {esc(model)}
                    </div>

                    <div class="metric-small">
                        Gemini cloud processing
                    </div>

                </div>

                <div style="height:10px;"></div>

                <div class="metric-card">

                    <div class="metric-label">
                        CONFIDENCE
                    </div>

                    <div class="metric-value">
                        {conf_text}
                    </div>

                    <div class="metric-small">
                        Gemini-provided confidence
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # --------------------------------------------------------
    # AUDIO PROCESSING
    # --------------------------------------------------------

    if analyze_audio:

        if not audio:

            st.warning(
                "Please upload an audio file first."
            )

        else:

            with st.spinner(
                "Analyzing audio with Gemini..."
            ):

                try:

                    audio_bytes = audio.getvalue()

                    uploaded = client.files.upload(
                        file=io.BytesIO(audio_bytes),
                        config=types.UploadFileConfig(
                            mime_type=audio.type
                        ),
                    )

                    prompt = f"""
You are an expert multimodal data annotation
and quality-control assistant.

Analyze the uploaded audio carefully.

Return ONLY valid JSON.

Required structure:

{{
  "transcript": "complete speech transcript",
  "translation": "translation into {language}",
  "description_lines": [
    "line 1",
    "line 2"
  ],
  "confidence": 0.0
}}

Rules:

1. Generate EXACTLY {int(lines)} description lines.
2. Each line must be a complete sentence.
3. Describe actual audio content.
4. Include speech, background sounds,
   environment and notable acoustic events
   when relevant.
5. Do not invent sounds.
6. Transcript should contain spoken content.
7. Translation should translate the transcript
   into {language}.
8. Confidence must be between 0 and 1.
9. Return JSON only.
"""

                    response, model, error = (
                        generate_with_fallback(
                            [
                                prompt,
                                uploaded,
                            ],
                            config=json_config(),
                        )
                    )

                    if response:

                        raw = response_text(
                            response
                        )

                        parsed = parse_json(raw)

                        parsed["model"] = model
                        parsed["_raw_response"] = raw

                        st.session_state.audio_result = parsed

                        desc = description_lines(
                            parsed
                        )

                        transcript = text_value(
                            parsed.get("transcript")
                        )

                        translation = text_value(
                            parsed.get("translation")
                        )

                        qc = [
                            {
                                "check":
                                    "Description line count",

                                "status":
                                    len(desc) == int(lines),

                                "detail":
                                    f"{len(desc)} / {int(lines)} lines",
                            },
                            {
                                "check":
                                    "Transcript generated",

                                "status":
                                    bool(transcript),

                                "detail":
                                    "Transcript available"
                                    if transcript
                                    else
                                    "Transcript is empty",
                            },
                            {
                                "check":
                                    "Translation generated",

                                "status":
                                    bool(translation),

                                "detail":
                                    "Translation available"
                                    if translation
                                    else
                                    "Translation is empty",
                            },
                        ]

                        st.session_state.audio_qc = qc

                        st.session_state.audio_manifest.append(
                            {
                                "timestamp":
                                    time.strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),

                                "file":
                                    audio.name,

                                "model":
                                    model,

                                "description_lines":
                                    len(desc),

                                "requested_lines":
                                    int(lines),

                                "confidence":
                                    confidence(parsed),

                                "qc_passed":
                                    sum(
                                        x["status"]
                                        for x in qc
                                    ),

                                "qc_total":
                                    len(qc),
                            }
                        )

                        st.success(
                            "Audio analysis completed."
                        )

                    else:

                        st.error(
                            "Gemini could not process the audio."
                        )

                        with st.expander(
                            "Technical Error"
                        ):
                            st.code(
                                error
                                or "Unknown error"
                            )

                except Exception as e:

                    st.error(
                        "Audio processing failed."
                    )

                    with st.expander(
                        "Technical Error"
                    ):
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

        if audio:

            st.markdown(
                '<div class="glass-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="card-header">

                    <div class="card-icon">
                        ♫
                    </div>

                    <div>

                        <div class="card-title">
                            {esc(audio.name)}
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
                audio.getvalue(),
                format=audio.type,
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        col1, col2 = st.columns(
            2,
            gap="large",
        )

        with col1:

            transcript = text_value(
                result.get("transcript")
            )

            st.markdown(
                f"""
                <div class="glass-card">

                    <div class="card-header">

                        <div class="card-icon">
                            ▤
                        </div>

                        <div>

                            <div class="card-title">
                                Live Audio Transcript
                            </div>

                            <div class="card-subtitle">
                                Detected speech
                            </div>

                        </div>

                    </div>

                    <div class="transcript-box">
                        {esc(transcript)
                        if transcript
                        else
                        "No transcript was generated."}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:

            translation = text_value(
                result.get("translation")
            )

            st.markdown(
                f"""
                <div class="glass-card">

                    <div class="card-header">

                        <div class="card-icon">
                            文
                        </div>

                        <div>

                            <div class="card-title">
                                Translation
                            </div>

                            <div class="card-subtitle">
                                Target: {esc(language)}
                            </div>

                        </div>

                    </div>

                    <div class="translation-box">
                        {esc(translation)
                        if translation
                        else
                        "No translation was generated."}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        desc = description_lines(
            result
        )

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">
                        🔊
                    </div>

                    <div>

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

        if desc:

            for i, line in enumerate(
                desc,
                1
            ):

                st.markdown(
                    f"""
                    <div class="description-line">

                        <div class="line-number">
                            {i:02d}
                        </div>

                        <div>
                            {esc(line)}
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

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

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

        passed = sum(
            item["status"]
            for item in qc
        )

        total = len(qc)

        if total and passed == total:

            st.markdown(
                f"""
                <div class="qc-pass">

                    <div class="qc-icon">
                        ✓
                    </div>

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

        with st.expander(
            "View QC Details"
        ):

            for item in qc:

                symbol = (
                    "✓"
                    if item["status"]
                    else "✕"
                )

                st.write(
                    f"{symbol} **{item['check']}** — "
                    f"{item['detail']}"
                )

        with st.expander(
            "Developer / Gemini Response"
        ):

            st.code(
                result.get(
                    "_raw_response",
                    ""
                ),
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

    left, right = st.columns(
        [1.05, 0.95],
        gap="large",
    )

    # --------------------------------------------------------
    # IMAGE INPUT
    # --------------------------------------------------------

    with left:

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">
                        ▧
                    </div>

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
            key="image",
        )

        if image_file:

            try:

                image = Image.open(
                    image_file
                )

                st.image(
                    image,
                    use_container_width=True,
                )

            except Exception:

                st.error(
                    "Could not read the image."
                )

        else:

            st.markdown(
                """
                <div class="upload-info">

                    <div style="
                        font-size:32px;
                        margin-bottom:8px;
                    ">
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

        lines = st.number_input(
            "Description Lines Required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
            key="image_lines",
        )

        analyze_image = st.button(
            "✦  Generate Image Analysis",
            key="image_generate",
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # IMAGE STATUS
    # --------------------------------------------------------

    with right:

        result = st.session_state.image_result

        conf = confidence(result)

        model = (
            result.get("model", PRIMARY_MODEL)
            if isinstance(result, dict)
            else PRIMARY_MODEL
        )

        conf_text = (
            f"{conf:.1f}%"
            if conf is not None
            else "Not supplied"
        )

        st.markdown(
            f"""
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">
                        ◈
                    </div>

                    <div style="flex:1;">

                        <div class="card-title">
                            Analysis Status
                        </div>

                        <div class="card-subtitle">
                            Gemini visual processing engine
                        </div>

                    </div>

                    <div class="status-active">
                        <span class="status-dot"></span>
                        ACTIVE
                    </div>

                </div>

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
                        ✦ {esc(model)}
                    </div>

                    <div class="metric-small">
                        Gemini visual processing
                    </div>

                </div>

                <div style="height:10px;"></div>

                <div class="metric-card">

                    <div class="metric-label">
                        CONFIDENCE
                    </div>

                    <div class="metric-value">
                        {conf_text}
                    </div>

                    <div class="metric-small">
                        Gemini-provided confidence
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # --------------------------------------------------------
    # IMAGE PROCESSING
    # --------------------------------------------------------

    if analyze_image:

        if not image_file:

            st.warning(
                "Please upload an image first."
            )

        else:

            with st.spinner(
                "Analyzing image with Gemini..."
            ):

                try:

                    image_bytes = image_file.getvalue()

                    image = Image.open(
                        io.BytesIO(image_bytes)
                    )

                    prompt = f"""
You are an expert multimodal data annotation
and quality-control assistant.

Analyze the uploaded image carefully.

Return ONLY valid JSON.

Required structure:

{{
  "ocr_text": "all clearly readable text",
  "translation": "translation into {language}",
  "description_lines": [
      "line 1",
      "line 2"
  ],
  "confidence": 0.0
}}

Rules:

1. Generate EXACTLY {int(lines)} description lines.
2. Each line must be a complete sentence.
3. Describe visible objects, setting,
   composition, colors, actions and
   relevant visual details.
4. Do not invent details.
5. OCR must contain only visible text.
6. Translate OCR into {language}.
7. Confidence must be between 0 and 1.
8. Return JSON only.
"""

                    response, model, error = (
                        generate_with_fallback(
                            [
                                prompt,
                                image,
                            ],
                            config=json_config(),
                        )
                    )

                    if response:

                        raw = response_text(
                            response
                        )

                        parsed = parse_json(raw)

                        parsed["model"] = model
                        parsed["_raw_response"] = raw

                        st.session_state.image_result = parsed

                        desc = description_lines(
                            parsed
                        )

                        ocr = text_value(
                            parsed.get("ocr_text")
                        )

                        translation = text_value(
                            parsed.get("translation")
                        )

                        qc = [
                            {
                                "check":
                                    "Description line count",

                                "status":
                                    len(desc) == int(lines),

                                "detail":
                                    f"{len(desc)} / {int(lines)} lines",
                            },
                            {
                                "check":
                                    "OCR generated",

                                "status":
                                    bool(ocr),

                                "detail":
                                    "OCR text detected"
                                    if ocr
                                    else
                                    "No OCR text detected",
                            },
                            {
                                "check":
                                    "Translation generated",

                                "status":
                                    bool(translation),

                                "detail":
                                    "Translation available"
                                    if translation
                                    else
                                    "Translation is empty",
                            },
                        ]

                        st.session_state.image_qc = qc

                        st.session_state.image_manifest.append(
                            {
                                "timestamp":
                                    time.strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),

                                "file":
                                    image_file.name,

                                "model":
                                    model,

                                "description_lines":
                                    len(desc),

                                "requested_lines":
                                    int(lines),

                                "confidence":
                                    confidence(parsed),

                                "qc_passed":
                                    sum(
                                        x["status"]
                                        for x in qc
                                    ),

                                "qc_total":
                                    len(qc),
                            }
                        )

                        st.success(
                            "Image analysis completed."
                        )

                    else:

                        st.error(
                            "Gemini could not process the image."
                        )

                        with st.expander(
                            "Technical Error"
                        ):
                            st.code(
                                error
                                or "Unknown error"
                            )

                except Exception as e:

                    st.error(
                        "Image processing failed."
                    )

                    with st.expander(
                        "Technical Error"
                    ):
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

        col1, col2 = st.columns(
            2,
            gap="large",
        )

        with col1:

            ocr = text_value(
                result.get("ocr_text")
            )

            st.markdown(
                f"""
                <div class="glass-card">

                    <div class="card-header">

                        <div class="card-icon">
                            ▤
                        </div>

                        <div>

                            <div class="card-title">
                                OCR Text
                            </div>

                            <div class="card-subtitle">
                                Detected text
                            </div>

                        </div>

                    </div>

                    <div class="transcript-box">
                        {esc(ocr)
                        if ocr
                        else
                        "No readable text detected."}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:

            translation = text_value(
                result.get("translation")
            )

            st.markdown(
                f"""
                <div class="glass-card">

                    <div class="card-header">

                        <div class="card-icon">
                            文
                        </div>

                        <div>

                            <div class="card-title">
                                Translation
                            </div>

                            <div class="card-subtitle">
                                Target: {esc(language)}
                            </div>

                        </div>

                    </div>

                    <div class="translation-box">
                        {esc(translation)
                        if translation
                        else
                        "No translation generated."}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        desc = description_lines(
            result
        )

        st.markdown(
            """
            <div class="glass-card">

                <div class="card-header">

                    <div class="card-icon">
                        ✦
                    </div>

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

        if desc:

            for i, line in enumerate(
                desc,
                1
            ):

                st.markdown(
                    f"""
                    <div class="description-line">

                        <div class="line-number">
                            {i:02d}
                        </div>

                        <div>
                            {esc(line)}
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

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

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

        passed = sum(
            x["status"]
            for x in qc
        )

        total = len(qc)

        if total and passed == total:

            st.markdown(
                f"""
                <div class="qc-pass">

                    <div class="qc-icon">
                        ✓
                    </div>

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

        with st.expander(
            "View QC Details"
        ):

            for item in qc:

                symbol = (
                    "✓"
                    if item["status"]
                    else "✕"
                )

                st.write(
                    f"{symbol} **{item['check']}** — "
                    f"{item['detail']}"
                )

        with st.expander(
            "Developer / Gemini Response"
        ):

            st.code(
                result.get(
                    "_raw_response",
                    ""
                ),
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

            <div class="card-icon">
                ✓
            </div>

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

audio_df = pd.DataFrame(
    st.session_state.audio_manifest
)

image_df = pd.DataFrame(
    st.session_state.image_manifest
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

        csv = audio_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇ Download Audio CSV",
            csv,
            "audio_manifest.csv",
            "text/csv",
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

        csv = image_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇ Download Image CSV",
            csv,
            "image_manifest.csv",
            "text/csv",
        )

    else:

        st.info(
            "No image audit records yet."
        )

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


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