import re
import spacy
import pytesseract
import PyPDF2
from PIL import Image
import csv

# Load English NLP model. We'll handle ModelNotFound by downloading it in requirements setup.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def load_skills(csv_path="skills.csv"):
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Flatten, lowercase, strip
            skills = []
            for row in reader:
                if row:
                    skills.append(row[0].strip().lower())
            return set(skills)
    except FileNotFoundError:
        return set()

def extract_text_from_image(image):
    """Extract text from a PIL Image using pytesseract."""
    text = pytesseract.image_to_string(image)
    return text

def extract_text_from_pdf(pdf_path):
    """Extract text directly from PDF using PyPDF2."""
    try:
        text = ""
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_entities(text):
    """Extract Name, Organization, Location using SpaCy."""
    doc = nlp(text)
    entities = {
        "Name": [],
        "Organization": [],
        "Location": []
    }
    
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["Name"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["Organization"].append(ent.text)
        elif ent.label_ == "GPE" or ent.label_ == "LOC":
            entities["Location"].append(ent.text)
            
    # Simple deduplication while preserving some order
    for key in entities:
        filtered = []
        for x in entities[key]:
            if x not in filtered:
                filtered.append(x)
        entities[key] = filtered
        
    # --- Conversational Dictation Fallbacks ---
    # If the user explicitly says "name is John" or "name: John", 
    # spaCy often misses the proper noun context.
    text_lower = text.lower()
    
    # Name Fallback
    if not entities["Name"]:
        name_match = re.search(r'(?:my\s+)?name\s*(?:is|:|-)\s*([a-zA-Z\s]+?)(?:(?:\.|,|\n|$)|(?:[a-z]+(?:\s+is|:|@)))', text_lower)
        if name_match:
            entities["Name"].append(name_match.group(1).strip().title())

    # Organization Fallback
    if not entities["Organization"]:
        org_match = re.search(r'(?:company|organization|education|school|college|university)\s*(?:is|:|-)\s*([a-zA-Z0-9\s&]+?)(?:(?:\.|,|\n|$)|(?:[a-z]+(?:\s+is|:|@)))', text_lower)
        if org_match:
            entities["Organization"].append(org_match.group(1).strip().title())

    # Location Fallback
    if not entities["Location"]:
        loc_match = re.search(r'(?:location|city|live in|from)\s*(?:is|:|-)?\s*([a-zA-Z\s]+?)(?:(?:\.|,|\n|$)|(?:[a-z]+(?:\s+is|:|@)))', text_lower)
        if loc_match:
            entities["Location"].append(loc_match.group(1).strip().title())
            
    return entities

def extract_contact_info(text):
    """Extract Email, Phone, and URLs using Regex."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    urls = re.findall(url_pattern, text)
    
    return {
        "Emails": list(set(emails)),
        "Phones": list(set(phones)),
        "URLs": list(set(urls))
    }

def match_skills(text, skills_list):
    """Match text against the provided skills list."""
    text_lower = text.lower()
    matched = []
    for skill in skills_list:
        # Simple string match or regex boundary match
        # Using word boundaries to avoid partial matches like "it" matching inside "with"
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            matched.append(skill)
    return list(set(matched))

def extract_all(text, skills_list):
    contact = extract_contact_info(text)
    entities = extract_entities(text)
    skills = match_skills(text, skills_list)
    
    return {
        "RawText": text,
        "ContactInfo": contact,
        "Entities": entities,
        "MatchedSkills": skills
    }
