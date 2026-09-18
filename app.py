import streamlit as st
import pandas as pd
from PIL import Image
from google import genai
from google.genai import types
import json
import io
import time


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SEED Lab Multimodal QC Studio",
    page_icon="🔬",
    layout="wide"
)


# ============================================================
# GEMINI INITIALIZATION
# ============================================================

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if API_KEY:
    client = genai.Client(api_key=API_KEY)
    MODEL_NAME = "gemini-3.6-flash"
else:
    client = None
    MODEL_NAME = ""


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🔬 Samsung SEED Lab: Unified Multimodal Data QC Studio")
st.caption("Centralized Quality Control Pipeline for Vision & Speech Assets")


# ============================================================
# SESSION STATE
# ============================================================

if "image_qc_log" not in st.session_state:
    st.session_state.image_qc_log = []

if "audio_qc_log" not in st.session_state:
    st.session_state.audio_qc_log = []

if "image_result" not in st.session_state:
    st.session_state.image_result = None

if "image_filename" not in st.session_state:
    st.session_state.image_filename = None

if "audio_result" not in st.session_state:
    st.session_state.audio_result = None

if "audio_filename" not in st.session_state:
    st.session_state.audio_filename = None

if "last_audio_error" not in st.session_state:
    st.session_state.last_audio_error = ""


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🎛️ Pipeline Control Center")

studio_mode = st.sidebar.radio(
    "Select Ingestion Modality:",
    [
        "🖼️ Image Data Studio",
        "🔊 Audio Data Studio"
    ]
)

target_lang = st.sidebar.selectbox(
    "Target Translation Language:",
    [
        "English",
        "Spanish",
        "French",
        "Hindi"
    ]
)

st.sidebar.markdown("---")

if client:
    st.sidebar.success("🟢 Gemini Cloud Engine Connected")
    st.sidebar.caption(f"Model: {MODEL_NAME}")
else:
    st.sidebar.warning(
        "🔒 Configure GEMINI_API_KEY in Streamlit Secrets."
    )


# ============================================================
# HELPER: MIME TYPE
# ============================================================

def get_audio_mime_type(filename):
    ext = filename.lower().split(".")[-1]

    mime_types = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg"
    }

    return mime_types.get(
        ext,
        "application/octet-stream"
    )


# ============================================================
# HELPER: RETRY GEMINI REQUEST
# ============================================================

def generate_with_retry(contents, config=None, retries=2):
    last_error = None

    for attempt in range(retries + 1):
        try:
            if config is not None:
                return client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=config
                )

            return client.models.generate_content(
                model=MODEL_NAME,
                contents=contents
            )

        except Exception as e:
            last_error = e
            error_text = str(e)

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            ):
                if attempt < retries:
                    time.sleep(2)
                    continue

            raise last_error

    raise last_error


# ============================================================
# HELPER: CLEAN GEMINI JSON
# ============================================================

def clean_json_response(text):
    if not text:
        raise ValueError("Gemini returned an empty response.")

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    return json.loads(text)


# ============================================================
# HELPER: EXACT DESCRIPTION LINES
# ============================================================

def enforce_description_lines(lines, requested_lines):
    """
    Makes the description contain exactly the requested
    number of displayed lines.
    """

    if isinstance(lines, str):
        raw_lines = [
            line.strip()
            for line in lines.splitlines()
            if line.strip()
        ]
    elif isinstance(lines, list):
        raw_lines = [
            str(line).strip()
            for line in lines
            if str(line).strip()
        ]
    else:
        raw_lines = []

    # Remove accidental numbering.
    cleaned = []

    for line in raw_lines:
        line = line.strip()

        while len(line) > 2 and line[0].isdigit():
            if line[1] in [".", ")", "-", ":"]:
                line = line[2:].strip()
            else:
                break

        cleaned.append(line)

    raw_lines = cleaned

    if not raw_lines:
        return "No audio description generated."

    # If Gemini produced enough lines, keep exactly requested count.
    if len(raw_lines) >= requested_lines:
        return "\n".join(
            raw_lines[:requested_lines]
        )

    # If fewer lines were returned, keep what we have.
    # We don't invent additional information.
    return "\n".join(raw_lines)


