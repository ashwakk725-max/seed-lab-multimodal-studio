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
# GEMINI CONFIG
# ============================================================

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not API_KEY:
    st.error("GEMINI_API_KEY is missing from Streamlit Secrets.")
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

if "image_result" not in st.session_state:
    st.session_state.image_result = None

if "audio_result" not in st.session_state:
    st.session_state.audio_result = None

if "image_qc_log" not in st.session_state:
    st.session_state.image_qc_log = []

if "audio_qc_log" not in st.session_state:
    st.session_state.audio_qc_log = []

if "image_manifest" not in st.session_state:
    st.session_state.image_manifest = []

if "audio_manifest" not in st.session_state:
    st.session_state.audio_manifest = []

if "image_generation_id" not in st.session_state:
    st.session_state.image_generation_id = 0

if "audio_generation_id" not in st.session_state:
    st.session_state.audio_generation_id = 0

if "target_language" not in st.session_state:
    st.session_state.target_language = "Hindi"


# ============================================================
# GENERAL HELPERS
# ============================================================

def is_retryable_error(error):
    text = str(error).upper()

    retry_terms = [
        "503",
        "UNAVAILABLE",
        "429",
        "RESOURCE_EXHAUSTED",
        "TOO MANY REQUESTS",
        "HIGH DEMAND",
        "TIMEOUT",
        "DEADLINE",
        "INTERNAL",
    ]

    return any(term in text for term in retry_terms)


def generate_with_fallback(contents, config=None):
    errors = []

    for index, model in enumerate(ALL_MODELS):

        attempts = 2 if index == 0 else 1

        for attempt in range(attempts):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )

                return response, model, errors

            except Exception as error:

                errors.append(
                    f"{model}: {str(error)}"
                )

                if (
                    is_retryable_error(error)
                    and attempt < attempts - 1
                ):
                    time.sleep(2)
                    continue

                break

    raise RuntimeError(
        "All Gemini models failed.\n\n"
        + "\n\n".join(errors)
    )


def get_response_text(response):
    """
    Safely extract text from Gemini response.
    """

    try:
        text = response.text

        if text:
            return str(text).strip()

    except Exception:
        pass

    try:
        candidates = response.candidates

        if candidates:

            parts = candidates[0].content.parts

            output = []

            for part in parts:

                if hasattr(part, "text") and part.text:
                    output.append(
                        str(part.text)
                    )

            if output:
                return "\n".join(output).strip()

    except Exception:
        pass

    return ""


def clean_json_response(text):

    if not text:
        return ""

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    return text.strip()


def safe_json_loads(text):

    if not text:
        return None

    cleaned = clean_json_response(text)

    try:
        return json.loads(cleaned)

    except Exception:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start >= 0 and end > start:

        candidate = cleaned[start:end + 1]

        try:
            return json.loads(candidate)

        except Exception:
            pass

    return None


def normalize_text(value):

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

    if value is None:
        return []

    if isinstance(value, list):

        lines = []

        for item in value:

            text = str(item).strip()

            if not text:
                continue

            for line in text.splitlines():

                line = line.strip()

                if line:
                    lines.append(line)

        return lines

    text = str(value).strip()

    if not text:
        return []

    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def description_to_text(lines):

    return "\n".join(
        str(line).strip()
        for line in lines
        if str(line).strip()
    )


def get_confidence(data):

    if not isinstance(data, dict):
        return None

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

            if 0 <= value <= 1:
                value = value * 100

            return max(
                0.0,
                min(100.0, value)
            )

        except Exception:
            continue

    return None


