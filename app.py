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
    layout="wide"
)


# ============================================================
# GEMINI INITIALIZATION
# ============================================================

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if API_KEY:
    client = genai.Client(api_key=API_KEY)

    # Primary model
    MODEL_NAME = "gemini-3.8-flash"

    # Automatic fallback models
    FALLBACK_MODELS = [
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash"
    ]

else:
    client = None
    MODEL_NAME = ""
    FALLBACK_MODELS = []


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🔬 Samsung SEED Lab: Unified Multimodal Data QC Studio")

st.caption(
    "Centralized Quality Control Pipeline for Vision & Speech Assets"
)


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

    st.sidebar.success(
        "🟢 Gemini Cloud Engine Connected"
    )

    st.sidebar.caption(
        f"Primary Model: {MODEL_NAME}"
    )

    st.sidebar.caption(
        "Automatic fallback enabled"
    )

else:

    st.sidebar.warning(
        "🔒 Configure GEMINI_API_KEY in Streamlit Secrets."
    )


# ============================================================
# HELPER: AUDIO MIME TYPE
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
# HELPER: CLEAN GEMINI JSON
# ============================================================

def clean_json_response(text):

    if not text:
        return ""

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# ============================================================
# HELPER: DESCRIPTION LINE PROCESSOR
# ============================================================

def normalize_description_lines(description, requested_lines):

    if not description:
        return "No description generated."

    # If Gemini returns a list
    if isinstance(description, list):

        lines = []

        for item in description:

            item = str(item).strip()

            if item:
                lines.append(item)

        lines = lines[:requested_lines]

        return "\n".join(lines)

    # If Gemini returns normal text
    description = str(description).strip()

    # Split existing lines first
    lines = [
        line.strip()
        for line in description.splitlines()
        if line.strip()
    ]

    if len(lines) >= requested_lines:

        return "\n".join(
            lines[:requested_lines]
        )

    # If Gemini returned fewer lines,
    # preserve the content instead of inventing text.
    return description


# ============================================================
# HELPER: GEMINI REQUEST WITH AUTOMATIC FALLBACK
# ============================================================

def generate_with_retry(contents, retries=2):

    if not client:

        raise RuntimeError(
            "Gemini client is not configured."
        )

    models_to_try = [
        MODEL_NAME
    ] + FALLBACK_MODELS

    last_error = None

    for model in models_to_try:

        for attempt in range(retries + 1):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=contents
                )

                return response, model

            except Exception as e:

                last_error = e

                error_text = str(e).upper()

                temporary_error = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "TOO MANY REQUESTS" in error_text
                )

                if temporary_error:

                    if attempt < retries:

                        wait_time = 2 ** (
                            attempt + 1
                        )

                        time.sleep(wait_time)

                        continue

                    # Current model still unavailable.
                    # Move to next model.
                    break

                # Non-temporary error:
                # do not silently hide it.
                raise last_error

    raise last_error


# ============================================================
# 🖼️ IMAGE DATA STUDIO
# ============================================================

