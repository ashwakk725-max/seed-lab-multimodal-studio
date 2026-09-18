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
# HELPER: GEMINI REQUEST WITH RETRY
# ============================================================
def generate_with_retry(contents, retries=2):
    last_error = None

    for attempt in range(retries + 1):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=contents
            )

        except Exception as e:
            last_error = e

            error_text = str(e)

            # Retry temporary server overload errors
            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt < retries:
                    time.sleep(2)
                    continue

            raise last_error

    raise last_error


# ============================================================
# 🖼️ IMAGE DATA STUDIO
# ============================================================
if studio_mode == "🖼️ Image Data Studio":

    st.sidebar.subheader("Ingest Image Asset")

    uploaded_file = st.sidebar.file_uploader(
        "Upload Image File",
        type=["jpg", "jpeg", "png"]
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
        f"AI will generate approximately {description_lines} lines."
    )

    left_panel, right_panel = st.columns([1, 1.2])

    # --------------------------------------------------------
    # LEFT PANEL
    # --------------------------------------------------------
    with left_panel:

        st.subheader("🖼️ Vision Feature Extraction")

        if uploaded_file is not None:

            raw_img = Image.open(uploaded_file)

            st.image(
                raw_img,
                caption="Active Image Asset",
                use_container_width=True
            )

            # ------------------------------------------------
            # SESSION STATE FOR IMAGE RESULT
            # ------------------------------------------------
            if "image_result" not in st.session_state:
                st.session_state.image_result = None

            if "image_filename" not in st.session_state:
                st.session_state.image_filename = None

            # Reset when new image is uploaded
            if (
                st.session_state.image_filename
                != uploaded_file.name
            ):
                st.session_state.image_result = None
                st.session_state.image_filename = uploaded_file.name

            # ------------------------------------------------
            # GENERATE BUTTON
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

                            if raw_img.mode in ("RGBA", "P"):
                                raw_img = raw_img.convert("RGB")

                            raw_img.thumbnail((1200, 1200))

                            raw_img.save(
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
Analyze this image for an AI data-quality-control pipeline.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "extracted_text": "Extract all clearly visible text exactly.",
    "translated_text": "Translate the extracted text into {target_lang}.",
    "visual_description": "Describe the important visual content in approximately {description_lines} lines.",
    "confidence_score": 0.95
}}

Description requirements:
- Generate approximately {description_lines} lines.
- Clearly describe the main objects, people, environment, actions,
  colors, setting, and other important visual information when applicable.
