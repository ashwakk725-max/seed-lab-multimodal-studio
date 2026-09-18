import io
import json
import re
import time

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
# GREEN THEME
# ============================================================

st.markdown(
    """
    <style>

    /* =========================
       MAIN BACKGROUND
       ========================= */

    .stApp {
        background: #f3faf7;
        color: #17352d;
    }

    .main .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }


    /* =========================
       SIDEBAR
       ========================= */

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #d8ebe3;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #174d3b !important;
    }

    [data-testid="stSidebar"] p {
        color: #5d756c !important;
    }

    [data-testid="stSidebar"] label {
        color: #24483d !important;
    }


    /* =========================
       HEADINGS
       ========================= */

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


    /* =========================
       CAPTIONS
       ========================= */

    [data-testid="stCaptionContainer"] {
        color: #6b837a !important;
    }


    /* =========================
       METRICS
       ========================= */

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


    /* =========================
       FILE UPLOADER
       ========================= */

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


    /* =========================
       BUTTONS
       ========================= */

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


    /* =========================
       TEXT AREAS
       ========================= */

    textarea {
        background: #ffffff !important;
        color: #183c31 !important;
        border: 1px solid #cfe4da !important;
        border-radius: 10px !important;
    }

    textarea:disabled {
        color: #284d41 !important;
        -webkit-text-fill-color: #284d41 !important;
        opacity: 1 !important;
    }


    /* =========================
       INPUTS
       ========================= */

    input {
        background: #ffffff !important;
        color: #183c31 !important;
    }

    [data-testid="stNumberInput"] input {
        background: #ffffff !important;
        color: #183c31 !important;
        border-color: #cfe4da !important;
    }


    /* =========================
       SELECT BOX
       ========================= */

    [data-baseweb="select"] > div {
        background: #ffffff !important;
        border-color: #cfe4da !important;
        color: #183c31 !important;
    }

    [data-baseweb="select"] {
        color: #183c31 !important;
    }


    /* =========================
       RADIO
       ========================= */

    [data-testid="stRadio"] label {
        color: #24483d !important;
    }


    /* =========================
       TABS
       ========================= */

    button[data-baseweb="tab"] {
        color: #5a7169 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #168457 !important;
        font-weight: 700;
    }


    /* =========================
       DATAFRAME
       ========================= */

    [data-testid="stDataFrame"] {
        background: #ffffff;
        border: 1px solid #d7ebe2;
        border-radius: 12px;
    }


    /* =========================
       EXPANDER
       ========================= */

    [data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #d7ebe2;
        border-radius: 12px;
    }


    /* =========================
       ALERTS
       ========================= */

    [data-testid="stAlert"] {
        border-radius: 10px;
    }


    /* =========================
       DIVIDERS
       ========================= */

    hr {
        border-color: #d7ebe2 !important;
    }


    /* =========================
       AUDIO PLAYER
       ========================= */

    audio {
        width: 100%;
    }


    /* =========================
       CODE
       ========================= */

    pre {
        background: #edf6f1 !important;
        color: #183c31 !important;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None


PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]


# ============================================================
# SESSION STATE
# ============================================================

if "image_result" not in st.session_state:
    st.session_state.image_result = None

if "audio_result" not in st.session_state:
    st.session_state.audio_result = None

if "manifest" not in st.session_state:
    st.session_state.manifest = []

if "last_error" not in st.session_state:
    st.session_state.last_error = None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def retryable(error):
    message = str(error).lower()

    retry_words = [
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

    return any(word in message for word in retry_words)


def response_text(response):
    if response is None:
        return ""

    try:
        text = getattr(response, "text", None)

        if text:
            return str(text).strip()

    except Exception:
        pass

    try:
        candidates = getattr(response, "candidates", [])

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

                return "\n".join(output).strip()

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

    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)

    except Exception:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1:

        candidate = cleaned[start:end + 1]

        try:
            return json.loads(candidate)

        except Exception:
            pass

    return None


def text_value(data, key, default=""):
    if not isinstance(data, dict):
        return default

    value = data.get(key, default)

    if value is None:
        return default

    if isinstance(value, str):
        return value.strip()

    return str(value)


def description_lines(data):
    if not isinstance(data, dict):
        return []

    value = data.get(
        "description_lines",
        [],
    )

    if isinstance(value, list):

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):

        return [
            line.strip()
            for line in value.splitlines()
            if line.strip()
        ]

    return []


def confidence(data):
    if not isinstance(data, dict):
        return None

    value = data.get("confidence")

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


def generate_with_fallback(contents):

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

    for model_index, model in enumerate(models):

        for attempt in range(2):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=json_config(),
                )

                text = response_text(response)

                if text:
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
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🌿 SEED Lab")

    st.caption(
        "Multimodal Data QC Studio"
    )

    st.divider()

    mode = st.radio(
        "Studio",
        [
            "Image Data Studio",
            "Audio Data Studio",
            "Auditor Console",
        ],
    )

    st.divider()

    st.subheader("System")

    if API_KEY:
        st.success(
            "Gemini API connected"
        )
    else:
        st.error(
            "Gemini API key missing"
        )

    st.caption(
        "AI-assisted data annotation and quality control"
    )

    st.divider()

    st.caption(
        "Image • Audio • OCR • Translation • QC"
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    "SEED Lab Multimodal Studio"
)

st.caption(
    "Unified multimodal data annotation, translation and quality-control workspace"
)

st.divider()


# ============================================================
# API WARNING
# ============================================================

if not API_KEY:

    st.warning(
        "GEMINI_API_KEY is not configured. "
        "Add it to Streamlit Secrets before running analysis."
    )


# ============================================================
# IMAGE DATA STUDIO
# ============================================================

if mode == "Image Data Studio":

    st.header("Image Data Studio")

    st.caption(
        "Extract text, translate content, generate visual descriptions and perform QC."
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
                io.BytesIO(image_bytes)
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

                st.subheader("Image Preview")

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

            analyze_image = st.button(
                "Analyze Image",
                type="primary",
                use_container_width=True,
            )

            if analyze_image:

                if not API_KEY:

                    st.error(
                        "Gemini API key is missing."
                    )

                else:

                    prompt = f"""
You are a professional multimodal data annotation and quality-control assistant.

Analyze the uploaded image.

Return ONLY valid JSON.

Required structure:

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

1. description_lines MUST contain exactly {image_description_count} lines.
2. Every line must contain useful visual information.
3. Do not number the lines.
4. Do not combine lines.
5. OCR should contain clearly readable text only.
6. If no readable text exists, use an empty string.
7. Translation should translate the extracted text into English.
8. If translation is not applicable, use an empty string.
9. confidence must be a number from 0 to 1.
10. Do not output markdown.
11. Do not output explanations outside the JSON.
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

                        st.session_state.last_error = error

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
                                "Gemini returned a response, but it could not be parsed."
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

                            actual_lines = len(
                                description_lines(
                                    result
                                )
                            )

                            add_manifest(
                                "Image",
                                image_file.name,
                                image_description_count,
                                actual_lines,
                                model_used,
                            )

                            st.success(
                                f"Analysis completed using {model_used}"
                            )

            # =================================================
            # IMAGE RESULTS
            # =================================================

            if st.session_state.image_result:

                saved = (
                    st.session_state.image_result
                )

                result = saved.get(
                    "data",
                    {},
                )

                st.divider()

                st.header(
                    "Image Analysis Results"
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

                m1, m2, m3 = st.columns(3)

                with m1:

                    st.metric(
                        "OCR",
                        (
                            "Available"
                            if ocr
                            else "No text"
                        ),
                    )

                with m2:

                    st.metric(
                        "Translation",
                        (
                            "Available"
                            if translation
                            else "N/A"
                        ),
                    )

                with m3:

                    st.metric(
                        "Confidence",
                        (
                            f"{conf:.1f}%"
                            if conf is not None
                            else "Not supplied"
                        ),
                    )

                st.divider()

                text_col, translation_col = st.columns(
                    2
                )

                with text_col:

                    st.subheader(
                        "OCR Text"
                    )

                    st.text_area(
                        "OCR output",
                        value=(
                            ocr
                            if ocr
                            else "No readable text detected."
                        ),
                        height=220,
                        disabled=True,
                        label_visibility="collapsed",
                    )

                with translation_col:

                    st.subheader(
                        "Translation"
                    )

                    st.text_area(
                        "Translation output",
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

                if lines:

                    for index, line in enumerate(
                        lines,
                        start=1,
                    ):

                        st.write(
                            f"**{index}.** {line}"
                        )

                else:

                    st.warning(
                        "No visual description was returned."
                    )

                st.divider()

                st.subheader(
                    "Quality Control"
                )

                actual_count = len(lines)

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

elif mode == "Audio Data Studio":

    st.header(
        "Audio Data Studio"
    )

    st.caption(
        "Transcribe audio, translate speech, generate audio descriptions and perform QC."
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

        analyze_audio = st.button(
            "Analyze Audio",
            type="primary",
            use_container_width=True,
        )

        if analyze_audio:

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

Return ONLY valid JSON.

Required structure:

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

1. description_lines MUST contain exactly {audio_description_count} lines.
2. Every line must contain useful information about the audio.
3. Do not number the lines.
4. Do not combine lines.
5. Describe identifiable speech, sounds, environment, events or other useful audio information.
6. transcript should contain understandable speech.
7. If there is no understandable speech, use an empty string.
8. translation should be English.
9. If translation is not applicable, use an empty string.
10. confidence must be a number from 0 to 1.
11. Do not output markdown.
12. Do not output explanations outside JSON.
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

                        st.session_state.last_error = error

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
                                "Gemini returned a response, but it could not be parsed."
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

                            actual_lines = len(
                                description_lines(
                                    result
                                )
                            )

                            add_manifest(
                                "Audio",
                                audio_file.name,
                                audio_description_count,
                                actual_lines,
                                model_used,
                            )

                            st.success(
                                f"Audio analysis completed using {model_used}"
                            )

    # ========================================================
    # AUDIO RESULTS
    # ========================================================

    if st.session_state.audio_result:

        saved = (
            st.session_state.audio_result
        )

        result = saved.get(
            "data",
            {},
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

        m1, m2, m3 = st.columns(3)

        with m1:

            st.metric(
                "Transcript",
                (
                    "Available"
                    if transcript
                    else "No speech"
                ),
            )

        with m2:

            st.metric(
                "Translation",
                (
                    "Available"
                    if translation
                    else "N/A"
                ),
            )

        with m3:

            st.metric(
                "Confidence",
                (
                    f"{conf:.1f}%"
                    if conf is not None
                    else "Not supplied"
                ),
            )

        st.divider()

        transcript_col, translation_col = st.columns(
            2
        )

        with transcript_col:

            st.subheader(
                "Live Audio Transcript"
            )

            st.text_area(
                "Transcript",
                value=(
                    transcript
                    if transcript
                    else "No understandable speech was detected."
                ),
                height=250,
                disabled=True,
                label_visibility="collapsed",
            )

        with translation_col:

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

        if lines:

            for index, line in enumerate(
                lines,
                start=1,
            ):

                st.write(
                    f"**{index}.** {line}"
                )

        else:

            st.warning(
                "No audio description was returned."
            )

        st.divider()

        st.subheader(
            "Quality Control"
        )

        actual_count = len(lines)

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
            "No analysis records available yet. "
            "Run an Image or Audio analysis first."
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
    "🌿 SEED Lab Multimodal Studio • Image + Audio Data Quality Control"
)