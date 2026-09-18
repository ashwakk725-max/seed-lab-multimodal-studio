import streamlit as st
import pandas as pd
from PIL import Image
import google.generativeai as genai
import json
import io
import time

# 1. Initialize the Master Live AI Engine
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = ""

if API_KEY != "":
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3.6-flash')
else:
    st.warning("🔒 Local Mode: Please deploy to Streamlit Cloud and configure your GEMINI_API_KEY in Advanced Secrets to activate live processing.")

# Set up the desktop web browser layout
st.set_page_config(page_title="SEED Lab Multimodal QC Studio", layout="wide")
st.title("🔬 Samsung SEED Lab: Unified Multimodal Data QC Studio")
st.caption("Centralized Quality Control Pipeline for Vision & Speech Assets")

if 'image_qc_log' not in st.session_state:
    st.session_state.image_qc_log = []
if 'audio_qc_log' not in st.session_state:
    st.session_state.audio_qc_log = []

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("🎛️ Pipeline Control Center")
studio_mode = st.sidebar.radio("Select Ingestion Modality:", ["🖼️ Image Data Studio", "🔊 Audio Data Studio"])
target_lang = st.sidebar.selectbox("Target Translation Language:", ["English", "Spanish", "French", "Hindi"])

st.sidebar.markdown("---")
st.sidebar.caption("System Connected: Cloud Engine Node")


# ==============================================================================
# 🖼️ MODE 1: IMAGE PROCESSING STUDIO
# ==============================================================================
if studio_mode == "🖼️ Image Data Studio":
    st.sidebar.subheader("Ingest Image Asset")
    uploaded_file = st.sidebar.file_uploader("Upload Image File", type=["jpg", "png", "jpeg"])
    
    left_panel, right_panel = st.columns([1, 1.2])
    
    with left_panel:
        st.subheader("🖼️ Vision Feature Extraction")
        if uploaded_file is not None:
            raw_img = Image.open(uploaded_file)
            st.image(raw_img, caption="Active Image Asset", use_container_width=True)
            
            if API_KEY != "":
                with st.spinner("🧠 Visual AI is running OCR and translation layout maps..."):
                    try:
                        img_buffer = io.BytesIO()
                        if raw_img.mode in ("RGBA", "P"):
                            raw_img = raw_img.convert("RGB")
                        raw_img.thumbnail((1200, 1200)) 
                        raw_img.save(img_buffer, format="JPEG", quality=75)
                        compressed_img = Image.open(img_buffer)

                        prompt = f"""
                        Analyze this image for an AI training data engineering pipeline. 
                        Return output strictly in this JSON structure:
                        {{
                            "extracted_text": "Extract all visible text. If none, say 'No text found.'",
                            "translated_text": "Translate the extracted text accurately into {target_lang}.",
                            "visual_description": "Provide a clean description of the visual scene, layout, colors, and objects.",
                            "confidence_score": 0.95
                    }}
                        Return ONLY the raw JSON string. No markdown wrappers.
                        """
                        response = model.generate_content([prompt, compressed_img])
                        clean_text = response.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_text)
                        
                        extracted_text = data.get("extracted_text", "No text detected.")
                        translated_text = data.get("translated_text", "No translation available.")
                        visual_description = data.get("visual_description", "No description available.")
                        ocr_confidence = data.get("confidence_score", 0.90)
                    except Exception as e:
                        st.error(f"Vision engine error: {str(e)}")
                        extracted_text, translated_text, visual_description, ocr_confidence = "Error", "Error", "Error", 0.0
                    
                raw_txt = st.text_area("1. Extracted Text (Live OCR)", value=extracted_text, height=70)
                trans_txt = st.text_area(f"2. Live Translated Output ({target_lang})", value=translated_text, height=70)
                desc_txt = st.text_area("3. AI Visual Scene Description", value=visual_description, height=100)
            else:
                st.info("System is offline. Active API key needed in Streamlit Secrets.")
        else:
            st.info("Awaiting image dataset payload via the control panel.")

    with right_panel:
        st.subheader("🛡️ Image QC Gatekeeper")
        if uploaded_file is not None and API_KEY != "":
            st.markdown("#### **Automated Integrity Diagnostics**")
            c1 = ocr_confidence >= 0.85
            st.write(f"{'✅' if c1 else '❌'} **Rule 1: OCR Confidence Baseline** ({ocr_confidence*100:.1f}%)")
            c2 = len(desc_txt.split()) >= 8
            st.write(f"{'✅' if c2 else '❌'} **Rule 2: Semantic Density Verification** ({len(desc_txt.split())} words)")
            c3 = all([raw_txt, trans_txt, desc_txt]) and "Error" not in [raw_txt, trans_txt, desc_txt]
            st.write(f"{'✅' if c3 else '❌'} **Rule 3: Non-Null Structural Payload**")
            
            st.markdown("---")
            st.markdown("#### **Data Auditor Console**")
            audit_verdict = st.radio("Pipeline Routing Action:", ["Approve & Record", "Flag for Text Adjustments", "Reject Dataset Item"])
            auditor_notes = st.text_input("Auditor Quality Log Entries:")
            
            if st.button("Commit Image Record"):
                st.session_state.image_qc_log.append({
                    "Filename": uploaded_file.name,
                    "Modality": "Vision",
                    "Language": target_lang,
                    "Confidence": ocr_confidence,
                    "Verdict": audit_verdict,
                    "Notes": auditor_notes if auditor_notes else "Verified Asset"
                })
                st.success("Image record successfully verified and logged!")

        st.markdown("### 📊 Active Batch Image Manifest")
        if st.session_state.image_qc_log:
            df_img = pd.DataFrame(st.session_state.image_qc_log)
            st.dataframe(df_img, use_container_width=True)
            csv_img = df_img.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Image Manifest (CSV)", csv_img, "image_pipeline_manifest.csv", "text/csv")
        else:
            st.caption("No dynamic image rows logged in this batch yet.")


