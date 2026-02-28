import re
import time

SKILLS_DATABASE = [
    "Python", "Java", "JavaScript", "SQL", "HTML/CSS", "React", "Angular",
    "Node.js", "Django", "Flask", "Machine Learning", "Data Analysis",
    "Excel", "Power BI", "Tableau", "AWS", "Azure", "Docker", "Git",
    "Linux", "AutoCAD", "MATLAB", "SAP", "Salesforce", "Tally",
    "MS Office", "Communication", "Leadership", "Teamwork",
    "Problem Solving", "Critical Thinking", "Time Management",
    "Public Speaking", "Negotiation", "Adaptability", "Planning",
    "Customer Service", "Management", "Writing", "Organization",
]


def extract_all_from_resume(uploaded_file):
    """
    Extract structured data from a PDF resume.
    Returns a dict with: name, email, phone, education, skills,
    experience_years, organizations, locations, years, raw_text, status.
    """
    start_time = time.time()

    result = {
        "status": "error",
        "errors": [],
        "name": None,
        "email": None,
        "phone": None,
        "aadhaar": None,
        "education": None,
        "skills": [],
        "experience_years": None,
        "organizations": [],
        "locations": [],
        "years": [],
        "raw_text": "",
        "extraction_time": 0,
    }

    try:
        # ── Try to read PDF ──────────────────────────────────────────
        raw_text = ""

        try:
            import PyPDF2
            uploaded_file.seek(0)
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n"
        except ImportError:
            try:
                import pdfplumber
                uploaded_file.seek(0)
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            raw_text += page_text + "\n"
            except ImportError:
                result["errors"].append(
                    "Install PyPDF2 or pdfplumber: "
                    "pip install PyPDF2 pdfplumber"
                )
                result["extraction_time"] = time.time() - start_time
                return result

        if not raw_text.strip():
            result["errors"].append(
                "No text found in PDF. It may be image-based."
            )
            result["extraction_time"] = time.time() - start_time
            return result

        result["raw_text"] = raw_text

        # ── Extract Email ────────────────────────────────────────────
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, raw_text)
        if emails:
            result["email"] = emails[0]

        # ── Extract Phone ────────────────────────────────────────────
        phone_pattern = r'(?:\+91[\s-]?)?(?:[6-9]\d{9})'
        phones = re.findall(phone_pattern, raw_text)
        if phones:
            phone = re.sub(r'[\s\-\+]', '', phones[0])
            if phone.startswith("91") and len(phone) == 12:
                phone = phone[2:]
            result["phone"] = phone[-10:]

        # ── Extract Aadhaar ──────────────────────────────────────────
        aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
        aadhaars = re.findall(aadhaar_pattern, raw_text)
        if aadhaars:
            aadhaar = re.sub(r'\s', '', aadhaars[0])
            if len(aadhaar) == 12:
                result["aadhaar"] = aadhaar

        # ── Extract Name (first non-empty line heuristic) ────────────
        lines = [
            ln.strip() for ln in raw_text.split("\n")
            if ln.strip()
            and not re.match(r'^(resume|curriculum|cv|portfolio)', ln.strip(), re.I)
        ]
        if lines:
            candidate_name = lines[0]
            # Remove numbers and special chars
            candidate_name = re.sub(r'[^a-zA-Z\s\.]', '', candidate_name)
            candidate_name = candidate_name.strip()
            if 2 <= len(candidate_name) <= 60:
                result["name"] = candidate_name.title()

        # ── Extract Education ────────────────────────────────────────
        text_lower = raw_text.lower()
        education_mapping = {
            "PhD": ["ph.d", "phd", "doctorate", "doctoral"],
            "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)": [
                "m.tech", "mtech", "m.e.", "mba", "mca",
                "m.sc", "msc", "m.a.", "m.com", "mcom",
                "post graduate", "postgraduate", "master",
            ],
            "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)": [
                "b.tech", "btech", "b.e.", "bba", "bca",
                "b.sc", "bsc", "b.a.", "b.com", "bcom",
                "undergraduate", "bachelor",
            ],
            "Diploma": ["diploma"],
            "Intermediate/12th": [
                "intermediate", "12th", "hsc", "plus two",
                "higher secondary",
            ],
            "SSC/10th": ["ssc", "10th", "matriculation"],
            "ITI": ["iti", "industrial training"],
        }

        for edu_level, keywords in education_mapping.items():
            for kw in keywords:
                if kw in text_lower:
                    result["education"] = edu_level
                    break
            if result["education"]:
                break

        # ── Extract Skills ───────────────────────────────────────────
        for skill in SKILLS_DATABASE:
            if re.search(
                r'\b' + re.escape(skill) + r'\b', raw_text, re.I
            ):
                result["skills"].append(skill)

        # ── Extract Years ────────────────────────────────────────────
        year_pattern = r'\b(19|20)\d{2}\b'
        years_found = [int(y) for y in re.findall(year_pattern, raw_text)]
        years_found = sorted(set(years_found), reverse=True)
        result["years"] = [
            y for y in years_found if 1980 <= y <= 2025
        ]

        # ── Extract Experience ───────────────────────────────────────
        exp_pattern = r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience)?'
        exp_matches = re.findall(exp_pattern, text_lower)
        if exp_matches:
            result["experience_years"] = int(exp_matches[0])

        # ── Extract Locations ────────────────────────────────────────
        telangana_cities = [
            "Hyderabad", "Warangal", "Nizamabad", "Karimnagar",
            "Khammam", "Ramagundam", "Secunderabad", "Nalgonda",
            "Adilabad", "Suryapet", "Miryalaguda", "Siddipet",
            "Mancherial", "Jagtial", "Kamareddy",
        ]
        indian_cities = [
            "Bangalore", "Mumbai", "Delhi", "Chennai", "Pune",
            "Kolkata", "Ahmedabad", "Jaipur", "Lucknow", "Noida",
            "Gurgaon", "Chandigarh", "Indore", "Coimbatore",
            "Visakhapatnam", "Vijayawada", "Tirupati",
        ]
        all_cities = telangana_cities + indian_cities
        for city in all_cities:
            if re.search(r'\b' + re.escape(city) + r'\b', raw_text, re.I):
                result["locations"].append(city)

        # ── Extract Organizations (simple heuristic) ─────────────────
        org_keywords = [
            "university", "institute", "college", "school",
            "technologies", "solutions", "pvt", "ltd", "inc",
            "corporation", "company", "foundation", "academy",
        ]
        for line in raw_text.split("\n"):
            line_stripped = line.strip()
            if any(kw in line_stripped.lower() for kw in org_keywords):
                clean = re.sub(r'[^\w\s\.\,\&]', '', line_stripped).strip()
                if 5 <= len(clean) <= 100 and clean not in result["organizations"]:
                    result["organizations"].append(clean)

        result["status"] = "success"

    except Exception as e:
        result["errors"].append(str(e))

    result["extraction_time"] = time.time() - start_time
    return result
