import streamlit as st 
import json
import random
import time
from datetime import datetime, date

# ─── Local Modules ───────────────────────────────────────────────────────────
from resume_extractor import extract_all_from_resume, SKILLS_DATABASE
from speech_handler import (
    check_dependencies, get_prompt, transcribe_audio,
    post_process_email, post_process_phone, post_process_name,
    post_process_gender, post_process_education, post_process_skills,
    LANGUAGE_MAP, get_audio_recorder,
)
from fraud_checker import run_fraud_check, calculate_health_score

# ─── Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="AutoDEET - Digital Employment Exchange of Telangana",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Header gradient */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #1565c0 100%);
        color: white;
        padding: 25px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2em;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .main-header .subtitle {
        font-size: 1.1em;
        opacity: 0.92;
        margin-top: 6px;
        font-weight: 400;
    }
    .main-header .telugu {
        font-size: 0.95em;
        opacity: 0.85;
        margin-top: 4px;
    }

    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #e3f2fd 0%, #f5f5f5 100%);
        border-left: 5px solid #1565c0;
        padding: 12px 18px;
        margin: 22px 0 14px 0;
        border-radius: 0 8px 8px 0;
        font-size: 1.15em;
        font-weight: 600;
        color: #0d47a1;
    }

    /* Status cards */
    .status-card {
        padding: 15px 20px;
        border-radius: 10px;
        margin: 8px 0;
        font-weight: 500;
    }
    .status-green {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        color: #2e7d32;
    }
    .status-red {
        background: #ffebee;
        border-left: 4px solid #f44336;
        color: #c62828;
    }
    .status-blue {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #1565c0;
    }
    .status-orange {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        color: #e65100;
    }

    /* Footer */
    .footer {
        background: #263238;
        color: #b0bec5;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin-top: 30px;
        font-size: 0.88em;
    }

    /* Success card */
    .success-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border: 2px solid #4caf50;
        border-radius: 12px;
        padding: 25px;
        text-align: center;
        margin: 15px 0;
    }
    .success-card h2 { color: #2e7d32; margin: 0; }
    .success-card .reg-id {
        font-size: 1.4em;
        font-weight: 700;
        color: #1b5e20;
        background: white;
        display: inline-block;
        padding: 8px 20px;
        border-radius: 6px;
        margin: 10px 0;
        border: 1px solid #a5d6a7;
    }

    /* Make multiselect tags bigger */
    .stMultiSelect [data-baseweb="tag"] {
        font-size: 0.9em;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8eaf6 0%, #f5f5f5 100%);
    }
</style>
""", unsafe_allow_html=True)

# ─── Constants ───────────────────────────────────────────────────────────────
TELANGANA_DISTRICTS = [
    "Hyderabad", "Rangareddy", "Medchal-Malkajgiri", "Sangareddy",
    "Warangal Urban", "Warangal Rural", "Karimnagar", "Nizamabad",
    "Khammam", "Nalgonda", "Mahabubnagar", "Adilabad", "Medak",
    "Siddipet", "Suryapet", "Mancherial", "Jagtial", "Peddapalli",
    "Kamareddy", "Wanaparthy", "Nagarkurnool", "Vikarabad", "Nirmal",
    "Rajanna Sircilla", "Jogulamba Gadwal", "Jayashankar Bhupalpally",
    "Bhadradri Kothagudem", "Yadadri Bhuvanagiri", "Kumuram Bheem",
    "Mulugu", "Narayanpet", "Mahabubabad", "Jangaon",
]

JOB_FUNCTIONS = [
    "Information Technology", "Artificial Intelligence", "Data Science",
    "Software Development", "Web Development", "Mobile Development",
    "Cloud Computing", "Cybersecurity", "Digital Marketing",
    "Content Writing", "Graphic Design", "Video Editing",
    "Teaching/Education", "Healthcare/Nursing", "Banking/Finance",
    "Accounting", "Human Resources", "Sales/Marketing",
    "Customer Service", "Logistics/Supply Chain", "Manufacturing",
    "Construction", "Agriculture", "Government Services",
    "Legal Services", "Mechanical Engineering", "Electrical Engineering",
    "Civil Engineering", "Automobile", "Hospitality/Tourism",
    "Retail", "Telecommunications",
]

ALL_SKILLS = [
    "Python", "Java", "JavaScript", "SQL", "HTML/CSS", "React", "Angular",
    "Node.js", "Django", "Flask", "Machine Learning", "Data Analysis",
    "Excel", "Power BI", "Tableau", "AWS", "Azure", "Docker", "Git",
    "Linux", "AutoCAD", "MATLAB", "SAP", "Salesforce", "Tally",
    "MS Office", "Business Acumen", "Conflict Resolution",
    "Customer Service", "Management", "Interpersonal Skills",
    "Leadership", "Problem Solving", "Writing", "Public Speaking",
    "Critical Thinking", "Decision Making", "Negotiation",
    "Emotional Intelligence", "Networking", "Teamwork",
    "Time Management", "Planning", "Entrepreneurship", "Translation",
    "Observation", "Organization", "Communication", "Adaptability",
]

EDUCATION_OPTIONS = [
    "", "PhD",
    "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)",
    "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)",
    "Diploma", "Intermediate/12th", "SSC/10th", "ITI",
    "Below 10th", "Other",
]

TRENDING_JOBS = {
    "PhD": ["Data Science", "Artificial Intelligence", "Teaching/Education"],
    "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)": [
        "Information Technology", "Software Development", "Banking/Finance",
        "Data Science", "Cloud Computing"
    ],
    "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)": [
        "Software Development", "Web Development", "Digital Marketing",
        "Sales/Marketing", "Customer Service"
    ],
    "Diploma": [
        "Manufacturing", "Mechanical Engineering", "Electrical Engineering",
        "Automobile", "Construction"
    ],
    "Intermediate/12th": [
        "Customer Service", "Retail", "Digital Marketing",
        "Content Writing", "Sales/Marketing"
    ],
    "SSC/10th": [
        "Customer Service", "Retail", "Manufacturing",
        "Logistics/Supply Chain", "Construction"
    ],
    "ITI": [
        "Mechanical Engineering", "Electrical Engineering", "Automobile",
        "Manufacturing", "Construction"
    ],
    "Below 10th": [
        "Agriculture", "Construction", "Manufacturing",
        "Logistics/Supply Chain", "Retail"
    ],
}


# ─── Session State Initialization ────────────────────────────────────────────
def init_session_state():
    defaults = {
        # Form fields
        "form_name": "",
        "form_phone": "",
        "form_email": "",
        "form_dob": date(2000, 1, 1),
        "form_gender": "Male",
        "form_aadhaar": "",
        "form_additional": "",
        "form_education": "",
        "form_year_passed": 2024,
        "form_currently_pursuing": "No",
        "form_skills": [],
        "form_optional_skills": [],
        "form_preferred_locations": [],
        "form_job_functions": [],
        "form_looking_for_job": "Yes",
        "form_exp_years": 0,
        "form_exp_months": 0,
        "form_is_fresher": False,
        "form_job_types": [],
        "form_profile_image": None,
        "form_resume_file": None,
        "form_identity_card": None,
        "form_cert1": None,
        "form_cert2": None,
        "form_cert3": None,
        # Academic details
        "form_inter_institution": "",
        "form_inter_type": "Government",
        "form_inter_college": "",
        "form_inter_location": "",
        "form_inter_year": 2024,
        "form_ug_institution": "",
        "form_ug_type": "Government",
        "form_ug_college": "",
        "form_ug_location": "",
        "form_ug_year": 2024,
        "form_pg_institution": "",
        "form_pg_type": "Government",
        "form_pg_college": "",
        "form_pg_location": "",
        "form_pg_year": 2024,
        "form_phd_institution": "",
        "form_phd_type": "Government",
        "form_phd_college": "",
        "form_phd_location": "",
        "form_phd_year": 2024,
        "form_other_institution": "",
        "form_other_type": "Government",
        "form_other_college": "",
        "form_other_location": "",
        "form_other_year": 2024,
        # Experience entries
        "experience_entries": [],
        # Mode tracking
        "registration_mode": "📝 Manual Entry",
        "extraction_result": None,
        "submitted": False,
        "registration_id": None,
        # Voice
        "voice_language": "English",
        "voice_step": 0,
        "voice_results": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


def reset_form():
    """Reset all form fields."""
    keys_to_remove = [k for k in st.session_state.keys()]
    for k in keys_to_remove:
        del st.session_state[k]
    init_session_state()


def count_filled_fields():
    """Count how many fields are filled."""
    count = 0
    if st.session_state.form_name:
        count += 1
    if st.session_state.form_phone:
        count += 1
    if st.session_state.form_email:
        count += 1
    if st.session_state.form_education:
        count += 1
    if st.session_state.form_skills:
        count += 1
    if st.session_state.form_preferred_locations:
        count += 1
    if st.session_state.form_job_functions:
        count += 1
    if st.session_state.form_aadhaar:
        count += 1
    if st.session_state.form_profile_image:
        count += 1
    if st.session_state.form_resume_file:
        count += 1
    return count


# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏛️ Digital Employment Exchange of Telangana</h1>
    <div class="subtitle">AutoDEET: Eliminate Manual Data Entry</div>
    <div class="telugu">తెలంగాణ డిజిటల్ ఉపాధి మార్పిడి | ఆటోడీట్: మాన్యువల్ డేటా ఎంట్రీని తొలగించండి</div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏛️ AutoDEET Portal")
    st.markdown("---")

    st.markdown("**📋 About**")
    st.info(
        "AutoDEET streamlines job seeker registration for the "
        "Digital Employment Exchange of Telangana through AI-powered "
        "resume parsing, voice input for accessibility, and smart "
        "fraud detection."
    )

    st.markdown("---")
    st.markdown("**📊 Quick Stats**")
    filled = count_filled_fields()
    st.metric("Fields Filled", f"{filled}/10")
    st.progress(min(filled / 10, 1.0))

    st.markdown("---")
    st.markdown("**🎯 Registration Mode**")
    mode = st.radio(
        "Select Mode:",
        ["📝 Manual Entry", "📄 Resume Upload (Auto-fill)", "🎤 Voice Registration"],
        key="registration_mode",
        label_visibility="collapsed",
    )

    st.markdown("---")
    if st.button("🔄 Reset Form", use_container_width=True, type="secondary"):
        reset_form()
        st.rerun()

    st.markdown("---")
    st.markdown(
        """<div style="text-align:center; font-size:0.8em; color:#666;">
        Government of Telangana<br>
        IT, E&C Department<br>
        © 2025 DEET Portal
        </div>""",
        unsafe_allow_html=True,
    )

# ─── MODE: Resume Upload ────────────────────────────────────────────────────
if st.session_state.registration_mode == "📄 Resume Upload (Auto-fill)":
    st.markdown(
        '<div class="section-header">📄 Resume Upload — Auto-fill Registration '
        '| రెజ్యూమ్ అప్‌లోడ్</div>',
        unsafe_allow_html=True,
    )

    # Show extraction results from previous run (persisted in session state)
    if st.session_state.extraction_result is not None:
        result = st.session_state.extraction_result
        if result["status"] == "success":
            st.success(
                f"✅ Data extracted successfully in "
                f"{result['extraction_time']:.2f} seconds! "
                f"Form has been auto-filled below."
            )

            # Show extraction summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Name", result["name"] or "Not found")
                st.metric("Email", result["email"] or "Not found")
            with col2:
                st.metric("Phone", result["phone"] or "Not found")
                st.metric("Education", result["education"] or "Not found")
            with col3:
                st.metric("Skills Found", len(result["skills"]))
                st.metric(
                    "Extraction Time",
                    f"{result['extraction_time']:.2f}s"
                )

            # Show extracted entities
            with st.expander("🏢 Organizations Detected"):
                if result["organizations"]:
                    for org in result["organizations"]:
                        st.write(f"• {org}")
                else:
                    st.write("No organizations detected")

            with st.expander("📍 Locations Detected"):
                if result["locations"]:
                    for loc in result["locations"]:
                        st.write(f"• {loc}")
                else:
                    st.write("No locations detected")

            with st.expander("📝 Raw Extracted Text"):
                st.text_area(
                    "Full text from PDF:",
                    result["raw_text"],
                    height=300,
                    disabled=True,
                )
        elif result["status"] == "error":
            st.error(
                "❌ Extraction failed: "
                + "; ".join(result.get("errors", ["Unknown error"]))
            )

    uploaded_resume = st.file_uploader(
        "Upload your Resume (PDF only)",
        type=["pdf"],
        help="Upload a text-based PDF resume. Max 5MB.",
        key="resume_uploader",
    )

    if uploaded_resume is not None:
        file_size_mb = uploaded_resume.size / (1024 * 1024)
        st.caption(f"📁 {uploaded_resume.name} ({file_size_mb:.2f} MB)")

        if file_size_mb > 5:
            st.error("File too large. Maximum 5MB allowed.")
        else:
            if st.button("🔍 Extract & Auto-fill", type="primary"):
                with st.spinner("Extracting data from resume..."):
                    result = extract_all_from_resume(uploaded_resume)

                st.session_state.extraction_result = result

                if result["status"] == "success":
                    # ── Auto-fill form fields ──
                    if result["name"]:
                        st.session_state.form_name = result["name"]
                        st.session_state.input_name = result["name"]
                    if result["email"]:
                        st.session_state.form_email = result["email"]
                        st.session_state.input_email = result["email"]
                    if result["phone"]:
                        st.session_state.form_phone = result["phone"]
                        st.session_state.input_phone = result["phone"]
                    if result["aadhaar"]:
                        st.session_state.form_aadhaar = result["aadhaar"]
                        st.session_state.input_aadhaar = result["aadhaar"]
                    if result["education"]:
                        if result["education"] in EDUCATION_OPTIONS:
                            st.session_state.form_education = result["education"]
                            st.session_state.input_education = result["education"]

                    # Case-insensitive skills matching
                    if result["skills"]:
                        all_skills_lower = {s.lower(): s for s in ALL_SKILLS}
                        matched = []
                        seen = set()
                        for s in result["skills"]:
                            key = s.lower()
                            if key in all_skills_lower and key not in seen:
                                seen.add(key)
                                matched.append(all_skills_lower[key])
                        st.session_state.form_skills = matched[:20]
                        st.session_state.input_skills = matched[:20]

                    # Experience years + months
                    if result["experience_years"] is not None:
                        exp_total = result["experience_years"]
                        st.session_state.form_exp_years = min(
                            int(exp_total), 50
                        )
                        st.session_state.input_exp_years = st.session_state.form_exp_years
                        frac = exp_total - int(exp_total)
                        st.session_state.form_exp_months = min(
                            int(frac * 12), 11
                        )
                        st.session_state.input_exp_months = st.session_state.form_exp_months

                    # Auto-fill locations from resume
                    if result["locations"]:
                        matched_locs = []
                        for loc in result["locations"]:
                            for dist in TELANGANA_DISTRICTS:
                                if (
                                    dist.lower() in loc.lower()
                                    or loc.lower() in dist.lower()
                                ):
                                    if dist not in matched_locs:
                                        matched_locs.append(dist)
                        if matched_locs:
                            st.session_state.form_preferred_locations = (
                                matched_locs
                            )
                            st.session_state.input_locations = matched_locs

                    # Auto-fill institution from organizations
                    if result["organizations"]:
                        first_org = result["organizations"][0]
                        edu = st.session_state.form_education or ""
                        if "Post Graduate" in edu:
                            st.session_state.form_pg_institution = first_org
                            st.session_state.input_pg_inst = first_org
                            st.session_state.form_pg_college = first_org
                            st.session_state.input_pg_college = first_org
                        elif "PhD" in edu:
                            st.session_state.form_phd_institution = first_org
                            st.session_state.input_phd_inst = first_org
                            st.session_state.form_phd_college = first_org
                            st.session_state.input_phd_college = first_org
                        else:
                            st.session_state.form_ug_institution = first_org
                            st.session_state.input_ug_inst = first_org
                            st.session_state.form_ug_college = first_org
                            st.session_state.input_ug_college = first_org

                    # Auto-fill year of passing
                    if result["years"]:
                        latest_year = result["years"][0]
                        if 1980 <= latest_year <= 2025:
                            st.session_state.form_year_passed = latest_year
                            st.session_state.input_year_passed = latest_year
                            
                            # Also set it for the specific sub-level
                            edu = st.session_state.form_education or ""
                            if "Post Graduate" in edu:
                                st.session_state.form_pg_year = latest_year
                                st.session_state.input_pg_year = latest_year
                            elif "PhD" in edu:
                                st.session_state.form_phd_year = latest_year
                                st.session_state.input_phd_year = latest_year
                            else:
                                st.session_state.form_ug_year = latest_year
                                st.session_state.input_ug_year = latest_year

                    # Auto-fill location into academic fields
                    if result["locations"]:
                        first_loc = result["locations"][0]
                        edu = st.session_state.form_education or ""
                        if "Post Graduate" in edu:
                            if not st.session_state.form_pg_location:
                                st.session_state.form_pg_location = first_loc
                                st.session_state.input_pg_location = first_loc
                        elif "PhD" in edu:
                            if not st.session_state.form_phd_location:
                                st.session_state.form_phd_location = first_loc
                                st.session_state.input_phd_location = first_loc
                        else:
                            if not st.session_state.form_ug_location:
                                st.session_state.form_ug_location = first_loc
                                st.session_state.input_ug_location = first_loc

                    # Store resume file reference
                    st.session_state.form_resume_file = uploaded_resume

                    # Rerun to reflect auto-filled values in form widgets
                    st.rerun()

    st.markdown("---")
    st.info("👇 Review and edit the auto-filled form below")

# ─── MODE: Voice Registration ───────────────────────────────────────────────
if st.session_state.registration_mode == "🎤 Voice Registration":
    st.markdown(
        '<div class="section-header">🎤 Voice Registration — Accessibility Mode '
        '| వాయిస్ రిజిస్ట్రేషన్</div>',
        unsafe_allow_html=True,
    )

    deps_ok, deps_msg = check_dependencies()

    if not deps_ok:
        st.error(f"⚠️ {deps_msg}")
    else:
        vcol1, vcol2 = st.columns([1, 2])
        with vcol1:
            voice_lang = st.selectbox(
                "🌐 Select Language / భాష ఎంచుకోండి",
                ["English", "Hindi", "Telugu"],
                key="voice_language",
            )
        with vcol2:
            openai_api_key = st.text_input(
                "🔑 OpenAI API Key (Optional for Whisper AI)",
                type="password",
                help="Provide your OpenAI API Key to use the ultra-accurate Whisper AI for speech recognition. Without it, it will fall back to standard Google Speech Recognition."
            )

        st.markdown("---")

        voice_fields = [
            ("name", "👤 Full Name"),
            ("phone", "📱 Phone Number"),
            ("email", "📧 Email Address"),
            ("gender", "⚧ Gender"),
            ("education", "🎓 Education"),
            ("skills", "💼 Skills"),
            ("location", "📍 Preferred Location"),
        ]

        audio_recorder = get_audio_recorder()

        for field_key, field_label in voice_fields:
            st.markdown(f"**{field_label}**")
            prompt = get_prompt(field_key, voice_lang)
            st.caption(f"🗣️ {prompt}")

            vcol_a, vcol_b = st.columns([1, 2])
            with vcol_a:
                if audio_recorder:
                    audio_bytes = audio_recorder(
                        text="",
                        recording_color="#e8b62c",
                        neutral_color="#6aa36f",
                        icon_name="microphone",
                        icon_size="2x",
                        key=f"voice_{field_key}",
                    )
                else:
                    audio_bytes = None
                    st.warning("Audio recorder not available")

            with vcol_b:
                if audio_bytes:
                    transcription = transcribe_audio(audio_bytes, voice_lang, openai_api_key)

                    if transcription["status"] == "success":
                        raw_text = transcription["text"]

                        # Post-process based on field type
                        if field_key == "name":
                            processed = post_process_name(raw_text)
                            st.session_state.form_name = processed
                            st.session_state.input_name = processed
                        elif field_key == "phone":
                            processed = post_process_phone(raw_text)
                            st.session_state.form_phone = processed
                            st.session_state.input_phone = processed
                        elif field_key == "email":
                            processed = post_process_email(raw_text)
                            st.session_state.form_email = processed
                            st.session_state.input_email = processed
                        elif field_key == "gender":
                            processed = post_process_gender(raw_text)
                            if processed in [
                                "Male", "Female", "Other", "Transgender"
                            ]:
                                st.session_state.form_gender = processed
                                st.session_state.input_gender = processed
                        elif field_key == "education":
                            processed = post_process_education(raw_text)
                            if processed and processed in EDUCATION_OPTIONS:
                                st.session_state.form_education = processed
                                st.session_state.input_education = processed
                            processed = processed or raw_text
                        elif field_key == "skills":
                            processed_list = post_process_skills(raw_text)
                            matched = [
                                s for s in processed_list if s in ALL_SKILLS
                            ]
                            if matched:
                                existing = st.session_state.form_skills
                                new_skills = list(set(existing + matched))
                                st.session_state.form_skills = new_skills
                                st.session_state.input_skills = new_skills
                            processed = ", ".join(processed_list)
                        elif field_key == "location":
                            processed = raw_text.strip().title()
                            # Try to match to districts
                            for dist in TELANGANA_DISTRICTS:
                                if dist.lower() in processed.lower():
                                    if dist not in st.session_state.form_preferred_locations:
                                        st.session_state.form_preferred_locations.append(dist)
                                        st.session_state.input_locations = st.session_state.form_preferred_locations
                        else:
                            processed = raw_text

                        st.success(f"✅ Recognized: **{processed}**")
                        if raw_text != str(processed):
                            st.caption(f"Raw: {raw_text}")
                        
                        # Rerun to reflect the newly spoken field in the form
                        time.sleep(1.5) # Give user a moment to see the success message
                        st.rerun()
                    else:
                        st.warning(f"⚠️ {transcription['message']}")
                else:
                    current_val = ""
                    if field_key == "name":
                        current_val = st.session_state.form_name
                    elif field_key == "phone":
                        current_val = st.session_state.form_phone
                    elif field_key == "email":
                        current_val = st.session_state.form_email
                    if current_val:
                        st.info(f"Current: {current_val}")
                    else:
                        st.caption("Click the mic button and speak")

            st.markdown("---")

        st.info("👇 Review and edit the auto-filled form below")


# ═══════════════════════════════════════════════════════════════════════════
# REGISTRATION FORM (All 6 Sections)
# ═══════════════════════════════════════════════════════════════════════════

if not st.session_state.submitted:

    # ─── SECTION 1: Profile Details ──────────────────────────────────────
    st.markdown(
        '<div class="section-header">📋 Section 1: Profile Details '
        '| ప్రొఫైల్ వివరాలు</div>',
        unsafe_allow_html=True,
    )

    s1_col1, s1_col2 = st.columns(2)

    with s1_col1:
        lang_pref = st.radio(
            "Language Selection / భాష ఎంపిక",
            ["Telugu", "English"],
            horizontal=True,
        )

        form_name = st.text_input(
            "Full Name / పూర్తి పేరు *",
            value=st.session_state.form_name,
            placeholder="Enter your full name",
            key="input_name",
        )
        st.session_state.form_name = form_name

        form_phone = st.text_input(
            "Phone Number / ఫోన్ నంబర్ *",
            value=st.session_state.form_phone,
            placeholder="10-digit mobile number",
            max_chars=10,
            key="input_phone",
        )
        st.session_state.form_phone = form_phone

        form_email = st.text_input(
            "Email / ఈమెయిల్ *",
            value=st.session_state.form_email,
            placeholder="your.email@example.com",
            key="input_email",
        )
        st.session_state.form_email = form_email

    with s1_col2:
        profile_image = st.file_uploader(
            "Upload Profile Image / ప్రొఫైల్ చిత్రం",
            type=["jpg", "jpeg", "png"],
            help="Max 500KB, JPG or PNG",
            key="input_profile_image",
        )
        if profile_image:
            if profile_image.size > 512000:
                st.warning("⚠️ Image exceeds 500KB limit")
            else:
                st.session_state.form_profile_image = True
                st.image(profile_image, width=120)

        form_dob = st.date_input(
            "Date of Birth / పుట్టిన తేదీ",
            value=st.session_state.form_dob,
            min_value=date(1950, 1, 1),
            max_value=date.today(),
            key="input_dob",
        )
        st.session_state.form_dob = form_dob

        form_gender = st.selectbox(
            "Gender / లింగం",
            ["Male", "Female", "Other", "Transgender"],
            index=["Male", "Female", "Other", "Transgender"].index(
                st.session_state.form_gender
            ),
            key="input_gender",
        )
        st.session_state.form_gender = form_gender

    aadhaar_col, extra_col = st.columns(2)
    with aadhaar_col:
        form_aadhaar = st.text_input(
            "Aadhaar Number (Optional) / ఆధార్ నంబర్",
            value=st.session_state.form_aadhaar,
            placeholder="12-digit Aadhaar number",
            max_chars=12,
            key="input_aadhaar",
        )
        st.session_state.form_aadhaar = form_aadhaar

    with extra_col:
        form_additional = st.text_area(
            "Additional Details / అదనపు వివరాలు",
            value=st.session_state.form_additional,
            placeholder="Any additional information...",
            height=80,
            key="input_additional",
        )
        st.session_state.form_additional = form_additional

    # ─── SECTION 2: Education Details ────────────────────────────────────
    st.markdown(
        '<div class="section-header">🎓 Section 2: Education Details '
        '| విద్యా వివరాలు</div>',
        unsafe_allow_html=True,
    )

    ed_col1, ed_col2 = st.columns(2)

    with ed_col1:
        form_pursuing = st.radio(
            "Are You Currently Pursuing? / ప్రస్తుతం చదువుతున్నారా?",
            ["Yes", "No"],
            index=["Yes", "No"].index(
                st.session_state.form_currently_pursuing
            ),
            horizontal=True,
            key="input_pursuing",
        )
        st.session_state.form_currently_pursuing = form_pursuing

        current_edu = st.session_state.form_education
        try:
            edu_index = EDUCATION_OPTIONS.index(current_edu)
        except ValueError:
            edu_index = 0

        form_education = st.selectbox(
            "Highest Education Qualification / అత్యున్నత విద్యార్హత",
            EDUCATION_OPTIONS,
            index=edu_index,
            key="input_education",
        )
        st.session_state.form_education = form_education

    with ed_col2:
        form_year = st.selectbox(
            "Year of Passed Out / ఉత్తీర్ణ సంవత్సరం",
            list(range(2025, 1979, -1)),
            index=list(range(2025, 1979, -1)).index(
                st.session_state.form_year_passed
            ) if st.session_state.form_year_passed in range(1980, 2026) else 0,
            key="input_year_passed",
        )
        st.session_state.form_year_passed = form_year

    # Academic Qualification sub-sections
    st.markdown("**Academic Qualifications / విద్యా అర్హతలు**")

    academic_levels = [
        ("Intermediate", "form_inter"),
        ("Undergraduate", "form_ug"),
        ("Post Graduate", "form_pg"),
        ("PhD", "form_phd"),
        ("Other (ITI/Polytechnic)", "form_other"),
    ]

    for level_name, prefix in academic_levels:
        with st.expander(f"➕ {level_name} Details"):
            ac1, ac2 = st.columns(2)
            with ac1:
                inst = st.text_input(
                    f"Institution Name",
                    value=st.session_state.get(f"{prefix}_institution", ""),
                    key=f"input_{prefix}_inst",
                    placeholder=f"Enter {level_name} institution",
                )
                st.session_state[f"{prefix}_institution"] = inst

                inst_type = st.selectbox(
                    "Institution Type",
                    ["Government", "Private"],
                    index=["Government", "Private"].index(
                        st.session_state.get(f"{prefix}_type", "Government")
                    ),
                    key=f"input_{prefix}_type",
                )
                st.session_state[f"{prefix}_type"] = inst_type

            with ac2:
                college = st.text_input(
                    "College Name",
                    value=st.session_state.get(f"{prefix}_college", ""),
                    key=f"input_{prefix}_college",
                    placeholder="Enter college name",
                )
                st.session_state[f"{prefix}_college"] = college

                loc = st.text_input(
                    "Location",
                    value=st.session_state.get(f"{prefix}_location", ""),
                    key=f"input_{prefix}_location",
                    placeholder="City / District",
                )
                st.session_state[f"{prefix}_location"] = loc

            passed_yr = st.selectbox(
                "Passed Year",
                [""] + list(range(2025, 1979, -1)),
                key=f"input_{prefix}_year",
            )
            if passed_yr:
                st.session_state[f"{prefix}_year"] = passed_yr

    # ─── SECTION 3: Job Preferences ─────────────────────────────────────
    st.markdown(
        '<div class="section-header">💼 Section 3: Job Preferences '
        '| ఉద్యోగ ప్రాధాన్యతలు</div>',
        unsafe_allow_html=True,
    )

    jp_col1, jp_col2 = st.columns(2)

    with jp_col1:
        form_looking = st.radio(
            "Actively Looking for Job? / ఉద్యోగం కోసం చూస్తున్నారా?",
            ["Yes", "No"],
            horizontal=True,
            key="input_looking",
        )
        st.session_state.form_looking_for_job = form_looking

        form_locations = st.multiselect(
            "Preferred Job Location(s) / ఇష్టపడే ఉద్యోగ ప్రదేశం",
            TELANGANA_DISTRICTS,
            default=st.session_state.form_preferred_locations,
            key="input_locations",
        )
        st.session_state.form_preferred_locations = form_locations

    with jp_col2:
        form_functions = st.multiselect(
            "Interested Job Functions / ఆసక్తి ఉన్న ఉద్యోగ విధులు",
            JOB_FUNCTIONS,
            default=st.session_state.form_job_functions,
            key="input_functions",
        )
        st.session_state.form_job_functions = form_functions

        # Trending jobs based on education
        if st.session_state.form_education and st.session_state.form_education in TRENDING_JOBS:
            trending = TRENDING_JOBS[st.session_state.form_education]
            st.markdown("**🔥 Trending Job Functions for your qualification:**")
            for tj in trending:
                st.markdown(f"&nbsp;&nbsp;• {tj}")

    # ─── SECTION 4: Skills ───────────────────────────────────────────────
    st.markdown(
        '<div class="section-header">🛠️ Section 4: Skills '
        '| నైపుణ్యాలు</div>',
        unsafe_allow_html=True,
    )

    form_skills = st.multiselect(
        "Mandatory Skills (Minimum 5 Required) / తప్పనిసరి నైపుణ్యాలు *",
        ALL_SKILLS,
        default=st.session_state.form_skills,
        key="input_skills",
        help="Select at least 5 skills from the list",
    )
    st.session_state.form_skills = form_skills

    skill_count = len(form_skills)
    if skill_count < 5:
        st.markdown(
            f'<div class="status-card status-orange">'
            f'⚠️ {skill_count}/5 skills selected — '
            f'Please add {5 - skill_count} more skills</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="status-card status-green">'
            f'✅ {skill_count} skills selected — Minimum requirement met!</div>',
            unsafe_allow_html=True,
        )

    form_opt_skills = st.multiselect(
        "Optional Skills (Soft/Non-Technical) / ఐచ్ఛిక నైపుణ్యాలు",
        [s for s in ALL_SKILLS if s not in form_skills],
        default=[
            s for s in st.session_state.form_optional_skills
            if s not in form_skills
        ],
        key="input_opt_skills",
    )
    st.session_state.form_optional_skills = form_opt_skills

    # ─── SECTION 5: Experience Details ───────────────────────────────────
    st.markdown(
        '<div class="section-header">📊 Section 5: Experience Details '
        '| అనుభవ వివరాలు</div>',
        unsafe_allow_html=True,
    )

    exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 1])

    with exp_col1:
        form_is_fresher = st.checkbox(
            "I am a Fresher / నేను ఫ్రెషర్ ని",
            value=st.session_state.form_is_fresher,
            key="input_fresher",
        )
        st.session_state.form_is_fresher = form_is_fresher

    with exp_col2:
        form_exp_years = st.selectbox(
            "Years / సంవత్సరాలు",
            list(range(0, 51)),
            index=st.session_state.form_exp_years
            if not form_is_fresher else 0,
            disabled=form_is_fresher,
            key="input_exp_years",
        )
        if not form_is_fresher:
            st.session_state.form_exp_years = form_exp_years
        else:
            st.session_state.form_exp_years = 0

    with exp_col3:
        form_exp_months = st.selectbox(
            "Months / నెలలు",
            list(range(0, 12)),
            index=st.session_state.form_exp_months
            if not form_is_fresher else 0,
            disabled=form_is_fresher,
            key="input_exp_months",
        )
        if not form_is_fresher:
            st.session_state.form_exp_months = form_exp_months
        else:
            st.session_state.form_exp_months = 0

    # Experience entries
    st.markdown("**Experience / Internship Details (Optional)**")

    if "experience_entries" not in st.session_state:
        st.session_state.experience_entries = []

    num_exp = st.number_input(
        "Number of experience entries to add:",
        min_value=0,
        max_value=10,
        value=len(st.session_state.experience_entries),
        key="num_exp_entries",
    )

    # Ensure the list has the right number of entries
    while len(st.session_state.experience_entries) < num_exp:
        st.session_state.experience_entries.append({
            "company": "", "role": "", "from": "", "to": "", "desc": ""
        })
    while len(st.session_state.experience_entries) > num_exp:
        st.session_state.experience_entries.pop()

    for i in range(num_exp):
        with st.expander(f"Experience {i + 1}", expanded=True):
            ec1, ec2 = st.columns(2)
            with ec1:
                company = st.text_input(
                    "Company Name",
                    key=f"exp_company_{i}",
                    value=st.session_state.experience_entries[i].get("company", ""),
                )
                st.session_state.experience_entries[i]["company"] = company

                duration_from = st.text_input(
                    "From (e.g., Jan 2022)",
                    key=f"exp_from_{i}",
                    value=st.session_state.experience_entries[i].get("from", ""),
                )
                st.session_state.experience_entries[i]["from"] = duration_from

            with ec2:
                role = st.text_input(
                    "Job Title / Role",
                    key=f"exp_role_{i}",
                    value=st.session_state.experience_entries[i].get("role", ""),
                )
                st.session_state.experience_entries[i]["role"] = role

                duration_to = st.text_input(
                    "To (e.g., Dec 2023)",
                    key=f"exp_to_{i}",
                    value=st.session_state.experience_entries[i].get("to", ""),
                )
                st.session_state.experience_entries[i]["to"] = duration_to

            desc = st.text_area(
                "Description",
                key=f"exp_desc_{i}",
                value=st.session_state.experience_entries[i].get("desc", ""),
                height=80,
            )
            st.session_state.experience_entries[i]["desc"] = desc

    st.markdown("**Preferred Job Type / ఇష్టపడే ఉద్యోగ రకం**")
    form_job_types = st.multiselect(
        "Select job types:",
        ["Full-time", "Part-time", "Contract", "Freelance",
         "Internship", "Remote", "Hybrid"],
        default=st.session_state.form_job_types,
        key="input_job_types",
        label_visibility="collapsed",
    )
    st.session_state.form_job_types = form_job_types

    # ─── SECTION 6: Document Upload ──────────────────────────────────────
    st.markdown(
        '<div class="section-header">📎 Section 6: Document Upload '
        '| పత్రాల అప్‌లోడ్</div>',
        unsafe_allow_html=True,
    )

    doc_col1, doc_col2 = st.columns(2)

    with doc_col1:
        resume_file = st.file_uploader(
            "📄 Upload Resume (Optional, PDF, max 1MB)",
            type=["pdf"],
            key="input_resume_doc",
        )
        if resume_file:
            if resume_file.size > 1048576:
                st.warning("⚠️ Resume exceeds 1MB limit")
            else:
                st.session_state.form_resume_file = resume_file
                st.markdown(
                    f'<div class="status-card status-green">'
                    f'✅ Resume uploaded: {resume_file.name} '
                    f'({resume_file.size/1024:.1f} KB)</div>',
                    unsafe_allow_html=True,
                )
        else:
            if st.session_state.form_resume_file:
                st.markdown(
                    '<div class="status-card status-green">'
                    '✅ Resume: Previously uploaded</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("📄 Not uploaded")

        identity_card = st.file_uploader(
            "🪪 Upload Identity Card (Aadhaar/Voter ID/College ID)",
            type=["pdf", "jpg", "jpeg", "png"],
            key="input_identity",
        )
        if identity_card:
            if identity_card.size > 1048576:
                st.warning("⚠️ File exceeds 1MB limit")
            else:
                st.session_state.form_identity_card = True
                st.markdown(
                    f'<div class="status-card status-green">'
                    f'✅ ID uploaded: {identity_card.name}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("🪪 Not uploaded")

    with doc_col2:
        for cert_num in range(1, 4):
            cert_file = st.file_uploader(
                f"📜 Certificate {cert_num} (Optional, PDF/Image, max 1MB)",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"input_cert_{cert_num}",
            )
            if cert_file:
                if cert_file.size > 1048576:
                    st.warning(f"⚠️ Certificate {cert_num} exceeds 1MB")
                else:
                    st.session_state[f"form_cert{cert_num}"] = True
                    st.markdown(
                        f'<div class="status-card status-green">'
                        f'✅ Certificate {cert_num}: {cert_file.name}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption(f"📜 Certificate {cert_num}: Not uploaded")

    # ═════════════════════════════════════════════════════════════════════
    # FRAUD DETECTION & HEALTH SCORE
    # ═════════════════════════════════════════════════════════════════════

    st.markdown("---")

    # Prepare form data dict
    form_data = {
        "name": st.session_state.form_name,
        "phone": st.session_state.form_phone,
        "email": st.session_state.form_email,
        "aadhaar": st.session_state.form_aadhaar,
        "education": st.session_state.form_education,
        "institution_name": st.session_state.get("form_ug_institution", "")
        or st.session_state.get("form_inter_institution", ""),
        "year_passed": st.session_state.form_year_passed,
        "skills": st.session_state.form_skills,
        "optional_skills": st.session_state.form_optional_skills,
        "preferred_locations": st.session_state.form_preferred_locations,
        "job_functions": st.session_state.form_job_functions,
        "experience_years": st.session_state.form_exp_years,
        "experience_months": st.session_state.form_exp_months,
        "is_fresher": st.session_state.form_is_fresher,
        "profile_image": st.session_state.form_profile_image,
        "resume_uploaded": st.session_state.form_resume_file is not None,
        "identity_card": st.session_state.form_identity_card,
        "certificate_1": st.session_state.form_cert1,
        "certificate_2": st.session_state.form_cert2,
        "certificate_3": st.session_state.form_cert3,
        "experience_entries": st.session_state.experience_entries,
    }

    # ─── Fraud Detection Panel ──────────────────────────────────────────
    fraud_col, health_col = st.columns(2)

    with fraud_col:
        st.markdown(
            '<div class="section-header">🛡️ Fraud Detection '
            '| మోసం గుర్తింపు</div>',
            unsafe_allow_html=True,
        )

        fraud_report = run_fraud_check(form_data)

        # Risk score display
        risk_color = fraud_report["risk_color"]
        risk_css = {
            "green": "status-green",
            "orange": "status-orange",
            "red": "status-red",
        }.get(risk_color, "status-blue")

        st.markdown(
            f'<div class="status-card {risk_css}">'
            f'<strong>Risk Level: {fraud_report["risk_level"]}</strong> '
            f'— Score: {fraud_report["risk_score"]}%<br>'
            f'Checks: {fraud_report["passed_checks"]} passed, '
            f'{fraud_report["failed_checks"]} failed out of '
            f'{fraud_report["total_checks"]}</div>',
            unsafe_allow_html=True,
        )

        st.progress(
            min(fraud_report["risk_score"] / 100, 1.0),
        )

        if fraud_report["flags"]:
            st.markdown("**⚠️ Flagged Issues:**")
            for flag in fraud_report["flags"]:
                st.markdown(f"&nbsp;&nbsp;🔴 {flag}")
        else:
            st.markdown(
                '<div class="status-card status-green">'
                '✅ No fraud indicators detected</div>',
                unsafe_allow_html=True,
            )

        with st.expander("📋 Detailed Check Results"):
            for check_name, check_data in fraud_report["details"].items():
                icon = "✅" if check_data["valid"] else "❌"
                st.markdown(f"**{icon} {check_name.title()}**")
                if check_data["issues"]:
                    for issue in check_data["issues"]:
                        st.caption(f"  → {issue}")
                else:
                    st.caption("  → No issues")

    # ─── Health Score Panel ──────────────────────────────────────────────
    with health_col:
        st.markdown(
            '<div class="section-header">💪 Profile Health Score '
            '| ప్రొఫైల్ ఆరోగ్య స్కోర్</div>',
            unsafe_allow_html=True,
        )

        health = calculate_health_score(form_data)

        health_css = {
            "green": "status-green",
            "blue": "status-blue",
            "orange": "status-orange",
            "red": "status-red",
        }.get(health["grade_color"], "status-blue")

        st.markdown(
            f'<div class="status-card {health_css}">'
            f'<strong>{health["grade_emoji"]} {health["grade"]}</strong> '
            f'— {health["score"]}/{health["max_score"]} points</div>',
            unsafe_allow_html=True,
        )

        st.progress(health["percentage"] / 100)

        with st.expander("📊 Score Breakdown", expanded=True):
            for item_name, item_score in health["breakdown"]:
                st.markdown(f"&nbsp;&nbsp;{item_name}: **+{item_score}**")

        if health["tips"]:
            st.markdown("**💡 Tips to Improve:**")
            for tip in health["tips"]:
                st.markdown(f"&nbsp;&nbsp;💡 {tip}")

    # ═════════════════════════════════════════════════════════════════════
    # SUBMIT BUTTON
    # ═════════════════════════════════════════════════════════════════════

    st.markdown("---")
    st.markdown(
        '<div class="section-header">✅ Submit Registration '
        '| నమోదు సమర్పించండి</div>',
        unsafe_allow_html=True,
    )

    # Validation messages
    validation_errors = []
    if not st.session_state.form_name or len(st.session_state.form_name.strip()) < 2:
        validation_errors.append("Full Name is required (minimum 2 characters)")
    if not st.session_state.form_phone or len(st.session_state.form_phone.strip()) < 10:
        validation_errors.append("Valid Phone Number is required (10 digits)")
    if not st.session_state.form_email or '@' not in st.session_state.form_email:
        validation_errors.append("Valid Email is required")
    if len(st.session_state.form_skills) < 5:
        validation_errors.append(
            f"Minimum 5 skills required (currently {len(st.session_state.form_skills)})"
        )

    if validation_errors:
        st.markdown(
            '<div class="status-card status-orange">'
            '<strong>⚠️ Please fix the following before submitting:</strong></div>',
            unsafe_allow_html=True,
        )
        for err in validation_errors:
            st.markdown(f"&nbsp;&nbsp;❌ {err}")

    submit_disabled = len(validation_errors) > 0

    if st.button(
        "🚀 Submit Registration / నమోదు సమర్పించండి",
        type="primary",
        use_container_width=True,
        disabled=submit_disabled,
    ):
        # Generate Registration ID
        random_num = random.randint(10000, 99999)
        reg_id = f"DEET-TS-2025-{random_num}"
        st.session_state.registration_id = reg_id
        st.session_state.submitted = True
        st.session_state.submission_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        st.session_state.form_data_snapshot = form_data.copy()
        st.session_state.form_data_snapshot["registration_id"] = reg_id
        st.session_state.form_data_snapshot["submission_time"] = (
            st.session_state.submission_time
        )
        st.session_state.form_data_snapshot["gender"] = st.session_state.form_gender
        st.session_state.form_data_snapshot["dob"] = str(st.session_state.form_dob)
        st.session_state.form_data_snapshot["additional_details"] = (
            st.session_state.form_additional
        )
        st.session_state.form_data_snapshot["currently_pursuing"] = (
            st.session_state.form_currently_pursuing
        )
        st.session_state.form_data_snapshot["year_passed"] = (
            st.session_state.form_year_passed
        )
        st.session_state.form_data_snapshot["job_types"] = (
            st.session_state.form_job_types
        )
        st.session_state.form_data_snapshot["looking_for_job"] = (
            st.session_state.form_looking_for_job
        )
        st.session_state.form_data_snapshot["fraud_report"] = fraud_report
        st.session_state.form_data_snapshot["health_score"] = health
        # Remove non-serializable
        st.session_state.form_data_snapshot.pop("resume_uploaded", None)
        st.session_state.form_data_snapshot.pop("profile_image", None)
        st.session_state.form_data_snapshot.pop("identity_card", None)
        st.session_state.form_data_snapshot.pop("certificate_1", None)
        st.session_state.form_data_snapshot.pop("certificate_2", None)
        st.session_state.form_data_snapshot.pop("certificate_3", None)

        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# POST-SUBMISSION SUCCESS PAGE
# ═════════════════════════════════════════════════════════════════════════════

if st.session_state.submitted:
    st.balloons()

    reg_id = st.session_state.registration_id
    sub_time = st.session_state.get("submission_time", "")

    st.markdown(
        f"""
        <div class="success-card">
            <h2>🎉 Registration Successful!</h2>
            <p>నమోదు విజయవంతంగా పూర్తయింది!</p>
            <div class="reg-id">{reg_id}</div>
            <p>Submitted: {sub_time}</p>
            <p><strong>{st.session_state.form_name}</strong> — 
            {st.session_state.form_email} — 
            {st.session_state.form_phone}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Summary cards
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("📚 Education", st.session_state.form_education or "N/A")
    with sc2:
        st.metric("🛠️ Skills", len(st.session_state.form_skills))
    with sc3:
        exp_str = (
            "Fresher" if st.session_state.form_is_fresher
            else f"{st.session_state.form_exp_years}y {st.session_state.form_exp_months}m"
        )
        st.metric("💼 Experience", exp_str)
    with sc4:
        st.metric(
            "📍 Locations",
            len(st.session_state.form_preferred_locations),
        )

    # JSON payload
    with st.expander("📋 Full JSON Payload"):
        payload = st.session_state.get("form_data_snapshot", {})
        st.json(payload)

    # Download receipt
    receipt_lines = [
        "=" * 60,
        "DIGITAL EMPLOYMENT EXCHANGE OF TELANGANA",
        "AutoDEET Registration Receipt",
        "=" * 60,
        f"Registration ID: {reg_id}",
        f"Submission Time: {sub_time}",
        "-" * 60,
        "PROFILE DETAILS",
        f"  Name: {st.session_state.form_name}",
        f"  Phone: {st.session_state.form_phone}",
        f"  Email: {st.session_state.form_email}",
        f"  Gender: {st.session_state.form_gender}",
        f"  Date of Birth: {st.session_state.form_dob}",
        f"  Aadhaar: {'*' * 8 + st.session_state.form_aadhaar[-4:] if st.session_state.form_aadhaar else 'Not provided'}",
        "-" * 60,
        "EDUCATION",
        f"  Qualification: {st.session_state.form_education}",
        f"  Year of Passing: {st.session_state.form_year_passed}",
        f"  Currently Pursuing: {st.session_state.form_currently_pursuing}",
        "-" * 60,
        "SKILLS",
        f"  Mandatory: {', '.join(st.session_state.form_skills)}",
        f"  Optional: {', '.join(st.session_state.form_optional_skills)}",
        "-" * 60,
        "JOB PREFERENCES",
        f"  Looking for Job: {st.session_state.form_looking_for_job}",
        f"  Locations: {', '.join(st.session_state.form_preferred_locations)}",
        f"  Functions: {', '.join(st.session_state.form_job_functions)}",
        f"  Job Types: {', '.join(st.session_state.form_job_types)}",
        "-" * 60,
        "EXPERIENCE",
        f"  Total: {st.session_state.form_exp_years} years, {st.session_state.form_exp_months} months",
        f"  Fresher: {'Yes' if st.session_state.form_is_fresher else 'No'}",
    ]

    for i, entry in enumerate(st.session_state.experience_entries):
        if entry.get("company"):
            receipt_lines.append(
                f"  Entry {i+1}: {entry.get('role', '')} at "
                f"{entry.get('company', '')} "
                f"({entry.get('from', '')} - {entry.get('to', '')})"
            )

    receipt_lines.extend([
        "-" * 60,
        "FRAUD CHECK",
        f"  Risk: {st.session_state.form_data_snapshot.get('fraud_report', {}).get('risk_level', 'N/A')} "
        f"({st.session_state.form_data_snapshot.get('fraud_report', {}).get('risk_score', 0)}%)",
        "PROFILE HEALTH",
        f"  Score: {st.session_state.form_data_snapshot.get('health_score', {}).get('score', 0)}/100",
        "=" * 60,
        "Government of Telangana | IT, E&C Department",
        "This is an auto-generated receipt from AutoDEET Portal",
        "=" * 60,
    ])

    receipt_text = "\n".join(receipt_lines)

    st.download_button(
        label="📥 Download Registration Receipt",
        data=receipt_text,
        file_name=f"DEET_Receipt_{reg_id}.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True,
    )

    st.markdown("---")

    if st.button(
        "🔄 New Registration",
        use_container_width=True,
        type="secondary",
    ):
        reset_form()
        st.rerun()

# ─── Footer ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="footer">
        <strong>Government of Telangana</strong> | 
        Information Technology, Electronics & Communications Department<br>
        Digital Employment Exchange of Telangana (DEET) | 
        AutoDEET v1.0 © 2025<br>
        <em>Designed to eliminate manual data entry and improve accessibility</em>
    </div>
    """,
    unsafe_allow_html=True,
)
