````python
import streamlit as st
import pandas as pd
from PIL import Image
from google import genai
from google.genai import types
import json
import io

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
    MODEL_NAME = "gemini-3.8-flash"
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

    return mime_types.get(ext, "application/octet-stream")


# ============================================================
# 🖼️ IMAGE DATA STUDIO
# ============================================================
if studio_mode == "🖼️ Image Data Studio":

    st.sidebar.subheader("Ingest Image Asset")

    uploaded_file = st.sidebar.file_uploader(
        "Upload Image File",
        type=["jpg", "jpeg", "png"]
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

            extracted_text = "No text detected."
            translated_text = "No translation available."
            visual_description = "No description available."
            ocr_confidence = 0.0

            if client:

                with st.spinner(
                    "🧠 Visual AI is processing image..."
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

                        image_bytes = img_buffer.getvalue()

                        prompt = f"""
Analyze this image for an AI data-quality-control pipeline.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "extracted_text": "Extract visible text exactly.",
    "translated_text": "Translate the extracted text into {target_lang}.",
    "visual_description": "Describe the important visual elements clearly.",
    "confidence_score": 0.95
}}

If there is no visible text, use:
"No text detected."

The confidence_score must be a number between 0 and 1.
"""

                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=[
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

                        extracted_text = data.get(
                            "extracted_text",
                            "No text detected."
                        )

                        translated_text = data.get(
                            "translated_text",
                            "No translation available."
                        )

                        visual_description = data.get(
                            "visual_description",
                            "No description available."
                        )

                        ocr_confidence = float(
                            data.get("confidence_score", 0.90)
                        )

                    except Exception as e:

                        st.error(
                            f"❌ Image processing error: {str(e)}"
                        )

            raw_txt = st.text_area(
                "1. Extracted Text (Live OCR)",
                value=extracted_text,
                height=100
            )

            trans_txt = st.text_area(
                f"2. Live Translated Output ({target_lang})",
                value=translated_text,
                height=100
            )

            desc_txt = st.text_area(
                "3. AI Visual Scene Description",
                value=visual_description,
                height=130
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

        if uploaded_file is not None and client:

            st.markdown("#### Automated Integrity Diagnostics")

            c1 = ocr_confidence >= 0.85

            st.write(
                f"{'✅' if c1 else '❌'} "
                f"**Rule 1: OCR Confidence Baseline** "
                f"({ocr_confidence * 100:.1f}%)"
            )

            description_words = len(desc_txt.split())

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

            st.markdown("#### Data Auditor Console")

            audit_verdict = st.radio(
                "Pipeline Routing Action:",
                [
                    "Approve & Record",
                    "Flag for Text Adjustments",
                    "Reject Dataset Item"
                ]
            )

            auditor_notes = st.text_input(
                "Auditor Quality Log Entries:"
            )

            if st.button("Commit Image Record"):

                st.session_state.image_qc_log.append(
                    {
                        "Filename": uploaded_file.name,
                        "Modality": "Vision",
                        "Language": target_lang,
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

        st.markdown("### 📊 Active Batch Image Manifest")

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

    left_panel, right_panel = st.columns([1, 1.2])

    # --------------------------------------------------------
    # LEFT PANEL
    # --------------------------------------------------------
    with left_panel:

        st.subheader("🔊 Acoustic Feature Extraction")

        if uploaded_audio is not None:

            st.audio(uploaded_audio)

            transcript = "No transcript generated."
            translation = "No translation generated."
            audio_description = "No audio description generated."
            audio_confidence = 0.0

            if client:

                with st.spinner(
                    "🧠 Gemini is listening to and analyzing the audio..."
                ):

                    try:

                        audio_bytes = uploaded_audio.getvalue()

                        mime_type = get_audio_mime_type(
                            uploaded_audio.name
                        )

                        # ----------------------------------------
                        # IMPORTANT:
                        # Send audio as a real Gemini Part.
                        # ----------------------------------------
                        audio_part = types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type=mime_type
                        )

                        prompt = f"""
You are an audio data-quality analyst.

Analyze the attached audio carefully.

Return ONLY valid JSON using exactly this structure:

{{
    "transcript": "Write the clearly understandable spoken words. If there is no understandable speech, write 'No clear speech detected.'",
    "translation": "Translate the transcript into {target_lang}. If there is no speech, write 'No translation available.'",
    "audio_description": "Give a detailed description of the audio. Mention whether it contains speech, music, instruments, background sounds, environment/noise, approximate tempo if applicable, speaker characteristics if reasonably identifiable, emotional tone when reasonably inferable, and overall audio clarity.",
    "confidence_score": 0.90
}}

Important:
- Do not invent speech that cannot be heard.
- If the recording is instrumental or mostly background sound, clearly say so.
- Keep the audio_description detailed and useful for a data-quality pipeline.
- Return JSON only.
"""

                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=[
                                prompt,
                                audio_part
                            ]
                        )

                        res_text = response.text.strip()

                        # Remove accidental markdown fences
                        clean_text = (
                            res_text
                            .replace("```json", "")
                            .replace("```", "")
                            .strip()
                        )

                        data = json.loads(clean_text)

                        transcript = data.get(
                            "transcript",
                            "No transcript generated."
                        )

                        translation = data.get(
                            "translation",
                            "No translation generated."
                        )

                        audio_description = data.get(
                            "audio_description",
                            "No audio description generated."
                        )

                        audio_confidence = float(
                            data.get(
                                "confidence_score",
                                0.90
                            )
                        )

                    except json.JSONDecodeError:

                        st.warning(
                            "⚠️ Gemini returned text instead of JSON. "
                            "Showing the raw AI response below."
                        )

                        audio_description = (
                            res_text
                            if "res_text" in locals()
                            else "No response received."
                        )

                    except Exception as e:

                        st.error(
                            f"❌ Audio processing error: {str(e)}"
                        )

            else:

                st.warning(
                    "🔒 Add GEMINI_API_KEY to Streamlit Secrets "
                    "to analyze the audio."
                )

            # ----------------------------------------
            # DISPLAY RESULTS
            # ----------------------------------------

            st.markdown("---")

            st.markdown("### 📝 1. Live Audio Transcript")

            transcript_txt = st.text_area(
                "Transcript",
                value=transcript,
                height=130,
                label_visibility="collapsed"
            )

            st.markdown(
                f"### 🌐 2. Translation ({target_lang})"
            )

            translation_txt = st.text_area(
                "Translation",
                value=translation,
                height=130,
                label_visibility="collapsed"
            )

            st.markdown("### 🎧 3. AI Audio Description")

            audio_desc_txt = st.text_area(
                "Audio Description",
                value=audio_description,
                height=220,
                label_visibility="collapsed"
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

        if uploaded_audio is not None and client:

            st.markdown(
                "#### Automated Integrity Diagnostics"
            )

            transcript_ok = bool(
                transcript_txt.strip()
            )

            description_ok = (
                len(audio_desc_txt.split()) >= 10
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
                f"({len(audio_desc_txt.split())} words)"
            )

            st.write(
                f"{'✅' if confidence_ok else '❌'} "
                "**Rule 3: AI Confidence Baseline** "
                f"({audio_confidence * 100:.1f}%)"
            )

            st.markdown("---")

            st.markdown("#### 🎛️ Data Auditor Console")

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
````
