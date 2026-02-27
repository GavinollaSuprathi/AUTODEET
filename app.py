import streamlit as st
import json
from extractor import extract_text_from_pdf, extract_text_from_image, extract_all, load_skills
from scorer import calculate_fraud_risk, calculate_health_score
from voice import transcribe_audio
from PIL import Image


def apply_custom_styles():
    st.markdown("""
    <style>

    .stApp {
        background: linear-gradient(135deg, #0f172a, #020617);
        color: #e2e8f0;
    }

    h1, h2, h3 {
        color: #38bdf8;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617, #0f172a);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    .stButton > button {
        background: linear-gradient(90deg, #38bdf8, #6366f1);
        color: white;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        border: none;
        transition: 0.3s;
    }

    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px rgba(99,102,241,0.6);
    }

    input, textarea {
        background-color: #020617 !important;
        color: #e2e8f0 !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, #22c55e, #38bdf8);
    }

    </style>
    """, unsafe_allow_html=True)


@st.cache_data
def run_extraction_and_scoring(raw_text, skills_list):
    extracted_data = extract_all(raw_text, skills_list)
    fraud_result = calculate_fraud_risk(extracted_data)
    health_score = calculate_health_score(extracted_data)
    return extracted_data, fraud_result, health_score


def main():

    st.set_page_config(page_title="DEET AutoRegister AI", page_icon="📄", layout="wide")
    apply_custom_styles()

    # 🔥 Gradient Title
    st.markdown("""
    <h1 style='text-align:center;
    background: linear-gradient(90deg,#38bdf8,#6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;'>
    📄 DEET AutoRegister AI
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("### Automated Registration with Resume Parsing • Fraud Detection • Voice Accessibility")

    skills_list = load_skills()

    st.sidebar.header("Registration Method")
    reg_method = st.sidebar.radio("Choose Input:", ["Upload Resume", "Voice Registration"])

    raw_text = ""

    
    if reg_method == "Upload Resume":
        st.header("Upload your Resume")
        uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "jpg", "jpeg", "png"])

        if uploaded_file:
            with st.spinner("Extracting text..."):
                if uploaded_file.name.lower().endswith('.pdf'):
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        raw_text = extract_text_from_pdf(tmp.name)
                else:
                    image = Image.open(uploaded_file)
                    raw_text = extract_text_from_image(image)

            st.success("Extraction Complete")

    
    else:
        st.header("Voice Registration")
        audio_value = st.audio_input("Record your details")

        if audio_value:
            with st.spinner("Transcribing..."):
                raw_text = transcribe_audio(audio_value.getvalue())

            if "Error" not in raw_text and "could not understand" not in raw_text:
                st.success("Transcription Complete")
                st.write(raw_text)
            else:
                st.error(raw_text)
                raw_text = ""

    
    if raw_text:

        with st.spinner("Analyzing Information..."):
            extracted_data, fraud_result, health_score = run_extraction_and_scoring(raw_text, skills_list)

        col1, col2 = st.columns([2, 1])

     
        with col2:
            st.subheader("Analysis Metrics")

            st.markdown("**Resume Health Score**")
            st.progress(health_score / 100)
            st.write(f"{health_score}%")

            risk = fraud_result["RiskLevel"]
            color = {"Low":"#22c55e","Medium":"#f59e0b","High":"#ef4444"}[risk]

            st.markdown(f"""
            <div style="padding:10px;border-radius:12px;
            background:{color}20;border:1px solid {color};font-weight:600;">
            Fraud Risk: <span style="color:{color}">{risk}</span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("View Raw Text"):
                st.write(raw_text)

      
        with col1:
            st.subheader("Editable DEET Form")

            names = extracted_data["Entities"].get("Name", [])
            name = names[0] if names else ""
            
            emails = extracted_data["ContactInfo"].get("Emails", [])
            email = emails[0] if emails else ""
            
            phones = extracted_data["ContactInfo"].get("Phones", [])
            phone = phones[0] if phones else ""
            
            skills = ", ".join(extracted_data.get("MatchedSkills", []))

            with st.form("deet_form"):
                f_name = st.text_input("Name", value=name)
                f_email = st.text_input("Email", value=email)
                f_phone = st.text_input("Phone", value=phone)
                f_skills = st.text_area("Skills", value=skills)

                submit = st.form_submit_button("Register to DEET")

                if submit:
                    payload = {
                        "Name": f_name,
                        "Email": f_email,
                        "Phone": f_phone,
                        "Skills": [s.strip() for s in f_skills.split(',')],
                        "HealthScore": health_score,
                        "FraudRisk": fraud_result["RiskLevel"]
                    }

                    st.success("Registration Submitted Successfully")
                    st.json(payload)


if __name__ == "__main__":
    main()
