import re

def calculate_fraud_risk(extracted_data):
    """
    Evaluate constraints:
    - Phone length != 10 (excluding special chars/country code) -> flag fraud
    - Experience years > age -> flag fraud (Need to infer experience or age, MVP logic might just check basic anomalies)
    - Skills count > 50 -> flag spam
    - Invalid email structure -> flag fraud
    """
    reasons = []
    risk = "Low"
    
    # 1. Phone check
    phones = extracted_data.get("ContactInfo", {}).get("Phones", [])
    if phones:
        for phone in phones:
            # strip non-digits to check length
            digits = re.sub(r'\D', '', phone)
            # Allowing for 10 or 11 (with country code 1) or 12 (+91 etc)
            # If standard 10 digit, but length is strange like 5 or 15+ digits
            if len(digits) < 10 or len(digits) > 13:
                reasons.append(f"Suspicious phone length: {phone}")
                risk = "High"
    
    # 2. Email invalid structure check
    # Regex in extractor already guarantees basic email form, but let's check for weird domains 
    emails = extracted_data.get("ContactInfo", {}).get("Emails", [])
    if emails:
        for email in emails:
            if email.count('@') > 1 or ".." in email:
                reasons.append(f"Invalid email structure: {email}")
                risk = "High"

    # 3. Skills count check
    skills = extracted_data.get("MatchedSkills", [])
    if len(skills) > 50:
        reasons.append("Skills count exceeds 50 (Possible Spam)")
        if risk == "Low":
            risk = "Medium"
            
    # MVP hack: Experience > age is hard without explicit parsing of dates. 
    # For now, we will flag empty name but with extensive skills
    names = extracted_data.get("Entities", {}).get("Name", [])
    if not names and len(skills) > 10:
        reasons.append("No Name extracted but high skills count")
        risk = "Medium"
        
    return {
        "RiskLevel": risk,
        "Reasons": reasons
    }

def calculate_health_score(extracted_data):
    """
    Resume Health Score:
    Email (+10), Phone (+10), Education (+20), Skills (+20)
    We will map Education to having 'Organization' or basic keyword matches.
    Max Score = 100
    """
    score = 40 # Base score for having a parseable resume
    
    contact_info = extracted_data.get("ContactInfo", {})
    if contact_info.get("Emails"):
        score += 10
    if contact_info.get("Phones"):
        score += 10
        
    if extracted_data.get("MatchedSkills"):
        score += 20
        
    # Education heuristic: finding universities or degrees in 'Organization'
    orgs = extracted_data.get("Entities", {}).get("Organization", [])
    edu_keywords = ["university", "college", "institute", "school", "academy", "b.tech", "bsc", "msc", "phd"]
    raw_text = extracted_data.get("RawText", "").lower()
    
    has_education = False
    for org in orgs:
        if any(keyword in org.lower() for keyword in edu_keywords):
            has_education = True
            break
            
    if not has_education:
        has_education = any(keyword in raw_text for keyword in edu_keywords)
        
    if has_education:
        score += 20
        
    return min(100, score)
