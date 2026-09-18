import streamlit as st
import pandas as pd
from PIL import Image
from google import genai
from google.genai import types
import json
import io
import time
import re


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SEED Lab Multimodal Studio",
    page_icon="🎙️",
    layout="wide",
)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not API_KEY:
    st.error(
        "GEMINI_API_KEY is missing. Add it to Streamlit secrets before running the app."
    )
    st.stop()

client = genai.Client(api_key=API_KEY)

PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]

ALL_MODELS = [PRIMARY_MODEL] + FALLBACK_MODELS


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "image_result": None,
    "audio_result": None,
    "image_qc_log": [],
    "audio_qc_log": [],
    "image_manifest": [],
    "audio_manifest": [],
    "image_generation_id": 0,
    "audio_generation_id": 0,
    "image_signature": None,
    "audio_signature": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_retryable_error(error):
    """Return True for temporary Gemini service/rate-limit errors."""
    text = str(error).upper()

    retry_words = [
        "503",
        "UNAVAILABLE",
        "429",
        "RESOURCE_EXHAUSTED",
        "TOO MANY REQUESTS",
        "HIGH DEMAND",
        "INTERNAL",
        "DEADLINE",
        "TIMEOUT",
    ]

    return any(word in text for word in retry_words)


def generate_with_fallback(contents, config=None):
    """
    Try primary Gemini model, then fallback models.
    Returns:
        response, model_used, error_messages
    """

    errors = []

    for model_index, model in enumerate(ALL_MODELS):

        attempts = 2 if model_index == 0 else 1

        for attempt in range(attempts):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )

                return response, model, errors

            except Exception as error:

                errors.append(f"{model}: {error}")

                if is_retryable_error(error) and attempt < attempts - 1:
                    time.sleep(2)
                    continue

                break

    raise RuntimeError(
        "All Gemini models failed.\n\n" + "\n\n".join(errors)
    )


def clean_json_response(text):
    """Clean common Gemini JSON formatting problems."""

    if not text:
        return ""

    text = text.strip()

    # Remove markdown code fences.
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return text.strip()


def safe_json_loads(text):
    """Try multiple ways to extract JSON from Gemini output."""

    if not text:
        return None

    cleaned = clean_json_response(text)

    # First attempt.
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Try extracting the largest JSON object.
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:

        candidate = cleaned[start:end + 1]

        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None


