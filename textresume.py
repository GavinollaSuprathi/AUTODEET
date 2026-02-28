"""
test_resume.py
Generate a test PDF resume for demo purposes.
Uses only built-in Python + PyPDF2 (which has basic PDF creation via reportlab fallback).
This creates a simple text-based PDF without requiring reportlab.
"""


def create_test_resume():
    """Create a minimal valid PDF with resume text."""
    # We'll create a PDF manually using raw PDF syntax
    # This is a valid PDF file that PyPDF2 can read

    resume_text = """Rajesh Kumar Sharma
Email: rajesh.sharma@gmail.com
Phone: 9876543210
Address: Flat 301, Jubilee Hills, Hyderabad, Telangana 500033

OBJECTIVE
Experienced software developer seeking challenging roles in IT.

EDUCATION
B.Tech in Computer Science - JNTU Hyderabad - 2020
Intermediate - Narayana Junior College, Hyderabad - 2016
SSC - Kendriya Vidyalaya, Secunderabad - 2014

SKILLS
Python, Java, JavaScript, SQL, React, Django, Machine Learning,
Data Analysis, Git, AWS, Docker, Linux, Communication, Teamwork,
Problem Solving, Leadership, Time Management, Excel, Power BI

EXPERIENCE
Software Developer at TCS (2020 - 2023)
- Developed web applications using Python and Django
- Managed AWS cloud infrastructure
- Led a team of 5 developers

Intern at Infosys (2019 - 2020)
- Worked on data analysis projects
- Built dashboards using Power BI

CERTIFICATIONS
AWS Certified Solutions Architect
Google Cloud Professional Data Engineer

Aadhaar: 2345 6789 0123"""

    # Manually construct a valid PDF
    lines = resume_text.split('\n')

    # Build page content stream
    text_operations = []
    text_operations.append("BT")
    text_operations.append("/F1 11 Tf")
    y = 750
    for line in lines:
        # Escape special PDF characters
        safe_line = (
            line.replace('\\', '\\\\')
            .replace('(', '\\(')
            .replace(')', '\\)')
        )
        text_operations.append(f"1 0 0 1 50 {y} Tm")
        text_operations.append(f"({safe_line}) Tj")
        y -= 16
        if y < 50:
            break
    text_operations.append("ET")

    stream_content = "\n".join(text_operations)
    stream_bytes = stream_content.encode('latin-1')
    stream_length = len(stream_bytes)

    pdf_parts = []

    # Header
    pdf_parts.append(b"%PDF-1.4\n")

    # Object 1: Catalog
    obj1_offset = sum(len(p) for p in pdf_parts)
    pdf_parts.append(
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    )

    # Object 2: Pages
    obj2_offset = sum(len(p) for p in pdf_parts)
    pdf_parts.append(
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    )

    # Object 3: Page
    obj3_offset = sum(len(p) for p in pdf_parts)
    pdf_parts.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> "
        b">>\nendobj\n"
    )

    # Object 4: Content Stream
    obj4_offset = sum(len(p) for p in pdf_parts)
    pdf_parts.append(
        f"4 0 obj\n<< /Length {stream_length} >>\nstream\n".encode('latin-1')
    )
    pdf_parts.append(stream_bytes)
    pdf_parts.append(b"\nendstream\nendobj\n")

    # Object 5: Font
    obj5_offset = sum(len(p) for p in pdf_parts)
    pdf_parts.append(
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 "
        b"/BaseFont /Helvetica >>\nendobj\n"
    )

    # Cross-reference table
    xref_offset = sum(len(p) for p in pdf_parts)
    pdf_parts.append(b"xref\n")
    pdf_parts.append(b"0 6\n")
    pdf_parts.append(b"0000000000 65535 f \n")
    pdf_parts.append(f"{obj1_offset:010d} 00000 n \n".encode())
    pdf_parts.append(f"{obj2_offset:010d} 00000 n \n".encode())
    pdf_parts.append(f"{obj3_offset:010d} 00000 n \n".encode())
    pdf_parts.append(f"{obj4_offset:010d} 00000 n \n".encode())
    pdf_parts.append(f"{obj5_offset:010d} 00000 n \n".encode())

    # Trailer
    pdf_parts.append(
        f"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode()
    )

    pdf_bytes = b"".join(pdf_parts)

    filename = "test_resume_rajesh.pdf"
    with open(filename, "wb") as f:
        f.write(pdf_bytes)

    print(f"✅ Test resume created: {filename}")
    print(f"   Size: {len(pdf_bytes)} bytes")
    print(f"   Name: Rajesh Kumar Sharma")
    print(f"   Email: rajesh.sharma@gmail.com")
    print(f"   Phone: 9876543210")
    print(f"   Education: B.Tech")
    print(f"   Skills: Python, Java, JavaScript, SQL, React, etc.")
    print(f"\n   Upload this file in AutoDEET to test resume parsing!")


if __name__ == "__main__":
    create_test_resume()
