"""
fraud_checker.py
Fraud detection scoring + Profile health/completeness score
"""

import re
from typing import Dict, List, Any, Tuple


# ─── Disposable Email Domains ───────────────────────────────────────────────
DISPOSABLE_DOMAINS = {
    'tempmail.com', 'throwaway.email', 'guerrillamail.com',
    'mailinator.com', 'yopmail.com', 'temp-mail.org',
    'fakeinbox.com', 'sharklasers.com', 'guerrillamail.info',
    'grr.la', 'guerrillamail.de', 'tmail.com', 'tempail.com',
    'dispostable.com', 'trashmail.com', 'trashmail.me',
    'trashmail.net', 'maildrop.cc', 'mailnesia.com',
    'mailcatch.com', 'tempr.email', 'discard.email',
    'tempmailo.com', 'mohmal.com', 'burnermail.io',
    'temp-mail.io', 'emailondeck.com', 'mintemail.com',
    'getnada.com', 'jetable.org', 'throwawaymail.com',
    '10minutemail.com', 'tempinbox.com', 'spambox.us',
    'mytemp.email', 'binkmail.com', 'safetymail.info',
}


def check_phone_fraud(phone: str) -> Tuple[bool, List[str]]:
    """
    Validate phone number.
    Returns (is_valid, list_of_issues)
    """
    issues = []

    if not phone:
        return True, []  # Empty is not fraud, just incomplete

    # Remove spaces/dashes
    phone_clean = re.sub(r'[\s\-]', '', phone)

    # Must be 10 digits
    if len(phone_clean) != 10:
        issues.append(
            f"Phone number must be exactly 10 digits (got {len(phone_clean)})"
        )

    # Must be all digits
    if not phone_clean.isdigit():
        issues.append("Phone number contains non-numeric characters")
        return False, issues

    # Must start with 6-9
    if phone_clean[0] not in '6789':
        issues.append(
            f"Indian phone numbers must start with 6-9 (starts with {phone_clean[0]})"
        )

    # Not all same digits (e.g., 9999999999)
    if len(set(phone_clean)) == 1:
        issues.append("Phone number has all identical digits — likely fake")

    # Not sequential (1234567890 or 9876543210)
    sequential_asc = ''.join(str(i % 10) for i in range(
        int(phone_clean[0]), int(phone_clean[0]) + 10
    ))
    if phone_clean == sequential_asc:
        issues.append("Phone number is a sequential pattern — likely fake")

    sequential_desc = ''.join(str(i % 10) for i in range(
        int(phone_clean[0]), int(phone_clean[0]) - 10, -1
    ))
    if phone_clean == sequential_desc:
        issues.append("Phone number is a reverse sequential pattern — likely fake")

    # Common fake patterns
    fake_patterns = [
        '1234567890', '0987654321', '1111111111', '0000000000',
        '9876543210', '1234512345', '9999999999', '8888888888',
        '7777777777', '6666666666',
    ]
    if phone_clean in fake_patterns:
        issues.append("Phone number matches a known fake pattern")

    is_valid = len(issues) == 0
    return is_valid, issues


def check_email_fraud(email: str) -> Tuple[bool, List[str]]:
    """
    Validate email address.
    Returns (is_valid, list_of_issues)
    """
    issues = []

    if not email:
        return True, []

    email = email.strip().lower()

    # Basic format check
    email_pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        issues.append("Email format is invalid")

    # Check for disposable domain
    try:
        domain = email.split('@')[1]
        if domain in DISPOSABLE_DOMAINS:
            issues.append(
                f"Disposable/temporary email domain detected: {domain}"
            )

        # Check domain has at least one dot
        if '.' not in domain:
            issues.append("Email domain is invalid (no TLD)")

        # Check for suspicious patterns in local part
        local = email.split('@')[0]
        if len(local) < 2:
            issues.append("Email local part is too short")
        if len(local) > 64:
            issues.append("Email local part is too long")

        # All numbers in local part
        if local.isdigit() and len(local) > 8:
            issues.append("Email local part is all numbers — potentially auto-generated")

    except (IndexError, AttributeError):
        issues.append("Email format is malformed")

    is_valid = len(issues) == 0
    return is_valid, issues