if studio_mode == "🖼️ Image Data Studio":

    st.sidebar.subheader(
        "Ingest Image Asset"
    )

    uploaded_file = st.sidebar.file_uploader(
        "Upload Image File",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    # --------------------------------------------------------
    # DESCRIPTION LINE CONTROL
    # --------------------------------------------------------

    description_lines = st.sidebar.number_input(
        "📝 Description Lines Required",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        key="image_description_lines"
    )

    st.sidebar.caption(
        f"AI will generate up to {description_lines} lines."
    )


    left_panel, right_panel = st.columns(
        [1, 1.2]
    )


    # ========================================================
    # IMAGE LEFT PANEL
    # ========================================================

    with left_panel:

        st.subheader(
            "🖼️ Vision Feature Extraction"
        )

        if uploaded_file is not None:

            raw_img = Image.open(
                uploaded_file
            )

            st.image(
                raw_img,
                caption="Active Image Asset",
                use_container_width=True
            )


            # ------------------------------------------------
            # RESET WHEN NEW IMAGE
            # ------------------------------------------------

            if (
                st.session_state.image_filename
                != uploaded_file.name
            ):

                st.session_state.image_result = None

                st.session_state.image_filename = (
                    uploaded_file.name
                )


            # ------------------------------------------------
            # GENERATE IMAGE ANALYSIS
            # ------------------------------------------------

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

                            image_for_analysis = raw_img.copy()

                            if image_for_analysis.mode in (
                                "RGBA",
                                "P"
                            ):

                                image_for_analysis = (
                                    image_for_analysis.convert(
                                        "RGB"
                                    )
                                )

                            image_for_analysis.thumbnail(
                                (1200, 1200)
                            )

                            image_for_analysis.save(
                                img_buffer,
                                format="JPEG",
                                quality=80
                            )

                            image_bytes = (
                                img_buffer.getvalue()
                            )


                            # --------------------------------
                            # IMAGE PROMPT
                            # --------------------------------

                            prompt = f"""
Analyze this image for an AI
data-quality-control pipeline.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "extracted_text": "Extract all clearly visible text exactly. If no visible text exists, write No text detected.",
    "translated_text": "Translate the extracted text into {target_lang}. If there is no text, write No translation available.",
    "visual_description": [
        "Description line 1",
        "Description line 2"
    ],
    "confidence_score": 0.95
}}

Visual description requirements:

- Generate up to {description_lines} useful lines.
- Each item in visual_description must be one separate line.
- Describe the important objects.
- Describe people only using visible information.
- Describe the environment and setting.
- Describe actions when visible.
- Mention important colors and visual characteristics.
- Do not invent information.
- Do not guess identities.
- Do not claim something is present if it cannot be seen.
- The confidence_score must be between 0 and 1.
- Return JSON only.
"""


                            response, used_model = (
                                generate_with_retry(
                                    [
                                        prompt,
                                        types.Part.from_bytes(
                                            data=image_bytes,
                                            mime_type="image/jpeg"
                                        )
                                    ]
                                )
                            )


                            clean_text = (
                                clean_json_response(
                                    response.text
                                )
                            )

                            data = json.loads(
                                clean_text
                            )


                            visual_description = (
                                normalize_description_lines(
                                    data.get(
                                        "visual_description",
                                        []
                                    ),
                                    int(
                                        description_lines
                                    )
                                )
                            )


                            confidence = float(
                                data.get(
                                    "confidence_score",
                                    0.90
                                )
                            )


                            # Keep confidence in valid range
                            confidence = max(
                                0.0,
                                min(
                                    1.0,
                                    confidence
                                )
                            )


                            st.session_state.image_result = {

                                "extracted_text":
                                    data.get(
                                        "extracted_text",
                                        "No text detected."
                                    ),

                                "translated_text":
                                    data.get(
                                        "translated_text",
                                        "No translation available."
                                    ),

                                "visual_description":
                                    visual_description,

                                "confidence_score":
                                    confidence,

                                "model":
                                    used_model
                            }


                            if used_model != MODEL_NAME:

                                st.warning(
                                    f"⚠️ Primary model was busy. "
                                    f"Analysis completed using "
                                    f"`{used_model}`."
                                )

                            else:

                                st.success(
                                    "✅ Image analysis completed!"
                                )


                        except json.JSONDecodeError:

                            st.error(
                                "⚠️ Gemini returned invalid JSON. "
                                "Please try Generate again."
                            )


                        except Exception as e:

                            st.error(
                                f"❌ Image processing error: {str(e)}"
                            )

            else:

                st.warning(
                    "🔒 Add GEMINI_API_KEY to "
                    "Streamlit Secrets."
                )


            # ------------------------------------------------
            # LOAD IMAGE RESULT
            # ------------------------------------------------

            result = (
                st.session_state.image_result
            )


            if result:

                extracted_text = (
                    result["extracted_text"]
                )

                translated_text = (
                    result["translated_text"]
                )

                visual_description = (
                    result["visual_description"]
                )

                ocr_confidence = (
                    result["confidence_score"]
                )

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


            # ------------------------------------------------
            # DISPLAY IMAGE RESULTS
            # ------------------------------------------------

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


            if result and result.get("model"):

                st.caption(
                    f"Generated using: "
                    f"`{result['model']}`"
                )


        else:

            st.info(
                "Awaiting image dataset payload "
                "via the control panel."
            )


    # ========================================================
    # IMAGE RIGHT PANEL
    # ========================================================

    with right_panel:

        st.subheader(
            "🛡️ Image QC Gatekeeper"
        )


        if (
            uploaded_file is not None
            and client
            and st.session_state.get(
                "image_result"
            )
        ):

            st.markdown(
                "#### Automated Integrity Diagnostics"
            )


            # Rule 1
            c1 = (
                ocr_confidence >= 0.85
            )


            st.write(
                f"{'✅' if c1 else '❌'} "
                f"**Rule 1: OCR Confidence Baseline** "
                f"({ocr_confidence * 100:.1f}%)"
            )


            # Rule 2
            description_words = len(
                desc_txt.split()
            )

            c2 = (
                description_words >= 8
            )


            st.write(
                f"{'✅' if c2 else '❌'} "
                f"**Rule 2: Semantic Density Verification** "
                f"({description_words} words)"
            )


            # Rule 3
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


            # ------------------------------------------------
            # DATA AUDITOR
            # ------------------------------------------------

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
                        "Filename":
                            uploaded_file.name,

                        "Modality":
                            "Vision",

                        "Language":
                            target_lang,

                        "Description Lines":
                            description_lines,

                        "Confidence":
                            ocr_confidence,

                        "Model":
                            st.session_state.image_result.get(
                                "model",
                                MODEL_NAME
                            ),

                        "Verdict":
                            audit_verdict,

                        "Notes":
                            (
                                auditor_notes
                                if auditor_notes
                                else "Verified Asset"
                            )
                    }
                )


                st.success(
                    "✅ Image record successfully "
                    "verified and logged!"
                )


        # ----------------------------------------------------
        # IMAGE MANIFEST
        # ----------------------------------------------------

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


            csv_img = (
                df_img
                .to_csv(index=False)
                .encode("utf-8")
            )


            st.download_button(
                "📥 Export Image Manifest (CSV)",
                csv_img,
                "image_pipeline_manifest.csv",
                "text/csv"
            )

        else:

            st.caption(
                "No dynamic image rows logged "
                "in this batch yet."
            )


