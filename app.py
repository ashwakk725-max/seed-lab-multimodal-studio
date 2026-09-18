import io
import json
import re
import time
import html

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
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SIMPLE CSS
# IMPORTANT:
# This is CSS ONLY. No visible HTML blocks are used in the UI.
# ============================================================

st.markdown(
    """
    <style>

    /* Main application */
    .stApp {
        background: #f5f7fb;
        color: #172033;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #dfe4ee;
    }

    [data-testid="stSidebar"] * {
        color: #172033 !important;
    }

    /* Main content */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    /* Headings */
    h1, h2, h3, h4 {
        color: #172033 !important;
        letter-spacing: -0.02em;
    }

    /* Normal text */
    p, label, span, div {
        color: #25304a;
    }

    /* Captions */
    [data-testid="stCaptionContainer"] {
        color: #65708a !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dfe4ee;
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 3px 12px rgba(20, 35, 70, 0.06);
    }

    [data-testid="stMetricLabel"] {
        color: #65708a !important;
    }

    [data-testid="stMetricValue"] {
        color: #172033 !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: #ffffff;
        border: 1px dashed #9aa8c7;
        border-radius: 14px;
        padding: 8px;
    }

    [data-testid="stFileUploader"] * {
        color: #25304a !important;
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: 1px solid #b7c1d8;
        background: #ffffff;
        color: #172033 !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #5969d8;
        color: #3f4fc4 !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: #4f5fd1;
        color: #ffffff !important;
        border: none;
    }

    /* Text areas */
    textarea {
        background: #ffffff !important;
        color: #172033 !important;
        border: 1px solid #d5dbe8 !important;
        border-radius: 10px !important;
    }

    /* Select boxes */
    [data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #172033 !important;
        border-color: #d5dbe8 !important;
    }

    [data-baseweb="select"] * {
        color: #172033 !important;
    }

    /* Number inputs */
    [data-testid="stNumberInput"] input {
        background: #ffffff !important;
        color: #172033 !important;
        border-color: #d5dbe8 !important;
    }

    /* Radio buttons */
    [data-testid="stRadio"] label {
        color: #25304a !important;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        color: #4b5872 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #3f4fc4 !important;
        font-weight: 700;
    }

    /* Dataframes */
    [data-testid="stDataFrame"] {
        background: #ffffff;
        border: 1px solid #dfe4ee;
        border-radius: 12px;
    }

    /* Alerts */
    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #dfe4ee;
        border-radius: 12px;
    }

    /* Dividers */
    hr {
        border-color: #dfe4ee;
    }

    /* Code blocks */
    pre {
        background: #eef1f7 !important;
        color: #172033 !important;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# GEMINI CONFIG
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

DEFAULT_STATE = {
    "image_result": None,
    "audio_result": None,
    "manifest": [],
    "last_error": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def retryable(error):
    """Detect common temporary Gemini/API failures."""
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
    """Safely extract text from a Gemini response."""
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
            content = getattr(candidates[0], "content", None)

            if content:
                parts = getattr(content, "parts", [])

                output = []

                for part in parts:
                    text_part = getattr(part, "text", None)

                    if text_part:
                        output.append(str(text_part))

                return "\n".join(output).strip()

    except Exception:
        pass

    return ""


def parse_json(text):
    """
    Extract JSON even if Gemini surrounds it with markdown fences
    or additional text.
    """

    if not text:
        return None

    cleaned = text.strip()

    # Remove markdown code fences.
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

    # Try to locate JSON object.
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start:end + 1]

        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None


def text_value(data, key, default=""):
    """Safely get text from a result dictionary."""
    if not isinstance(data, dict):
        return default

    value = data.get(key, default)

    if value is None:
        return default

    if isinstance(value, str):
        return value.strip()

    return str(value)


def description_lines(data):
    """
    Convert Gemini description output into a clean list.
    Supports:
    - list
    - string separated by newline
    """

    if not isinstance(data, dict):
        return []

    value = data.get("description_lines", [])

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        lines = value.splitlines()

        return [
            line.strip()
            for line in lines
            if line.strip()
        ]

    return []


def confidence(data):
    """Safely retrieve confidence."""
    if not isinstance(data, dict):
        return None

    value = data.get("confidence")

    if value is None:
        return None

    try:
        number = float(value)

        if number <= 1:
            number *= 100

        return max(0, min(100, number))

    except Exception:
        return None


def json_config():
    """Gemini generation configuration."""
    return types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    )


def generate_with_fallback(contents):
    """
    Try the primary model, then fallback models.
    Returns:
        response, model_used, error
    """

    if client is None:
        return None, None, "GEMINI_API_KEY is not configured."

    models = [PRIMARY_MODEL] + FALLBACK_MODELS

    last_error = None

    for model_index, model in enumerate(models):

        attempts = 2

        for attempt in range(attempts):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=json_config(),
                )

                text = response_text(response)

                if text:
                    return response, model, None

                last_error = "Gemini returned an empty response."

            except Exception as error:
                last_error = str(error)

                if not retryable(error):
                    break

                if attempt < attempts - 1:
                    time.sleep(2)

        # Small pause before switching model.
        if model_index < len(models) - 1:
            time.sleep(1)

    return None, None, last_error or "Gemini request failed."


def make_manifest_record(
    mode,
    filename,
    description_count,
    qc_pass,
    model,
):
    return {
        "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "Mode": mode,
        "File": filename,
        "Description Lines": description_count,
        "QC": "PASS" if qc_pass else "FAIL",
        "Model": model or "Unknown",
    }


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("◈ SEED Lab")

    st.caption("Multimodal Data QC Studio")

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
        st.success("Gemini API connected")
    else:
        st.error("Gemini API key missing")

    st.caption("AI-assisted data annotation and quality control")

    st.divider()

    st.caption("SEED Lab Multimodal Studio")
    st.caption("Image + Audio • OCR • Translation • QC")


# ============================================================
# HEADER
# ============================================================

st.title("SEED Lab Multimodal Studio")

st.caption(
    "Unified multimodal data annotation, translation and quality-control workspace"
)

st.divider()


# ============================================================
# API KEY WARNING
# ============================================================

if not API_KEY:

    st.warning(
        "Gemini API key is not configured. Add GEMINI_API_KEY to "
        "Streamlit secrets before running analysis."
    )


# ============================================================
# IMAGE DATA STUDIO
# ============================================================

if mode == "Image Data Studio":

    st.header("Image Data Studio")

    st.caption(
        "Upload an image for OCR, translation, visual description and QC."
    )

    # --------------------------------------------------------
    # Controls
    # --------------------------------------------------------

    col1, col2 = st.columns([2, 1])

    with col1:

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

    with col2:

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

        image = Image.open(io.BytesIO(image_bytes))

        st.divider()

        preview_col, info_col = st.columns([1.3, 1])

        with preview_col:

            st.subheader("Preview")

            st.image(
                image,
                use_container_width=True,
            )

        with info_col:

            st.subheader("File Information")

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
                    "Gemini API key is missing. Configure GEMINI_API_KEY first."
                )

            else:

                with st.spinner("Analyzing image with Gemini..."):

                    prompt = f"""
You are a professional multimodal data annotation and quality-control assistant.

Analyze the uploaded image.

Return ONLY valid JSON with exactly these keys:

{{
  "ocr_text": "all clearly readable text from the image",
  "translation": "English translation of the readable text",
  "description_lines": [
    "description line 1",
    "description line 2"
  ],
  "confidence": 0.0
}}

IMPORTANT RULES:

1. description_lines MUST contain exactly {image_description_count} separate lines.
2. Each line must contain useful visual information.
3. Do not number the lines.
4. Do not combine multiple lines into one string.
5. If there is no readable text, use an empty string for ocr_text.
6. If translation is not applicable, use an empty string.
7. confidence must be a number from 0 to 1.
8. Do not include markdown.
9. Do not include explanations outside the JSON.
"""

                    response, model_used, error = generate_with_fallback(
                        [
                            prompt,
                            image,
                        ]
                    )

                if error:

                    st.session_state.last_error = error

                    st.error(
                        f"Analysis failed: {error}"
                    )

                else:

                    raw = response_text(response)

                    result = parse_json(raw)

                    if result is None:

                        st.error(
                            "Gemini responded, but the response could not be parsed as JSON."
                        )

                        with st.expander("Developer response"):

                            st.code(
                                raw or "EMPTY RESPONSE",
                                language="text",
                            )

                    else:

                        st.session_state.image_result = {
                            "data": result,
                            "model": model_used,
                            "filename": image_file.name,
                        }

                        st.session_state.manifest.append(
                            make_manifest_record(
                                "Image",
                                image_file.name,
                                len(description_lines(result)),
                                (
                                    len(description_lines(result))
                                    == image_description_count
                                ),
                                model_used,
                            )
                        )

                        st.success(
                            f"Analysis completed using {model_used}"
                        )

        # ----------------------------------------------------
        # Results
        # ----------------------------------------------------

        if st.session_state.image_result:

            saved = st.session_state.image_result

            result = saved.get("data", {})

            st.divider()

            st.header("Image Analysis Results")

            metric1, metric2, metric3 = st.columns(3)

            with metric1:

                st.metric(
                    "OCR",
                    "Available"
                    if text_value(result, "ocr_text")
                    else "No text",
                )

            with metric2:

                st.metric(
                    "Translation",
                    "Available"
                    if text_value(result, "translation")
                    else "N/A",
                )

            with metric3:

                conf = confidence(result)

                st.metric(
                    "Confidence",
                    f"{conf:.1f}%"
                    if conf is not None
                    else "Not supplied",
                )

            st.divider()

            result_col1, result_col2 = st.columns(2)

            with result_col1:

                st.subheader("OCR Text")

                ocr = text_value(
                    result,
                    "ocr_text",
                    "No readable text detected.",
                )

                st.text_area(
                    "Extracted text",
                    value=ocr,
                    height=220,
                    disabled=True,
                    label_visibility="collapsed",
                )

            with result_col2:

                st.subheader("Translation")

                translation = text_value(
                    result,
                    "translation",
                    "No translation available.",
                )

                st.text_area(
                    "Translated text",
                    value=translation,
                    height=220,
                    disabled=True,
                    label_visibility="collapsed",
                )

            st.divider()

            st.subheader(
                f"AI Visual Description — {image_description_count} lines requested"
            )

            image_lines = description_lines(result)

            if image_lines:

                for index, line in enumerate(image_lines, start=1):

                    st.write(
                        f"**{index}.** {line}"
                    )

            else:

                st.warning("No visual description was returned.")

            st.divider()

            # ------------------------------------------------
            # QC
            # ------------------------------------------------

            st.subheader("Quality Control")

            actual_count = len(image_lines)

            qc1, qc2, qc3 = st.columns(3)

            with qc1:

                if actual_count == image_description_count:
                    st.success(
                        f"Description count: PASS ({actual_count})"
                    )
                else:
                    st.error(
                        f"Description count: FAIL ({actual_count}/{image_description_count})"
                    )

            with qc2:

                if ocr:
                    st.success("OCR: PASS")
                else:
                    st.warning("OCR: No readable text")

            with qc3:

                if translation:
                    st.success("Translation: PASS")
                else:
                    st.info("Translation: N/A")

            if actual_count == image_description_count:

                st.success(
                    "Image QC completed successfully."
                )

            else:

                st.warning(
                    "Image QC requires the requested number of description lines."
                )


# ============================================================
# AUDIO DATA STUDIO
# ============================================================

elif mode == "Audio Data Studio":

    st.header("Audio Data Studio")

    st.caption(
        "Upload an audio file for transcription, translation, audio description and QC."
    )

    col1, col2 = st.columns([2, 1])

    with col1:

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

    with col2:

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

        info1, info2, info3 = st.columns(3)

        with info1:

            st.metric(
                "File size",
                f"{len(audio_bytes) / (1024 * 1024):.2f} MB",
            )

        with info2:

            st.metric(
                "Format",
                audio_file.type or "Unknown",
            )

        with info3:

            st.metric(
                "Description lines",
                audio_description_count,
            )

        st.subheader("Audio Preview")

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
                    "Gemini API key is missing. Configure GEMINI_API_KEY first."
                )

            else:

                uploaded_file = None

                with st.spinner("Uploading audio to Gemini..."):

                    try:

                        uploaded_file = client.files.upload(
                            file=io.BytesIO(audio_bytes),
                            config=types.UploadFileConfig(
                                mime_type=audio_file.type
                            ),
                        )

                    except Exception as error:

                        st.error(
                            f"Audio upload failed: {error}"
                        )

                if uploaded_file:

                    with st.spinner(
                        "Transcribing and analyzing audio..."
                    ):

                        prompt = f"""
You are a professional multimodal data annotation and quality-control assistant.

Analyze the uploaded audio.

Return ONLY valid JSON with exactly these keys:

{{
  "transcript": "complete available speech transcription",
  "translation": "English translation of the spoken content",
  "description_lines": [
    "description line 1",
    "description line 2"
  ],
  "confidence": 0.0
}}

IMPORTANT RULES:

1. description_lines MUST contain exactly {audio_description_count} separate lines.
2. Each line must describe useful information about the audio.
3. Do not number the lines.
4. Do not combine multiple lines into one string.
5. Include relevant sounds, speech, environment, tone, or events when identifiable.
6. transcript should contain the spoken content when speech is present.
7. If there is no understandable speech, use an empty string for transcript.
8. If translation is not applicable, use an empty string.
9. confidence must be a number from 0 to 1.
10. Do not include markdown.
11. Do not include explanations outside the JSON.
"""

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

                        raw = response_text(response)

                        result = parse_json(raw)

                        if result is None:

                            st.error(
                                "Gemini responded, but the audio response could not be parsed as JSON."
                            )

                            with st.expander(
                                "Developer response"
                            ):

                                st.code(
                                    raw or "EMPTY RESPONSE",
                                    language="text",
                                )

                        else:

                            st.session_state.audio_result = {
                                "data": result,
                                "model": model_used,
                                "filename": audio_file.name,
                            }

                            st.session_state.manifest.append(
                                make_manifest_record(
                                    "Audio",
                                    audio_file.name,
                                    len(
                                        description_lines(
                                            result
                                        )
                                    ),
                                    (
                                        len(
                                            description_lines(
                                                result
                                            )
                                        )
                                        == audio_description_count
                                    ),
                                    model_used,
                                )
                            )

                            st.success(
                                f"Audio analysis completed using {model_used}"
                            )

    # --------------------------------------------------------
    # AUDIO RESULTS
    # --------------------------------------------------------

    if st.session_state.audio_result:

        saved = st.session_state.audio_result

        result = saved.get("data", {})

        st.divider()

        st.header("Audio Analysis Results")

        transcript = text_value(
            result,
            "transcript",
        )

        translation = text_value(
            result,
            "translation",
        )

        audio_lines = description_lines(result)

        conf = confidence(result)

        m1, m2, m3 = st.columns(3)

        with m1:

            st.metric(
                "Transcript",
                "Available"
                if transcript
                else "No speech detected",
            )

        with m2:

            st.metric(
                "Translation",
                "Available"
                if translation
                else "N/A",
            )

        with m3:

            st.metric(
                "Confidence",
                f"{conf:.1f}%"
                if conf is not None
                else "Not supplied",
            )

        st.divider()

        left, right = st.columns(2)

        with left:

            st.subheader("Live Audio Transcript")

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

        with right:

            st.subheader("Translation")

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
            f"AI Audio Description — {audio_description_count} lines requested"
        )

        if audio_lines:

            for index, line in enumerate(
                audio_lines,
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

        st.subheader("Quality Control")

        actual_count = len(audio_lines)

        q1, q2, q3 = st.columns(3)

        with q1:

            if actual_count == audio_description_count:

                st.success(
                    f"Description count: PASS ({actual_count})"
                )

            else:

                st.error(
                    f"Description count: FAIL ({actual_count}/{audio_description_count})"
                )

        with q2:

            if transcript:

                st.success("Transcript: PASS")

            else:

                st.warning("Transcript: No speech")

        with q3:

            if translation:

                st.success("Translation: PASS")

            else:

                st.info("Translation: N/A")

        if actual_count == audio_description_count:

            st.success(
                "Audio QC completed successfully."
            )

        else:

            st.warning(
                "Audio QC requires the requested number of description lines."
            )


# ============================================================
# AUDITOR CONSOLE
# ============================================================

else:

    st.header("Auditor Console")

    st.caption(
        "Review generated records and export the annotation manifest."
    )

    manifest = st.session_state.manifest

    if not manifest:

        st.info(
            "No analysis records are available yet. "
            "Run an Image or Audio analysis first."
        )

    else:

        df = pd.DataFrame(manifest)

        total = len(df)

        passed = int(
            (df["QC"] == "PASS").sum()
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
                use_container_width=True,
            )

        with tab2:

            if "Mode" in df.columns:

                st.subheader("Records by Mode")

                mode_counts = (
                    df["Mode"]
                    .value_counts()
                    .rename_axis("Mode")
                    .reset_index(name="Records")
                )

                st.dataframe(
                    mode_counts,
                    use_container_width=True,
                    hide_index=True,
                )

            if "QC" in df.columns:

                st.subheader("QC Summary")

                qc_counts = (
                    df["QC"]
                    .value_counts()
                    .rename_axis("QC Status")
                    .reset_index(name="Records")
                )

                st.dataframe(
                    qc_counts,
                    use_container_width=True,
                    hide_index=True,
                )

        st.divider()

        if st.button(
            "Clear Auditor Manifest",
            type="secondary",
        ):

            st.session_state.manifest = []

            st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "SEED Lab Multimodal Studio • Image + Audio Data Quality Control"
)