# ============================================================
# HELPER: SAFE FLOAT
# ============================================================

def safe_confidence(value, default=0.90):
    try:
        number = float(value)

        if number > 1:
            number = number / 100

        return max(0.0, min(1.0, number))

    except Exception:
        return default


# ============================================================
# IMAGE DATA STUDIO
# ============================================================

if studio_mode == "🖼️ Image Data Studio":

    st.sidebar.subheader("Ingest Image Asset")

    uploaded_file = st.sidebar.file_uploader(
        "Upload Image File",
        type=["jpg", "jpeg", "png"]
    )

    description_lines = st.sidebar.number_input(
        "📝 Description Lines Required",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        key="image_description_lines"
    )

    st.sidebar.caption(
        f"AI will generate approximately {description_lines} lines."
    )

    left_panel, right_panel = st.columns([1, 1.2])

    # ========================================================
    # IMAGE LEFT PANEL
    # ========================================================

    with left_panel:

        st.subheader("🖼️ Vision Feature Extraction")

        if uploaded_file is not None:

            raw_img = Image.open(uploaded_file)

            st.image(
                raw_img,
                caption="Active Image Asset",
                use_container_width=True
            )

            # Reset result when new image is uploaded.
            if (
                st.session_state.image_filename
                != uploaded_file.name
            ):
                st.session_state.image_result = None
                st.session_state.image_filename = uploaded_file.name

            if client:

                if st.button(
                    "⚡ Generate Image Analysis",
                    key="generate_image"
                ):

                    with st.spinner(
                        "🧠 Gemini is analyzing the image..."
                    ):

                        try:

                            img_buffer = io.BytesIO()

                            processed_img = raw_img.copy()

                            if processed_img.mode in ("RGBA", "P"):
                                processed_img = processed_img.convert(
                                    "RGB"
                                )

                            processed_img.thumbnail(
                                (1200, 1200)
                            )

                            processed_img.save(
                                img_buffer,
                                format="JPEG",
                                quality=80
                            )

                            image_bytes = (
                                img_buffer.getvalue()
                            )

                            image_prompt = f"""
Analyze this image for a multimodal data-quality-control pipeline.

Return structured data containing:

1. Extract all clearly visible text exactly.
2. Translate that text into {target_lang}.
3. Describe the visual scene.
4. Give a confidence score between 0 and 1.

The visual description should contain up to {description_lines}
useful lines.

Do not invent information.
"""

                            image_schema = types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "extracted_text": types.Schema(
                                        type=types.Type.STRING
                                    ),
                                    "translated_text": types.Schema(
                                        type=types.Type.STRING
                                    ),
                                    "visual_description": types.Schema(
                                        type=types.Type.STRING
                                    ),
                                    "confidence_score": types.Schema(
                                        type=types.Type.NUMBER
                                    )
                                },
                                required=[
                                    "extracted_text",
                                    "translated_text",
                                    "visual_description",
                                    "confidence_score"
                                ]
                            )

                            image_config = (
                                types.GenerateContentConfig(
                                    response_mime_type="application/json",
                                    response_schema=image_schema
                                )
                            )

                            response = generate_with_retry(
                                [
                                    image_prompt,
                                    types.Part.from_bytes(
                                        data=image_bytes,
                                        mime_type="image/jpeg"
                                    )
                                ],
                                config=image_config
                            )

                            data = clean_json_response(
                                response.text
                            )

                            st.session_state.image_result = {
                                "extracted_text": data.get(
                                    "extracted_text",
                                    "No text detected."
                                ),

                                "translated_text": data.get(
                                    "translated_text",
                                    "No translation available."
                                ),

                                "visual_description": data.get(
                                    "visual_description",
                                    "No description available."
                                ),

                                "confidence_score": safe_confidence(
                                    data.get(
                                        "confidence_score",
                                        0.90
                                    )
                                )
                            }

                            st.success(
                                "✅ Image analysis completed!"
                            )

                        except Exception as e:

                            st.session_state.image_result = None

                            st.error(
                                "❌ Image processing error"
                            )

                            st.code(
                                str(e)
                            )

            else:

                st.warning(
                    "🔒 Add GEMINI_API_KEY to Streamlit Secrets."
                )

            # ====================================================
            # IMAGE RESULTS
            # ====================================================

            result = st.session_state.image_result

            if result:

                extracted_text = result[
                    "extracted_text"
                ]

                translated_text = result[
                    "translated_text"
                ]

                visual_description = result[
                    "visual_description"
                ]

                ocr_confidence = result[
                    "confidence_score"
                ]

            else:

                extracted_text = (
                    "No analysis generated yet."
                )

                translated_text = (
                    "No translation generated yet."
                )

                visual_description = (
                    "No description generated yet."
                )

                ocr_confidence = 0.0

            st.markdown("---")

            raw_txt = st.text_area(
                "1. Extracted Text (Live OCR)",
                value=extracted_text,
                height=100,
                key="image_raw_text"
            )

            trans_txt = st.text_area(
                f"2. Live Translated Output ({target_lang})",
                value=translated_text,
                height=100,
                key="image_translation"
            )

            desc_txt = st.text_area(
                "3. AI Visual Scene Description",
                value=visual_description,
                height=180,
                key="image_description"
            )

        else:

            st.info(
                "Awaiting image dataset payload via the control panel."
            )

    # ========================================================
    # IMAGE RIGHT PANEL
    # ========================================================

    with right_panel:

        st.subheader("🛡️ Image QC Gatekeeper")

        if (
            uploaded_file is not None
            and client
            and st.session_state.get("image_result")
        ):

            st.markdown(
                "#### Automated Integrity Diagnostics"
            )

            c1 = ocr_confidence >= 0.85

            st.write(
                f"{'✅' if c1 else '❌'} "
                f"**Rule 1: OCR Confidence Baseline** "
                f"({ocr_confidence * 100:.1f}%)"
            )

            description_words = len(
                desc_txt.split()
            )

            c2 = description_words >= 8

            st.write(
                f"{'✅' if c2 else '❌'} "
                f"**Rule 2: Semantic Density Verification** "
                f"({description_words} words)"
            )

            c3 = bool(
                raw_txt.strip()
                and trans_txt.strip()
                and desc_txt.strip()
            )

            st.write(
                f"{'✅' if c3 else '❌'} "
                "**Rule 3: Non-Null Structural Payload**"
            )

            st.markdown("---")

            st.markdown(
                "#### Data Auditor Console"
            )

            audit_verdict = st.radio(
                "Pipeline Routing Action:",
                [
                    "Approve & Record",
                    "Flag for Text Adjustments",
                    "Reject Dataset Item"
                ],
                key="image_verdict"
            )

            auditor_notes = st.text_input(
                "Auditor Quality Log Entries:",
                key="image_notes"
            )

            if st.button(
                "Commit Image Record",
                key="commit_image"
            ):

                st.session_state.image_qc_log.append(
                    {
                        "Filename": uploaded_file.name,
                        "Modality": "Vision",
                        "Language": target_lang,
                        "Description Lines": description_lines,
                        "Confidence": ocr_confidence,
                        "Verdict": audit_verdict,
                        "Notes": (
                            auditor_notes
                            if auditor_notes
                            else "Verified Asset"
                        )
                    }
                )

                st.success(
                    "✅ Image record successfully verified and logged!"
                )

        st.markdown(
            "### 📊 Active Batch Image Manifest"
        )

        if st.session_state.image_qc_log:

            df_img = pd.DataFrame(
                st.session_state.image_qc_log
            )

            st.dataframe(
                df_img,
                use_container_width=True
            )

            csv_img = df_img.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "📥 Export Image Manifest (CSV)",
                csv_img,
                "image_pipeline_manifest.csv",
                "text/csv"
            )

        else:

            st.caption(
                "No dynamic image rows logged in this batch yet."
            )