def normalize_text(value):
    """Convert any returned value into clean display text."""

    if value is None:
        return ""

    if isinstance(value, list):
        return "\n".join(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    return str(value).strip()


def get_description_lines(value):
    """
    Convert Gemini audio/image description into individual lines.
    """

    if value is None:
        return []

    if isinstance(value, list):
        lines = []

        for item in value:
            text = str(item).strip()

            if text:
                # If an item itself contains multiple lines,
                # split those too.
                for subline in text.splitlines():
                    subline = subline.strip()

                    if subline:
                        lines.append(subline)

        return lines

    text = str(value).strip()

    if not text:
        return []

    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def format_description_lines(value):
    lines = get_description_lines(value)
    return "\n".join(lines)


def ensure_display_value(value, fallback):
    value = normalize_text(value)

    if value:
        return value

    return fallback


def get_response_text(response):
    """
    Safely obtain text from Gemini response.
    """

    try:
        text = response.text

        if text:
            return text.strip()
    except Exception:
        pass

    # Fallback through candidates.
    try:
        candidates = response.candidates

        if candidates:
            parts = candidates[0].content.parts

            collected = []

            for part in parts:
                if hasattr(part, "text") and part.text:
                    collected.append(part.text)

            if collected:
                return "\n".join(collected).strip()

    except Exception:
        pass

    return ""


def extract_confidence(data):
    """Extract confidence without inventing a value."""

    possible_keys = [
        "confidence_score",
        "confidence",
        "ai_confidence",
        "confidence_percentage",
    ]

    for key in possible_keys:

        if key not in data:
            continue

        try:
            value = float(data[key])

            # Convert 0-1 to percentage.
            if 0 <= value <= 1:
                value *= 100

            return max(0.0, min(100.0, value))

        except Exception:
            continue

    return None


def build_json_config():
    """
    Ask Gemini to return JSON.
    Temperature is kept low for stable QC output.
    """

    return types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
    )


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def analyze_image(image_bytes, filename, target_language, requested_lines):

    image_prompt = f"""
You are a professional multimodal data-quality annotator.

Analyze the supplied image.

Return ONLY valid JSON.

Required JSON structure:

{{
  "ocr_text": "all clearly readable text in the image",
  "translation": "translation of the readable text into {target_language}",
  "image_description_lines": [
    "description line 1",
    "description line 2"
  ],
  "confidence_score": 0
}}

IMPORTANT:

1. image_description_lines MUST contain EXACTLY {requested_lines} separate strings.
2. Do not return fewer than {requested_lines} lines.
3. Do not return more than {requested_lines} lines.
4. Do not invent objects, people, text, locations, events or facts.
5. If the image has limited information, describe different valid visual aspects separately.
6. OCR should contain only text actually visible in the image.
7. Translation should translate the OCR text into {target_language}.
8. confidence_score must be between 0 and 100.
9. Return JSON only. No markdown.
"""

    image = Image.open(io.BytesIO(image_bytes))

    image_buffer = io.BytesIO()

    # Keep original visual quality while ensuring a supported format.
    image.convert("RGB").save(
        image_buffer,
        format="JPEG",
        quality=92,
    )

    image_data = image_buffer.getvalue()

    contents = [
        image_prompt,
        types.Part.from_bytes(
            data=image_data,
            mime_type="image/jpeg",
        ),
    ]

    response, model_used, errors = generate_with_fallback(
        contents,
        config=build_json_config(),
    )

    raw_response = get_response_text(response)

    parsed = safe_json_loads(raw_response)

    if parsed is None:
        parsed = {}

    ocr_text = ensure_display_value(
        parsed.get("ocr_text"),
        "No readable text detected.",
    )

    translation = ensure_display_value(
        parsed.get("translation"),
        "No translation available.",
    )

    description_lines = get_description_lines(
        parsed.get("image_description_lines")
        or parsed.get("description")
        or parsed.get("image_description")
    )

    confidence = extract_confidence(parsed)

    return {
        "filename": filename,
        "ocr_text": ocr_text,
        "translation": translation,
        "description_lines": description_lines,
        "confidence": confidence,
        "model": model_used,
        "raw_response": raw_response,
        "errors": errors,
        "requested_lines": requested_lines,
    }


# ============================================================
# AUDIO ANALYSIS
# ============================================================

def upload_audio_to_gemini(audio_bytes, filename, mime_type):

    audio_stream = io.BytesIO(audio_bytes)

    # Gemini SDK uses the file name to infer useful metadata.
    audio_stream.name = filename

    uploaded_file = client.files.upload(
        file=audio_stream,
        config=types.UploadFileConfig(
            mime_type=mime_type
        ),
    )

    return uploaded_file


def analyze_audio(
    audio_bytes,
    filename,
    mime_type,
    target_language,
    requested_lines,
):

    audio_prompt = f"""
You are a professional audio data-quality annotator.

Analyze the supplied audio file carefully.

Return ONLY valid JSON.

Required JSON structure:

{{
  "transcript": "complete understandable speech transcript",
  "translation": "translation of the spoken content into {target_language}",
  "audio_description_lines": [
    "description line 1",
    "description line 2"
  ],
  "confidence_score": 0
}}

CRITICAL REQUIREMENTS:

1. audio_description_lines MUST contain EXACTLY {requested_lines} separate strings.
2. Do not return fewer than {requested_lines} lines.
3. Do not return more than {requested_lines} lines.
4. Do not invent sounds or events that cannot reasonably be heard.
5. If speech is present, describe speech characteristics separately from environmental/audio characteristics.
6. Valid description categories can include:
   - speech presence
   - speaker characteristics when reasonably identifiable
   - language
   - music
   - background sounds
   - environmental sounds
   - recording quality
   - clarity
   - noise
   - silence
   - acoustic setting
   - notable audio events
7. Do not repeat the same sentence merely to reach the required number of lines.
8. If there is no understandable speech, set transcript to:
   "No clear speech detected."
9. If there is no speech to translate, set translation to:
   "No translation available."
10. confidence_score must be between 0 and 100.
11. Return JSON only. No markdown.
"""

    # Upload audio through Gemini File API.
    uploaded_file = upload_audio_to_gemini(
        audio_bytes,
        filename,
        mime_type,
    )

    contents = [
        audio_prompt,
        uploaded_file,
    ]

    response, model_used, errors = generate_with_fallback(
        contents,
        config=build_json_config(),
    )

    raw_response = get_response_text(response)

    parsed = safe_json_loads(raw_response)

    if parsed is None:
        parsed = {}

    transcript = normalize_text(
        parsed.get("transcript")
        or parsed.get("transcription")
    )

    translation = normalize_text(
        parsed.get("translation")
        or parsed.get("translated_text")
    )

    description_lines = get_description_lines(
        parsed.get("audio_description_lines")
        or parsed.get("description")
        or parsed.get("audio_description")
    )

    confidence = extract_confidence(parsed)

    if not transcript:
        transcript = "No clear speech detected."

    if not translation:
        translation = "No translation available."

    return {
        "filename": filename,
        "transcript": transcript,
        "translation": translation,
        "description_lines": description_lines,
        "confidence": confidence,
        "model": model_used,
        "raw_response": raw_response,
        "errors": errors,
        "requested_lines": requested_lines,
    }