- Do not invent information that cannot be seen.
- If there is no visible text, use "No text detected."
- The confidence_score must be between 0 and 1.
- Return JSON only.
"""

                            response = generate_with_retry(
                                [
                                    prompt,
                                    types.Part.from_bytes(
                                        data=image_bytes,
                                        mime_type="image/jpeg"
                                    )
                                ]
                            )

                            clean_text = (
                                response.text
                                .replace("```json", "")
                                .replace("```", "")
                                .strip()
                            )

                            data = json.loads(clean_text)

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
                                "confidence_score": float(
                                    data.get(
                                        "confidence_score",
                                        0.90
                                    )
                                )
                            }

                            st.success(
                                "✅ Image analysis completed!"
                            )

                        except json.JSONDecodeError:

                            st.error(
                                "⚠️ Gemini returned an invalid JSON response."
                            )

                        except Exception as e:

                            st.error(
                                f"❌ Image processing error: {str(e)}"
                            )

            else:

                st.warning(
                    "🔒 Add GEMINI_API_KEY to Streamlit Secrets."
                )

            # ------------------------------------------------
            # LOAD RESULTS
            # ------------------------------------------------
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

            # ------------------------------------------------
            # DISPLAY RESULTS
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

        else:

            st.info(
                "Awaiting image dataset payload via the control panel."
            )

    # --------------------------------------------------------
    # RIGHT PANEL
    # --------------------------------------------------------
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
# 🔊 AUDIO DATA STUDIO
# ============================================================
elif studio_mode == "🔊 Audio Data Studio":

    st.sidebar.subheader("Ingest Audio Asset")

    uploaded_audio = st.sidebar.file_uploader(
        "Upload Audio File",
        type=["mp3", "wav", "m4a", "ogg"]
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
        f"AI will generate approximately {description_lines} lines."
    )

    left_panel, right_panel = st.columns([1, 1.2])

    # --------------------------------------------------------
    # LEFT PANEL
    # --------------------------------------------------------
    with left_panel:

        st.subheader("🔊 Acoustic Feature Extraction")

        if uploaded_audio is not None:

            st.audio(uploaded_audio)

            # ------------------------------------------------
            # SESSION STATE FOR AUDIO RESULT
            # ------------------------------------------------
            if "audio_result" not in st.session_state:
                st.session_state.audio_result = None

            if "audio_filename" not in st.session_state:
                st.session_state.audio_filename = None

            # Reset when a new audio file is uploaded
            if (
                st.session_state.audio_filename
                != uploaded_audio.name
            ):
                st.session_state.audio_result = None
                st.session_state.audio_filename = (
                    uploaded_audio.name
                )

            # ------------------------------------------------
            # GENERATE BUTTON
            # ------------------------------------------------
            if client:

                if st.button(
                    "⚡ Generate Audio Analysis",
                    key="generate_audio"
                ):

                    with st.spinner(
                        "🧠 Gemini is listening and analyzing the audio..."
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

                            audio_part = (
                                types.Part.from_bytes(
                                    data=audio_bytes,
                                    mime_type=mime_type
                                )
                            )

                            # --------------------------------
                            # SHORT + FAST AUDIO PROMPT
                            # --------------------------------
                            prompt = f"""
Analyze this audio quickly for a data-quality pipeline.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "transcript": "Transcribe clearly understandable speech. If there is no understandable speech, write 'No clear speech detected.'",
    "translation": "Translate the transcript into {target_lang}. If there is no speech, write 'No translation available.'",
    "audio_description": "Describe the audio in approximately {description_lines} lines.",
    "confidence_score": 0.90
}}

Audio description requirements:
- Generate approximately {description_lines} lines.
- Mention speech, music, instruments, background sounds,
  environment/noise, speaker characteristics and overall clarity
  when applicable.
- Do not invent unclear speech.
- If the recording is instrumental or mostly background sound,
  clearly state that.
- Keep the description useful for a data-quality pipeline.
- Return JSON only.
"""

                            response = generate_with_retry(
                                [
                                    prompt,
                                    audio_part
                                ]
                            )

                            res_text = (
                                response.text.strip()
                            )

                            clean_text = (
                                res_text
                                .replace("```json", "")
                                .replace("```", "")
                                .strip()
                            )

                            data = json.loads(
                                clean_text
                            )

                            st.session_state.audio_result = {
                                "transcript": data.get(
                                    "transcript",
                                    "No transcript generated."
                                ),
                                "translation": data.get(
                                    "translation",
                                    "No translation generated."
                                ),
                                "audio_description": data.get(
                                    "audio_description",
                                    "No audio description generated."
                                ),
                                "confidence_score": float(
                                    data.get(
                                        "confidence_score",
                                        0.90
                                    )
                                )
                            }

                            st.success(
                                "✅ Audio analysis completed!"
                            )

                        except json.JSONDecodeError:

                            st.error(
                                "⚠️ Gemini returned an invalid JSON response."
                            )

                        except Exception as e:

                            st.error(
                                f"❌ Audio processing error: {str(e)}"
                            )

            else:

                st.warning(
                    "🔒 Add GEMINI_API_KEY to Streamlit Secrets."
                )

            # ------------------------------------------------
            # LOAD RESULTS
            # ------------------------------------------------
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

            # ------------------------------------------------
            # DISPLAY RESULTS
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

        else:

            st.info(
                "🎵 Upload an MP3, WAV, M4A or OGG file "
                "from the control panel."
            )

    # --------------------------------------------------------
    # RIGHT PANEL
    # --------------------------------------------------------
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