# ============================================================
# 🔊 AUDIO DATA STUDIO
# ============================================================

elif studio_mode == "🔊 Audio Data Studio":

    st.sidebar.subheader(
        "Ingest Audio Asset"
    )


    uploaded_audio = st.sidebar.file_uploader(
        "Upload Audio File",
        type=[
            "mp3",
            "wav",
            "m4a",
            "ogg"
        ]
    )


    # --------------------------------------------------------
    # AUDIO DESCRIPTION LINE CONTROL
    # --------------------------------------------------------

    description_lines = st.sidebar.number_input(
        "📝 Audio Description Lines Required",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        key="audio_description_lines"
    )


    st.sidebar.caption(
        f"AI will generate up to "
        f"{description_lines} lines."
    )


    left_panel, right_panel = st.columns(
        [1, 1.2]
    )


    # ========================================================
    # AUDIO LEFT PANEL
    # ========================================================

    with left_panel:

        st.subheader(
            "🔊 Acoustic Feature Extraction"
        )


        if uploaded_audio is not None:

            st.audio(
                uploaded_audio
            )


            # ------------------------------------------------
            # RESET FOR NEW AUDIO
            # ------------------------------------------------

            if (
                st.session_state.audio_filename
                != uploaded_audio.name
            ):

                st.session_state.audio_result = None

                st.session_state.audio_filename = (
                    uploaded_audio.name
                )


            # ------------------------------------------------
            # GENERATE AUDIO ANALYSIS
            # ------------------------------------------------

            if client:

                if st.button(
                    "⚡ Generate Audio Analysis",
                    key="generate_audio"
                ):

                    with st.spinner(
                        "🧠 Uploading and analyzing audio..."
                    ):

                        try:

                            audio_bytes = (
                                uploaded_audio.getvalue()
                            )


                            mime_type = (
                                get_audio_mime_type(
                                    uploaded_audio.name
                                )
                            )


                            # --------------------------------
                            # GEMINI FILE API
                            # --------------------------------
                            #
                            # This is more reliable for audio
                            # than sending the complete audio
                            # as an inline byte Part.
                            #
                            # Google documents this method for
                            # audio input.
                            # --------------------------------

                            audio_stream = (
                                io.BytesIO(
                                    audio_bytes
                                )
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


                            # --------------------------------
                            # AUDIO PROMPT
                            # --------------------------------

                            prompt = f"""
You are an expert audio data-quality analyst.

Analyze the attached audio carefully.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "transcript": "Clearly transcribe understandable spoken words. If there is no understandable speech, write No clear speech detected.",
    "translation": "Translate the transcript into {target_lang}. If there is no speech, write No translation available.",
    "audio_description": [
        "Audio description line 1",
        "Audio description line 2"
    ],
    "confidence_score": 0.90
}}

Audio description requirements:

- Generate up to {description_lines} separate lines.
- Each array item must represent one description line.
- Describe speech when present.
- Describe music when present.
- Describe instruments when identifiable.
- Describe background sounds.
- Describe environmental sounds.
- Describe noise and audio clarity.
- Mention speaker characteristics only when reasonably identifiable.
- Mention emotional tone only when reasonably inferable from the audio.
- Mention rhythm or tempo only when reasonably inferable.
- Do not invent words that cannot be heard.
- Do not invent speakers or events.
- If the recording is instrumental or mostly background sound, clearly state that.
- Keep the description useful for a data-quality pipeline.
- Confidence must be between 0 and 1.
- Return JSON only.
"""


                            # --------------------------------
                            # SEND AUDIO TO GEMINI
                            # --------------------------------

                            response, used_model = (
                                generate_with_retry(
                                    [
                                        prompt,
                                        uploaded_gemini_file
                                    ]
                                )
                            )


                            res_text = (
                                response.text.strip()
                            )


                            clean_text = (
                                clean_json_response(
                                    res_text
                                )
                            )


                            data = json.loads(
                                clean_text
                            )


                            # --------------------------------
                            # PROCESS DESCRIPTION
                            # --------------------------------

                            audio_description = (
                                normalize_description_lines(
                                    data.get(
                                        "audio_description",
                                        []
                                    ),
                                    int(
                                        description_lines
                                    )
                                )
                            )


                            audio_confidence = float(
                                data.get(
                                    "confidence_score",
                                    0.90
                                )
                            )


                            audio_confidence = max(
                                0.0,
                                min(
                                    1.0,
                                    audio_confidence
                                )
                            )


                            # --------------------------------
                            # SAVE RESULT
                            # --------------------------------

                            st.session_state.audio_result = {

                                "transcript":
                                    data.get(
                                        "transcript",
                                        "No transcript generated."
                                    ),

                                "translation":
                                    data.get(
                                        "translation",
                                        "No translation generated."
                                    ),

                                "audio_description":
                                    audio_description,

                                "confidence_score":
                                    audio_confidence,

                                "model":
                                    used_model
                            }


                            if used_model != MODEL_NAME:

                                st.warning(
                                    f"⚠️ Primary model was busy. "
                                    f"Analysis completed using "
                                    f"`{used_model}`."
                                )

                            else:

                                st.success(
                                    "✅ Audio analysis completed!"
                                )


                        except json.JSONDecodeError:

                            st.error(
                                "⚠️ Gemini returned invalid JSON. "
                                "Please press Generate again."
                            )


                        except Exception as e:

                            st.error(
                                f"❌ Audio processing error: {str(e)}"
                            )


            else:

                st.warning(
                    "🔒 Add GEMINI_API_KEY to "
                    "Streamlit Secrets."
                )


            # ------------------------------------------------
            # LOAD AUDIO RESULT
            # ------------------------------------------------

            result = (
                st.session_state.audio_result
            )


            if result:

                transcript = (
                    result["transcript"]
                )

                translation = (
                    result["translation"]
                )

                audio_description = (
                    result["audio_description"]
                )

                audio_confidence = (
                    result["confidence_score"]
                )

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


            # ------------------------------------------------
            # DISPLAY AUDIO RESULTS
            # ------------------------------------------------

            st.markdown("---")


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


            if result and result.get("model"):

                st.caption(
                    f"Generated using: "
                    f"`{result['model']}`"
                )


        else:

            st.info(
                "🎵 Upload an MP3, WAV, M4A or OGG "
                "file from the control panel."
            )


    # ========================================================
    # AUDIO RIGHT PANEL
    # ========================================================

    with right_panel:

        st.subheader(
            "🛡️ Audio QC Gatekeeper"
        )


        if (
            uploaded_audio is not None
            and client
            and st.session_state.get(
                "audio_result"
            )
        ):

            st.markdown(
                "#### Automated Integrity Diagnostics"
            )


            # Rule 1
            transcript_ok = bool(
                transcript_txt.strip()
            )


            st.write(
                f"{'✅' if transcript_ok else '❌'} "
                "**Rule 1: Transcript Payload**"
            )


            # Rule 2
            description_word_count = len(
                audio_desc_txt.split()
            )


            description_ok = (
                description_word_count >= 10
            )


            st.write(
                f"{'✅' if description_ok else '❌'} "
                "**Rule 2: Audio Description Density** "
                f"({description_word_count} words)"
            )


            # Rule 3
            confidence_ok = (
                audio_confidence >= 0.75
            )


            st.write(
                f"{'✅' if confidence_ok else '❌'} "
                "**Rule 3: AI Confidence Baseline** "
                f"({audio_confidence * 100:.1f}%)"
            )


            st.markdown("---")


            # ------------------------------------------------
            # AUDIO AUDITOR
            # ------------------------------------------------

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
                        "Filename":
                            uploaded_audio.name,

                        "Modality":
                            "Audio",

                        "Language":
                            target_lang,

                        "Description Lines":
                            description_lines,

                        "Confidence":
                            audio_confidence,

                        "Model":
                            st.session_state.audio_result.get(
                                "model",
                                MODEL_NAME
                            ),

                        "Verdict":
                            audio_verdict,

                        "Notes":
                            (
                                audio_notes
                                if audio_notes
                                else "Verified Audio Asset"
                            )
                    }
                )


                st.success(
                    "✅ Audio record successfully "
                    "verified and logged!"
                )


        # ----------------------------------------------------
        # AUDIO MANIFEST
        # ----------------------------------------------------

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


            csv_audio = (
                df_audio
                .to_csv(index=False)
                .encode("utf-8")
            )


            st.download_button(
                "📥 Export Audio Manifest (CSV)",
                csv_audio,
                "audio_pipeline_manifest.csv",
                "text/csv"
            )


        else:

            st.caption(
                "No dynamic audio rows logged "
                "in this batch yet."
            )