def json_config():

    return types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
    )


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def analyze_image(
    image_bytes,
    filename,
    target_language,
    requested_lines,
):

    prompt = f"""
You are a professional multimodal data-quality annotator.

Analyze the supplied image.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "ocr_text": "readable text visible in the image",
  "translation": "translation into {target_language}",
  "image_description_lines": [
    "line 1",
    "line 2"
  ],
  "confidence_score": 0
}}

IMPORTANT:

- image_description_lines MUST contain EXACTLY {requested_lines} strings.
- Do not return fewer lines.
- Do not return more lines.
- Each item must be a separate description line.
- Do not invent visual information.
- Describe different valid visual aspects when possible.
- OCR must contain only text actually visible.
- Translation must translate the OCR text into {target_language}.
- confidence_score must be between 0 and 100.
- Return JSON only.
"""

    image = Image.open(
        io.BytesIO(image_bytes)
    )

    image_buffer = io.BytesIO()

    image.convert("RGB").save(
        image_buffer,
        format="JPEG",
        quality=92,
    )

    image_data = image_buffer.getvalue()

    contents = [
        prompt,
        types.Part.from_bytes(
            data=image_data,
            mime_type="image/jpeg",
        ),
    ]

    response, model_used, errors = generate_with_fallback(
        contents,
        config=json_config(),
    )

    raw_response = get_response_text(response)

    data = safe_json_loads(raw_response)

    if not isinstance(data, dict):
        data = {}

    ocr_text = normalize_text(
        data.get("ocr_text")
    )

    translation = normalize_text(
        data.get("translation")
    )

    description_lines = get_description_lines(
        data.get("image_description_lines")
        or data.get("description")
        or data.get("image_description")
    )

    confidence = get_confidence(data)

    if not ocr_text:
        ocr_text = "No readable text detected."

    if not translation:
        translation = "No translation available."

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
# AUDIO UPLOAD
# ============================================================

def upload_audio(
    audio_bytes,
    filename,
    mime_type,
):

    audio_stream = io.BytesIO(
        audio_bytes
    )

    audio_stream.name = filename

    uploaded_file = client.files.upload(
        file=audio_stream,
        config=types.UploadFileConfig(
            mime_type=mime_type
        ),
    )

    return uploaded_file


# ============================================================
# AUDIO ANALYSIS
# ============================================================

def analyze_audio(
    audio_bytes,
    filename,
    mime_type,
    target_language,
    requested_lines,
):

    prompt = f"""
You are a professional audio data-quality annotator.

Analyze the supplied audio file carefully.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "transcript": "complete understandable spoken content",
  "translation": "translation into {target_language}",
  "audio_description_lines": [
    "line 1",
    "line 2"
  ],
  "confidence_score": 0
}}

CRITICAL REQUIREMENTS:

1. audio_description_lines MUST contain EXACTLY {requested_lines} separate strings.

2. Do NOT return fewer than {requested_lines} lines.

3. Do NOT return more than {requested_lines} lines.

4. Each description must be a separate meaningful observation.

5. Do not repeat the same sentence.

6. Do not invent sounds or events.

7. If speech exists, describe speech-related characteristics.

8. You may separately describe:
   - speech presence
   - language
   - speaker characteristics when reasonably identifiable
   - music
   - background sounds
   - environmental sounds
   - noise
   - clarity
   - recording quality
   - acoustic environment
   - silence
   - notable audio events

9. If there is no understandable speech, use:
   "No clear speech detected."

10. If there is no speech to translate, use:
   "No translation available."

11. confidence_score must be between 0 and 100.

12. Return JSON only.
"""

    uploaded_file = upload_audio(
        audio_bytes,
        filename,
        mime_type,
    )

    contents = [
        prompt,
        uploaded_file,
    ]

    response, model_used, errors = generate_with_fallback(
        contents,
        config=json_config(),
    )

    raw_response = get_response_text(response)

    data = safe_json_loads(raw_response)

    if not isinstance(data, dict):
        data = {}

    transcript = normalize_text(
        data.get("transcript")
        or data.get("transcription")
    )

    translation = normalize_text(
        data.get("translation")
        or data.get("translated_text")
    )

    description_lines = get_description_lines(
        data.get("audio_description_lines")
        or data.get("description")
        or data.get("audio_description")
    )

    confidence = get_confidence(data)

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
# IMAGE QC
# ============================================================