# ============================================================
# AUDIO DATA STUDIO
# ============================================================

elif studio_mode == "🔊 Audio Data Studio":

    st.sidebar.subheader("Ingest Audio Asset")

    uploaded_audio = st.sidebar.file_uploader(
        "Upload Audio File",
        type=["mp3", "wav", "m4a", "ogg"]
    )

    description_lines = st.sidebar.number_input(
        "📝 Audio Description Lines Required",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        key="audio_description_lines"
    )

    st.sidebar.caption(
        f"AI will generate approximately {description_lines} lines."
    )

    left_panel, right_panel = st.columns([1, 1.2])

    # ========================================================
    # AUDIO LEFT PANEL
    # ========================================================

    with left_panel:

        st.subheader("🔊 Acoustic Feature Extraction")

        if uploaded_audio is not None:

            st.audio(uploaded_audio)

            # Reset when new audio is uploaded.
            if (
                st.session_state.audio_filename
                != uploaded_audio.name
            ):
                st.session_state.audio_result = None
                st.session_state.audio_filename = (
                    uploaded_audio.name
                )
                st.session_state.last_audio_error = ""

            if client:

                if st.button(
                    "⚡ Generate Audio Analysis",
                    key="generate_audio"
                ):

                    with st.spinner(
                        "🧠 Gemini is listening and analyzing the audio..."
                    ):

                        try:

                            # ------------------------------------
                            # READ AUDIO
                            # ------------------------------------

                            audio_bytes = (
                                uploaded_audio.getvalue()
                            )

                            if not audio_bytes:
                                raise ValueError(
                                    "The uploaded audio file is empty."
                                )

                            mime_type = (
                                get_audio_mime_type(
                                    uploaded_audio.name
                                )
                            )

                            # ------------------------------------
                            # UPLOAD AUDIO USING GEMINI FILE API
                            # ------------------------------------

                            audio_stream = io.BytesIO(
                                audio_bytes
                            )

                            audio_stream.name = (
                                uploaded_audio.name
                            )

                            uploaded_gemini_file = (
                                client.files.upload(
                                    file=audio_stream,
                                    config=types.UploadFileConfig(
                                        mime_type=mime_type
                                    )
                                )
                            )

                            # ------------------------------------
                            # AUDIO PROMPT
                            # ------------------------------------

                            audio_prompt = f"""
Analyze this audio recording for a multimodal
data-quality-control pipeline.

Return:

1. A clear transcript of understandable speech.
2. A translation of the transcript into {target_lang}.
3. An audio description containing approximately
   {description_lines} separate lines.
4. A confidence score from 0 to 1.

For the audio description, describe only information
that can reasonably be determined from the recording.

Consider:
- speech
- language
- music
- instruments
- background sounds
- environmental sounds
- noise
- speaker characteristics when reasonably identifiable
- recording clarity
- overall acoustic content

If there is no understandable speech, say:
"No clear speech detected."

If the recording is mainly music or environmental sound,
describe that clearly.

Do not invent sounds or events.
"""

                            # ------------------------------------
                            # STRUCTURED OUTPUT SCHEMA
                            # ------------------------------------

                            audio_schema = types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "transcript": types.Schema(
                                        type=types.Type.STRING,
                                        description=(
                                            "Clear transcription "
                                            "of understandable speech."
                                        )
                                    ),

                                    "translation": types.Schema(
                                        type=types.Type.STRING,
                                        description=(
                                            f"Translation of the "
                                            f"transcript into "
                                            f"{target_lang}."
                                        )
                                    ),

                                    "audio_description_lines": (
                                        types.Schema(
                                            type=types.Type.ARRAY,
                                            items=types.Schema(
                                                type=types.Type.STRING
                                            ),
                                            description=(
                                                "Separate description "
                                                "lines describing the "
                                                "audio."
                                            )
                                        )
                                    ),

                                    "confidence_score": types.Schema(
                                        type=types.Type.NUMBER,
                                        description=(
                                            "Confidence from 0 to 1."
                                        )
                                    )
                                },

                                required=[
                                    "transcript",
                                    "translation",
                                    "audio_description_lines",
                                    "confidence_score"
                                ]
                            )

                            audio_config = (
                                types.GenerateContentConfig(
                                    response_mime_type=(
                                        "application/json"
                                    ),
                                    response_schema=audio_schema
                                )
                            )

                            # ------------------------------------
                            # GEMINI AUDIO REQUEST
                            # ------------------------------------

                            response = generate_with_retry(
                                [
                                    uploaded_gemini_file,
                                    audio_prompt
                                ],
                                config=audio_config
                            )

                            # ------------------------------------
                            # DEBUG RESPONSE CHECK
                            # ------------------------------------

                            if not response:
                                raise ValueError(
                                    "Gemini returned no response."
                                )

                            response_text = (
                                response.text
                            )

                            if not response_text:
                                raise ValueError(
                                    "Gemini returned an empty text response."
                                )

                            # ------------------------------------
                            # PARSE STRUCTURED JSON
                            # ------------------------------------

                            data = clean_json_response(
                                response_text
                            )

                            transcript_value = (
                                data.get(
                                    "transcript",
                                    ""
                                )
                            )

                            translation_value = (
                                data.get(
                                    "translation",
                                    ""
                                )
                            )

                            description_value = (
                                data.get(
                                    "audio_description_lines",
                                    []
                                )
                            )

                            confidence_value = (
                                data.get(
                                    "confidence_score",
                                    0.90
                                )
                            )

                            # ------------------------------------
                            # DESCRIPTION LINE PROCESSING
                            # ------------------------------------

                            final_description = (
                                enforce_description_lines(
                                    description_value,
                                    int(description_lines)
                                )
                            )

                            # ------------------------------------
                            # FALLBACKS
                            # ------------------------------------

                            if not transcript_value:
                                transcript_value = (
                                    "No clear speech detected."
                                )

                            if not translation_value:
                                translation_value = (
                                    "No translation available."
                                )

                            if not final_description:
                                final_description = (
                                    "No audio description generated."
                                )

                            # ------------------------------------
                            # SAVE RESULT
                            # ------------------------------------

                            st.session_state.audio_result = {
                                "transcript": (
                                    str(
                                        transcript_value
                                    )
                                ),

                                "translation": (
                                    str(
                                        translation_value
                                    )
                                ),

                                "audio_description": (
                                    final_description
                                ),

                                "confidence_score": (
                                    safe_confidence(
                                        confidence_value
                                    )
                                )
                            }

                            st.session_state.last_audio_error = ""

                            st.success(
                                "✅ Audio analysis completed successfully!"
                            )

                        except json.JSONDecodeError as e:

                            st.session_state.audio_result = None

                            error_message = (
                                "Gemini returned data that "
                                "could not be parsed as JSON."
                            )

                            st.session_state.last_audio_error = (
                                error_message
                            )

                            st.error(
                                f"❌ {error_message}"
                            )

                            st.code(
                                str(e)
                            )

                        except Exception as e:

                            st.session_state.audio_result = None

                            error_message = str(e)

                            st.session_state.last_audio_error = (
                                error_message
                            )

                            st.error(
                                "❌ Audio processing error"
                            )

                            st.code(
                                error_message
                            )

            else:

                st.warning(
                    "🔒 Add GEMINI_API_KEY to Streamlit Secrets."
                )

            # ====================================================
            # AUDIO RESULTS
            # ====================================================

            result = st.session_state.audio_result

            if result:

                transcript = result[
                    "transcript"
                ]

                translation = result[
                    "translation"
                ]

                audio_description = result[
                    "audio_description"
                ]

                audio_confidence = result[
                    "confidence_score"
                ]

            else:

                transcript = (
                    "No analysis generated yet."
                )

                translation = (
                    "No translation generated yet."
                )

                audio_description = (
                    "No audio description generated yet."
                )

                audio_confidence = 0.0

            st.markdown("---")

            # ====================================================
            # 1. TRANSCRIPT
            # ====================================================

            st.markdown(
                "### 📝 1. Live Audio Transcript"
            )

            transcript_txt = st.text_area(
                "Transcript",
                value=transcript,
                height=130,
                label_visibility="collapsed",
                key="audio_transcript"
            )

            # ====================================================
            # 2. TRANSLATION
            # ====================================================

            st.markdown(
                f"### 🌐 2. Translation ({target_lang})"
            )

            translation_txt = st.text_area(
                "Translation",
                value=translation,
                height=130,
                label_visibility="collapsed",
                key="audio_translation"
            )

            # ====================================================
            # 3. AUDIO DESCRIPTION
            # ====================================================

            st.markdown(
                "### 🎧 3. AI Audio Description"
            )

            audio_desc_txt = st.text_area(
                "Audio Description",
                value=audio_description,
                height=220,
                label_visibility="collapsed",
                key="audio_description"
            )

            st.markdown(
                f"**AI Analysis Confidence:** "
                f"{audio_confidence * 100:.1f}%"
            )

            # Show previous error if one exists.
            if (
                st.session_state.last_audio_error
                and not st.session_state.audio_result
            ):

                with st.expander(
                    "🔎 Show technical error"
                ):

                    st.code(
                        st.session_state.last_audio_error
                    )

        else:

            st.info(
                "🎵 Upload an MP3, WAV, M4A or OGG file "
                "from the control panel."
            )

    # ========================================================
    # AUDIO RIGHT PANEL
    # ========================================================

    with right_panel:

        st.subheader("🛡️ Audio QC Gatekeeper")

        if (
            uploaded_audio is not None
            and client
            and st.session_state.get("audio_result")
        ):

            st.markdown(
                "#### Automated Integrity Diagnostics"
            )

            transcript_ok = bool(
                transcript_txt.strip()
                and
                "No analysis generated yet."
                not in transcript_txt
            )

            description_word_count = len(
                audio_desc_txt.split()
            )

            description_ok = (
                description_word_count >= 10
            )

            confidence_ok = (
                audio_confidence >= 0.75
            )

            st.write(
                f"{'✅' if transcript_ok else '❌'} "
                "**Rule 1: Transcript Payload**"
            )

            st.write(
                f"{'✅' if description_ok else '❌'} "
                "**Rule 2: Audio Description Density** "
                f"({description_word_count} words)"
            )

            st.write(
                f"{'✅' if confidence_ok else '❌'} "
                "**Rule 3: AI Confidence Baseline** "
                f"({audio_confidence * 100:.1f}%)"
            )

            st.markdown("---")

            st.markdown(
                "#### 🎛️ Data Auditor Console"
            )

            audio_verdict = st.radio(
                "Pipeline Routing Action:",
                [
                    "Approve & Record",
                    "Flag for Audio Adjustments",
                    "Reject Dataset Item"
                ],
                key="audio_verdict"
            )

            audio_notes = st.text_input(
                "Audio Auditor Quality Log Entries:",
                key="audio_notes"
            )

            if st.button(
                "Commit Audio Record",
                key="commit_audio"
            ):

                st.session_state.audio_qc_log.append(
                    {
                        "Filename": uploaded_audio.name,
                        "Modality": "Audio",
                        "Language": target_lang,
                        "Description Lines": description_lines,
                        "Confidence": audio_confidence,
                        "Verdict": audio_verdict,
                        "Notes": (
                            audio_notes
                            if audio_notes
                            else "Verified Audio Asset"
                        )
                    }
                )

                st.success(
                    "✅ Audio record successfully verified and logged!"
                )

        st.markdown(
            "### 📊 Active Batch Audio Manifest"
        )

        if st.session_state.audio_qc_log:

            df_audio = pd.DataFrame(
                st.session_state.audio_qc_log
            )

            st.dataframe(
                df_audio,
                use_container_width=True
            )

            csv_audio = df_audio.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "📥 Export Audio Manifest (CSV)",
                csv_audio,
                "audio_pipeline_manifest.csv",
                "text/csv"
            )

        else:

            st.caption(
                "No dynamic audio rows logged in this batch yet."
            )