# ============================================================
# QC FUNCTIONS
# ============================================================

def run_image_qc(result):

    checks = []

    ocr_ok = bool(
        result["ocr_text"]
        and result["ocr_text"] != "No readable text detected."
    )

    checks.append({
        "rule": "Rule 1 - OCR Payload",
        "status": "PASS" if ocr_ok else "FAIL",
        "details": (
            "Readable OCR detected"
            if ocr_ok
            else "No readable OCR detected"
        ),
    })

    actual_lines = len(result["description_lines"])
    required_lines = result["requested_lines"]

    description_ok = actual_lines == required_lines

    checks.append({
        "rule": "Rule 2 - Image Description Density",
        "status": "PASS" if description_ok else "FAIL",
        "details": f"{actual_lines}/{required_lines} lines",
    })

confidence = result.get("confidence")

    if confidence is None:
        confidence_ok = False
        confidence_details = "Confidence not supplied by Gemini"
    else:
        confidence_ok = confidence >= 80
        confidence_details = f"{confidence:.1f}%"

    checks.append({
        "rule": "Rule 3 - AI Confidence Baseline",
        "status": "PASS" if confidence_ok else "FAIL",
        "details": confidence_details,
    })

    return checks


def run_audio_qc(result):

    checks = []

    transcript_ok = bool(
        result["transcript"]
        and result["transcript"].strip()
        and result["transcript"] != "No clear speech detected."
    )

    checks.append({
        "rule": "Rule 1 - Transcript Payload",
        "status": "PASS" if transcript_ok else "FAIL",
        "details": (
            "Transcript detected"
            if transcript_ok
            else "No clear speech detected"
        ),
    })

    actual_lines = len(result["description_lines"])
    required_lines = result["requested_lines"]

    description_ok = actual_lines == required_lines

    checks.append({
        "rule": "Rule 2 - Audio Description Density",
        "status": "PASS" if description_ok else "FAIL",
        "details": f"{actual_lines}/{required_lines} lines",
    })

    confidence = result.get("confidence")

    if confidence is None:
        confidence_ok = False
        confidence_details = "Confidence not supplied by Gemini"
    else:
        confidence_ok = confidence >= 80
        confidence_details = f"{confidence:.1f}%"

    checks.append({
        "rule": "Rule 3 - AI Confidence Baseline",
        "status": "PASS" if confidence_ok else "FAIL",
        "details": confidence_details,
    })

    return checks


def qc_pass_count(checks):
    return sum(
        1
        for check in checks
        if check["status"] == "PASS"
    )


# ============================================================
# MANIFEST FUNCTIONS
# ============================================================

