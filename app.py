# app.py (fixed for your OCR + Hugging Face AI + existing features)
import tempfile

import os
import sys
import json
from io import BytesIO

import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
from dotenv import load_dotenv
from streamlit_lottie import st_lottie
import requests
from pyvis.network import Network
import speech_recognition as sr
import pyttsx3

# ------------------- PATHS / PROJECT IMPORTS -------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core import ocr, nlp, granite_client, risk, db, report, hugging

# ------------------- CONFIG / ENV -------------------
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")  # must be set in .env
db.init_db()

st.set_page_config(page_title="AI Prescription Verifier", layout="wide")
st.write("✅ Running the latest version of app.py")

# ------------------- HUGGING FACE HELPERS -------------------
HF_MODEL = "google/flan-t5-large"
HF_BASE = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}

def _call_hf(prompt: str, max_tokens: int = 200, temperature: float = 0.7):
    if not HF_API_KEY:
        raise RuntimeError("HF_API_KEY not set in .env")
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": max_tokens, "temperature": temperature},
        "options": {"wait_for_model": True}
    }
    resp = requests.post(HF_BASE, headers=HF_HEADERS, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Hugging Face API error {resp.status_code}: {resp.text}")
    data = resp.json()
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        if "generated_text" in data[0]:
            return data[0]["generated_text"].strip()
        if "summary_text" in data[0]:
            return data[0]["summary_text"].strip()
    return str(data)

def get_ai_alternatives(drug_list):
    if not drug_list:
        return "No drugs provided."
    drug_text = ", ".join(drug_list) if isinstance(drug_list, (list, tuple)) else str(drug_list)
    prompt = (
        "You are a clinical decision support assistant. "
        f"Suggest up to 3 safer and effective alternative medications for: {drug_text}. "
        "For each alternative, write a brief reason why it is safer (1-2 sentences). "
        "Keep it concise and suitable for a clinician."
    )
    try:
        return _call_hf(prompt, max_tokens=180, temperature=0.2)
    except Exception as e:
        return f"AI error: {e}"

def get_ai_dosage_warnings(drug_list, age):
    if not drug_list:
        return "No drugs provided."
    drug_text = ", ".join(drug_list) if isinstance(drug_list, (list, tuple)) else str(drug_list)
    prompt = (
        "You are a clinical assistant. For the following medications: "
        f"{drug_text} and a patient aged {age}, list key dosage cautions, monitoring needs, "
        "and age-specific precautions (3-6 bullet points). Keep concise and clinical."
    )
    try:
        return _call_hf(prompt, max_tokens=220, temperature=0.2)
    except Exception as e:
        return f"AI error: {e}"

# ------------------- THEME & ANIMATION -------------------
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_medical = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_jbrw3hcz.json")

st.markdown(
    """
    <h1 style='text-align: center; color: #4CAF50;'>💊 AI Prescription Verifier</h1>
    <p style='text-align: center; font-size:18px; color: gray;'>
        Instantly verify prescriptions, detect drug interactions, and suggest safer alternatives.
    </p>
    """,
    unsafe_allow_html=True
)
if lottie_medical:
    st_lottie(lottie_medical, height=180, key="med")

st.markdown(
    "<style>div.stButton > button {background-color: #4CAF50; color:white; font-size:16px; padding:10px; border-radius:10px;}</style>",
    unsafe_allow_html=True
)

# ------------------- SESSION STATE -------------------
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""
if "parsed" not in st.session_state:
    st.session_state.parsed = {"patient_age": None, "drugs": [], "raw_text": ""}
if "result" not in st.session_state:
    st.session_state.result = {}
if "risk_score" not in st.session_state:
    st.session_state.risk_score = 0
if "saved_case_id" not in st.session_state:
    st.session_state.saved_case_id = None

menu = ["Upload Prescription", "Drug Verification", "Doctor Override", "Reports & History"]
choice = st.sidebar.radio("Navigate", menu)

# ------------------- GAUGE CHART -------------------
def risk_gauge(value: int):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': "Risk Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "red" if value > 70 else "orange" if value > 30 else "green"},
            'steps': [
                {'range': [0, 30], 'color': "#E8F5E9"},
                {'range': [30, 70], 'color': "#FFF3E0"},
                {'range': [70, 100], 'color': "#FFEBEE"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

def draw_interaction_graph(drugs, interactions):
    net = Network(height="400px", width="100%", notebook=False)
    for d in drugs:
        net.add_node(d["name"], label=d["name"], color="#4CAF50")
    for i in interactions:
        net.add_edge(i["drug1"], i["drug2"], color="red", title=i.get("risk", ""))
    net.save_graph("interaction_graph.html")
    HtmlFile = open("interaction_graph.html", 'r', encoding='utf-8')
    components.html(HtmlFile.read(), height=420)

# ------------------- VOICE FUNCTIONS -------------------
def capture_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak your prescription now.")
        audio = r.listen(source, phrase_time_limit=10)
    try:
        text = r.recognize_google(audio)
        st.success("🗣️ Voice captured successfully!")
        return text
    except sr.UnknownValueError:
        st.error("❌ Could not understand audio")
        return ""
    except sr.RequestError:
        st.error("❌ Google API error")
        return ""

def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# ------------------- UPLOAD PRESCRIPTION -------------------
if choice == "Upload Prescription":
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Upload image/PDF or paste text")
        file = st.file_uploader("Upload prescription file", type=["png", "jpg", "jpeg", "pdf"])
        text_area = st.text_area("...or paste prescription text here", height=200)

        if st.button("Extract Text"):
            if file is not None:
                # Cross-platform temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
                    tmp.write(file.read())
                    tmp_path = tmp.name
                
                # Extract text & drug info
                ocr_result = ocr.extract_drug_info(tmp_path)
                st.session_state.raw_text = ocr_result.get("raw_text", "")
            else:
                st.session_state.raw_text = text_area or ""

        st.text_area("Extracted Text", value=st.session_state.raw_text, height=220)

        if st.button("Parse Drugs & Age"):
            st.session_state.parsed = nlp.extract_drug_structures(st.session_state.raw_text)
            st.success("✅ Parsed successfully. Switch to 'Drug Verification' tab to analyze.")

    with col2:
        st.info("💡 Tips:\n- If PDF text is empty, it may be an image PDF. Export as image and upload.\n- Include patient's age in the text for age-aware checks.")

# ------------------- DRUG VERIFICATION -------------------
elif choice == "Drug Verification":
    parsed = st.session_state.parsed
    st.subheader("Parsed Data")
    st.json(parsed)

    if st.button("🎤 Voice Input Prescription"):
        voice_text = capture_voice()
        if voice_text:
            st.session_state.raw_text = voice_text
            st.text_area("Extracted Prescription Text", value=voice_text, height=200)
            st.session_state.parsed = nlp.extract_drug_structures(voice_text)
            parsed = st.session_state.parsed
            st.success("✅ Parsed successfully from voice input.")

    age = st.number_input("Patient Age", min_value=0, max_value=120, value=int(parsed.get("patient_age") or 30))
    if age != parsed.get("patient_age"):
        parsed["patient_age"] = int(age)

    if st.button("Run Safety Check"):
        custom_risk = risk.score_from_drugs(parsed["drugs"], parsed.get("patient_age") or age)
        st.session_state.result = custom_risk
        st.session_state.risk_score = custom_risk["risk_score"]

    if st.session_state.result:
        if st.session_state.risk_score > 70:
            st.error("🚨 High Risk Prescription – Immediate review required!")
        elif st.session_state.risk_score > 30:
            st.warning("⚠️ Moderate Risk – Caution advised.")
        else:
            st.success("✅ Prescription appears safe.")

        col1, col2 = st.columns([1,1])
        with col1:
            risk_gauge(st.session_state.risk_score)
            st.metric("Interaction Risk Level", st.session_state.result.get("interaction_risk","-"))

        with col2:
            st.markdown("### Flags / Reasons")
            if st.session_state.result.get("flags"):
                for f in st.session_state.result["flags"]:
                    st.error(f)
            else:
                st.write("No flags detected. Prescription seems safe.")

            st.markdown("### Suggested Alternatives")
            alts = st.session_state.result.get("alternatives", [])
            if alts:
                for a in alts:
                    st.success(a)
            else:
                st.write("No alternatives needed.")

            st.markdown("### Predicted Future Risks")
            future_risks = st.session_state.result.get("predicted_risks", ["No predicted risks"])
            for r in future_risks:
                st.warning(r)

        draw_interaction_graph(parsed["drugs"], st.session_state.result.get("interactions", []))

        with st.expander("🤖 AI-Suggested Safer Alternatives (Hugging Face)"):
            try:
                drug_names = [d["name"] for d in parsed["drugs"]]
                ai_alts = get_ai_alternatives(drug_names)
                st.write(ai_alts)
            except Exception as e:
                st.error(f"AI Alternative suggestion failed: {e}")

        with st.expander("⚠️ AI Dosage Warnings Based on Age (Hugging Face)"):
            try:
                drug_names = [d["name"] for d in parsed["drugs"]]
                ai_warnings = get_ai_dosage_warnings(drug_names, parsed.get("patient_age"))
                st.write(ai_warnings)
            except Exception as e:
                st.error(f"AI Dosage check failed: {e}")

        if st.button("🔊 Speak Risk Summary"):
            result = st.session_state.result
            summary = f"Risk Level: {result['interaction_risk']}. "
            summary += f"{len(result.get('flags', []))} flags detected. "
            summary += f"{len(result.get('predicted_risks', []))} predicted future risks."
            speak_text(summary)
            st.info("🔊 Spoken summary complete.")

# ------------------- DOCTOR OVERRIDE -------------------
elif choice == "Doctor Override":
    st.subheader("Adjust detected drugs and re-verify")
    parsed = st.session_state.parsed
    if not parsed.get("drugs"):
        st.warning("⚠️ No drugs parsed yet. Go to 'Upload Prescription' and parse first.")
    else:
        edited = st.data_editor(parsed["drugs"], num_rows="dynamic", key="editor_drugs")
        st.session_state.parsed["drugs"] = edited
        if st.button("Re-Verify"):
            granite_result = granite_client.analyze(st.session_state.parsed)
            custom_risk = risk.score_from_drugs(parsed["drugs"], parsed.get("patient_age") or 30)
            st.session_state.result = {**granite_result, **custom_risk}
            st.session_state.risk_score = custom_risk["risk_score"]
            st.success("✅ Re-verified. Check 'Drug Verification' tab for updated results.")

# ------------------- REPORTS & HISTORY -------------------
elif choice == "Reports & History":
    st.subheader("Save current case and download report")
    parsed = st.session_state.parsed
    result = st.session_state.result
    risk_score = st.session_state.risk_score

    c1, c2, _ = st.columns(3)
    with c1:
        if st.button("Save Case"):
            case_id = db.save_case(parsed, result, risk_score)
            st.session_state.saved_case_id = case_id
            st.success(f"💾 Saved case #{case_id}")
    with c2:
        if st.button("Download JSON"):
            data = {"parsed": parsed, "result": result, "risk_score": risk_score}
            st.download_button(
                "Download JSON file",
                data=json.dumps(data, indent=2),
                file_name="case.json",
                mime="application/json"
            )

    st.divider()
    st.subheader("History")
    cases = db.list_cases()
    if cases:
        for c in cases:
            with st.expander(f"Case #{c['id']} — Age {c['patient_age']} — Risk {c['risk_score']} — {c['timestamp']}"):
                case = db.get_case(c["id"])
                st.json(case)
    else:
        st.info("No saved cases yet.")

# ------------------- FOOTER -------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>Built with ❤️ using Hugging Face & Granite for IBM Hackathon 2025</p>", unsafe_allow_html=True)
