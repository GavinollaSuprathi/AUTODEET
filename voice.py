import re

LANGUAGE_MAP = {
    "English": "en-US",
    "Hindi": "hi-IN",
    "Telugu": "te-IN",
}

PROMPTS = {
    "name": {
        "English": "Please say your full name",
        "Hindi": "कृपया अपना पूरा नाम बोलें",
        "Telugu": "దయచేసి మీ పూర్తి పేరు చెప్పండి",
    },
    "phone": {
        "English": "Please say your 10-digit phone number",
        "Hindi": "कृपया अपना 10 अंकों का फोन नंबर बोलें",
        "Telugu": "దయచేసి మీ 10 అంకెల ఫోన్ నంబర్ చెప్పండి",
    },
    "email": {
        "English": "Please say your email address",
        "Hindi": "कृपया अपना ईमेल पता बोलें",
        "Telugu": "దయచేసి మీ ఈమెయిల్ చిరునామా చెప్పండి",
    },
    "gender": {
        "English": "Please say your gender: Male, Female, or Other",
        "Hindi": "कृपया अपना लिंग बोलें: पुरुष, महिला, या अन्य",
        "Telugu": "దయచేసి మీ లింగం చెప్పండి: పురుషుడు, స్త్రీ, లేదా ఇతర",
    },
    "education": {
        "English": "Please say your highest education qualification",
        "Hindi": "कृपया अपनी उच्चतम शिक्षा योग्यता बोलें",
        "Telugu": "దయచేసి మీ అత్యున్నత విద్యార్హత చెప్పండి",
    },
    "skills": {
        "English": "Please say your skills, separated by commas",
        "Hindi": "कृपया अपने कौशल बोलें, अल्पविराम से अलग करें",
        "Telugu": "దయచేసి మీ నైపుణ్యాలు చెప్పండి, కామాలతో వేరు చేయండి",
    },
    "location": {
        "English": "Please say your preferred job location",
        "Hindi": "कृपया अपना पसंदीदा नौकरी स्थान बोलें",
        "Telugu": "దయచేసి మీ ఇష్టపడే ఉద్యోగ ప్రదేశం చెప్పండి",
    },
}


def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import speech_recognition
        return True, "All dependencies available"
    except ImportError:
        pass

    # Even without speech_recognition, we can use OpenAI Whisper API
    try:
        import openai
        return True, "OpenAI available for Whisper API"
    except ImportError:
        pass

    return True, (
        "Basic mode available. For better results install: "
        "pip install SpeechRecognition openai"
    )


def get_audio_recorder():
    """Get the audio recorder function."""
    try:
        from audio_recorder_streamlit import audio_recorder
        return audio_recorder
    except ImportError:
        return None


def get_prompt(field_key, language="English"):
    """Get the voice prompt for a field."""
    return PROMPTS.get(field_key, {}).get(language, f"Please say your {field_key}")


def transcribe_audio(audio_bytes, language="English", api_key=None):
    """
    Transcribe audio bytes to text.
    Tries OpenAI Whisper API first (if key provided),
    then falls back to Google Speech Recognition.
    """
    result = {"status": "error", "text": "", "message": ""}

    if not audio_bytes:
        result["message"] = "No audio received"
        return result

    # ── Method 1: OpenAI Whisper API ─────────────────────────────────
    if api_key:
        try:
            import openai
            import tempfile
            import os

            client = openai.OpenAI(api_key=api_key)

            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=LANGUAGE_MAP.get(language, "en")[:2],
                )

            os.unlink(tmp_path)

            if transcript.text:
                result["status"] = "success"
                result["text"] = transcript.text
                return result
        except Exception as e:
            result["message"] = f"Whisper API error: {str(e)}"
            # Fall through to next method

    # ── Method 2: Google Speech Recognition ──────────────────────────
    try:
        import speech_recognition as sr
        import io

        recognizer = sr.Recognizer()

        audio_io = io.BytesIO(audio_bytes)

        try:
            with sr.AudioFile(audio_io) as source:
                audio_data = recognizer.record(source)
        except Exception:
            # Try saving as WAV first
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            with sr.AudioFile(tmp_path) as source:
                audio_data = recognizer.record(source)
            os.unlink(tmp_path)

        lang_code = LANGUAGE_MAP.get(language, "en-US")
        text = recognizer.recognize_google(
            audio_data, language=lang_code
        )

        result["status"] = "success"
        result["text"] = text
        return result

    except ImportError:
        result["message"] = (
            "Install SpeechRecognition: pip install SpeechRecognition"
        )
    except Exception as e:
        result["message"] = f"Speech recognition error: {str(e)}"

    return result