def add_image_manifest(result, checks):

    st.session_state.image_manifest.append({
        "filename": result["filename"],
        "model": result["model"],
        "target_language": st.session_state.target_language,
        "description_lines_required": result["requested_lines"],
        "description_lines_generated": len(result["description_lines"]),
        "confidence": (
            result["confidence"]
            if result["confidence"] is not None
            else ""
        ),
        "qc_passed": qc_pass_count(checks),
        "qc_total": len(checks),
        "status": (
            "PASS"
            if qc_pass_count(checks) == len(checks)
            else "REVIEW"
        ),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


def add_audio_manifest(result, checks):

    st.session_state.audio_manifest.append({
        "filename": result["filename"],
        "model": result["model"],
        "target_language": st.session_state.target_language,
        "description_lines_required": result["requested_lines"],
        "description_lines_generated": len(result["description_lines"]),
        "confidence": (
            result["confidence"]
            if result["confidence"] is not None
            else ""
        ),
        "qc_passed": qc_pass_count(checks),
        "qc_total": len(checks),
        "status": (
            "PASS"
            if qc_pass_count(checks) == len(checks)
            else "REVIEW"
        ),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎙️ SEED Lab")

mode = st.sidebar.radio(
    "Studio Mode",
    [
        "🖼️ Image Data Studio",
        "🎧 Audio Data Studio",
    ],
)

target_language = st.sidebar.selectbox(
    "Target Translation Language",
    [
        "Hindi",
        "English",
        "Kannada",
        "Tamil",
        "Telugu",
        "Malayalam",
        "Spanish",
        "French",
        "German",
        "Arabic",
        "Japanese",
        "Chinese",
    ],
)

st.session_state.target_language = target_language

st.sidebar.divider()

st.sidebar.success("Gemini Cloud Engine Connected")

st.sidebar.caption(
    f"Primary Model: {PRIMARY_MODEL}"
)

st.sidebar.caption(
    "Automatic fallback enabled"
)

st.sidebar.divider()

st.sidebar.info(
    "Designed for multimodal data annotation, "
    "translation and quality-control workflows."
)


# ============================================================
# HEADER
# ============================================================

st.title("SEED Lab Multimodal Studio")

st.caption(
    "Unified multimodal data annotation, translation and QC workspace"
)


# ============================================================
# IMAGE DATA STUDIO
# ============================================================

if mode == "🖼️ Image Data Studio":

    st.header("🖼️ Image Data Studio")

    col1, col2 = st.columns([2, 1])

    with col1:

        uploaded_image = st.file_uploader(
            "Upload Image",
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

        image_description_lines = st.number_input(
            "Description Lines Required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
            key="image_description_line_count",
        )

    if uploaded_image:

        image_bytes = uploaded_image.getvalue()

        signature = (
            uploaded_image.name,
            len(image_bytes),
            target_language,
            image_description_lines,
        )

        if st.session_state.image_signature != signature:

            # Do not automatically destroy old result until
            # user requests a new generation.
            pass

        col1, col2 = st.columns(2)

        with col1:
            st.image(
                image_bytes,
                caption=uploaded_image.name,
                use_container_width=True,
            )

        with col2:

            st.markdown("### Generation Settings")

            st.write(
                f"Translation: **{target_language}**"
            )

            st.write(
                f"Description lines: **{image_description_lines}**"
            )

            generate_image = st.button(
                "🚀 Generate Image Analysis",
                type="primary",
                use_container_width=True,
            )

        if generate_image:

            with st.spinner(
                "Gemini is analyzing the image..."
            ):

                try:

                    result = analyze_image(
                        image_bytes=image_bytes,
                        filename=uploaded_image.name,
                        target_language=target_language,
                        requested_lines=int(
                            image_description_lines
                        ),
                    )

                    st.session_state.image_result = result

                    st.session_state.image_generation_id += 1

                    st.session_state.image_signature = signature

                    checks = run_image_qc(result)

                    st.session_state.image_qc_log = checks

                    add_image_manifest(
                        result,
                        checks,
                    )

                    st.success(
                        f"Analysis completed using {result['model']}"
                    )

                    if result["model"] != PRIMARY_MODEL:
                        st.warning(
                            f"Primary model was busy. "
                            f"Analysis completed using `{result['model']}`."
                        )

                except Exception as error:

                    st.error(
                        "Image analysis failed."
                    )

                    st.exception(error)

        # ====================================================
        # DISPLAY IMAGE RESULT
        # ====================================================

        result = st.session_state.image_result

        if result:

            st.divider()

            st.subheader("AI Image Analysis")

            col1, col2 = st.columns(2)

            with col1:

                st.markdown("### OCR Text")

                st.text_area(
                    "Detected Text",
                    value=result["ocr_text"],
                    height=180,
                    key=(
                        f"image_ocr_"
                        f"{st.session_state.image_generation_id}"
                    ),
                )

            with col2:

                st.markdown(
                    f"### Translation ({target_language})"
                )

                st.text_area(
                    "Translated Text",
                    value=result["translation"],
                    height=180,
                    key=(
                        f"image_translation_"
                        f"{st.session_state.image_generation_id}"
                    ),
                )

            st.markdown("### AI Image Description")

            st.text_area(
                "Description",
                value=format_description_lines(
                    result["description_lines"]
                ),
                height=220,
                key=(
                    f"image_description_"
                    f"{st.session_state.image_generation_id}"
                ),
            )

            # =================================================
            # IMAGE QC
            # =================================================

            st.subheader("Quality Control")

            if result["confidence"] is not None:

                st.metric(
                    "AI Analysis Confidence",
                    f"{result['confidence']:.1f}%",
                )

            else:

                st.metric(
                    "AI Analysis Confidence",
                    "Not supplied",
                )

            st.caption(
                f"Generated using `{result['model']}`"
            )

            for check in st.session_state.image_qc_log:

                if check["status"] == "PASS":
                    st.success(
                        f"{check['rule']}: "
                        f"✅ {check['details']}"
                    )
                else:
                    st.error(
                        f"{check['rule']}: "
                        f"❌ {check['details']}"
                    )

            # =================================================
            # RAW RESPONSE
            # =================================================

            if not result["ocr_text"] or not result["description_lines"]:

                with st.expander(
                    "🔎 Debug: Raw Gemini Response"
                ):

                    st.code(
                        result["raw_response"]
                        or "Gemini returned an empty response.",
                        language="text",
                    )

                    if result["errors"]:
                        st.write("Model attempts:")

                        for error in result["errors"]:
                            st.code(
                                error,
                                language="text",
                            )

    else:

        st.info(
            "Upload an image to begin analysis."
        )


# ============================================================
# AUDIO DATA STUDIO
# ============================================================

else:

    st.header("🎧 Audio Data Studio")

    col1, col2 = st.columns([2, 1])

    with col1:

        uploaded_audio = st.file_uploader(
            "Upload Audio",
            type=[
                "mp3",
                "wav",
                "m4a",
                "ogg",
                "flac",
            ],
            key="audio_uploader",
        )

    with col2:

        audio_description_lines = st.number_input(
            "Description Lines Required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
            key="audio_description_line_count",
        )

    if uploaded_audio:

        audio_bytes = uploaded_audio.getvalue()

        file_extension = (
            uploaded_audio.name
            .lower()
            .split(".")[-1]
        )

        mime_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "m4a": "audio/mp4",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
        }

        mime_type = mime_map.get(
            file_extension,
            "application/octet-stream",
        )

        signature = (
            uploaded_audio.name,
            len(audio_bytes),
            target_language,
            audio_description_lines,
        )

        st.audio(
            audio_bytes,
            format=mime_type,
        )

        st.caption(
            f"File: {uploaded_audio.name} | "
            f"Size: {len(audio_bytes) / (1024 * 1024):.2f} MB"
        )

        st.info(
            f"Target translation: **{target_language}**  \n"
            f"AI audio description: **{audio_description_lines} lines**"
        )

        generate_audio = st.button(
            "🚀 Generate Audio Analysis",
            type="primary",
            use_container_width=True,
        )

        if generate_audio:

            with st.spinner(
                "Gemini is listening to the audio and generating the analysis..."
            ):

                try:

                    result = analyze_audio(
                        audio_bytes=audio_bytes,
                        filename=uploaded_audio.name,
                        mime_type=mime_type,
                        target_language=target_language,
                        requested_lines=int(
                            audio_description_lines
                        ),
                    )

                    st.session_state.audio_result = result

                    st.session_state.audio_generation_id += 1

                    st.session_state.audio_signature = signature

                    checks = run_audio_qc(result)

                    st.session_state.audio_qc_log = checks

                    add_audio_manifest(
                        result,
                        checks,
                    )

                    st.success(
                        f"Audio analysis completed using `{result['model']}`"
                    )

                    if result["model"] != PRIMARY_MODEL:
                        st.warning(
                            f"Primary model was busy. "
                            f"Analysis completed using `{result['model']}`."
                        )

                except Exception as error:

                    st.error(
                        "Audio analysis failed."
                    )

                    st.exception(error)

        # ====================================================
        # DISPLAY AUDIO RESULT
        # ====================================================

        result = st.session_state.audio_result

        if result:

            st.divider()

            st.subheader("AI Audio Analysis")

            # ------------------------------------------------
            # CONFIDENCE
            # ------------------------------------------------

            confidence = result.get("confidence")

            if confidence is not None:

                st.metric(
                    "AI Analysis Confidence",
                    f"{confidence:.1f}%",
                )

            else:

                st.metric(
                    "AI Analysis Confidence",
                    "Not supplied",
                )

            st.caption(
                f"Generated using `{result['model']}`"
            )

            # ------------------------------------------------
            # TRANSCRIPT
            # ------------------------------------------------

            st.markdown("### 🎤 Live Audio Transcript")

            transcript_display = result["transcript"]

            if not transcript_display.strip():
                transcript_display = (
                    "No clear speech detected."
                )

            st.text_area(
                "Transcript",
                value=transcript_display,
                height=180,
                key=(
                    f"audio_transcript_"
                    f"{st.session_state.audio_generation_id}"
                ),
            )

            # ------------------------------------------------
            # TRANSLATION
            # ------------------------------------------------

            st.markdown(
                f"### 🌐 Translation ({target_language})"
            )

            translation_display = result["translation"]

            if not translation_display.strip():
                translation_display = (
                    "No translation available."
                )

            st.text_area(
                "Translation",
                value=translation_display,
                height=180,
                key=(
                    f"audio_translation_"
                    f"{st.session_state.audio_generation_id}"
                ),
            )

            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------

            st.markdown("### 🔊 AI Audio Description")

            description_text = format_description_lines(
                result["description_lines"]
            )

            if not description_text.strip():

                description_text = (
                    "No audio description was returned by Gemini."
                )

            st.text_area(
                "Audio Description",
                value=description_text,
                height=250,
                key=(
                    f"audio_description_"
                    f"{st.session_state.audio_generation_id}"
                ),
            )

            actual_lines = len(
                result["description_lines"]
            )

            required_lines = result["requested_lines"]

            if actual_lines == required_lines:

                st.success(
                    f"Description density: "
                    f"{actual_lines}/{required_lines} lines generated."
                )

            else:

                st.warning(
                    f"Description density: "
                    f"{actual_lines}/{required_lines} lines generated. "
                    f"Gemini did not return the requested number of lines."
                )

            # =================================================
            # AUDIO QC
            # =================================================

            st.subheader("Quality Control")

            for check in st.session_state.audio_qc_log:

                if check["status"] == "PASS":

                    st.success(
                        f"{check['rule']}: "
                        f"✅ {check['details']}"
                    )

                else:

                    st.error(
                        f"{check['rule']}: "
                        f"❌ {check['details']}"
                    )

            # =================================================
            # DEBUG SECTION
            # =================================================

            with st.expander(
                "🔎 Technical Response / Debug"
            ):

                st.write(
                    "Model used:",
                    result["model"],
                )

                st.write(
                    "Requested description lines:",
                    result["requested_lines"],
                )

                st.write(
                    "Description lines actually returned:",
                    len(result["description_lines"]),
                )

                st.markdown("#### Raw Gemini Response")

                if result["raw_response"]:

                    st.code(
                        result["raw_response"],
                        language="text",
                    )

                else:

                    st.warning(
                        "Gemini returned an empty text response."
                    )

                if result["errors"]:

                    st.markdown(
                        "#### Previous Model Errors"
                    )

                    for error in result["errors"]:

                        st.code(
                            error,
                            language="text",
                        )

    else:

        st.info(
            "Upload an MP3, WAV, M4A, OGG or FLAC file to begin."
        )


# ============================================================
# AUDITOR CONSOLE
# ============================================================

st.divider()

st.header("🧑‍💻 Auditor Console")

auditor_tab1, auditor_tab2 = st.tabs(
    [
        "🖼️ Image Manifest",
        "🎧 Audio Manifest",
    ]
)


# ============================================================
# IMAGE MANIFEST
# ============================================================

with auditor_tab1:

    if st.session_state.image_manifest:

        image_df = pd.DataFrame(
            st.session_state.image_manifest
        )

        st.dataframe(
            image_df,
            use_container_width=True,
        )

        csv_data = image_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Image Manifest CSV",
            data=csv_data,
            file_name="image_manifest.csv",
            mime="text/csv",
        )

    else:

        st.info(
            "No image audit records yet."
        )


# ============================================================
# AUDIO MANIFEST
# ============================================================

with auditor_tab2:

    if st.session_state.audio_manifest:

        audio_df = pd.DataFrame(
            st.session_state.audio_manifest
        )

        st.dataframe(
            audio_df,
            use_container_width=True,
        )

        csv_data = audio_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Audio Manifest CSV",
            data=csv_data,
            file_name="audio_manifest.csv",
            mime="text/csv",
        )

    else:

        st.info(
            "No audio audit records yet."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "SEED Lab Multimodal Studio • "
    "Gemini-powered annotation, translation and QC"
)