def image_qc(result):

    checks = []

    ocr_ok = (
        bool(result.get("ocr_text"))
        and result.get("ocr_text")
        != "No readable text detected."
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

    actual = len(
        result.get("description_lines", [])
    )

    required = result.get(
        "requested_lines",
        0,
    )

    description_ok = actual == required

    checks.append({
        "rule": "Rule 2 - Image Description Density",
        "status": "PASS" if description_ok else "FAIL",
        "details": f"{actual}/{required} lines",
    })

    confidence = result.get(
        "confidence"
    )

    if confidence is None:

        confidence_ok = False
        confidence_details = (
            "Confidence not supplied by Gemini"
        )

    else:

        confidence_ok = confidence >= 80
        confidence_details = (
            f"{confidence:.1f}%"
        )

    checks.append({
        "rule": "Rule 3 - AI Confidence Baseline",
        "status": (
            "PASS"
            if confidence_ok
            else "FAIL"
        ),
        "details": confidence_details,
    })

    return checks


# ============================================================
# AUDIO QC
# ============================================================

def audio_qc(result):

    checks = []

    transcript = normalize_text(
        result.get("transcript")
    )

    transcript_ok = (
        bool(transcript)
        and transcript
        != "No clear speech detected."
    )

    checks.append({
        "rule": "Rule 1 - Transcript Payload",
        "status": (
            "PASS"
            if transcript_ok
            else "FAIL"
        ),
        "details": (
            "Transcript detected"
            if transcript_ok
            else "No clear speech detected"
        ),
    })

    actual = len(
        result.get("description_lines", [])
    )

    required = result.get(
        "requested_lines",
        0,
    )

    description_ok = actual == required

    checks.append({
        "rule": "Rule 2 - Audio Description Density",
        "status": (
            "PASS"
            if description_ok
            else "FAIL"
        ),
        "details": f"{actual}/{required} lines",
    })

    confidence = result.get(
        "confidence"
    )

    if confidence is None:

        confidence_ok = False
        confidence_details = (
            "Confidence not supplied by Gemini"
        )

    else:

        confidence_ok = confidence >= 80
        confidence_details = (
            f"{confidence:.1f}%"
        )

    checks.append({
        "rule": "Rule 3 - AI Confidence Baseline",
        "status": (
            "PASS"
            if confidence_ok
            else "FAIL"
        ),
        "details": confidence_details,
    })

    return checks


def count_passed(checks):

    return sum(
        1
        for item in checks
        if item["status"] == "PASS"
    )


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

st.sidebar.success(
    "Gemini Cloud Engine Connected"
)

st.sidebar.caption(
    f"Primary Model: {PRIMARY_MODEL}"
)

st.sidebar.caption(
    "Automatic fallback enabled"
)


# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    "SEED Lab Multimodal Studio"
)

st.caption(
    "Unified multimodal data annotation, "
    "translation and quality-control workspace"
)


# ============================================================
# IMAGE DATA STUDIO
# ============================================================