def check_aadhaar_fraud(aadhaar: str) -> Tuple[bool, List[str]]:
    """
    Validate Aadhaar number (basic checks).
    Returns (is_valid, list_of_issues)
    """
    issues = []

    if not aadhaar:
        return True, []

    aadhaar_clean = re.sub(r'\s', '', aadhaar)

    # Must be 12 digits
    if len(aadhaar_clean) != 12:
        issues.append(
            f"Aadhaar must be 12 digits (got {len(aadhaar_clean)})"
        )

    if not aadhaar_clean.isdigit():
        issues.append("Aadhaar contains non-numeric characters")
        return False, issues

    # Cannot start with 0 or 1
    if aadhaar_clean[0] in '01':
        issues.append("Aadhaar number cannot start with 0 or 1")

    # Not all same digits
    if len(set(aadhaar_clean)) == 1:
        issues.append("Aadhaar has all identical digits — likely fake")

    # Not sequential
    if aadhaar_clean == '123456789012' or aadhaar_clean == '210987654321':
        issues.append("Aadhaar is a sequential pattern — likely fake")

    is_valid = len(issues) == 0
    return is_valid, issues


def check_name_fraud(name: str) -> Tuple[bool, List[str]]:
    """
    Validate name.
    Returns (is_valid, list_of_issues)
    """
    issues = []

    if not name:
        return True, []

    name = name.strip()

    # Too short
    if len(name) < 2:
        issues.append("Name is too short (less than 2 characters)")

    # Too long
    if len(name) > 100:
        issues.append("Name is unusually long (more than 100 characters)")

    # Contains numbers
    if any(c.isdigit() for c in name):
        issues.append("Name contains numbers — likely invalid")

    # Contains special characters (except spaces, dots, hyphens, apostrophes)
    if re.search(r'[^a-zA-Z\s.\-\'\u0C00-\u0C7F\u0900-\u097F]', name):
        issues.append("Name contains unusual special characters")

    # All same character
    if len(set(name.replace(' ', ''))) <= 1:
        issues.append("Name has all identical characters — likely fake")

    # Common test names
    test_names = [
        'test', 'testing', 'asdf', 'qwerty', 'abc', 'xyz',
        'name', 'your name', 'full name', 'n/a', 'na', 'none',
        'null', 'undefined', 'admin', 'user',
    ]
    if name.lower() in test_names:
        issues.append(f"Name '{name}' appears to be a test/placeholder value")

    is_valid = len(issues) == 0
    return is_valid, issues


def check_skills_fraud(skills: list) -> Tuple[bool, List[str]]:
    """Check skills for spam patterns."""
    issues = []

    if not skills:
        return True, []

    if len(skills) > 50:
        issues.append(
            f"Too many skills listed ({len(skills)}) — possible spam"
        )

    # Check for duplicate skills
    seen = set()
    dupes = []
    for s in skills:
        s_lower = s.lower().strip()
        if s_lower in seen:
            dupes.append(s)
        seen.add(s_lower)
    if dupes:
        issues.append(f"Duplicate skills found: {', '.join(dupes)}")

    is_valid = len(issues) == 0
    return is_valid, issues


def check_experience_fraud(years: int, months: int = 0) -> Tuple[bool, List[str]]:
    """Check experience for unrealistic values."""
    issues = []

    total = years + months / 12.0

    if total > 50:
        issues.append(
            f"Experience of {years}y {months}m ({total:.1f} years) is unrealistic"
        )

    if total > 40:
        issues.append(
            f"Experience of {total:.1f} years is unusually high — please verify"
        )

    is_valid = len(issues) == 0
    return is_valid, issues