# ─── Post-Processing Functions ───────────────────────────────────────────

def post_process_name(text):
    """Clean up a spoken name."""
    name = re.sub(r'[^a-zA-Z\s\.]', '', text)
    name = " ".join(name.split())
    return name.title().strip()


def post_process_phone(text):
    """Extract phone number from spoken text."""
    # Map spoken words to digits
    word_to_digit = {
        "zero": "0", "one": "1", "two": "2", "three": "3",
        "four": "4", "five": "5", "six": "6", "seven": "7",
        "eight": "8", "nine": "9", "oh": "0", "o": "0",
        "to": "2", "too": "2", "for": "4", "won": "1",
        "tree": "3", "ate": "8", "niner": "9",
        "double": "", "triple": "",
    }

    text_lower = text.lower()

    # Handle "double X" → "XX"
    text_lower = re.sub(
        r'double\s+(\w+)',
        lambda m: (word_to_digit.get(m.group(1), m.group(1))) * 2,
        text_lower,
    )
    text_lower = re.sub(
        r'triple\s+(\w+)',
        lambda m: (word_to_digit.get(m.group(1), m.group(1))) * 3,
        text_lower,
    )

    # Replace words with digits
    for word, digit in word_to_digit.items():
        text_lower = re.sub(r'\b' + word + r'\b', digit, text_lower)

    # Extract only digits
    digits = re.sub(r'[^\d]', '', text_lower)

    # Take last 10 digits
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def post_process_email(text):
    """Clean up a spoken email address."""
    email = text.lower().strip()

    replacements = {
        " at the rate ": "@",
        " at the rate of ": "@",
        " at ": "@",
        " at sign ": "@",
        " dot ": ".",
        " period ": ".",
        " underscore ": "_",
        " hyphen ": "-",
        " dash ": "-",
        " space ": "",
        " ": "",
    }

    for spoken, symbol in replacements.items():
        email = email.replace(spoken, symbol)

    # Remove remaining spaces
    email = email.replace(" ", "")

    return email


def post_process_gender(text):
    """Map spoken text to gender option."""
    text_lower = text.lower().strip()

    if any(w in text_lower for w in ["male", "man", "boy", "purush", "పురుషుడు"]):
        if "female" in text_lower or "woman" in text_lower:
            return "Female"
        return "Male"
    if any(w in text_lower for w in ["female", "woman", "girl", "mahila", "స్త్రీ"]):
        return "Female"
    if any(w in text_lower for w in ["trans", "transgender"]):
        return "Transgender"
    if any(w in text_lower for w in ["other", "anya", "ఇతర"]):
        return "Other"

    return text.strip().title()


def post_process_education(text):
    """Map spoken text to education option."""
    text_lower = text.lower().strip()

    mapping = {
        "phd": "PhD",
        "doctorate": "PhD",
        "post graduate": "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)",
        "postgraduate": "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)",
        "masters": "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)",
        "mtech": "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)",
        "m tech": "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)",
        "mba": "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)",
        "mca": "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)",
        "msc": "Post Graduate (M.Tech/ME/MBA/MCA/MSc/MA/MCom)",
        "undergraduate": "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)",
        "bachelors": "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)",
        "bachelor": "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)",
        "btech": "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)",
        "b tech": "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)",
        "degree": "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)",
        "graduation": "Undergraduate (B.Tech/BE/BBA/BCA/BSc/BA/BCom)",
        "diploma": "Diploma",
        "intermediate": "Intermediate/12th",
        "12th": "Intermediate/12th",
        "inter": "Intermediate/12th",
        "plus two": "Intermediate/12th",
        "ssc": "SSC/10th",
        "10th": "SSC/10th",
        "tenth": "SSC/10th",
        "matriculation": "SSC/10th",
        "iti": "ITI",
        "below 10th": "Below 10th",
        "below tenth": "Below 10th",
    }

    for keyword, education_level in mapping.items():
        if keyword in text_lower:
            return education_level

    return None


def post_process_skills(text):
    """Extract skills from spoken text."""
    # Split by common delimiters
    raw_skills = re.split(r'[,;]|\band\b|\balso\b', text)
    skills = []

    for skill in raw_skills:
        cleaned = skill.strip().title()
        if len(cleaned) >= 2:
            skills.append(cleaned)

    return skills