# ==============================================================================
# 🔊 MODE 2: AUDIO PROCESSING STUDIO
# ==============================================================================
elif studio_mode == "🔊 Audio Data Studio":
    st.sidebar.subheader("Ingest Audio Asset")
    uploaded_audio = st.sidebar.file_uploader("Upload Audio File", type=["mp3", "wav", "m4a", "ogg"])
    
    left_panel, right_panel = st.columns([1, 1.2])
    
    with left_panel:
        st.subheader("🔊 Acoustic Feature Extraction")
        if uploaded_audio is not None:
            st.audio(uploaded_audio, format=f"audio/{uploaded_audio.name.split('.')[-1]}")
            
            if API_KEY != "":
                with st.spinner("🧠 Speech AI is rendering acoustic layers and transcribing..."):
                    try:
                        audio_bytes = uploaded_audio.read()
                        
                        # FIX: Mapping file types cleanly to official Internet MIME types
                        ext = uploaded_audio.name.split('.')[-1].lower()
                        if ext == "mp3":
                            mime_type = "audio/mpeg"
                        elif ext == "m4a":
                            mime_type = "audio/m4a"
                        elif ext == "wav":
                            mime_type = "audio/wav"
                        else:
                            mime_type = f"audio/{ext}"

                        audio_payload = {
                            "mime_type": mime_type,
                            "data": audio_bytes
                        }

                        prompt = f"""
                        Listen to this audio track for an AI data engineering pipeline. 
                        Return output strictly in this JSON structure:
                        {{
                            "transcript": "Transcribe every spoken word exactly. If none, say 'No speech detected.'",
                            "translation": "Translate the spoken transcript accurately into {target_lang}.",
                            "audio_description": "Describe acoustic environment details: background noises, speaker tone/emotion, and signal clarity.",
                            "confidence_score": 0.96
                        }}
                        Return ONLY raw JSON. No markdown wrappers.
                        """
                        response = model.generate_content([prompt, audio_payload])
                        clean_text = response.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_text)
                        
                        transcript = data.get("transcript", "No speech detected.")
                        translation = data.get("translation", "No translation available.")
                        audio_description = data.get("audio_description", "No acoustic description.")
                        audio_confidence = data.get("confidence_score", 0.90)
                    except Exception as e:
                        st.error(f"Audio engine error: {str(e)}")