def run_fraud_check(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all fraud checks on the form data.
    Returns comprehensive fraud report with risk score.
    """
    report = {
        "risk_score": 0,
        "risk_level": "LOW",
        "risk_color": "green",
        "total_checks": 0,
        "passed_checks": 0,
        "failed_checks": 0,
        "flags": [],
        "details": {},
    }

    all_issues = []

    # 1. Phone check
    phone_valid, phone_issues = check_phone_fraud(
        form_data.get("phone", "")
    )
    report["details"]["phone"] = {
        "valid": phone_valid,
        "issues": phone_issues
    }
    if form_data.get("phone"):
        report["total_checks"] += 1
        if phone_valid:
            report["passed_checks"] += 1
        else:
            report["failed_checks"] += 1
            all_issues.extend(phone_issues)

    # 2. Email check
    email_valid, email_issues = check_email_fraud(
        form_data.get("email", "")
    )
    report["details"]["email"] = {
        "valid": email_valid,
        "issues": email_issues
    }
    if form_data.get("email"):
        report["total_checks"] += 1
        if email_valid:
            report["passed_checks"] += 1
        else:
            report["failed_checks"] += 1
            all_issues.extend(email_issues)

    # 3. Aadhaar check
    aadhaar_valid, aadhaar_issues = check_aadhaar_fraud(
        form_data.get("aadhaar", "")
    )
    report["details"]["aadhaar"] = {
        "valid": aadhaar_valid,
        "issues": aadhaar_issues
    }
    if form_data.get("aadhaar"):
        report["total_checks"] += 1
        if aadhaar_valid:
            report["passed_checks"] += 1
        else:
            report["failed_checks"] += 1
            all_issues.extend(aadhaar_issues)

    # 4. Name check
    name_valid, name_issues = check_name_fraud(
        form_data.get("name", "")
    )
    report["details"]["name"] = {
        "valid": name_valid,
        "issues": name_issues
    }
    if form_data.get("name"):
        report["total_checks"] += 1
        if name_valid:
            report["passed_checks"] += 1
        else:
            report["failed_checks"] += 1
            all_issues.extend(name_issues)

    # 5. Skills check
    skills_valid, skills_issues = check_skills_fraud(
        form_data.get("skills", [])
    )
    report["details"]["skills"] = {
        "valid": skills_valid,
        "issues": skills_issues
    }
    if form_data.get("skills"):
        report["total_checks"] += 1
        if skills_valid:
            report["passed_checks"] += 1
        else:
            report["failed_checks"] += 1
            all_issues.extend(skills_issues)

    # 6. Experience check
    exp_years = form_data.get("experience_years", 0)
    exp_months = form_data.get("experience_months", 0)
    exp_valid, exp_issues = check_experience_fraud(exp_years, exp_months)
    report["details"]["experience"] = {
        "valid": exp_valid,
        "issues": exp_issues
    }
    report["total_checks"] += 1
    if exp_valid:
        report["passed_checks"] += 1
    else:
        report["failed_checks"] += 1
        all_issues.extend(exp_issues)

    report["flags"] = all_issues

    # Calculate risk score
    if report["total_checks"] > 0:
        risk_pct = (report["failed_checks"] / report["total_checks"]) * 100
    else:
        risk_pct = 0

    # Add weight for severity
    severity_boost = 0
    for issue in all_issues:
        if 'fake' in issue.lower() or 'spam' in issue.lower():
            severity_boost += 10
        elif 'disposable' in issue.lower():
            severity_boost += 15
        elif 'test' in issue.lower() or 'placeholder' in issue.lower():
            severity_boost += 10

    risk_pct = min(100, risk_pct + severity_boost)
    report["risk_score"] = round(risk_pct, 1)

    if risk_pct < 30:
        report["risk_level"] = "LOW"
        report["risk_color"] = "green"
    elif risk_pct < 60:
        report["risk_level"] = "MEDIUM"
        report["risk_color"] = "orange"
    else:
        report["risk_level"] = "HIGH"
        report["risk_color"] = "red"

    return report


def calculate_health_score(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate profile completeness / health score.
    Returns score 0-100 with breakdown and tips.
    """
    score = 0
    max_score = 100
    breakdown = []
    tips = []

    # Name: +5
    if form_data.get("name") and len(str(form_data["name"]).strip()) > 1:
        score += 5
        breakdown.append(("✅ Full Name", 5))
    else:
        breakdown.append(("❌ Full Name", 0))
        tips.append("Add your full name to improve your profile")

    # Phone: +5
    if form_data.get("phone") and len(str(form_data["phone"]).strip()) >= 10:
        score += 5
        breakdown.append(("✅ Phone Number", 5))
    else:
        breakdown.append(("❌ Phone Number", 0))
        tips.append("Add a valid 10-digit phone number")

    # Email: +5
    if form_data.get("email") and '@' in str(form_data["email"]):
        score += 5
        breakdown.append(("✅ Email Address", 5))
    else:
        breakdown.append(("❌ Email Address", 0))
        tips.append("Add your email address")

    # Profile Image: +5
    if form_data.get("profile_image"):
        score += 5
        breakdown.append(("✅ Profile Image", 5))
    else:
        breakdown.append(("❌ Profile Image", 0))
        tips.append("Upload a profile photo to stand out")

    # Education: +10
    if form_data.get("education") and form_data["education"] != "":
        score += 10
        breakdown.append(("✅ Education Qualification", 10))
    else:
        breakdown.append(("❌ Education Qualification", 0))
        tips.append("Select your highest education qualification")

    # Institution: +5
    if form_data.get("institution_name") and len(
        str(form_data["institution_name"]).strip()
    ) > 2:
        score += 5
        breakdown.append(("✅ Institution Details", 5))
    else:
        breakdown.append(("❌ Institution Details", 0))
        tips.append("Add your institution/college name")

    # Year: +5
    if form_data.get("year_passed"):
        score += 5
        breakdown.append(("✅ Year of Passing", 5))
    else:
        breakdown.append(("❌ Year of Passing", 0))
        tips.append("Select your year of passing")

    # Skills (5+): +15
    skills = form_data.get("skills", [])
    if len(skills) >= 5:
        score += 15
        breakdown.append(("✅ Skills (5+ added)", 15))
    elif len(skills) > 0:
        partial = int(15 * len(skills) / 5)
        score += partial
        breakdown.append((f"⚠️ Skills ({len(skills)}/5 minimum)", partial))
        tips.append(f"Add {5 - len(skills)} more skills (minimum 5 required)")
    else:
        breakdown.append(("❌ Skills (none added)", 0))
        tips.append("Add at least 5 skills — this is required")

    # Job Preferences: +10
    has_location = bool(form_data.get("preferred_locations"))
    has_functions = bool(form_data.get("job_functions"))
    if has_location and has_functions:
        score += 10
        breakdown.append(("✅ Job Preferences", 10))
    elif has_location or has_functions:
        score += 5
        breakdown.append(("⚠️ Job Preferences (partial)", 5))
        if not has_location:
            tips.append("Select your preferred job locations")
        if not has_functions:
            tips.append("Select interested job functions")
    else:
        breakdown.append(("❌ Job Preferences", 0))
        tips.append("Add job location and function preferences")

    # Experience: +10
    if (
        form_data.get("experience_years", 0) > 0
        or form_data.get("is_fresher", False)
        or form_data.get("experience_entries")
    ):
        score += 10
        breakdown.append(("✅ Experience Details", 10))
    else:
        breakdown.append(("❌ Experience Details", 0))
        tips.append("Add your experience details or mark as fresher")

    # Address/Location: +5
    if form_data.get("preferred_locations"):
        score += 5
        breakdown.append(("✅ Location/Address", 5))
    else:
        breakdown.append(("❌ Location/Address", 0))
        tips.append("Select at least one preferred location")

    # Resume uploaded: +10
    if form_data.get("resume_uploaded"):
        score += 10
        breakdown.append(("✅ Resume Uploaded", 10))
    else:
        breakdown.append(("❌ Resume Uploaded", 0))
        tips.append("Upload your resume PDF for better visibility")

    # Documents: +10
    doc_count = 0
    if form_data.get("identity_card"):
        doc_count += 1
    for i in range(1, 4):
        if form_data.get(f"certificate_{i}"):
            doc_count += 1
    if doc_count > 0:
        doc_score = min(10, doc_count * 3)
        score += doc_score
        breakdown.append((f"✅ Documents ({doc_count} uploaded)", doc_score))
    else:
        breakdown.append(("❌ Documents (none uploaded)", 0))
        tips.append("Upload identity card and certificates for verification")

    # Clamp
    score = min(score, max_score)

    # Determine grade
    if score >= 90:
        grade = "Excellent"
        grade_color = "green"
        grade_emoji = "🌟"
    elif score >= 70:
        grade = "Good"
        grade_color = "blue"
        grade_emoji = "👍"
    elif score >= 50:
        grade = "Average"
        grade_color = "orange"
        grade_emoji = "⚠️"
    else:
        grade = "Needs Improvement"
        grade_color = "red"
        grade_emoji = "❗"

    return {
        "score": score,
        "max_score": max_score,
        "percentage": score,
        "breakdown": breakdown,
        "tips": tips,
        "grade": grade,
        "grade_color": grade_color,
        "grade_emoji": grade_emoji,
    }