if mode == "🖼️ Image Data Studio":

    st.header("🖼️ Image Data Studio")

    col1, col2 = st.columns(
        [2, 1]
    )

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

        image_lines = st.number_input(
            "Description Lines Required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
            key="image_line_count",
        )

    if uploaded_image:

        image_bytes = (
            uploaded_image.getvalue()
        )

        st.image(
            image_bytes,
            caption=uploaded_image.name,
            use_container_width=True,
        )

        st.write(
            f"Translation language: **{target_language}**"
        )

        st.write(
            f"Description lines required: "
            f"**{image_lines}**"
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
                            image_lines
                        ),
                    )

                    st.session_state.image_result = result

                    st.session_state.image_generation_id += 1

                    checks = image_qc(
                        result
                    )

                    st.session_state.image_qc_log = checks

                    st.success(
                        "Image analysis completed."
                    )

                    if (
                        result["model"]
                        != PRIMARY_MODEL
                    ):

                        st.warning(
                            "Primary model was busy. "
                            f"Analysis completed using "
                            f"`{result['model']}`."
                        )

                except Exception as error:

                    st.error(
                        "Image analysis failed."
                    )

                    st.exception(error)

        result = st.session_state.image_result

        if result:

            st.divider()

            st.subheader(
                "AI Image Analysis"
            )

            # =================================================
            # CONFIDENCE
            # =================================================

            confidence = result.get(
                "confidence"
            )

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
                f"Generated using "
                f"`{result.get('model', 'Unknown')}`"
            )

            # =================================================
            # OCR
            # =================================================

            st.markdown(
                "### 📝 OCR Text"
            )

            st.text_area(
                "Detected Text",
                value=result.get(
                    "ocr_text",
                    "No readable text detected.",
                ),
                height=180,
                key=(
                    f"image_ocr_"
                    f"{st.session_state.image_generation_id}"
                ),
            )

            # =================================================
            # TRANSLATION
            # =================================================

            st.markdown(
                f"### 🌐 Translation ({target_language})"
            )

            st.text_area(
                "Translated Text",
                value=result.get(
                    "translation",
                    "No translation available.",
                ),
                height=180,
                key=(
                    f"image_translation_"
                    f"{st.session_state.image_generation_id}"
                ),
            )

            # =================================================
            # DESCRIPTION
            # =================================================

            st.markdown(
                "### 👁️ AI Image Description"
            )

            image_description = (
                description_to_text(
                    result.get(
                        "description_lines",
                        [],
                    )
                )
            )

            if not image_description:

                image_description = (
                    "No image description was returned."
                )

            st.text_area(
                "Description",
                value=image_description,
                height=240,
                key=(
                    f"image_description_"
                    f"{st.session_state.image_generation_id}"
                ),
            )

            # =================================================
            # QC
            # =================================================

            st.subheader(
                "Quality Control"
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

            with st.expander(
                "🔎 Technical Response / Debug"
            ):

                st.write(
                    "Model:",
                    result.get(
                        "model",
                        "Unknown",
                    ),
                )

                st.write(
                    "Requested lines:",
                    result.get(
                        "requested_lines",
                        0,
                    ),
                )

                st.write(
                    "Generated lines:",
                    len(
                        result.get(
                            "description_lines",
                            [],
                        )
                    ),
                )

                st.markdown(
                    "#### Raw Gemini Response"
                )

                raw = result.get(
                    "raw_response",
                    "",
                )

                if raw:

                    st.code(
                        raw,
                        language="text",
                    )

                else:

                    st.warning(
                        "Gemini returned an empty response."
                    )

                errors = result.get(
                    "errors",
                    [],
                )

                if errors:

                    st.markdown(
                        "#### Model Errors"
                    )

                    for error in errors:

                        st.code(
                            error,
                            language="text",
                        )

    else:

        st.info(
            "Upload an image to begin."
        )


# ============================================================
# AUDIO DATA STUDIO
# ============================================================

else:

    st.header("🎧 Audio Data Studio")

    col1, col2 = st.columns(
        [2, 1]
    )

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

        audio_lines = st.number_input(
            "Description Lines Required",
            min_value=1,
            max_value=20,
            value=7,
            step=1,
            key="audio_line_count",
        )

    if uploaded_audio:

        audio_bytes = (
            uploaded_audio.getvalue()
        )

        extension = (
            uploaded_audio.name
            .lower()
            .split(".")[-1]
        )

        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "m4a": "audio/mp4",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
        }

        mime_type = mime_types.get(
            extension,
            "application/octet-stream",
        )

        # ====================================================
        # AUDIO PLAYER
        # ====================================================

        st.audio(
            audio_bytes,
            format=mime_type,
        )

        st.caption(
            f"File: {uploaded_audio.name} | "
            f"Size: "
            f"{len(audio_bytes) / (1024 * 1024):.2f} MB"
        )

        st.info(
            f"Target translation: **{target_language}**  \n"
            f"Description lines required: **{audio_lines}**"
        )

        # ====================================================
        # GENERATE
        # ====================================================

        generate_audio = st.button(
            "🚀 Generate Audio Analysis",
            type="primary",
            use_container_width=True,
        )

        if generate_audio:

            with st.spinner(
                "Gemini is listening to the audio..."
            ):

                try:

                    result = analyze_audio(
                        audio_bytes=audio_bytes,
                        filename=uploaded_audio.name,
                        mime_type=mime_type,
                        target_language=target_language,
                        requested_lines=int(
                            audio_lines
                        ),
                    )

                    st.session_state.audio_result = result

                    st.session_state.audio_generation_id += 1

                    checks = audio_qc(
                        result
                    )

                    st.session_state.audio_qc_log = checks

                    st.success(
                        "Audio analysis completed."
                    )

                    if (
                        result["model"]
                        != PRIMARY_MODEL
                    ):

                        st.warning(
                            "Primary model was busy. "
                            f"Analysis completed using "
                            f"`{result['model']}`."
                        )

                except Exception as error:

                    st.error(
                        "Audio analysis failed."
                    )

                    st.exception(error)

        # ====================================================
        # DISPLAY RESULT
        # ====================================================

        result = st.session_state.audio_result

        if result:

            st.divider()

            st.subheader(
                "AI Audio Analysis"
            )

            # =================================================
            # CONFIDENCE
            # =================================================

            confidence = result.get(
                "confidence"
            )

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
                f"Generated using "
                f"`{result.get('model', 'Unknown')}`"
            )

            # =================================================
            # TRANSCRIPT
            # =================================================

            st.markdown(
                "### 🎤 Live Audio Transcript"
            )

            transcript = normalize_text(
                result.get(
                    "transcript"
                )
            )

            if not transcript:

                transcript = (
                    "No clear speech detected."
                )

            st.text_area(
                "Transcript",
                value=transcript,
                height=200,
                key=(
                    f"audio_transcript_"
                    f"{st.session_state.audio_generation_id}"
                ),
            )

            # =================================================
            # TRANSLATION
            # =================================================

            st.markdown(
                f"### 🌐 Translation ({target_language})"
            )

            translation = normalize_text(
                result.get(
                    "translation"
                )
            )

            if not translation:

                translation = (
                    "No translation available."
                )

            st.text_area(
                "Translation",
                value=translation,
                height=200,
                key=(
                    f"audio_translation_"
                    f"{st.session_state.audio_generation_id}"
                ),
            )

            # =================================================
            # AUDIO DESCRIPTION
            # =================================================

            st.markdown(
                "### 🔊 AI Audio Description"
            )

            description = description_to_text(
                result.get(
                    "description_lines",
                    [],
                )
            )

            if not description:

                description = (
                    "No audio description was returned by Gemini."
                )

            st.text_area(
                "Audio Description",
                value=description,
                height=280,
                key=(
                    f"audio_description_"
                    f"{st.session_state.audio_generation_id}"
                ),
            )

            # =================================================
            # LINE COUNT
            # =================================================

            actual_lines = len(
                result.get(
                    "description_lines",
                    [],
                )
            )

            required_lines = result.get(
                "requested_lines",
                0,
            )

            if actual_lines == required_lines:

                st.success(
                    f"Description density: "
                    f"{actual_lines}/{required_lines} "
                    f"lines generated."
                )

            else:

                st.warning(
                    f"Description density: "
                    f"{actual_lines}/{required_lines} "
                    f"lines generated."
                )

            # =================================================
            # QC
            # =================================================

            st.subheader(
                "Quality Control"
            )

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
            # DEBUG
            # =================================================

            with st.expander(
                "🔎 Technical Response / Debug"
            ):

                st.write(
                    "Model:",
                    result.get(
                        "model",
                        "Unknown",
                    ),
                )

                st.write(
                    "Requested lines:",
                    result.get(
                        "requested_lines",
                        0,
                    ),
                )

                st.write(
                    "Generated lines:",
                    len(
                        result.get(
                            "description_lines",
                            [],
                        )
                    ),
                )

                st.markdown(
                    "#### Raw Gemini Response"
                )

                raw_response = result.get(
                    "raw_response",
                    "",
                )

                if raw_response:

                    st.code(
                        raw_response,
                        language="text",
                    )

                else:

                    st.warning(
                        "Gemini returned an empty response."
                    )

                errors = result.get(
                    "errors",
                    [],
                )

                if errors:

                    st.markdown(
                        "#### Model Errors"
                    )

                    for error in errors:

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

st.header(
    "🧑‍💻 Auditor Console"
)

tab1, tab2 = st.tabs(
    [
        "🖼️ Image Manifest",
        "🎧 Audio Manifest",
    ]
)


# ============================================================
# IMAGE MANIFEST
# ============================================================

with tab1:

    if st.session_state.image_manifest:

        image_df = pd.DataFrame(
            st.session_state.image_manifest
        )

        st.dataframe(
            image_df,
            use_container_width=True,
        )

        image_csv = image_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Image Manifest CSV",
            data=image_csv,
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

with tab2:

    if st.session_state.audio_manifest:

        audio_df = pd.DataFrame(
            st.session_state.audio_manifest
        )

        st.dataframe(
            audio_df,
            use_container_width=True,
        )

        audio_csv = audio_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Audio Manifest CSV",
            data=audio_csv,
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
    "Gemini-powered multimodal annotation, "
    "translation and quality control"
)