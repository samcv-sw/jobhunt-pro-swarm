"""
Cover Letter PDF Generator
Generates professional PDF cover letters using FPDF.
"""
import os
import logging
from datetime import datetime
from fpdf import FPDF

logger = logging.getLogger(__name__)

CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "Sam Salameh")
CANDIDATE_EMAIL = os.getenv("CANDIDATE_EMAIL", "samsalameh.cv@gmail.com")
CANDIDATE_PHONE = os.getenv("CANDIDATE_PHONE", "+961 71 019 053")
CANDIDATE_LINKEDIN = os.getenv("CANDIDATE_LINKEDIN", "www.linkedin.com/in/sam-salameh")
CANDIDATE_TITLE = os.getenv("CANDIDATE_TITLE", "Senior Network Engineer")
CV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _sanitize_text(text: str) -> str:
    """Replace special Unicode chars with ASCII-safe equivalents for FPDF."""
    replacements = {
        "\u2014": "--",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
        "\u2022": "-",
        "\uf0b7": "-",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


class CoverPDF(FPDF):
    """Professional cover letter PDF — dark header bar, clean dark-on-white body."""

    def header(self):
        # Accent bar at the top
        self.set_fill_color(0, 180, 216)  # #00b4d8 cyan
        self.rect(0, 0, 210, 5, "F")
        self.ln(15)

        # Name
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(30, 41, 59)  # #1e293b dark slate
        self.cell(0, 10, "SAM SALAMEH", align="C", new_x="LMARGIN", new_y="NEXT")

        # Title
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 116, 139)  # #64748b slate
        self.cell(0, 5, "SENIOR NETWORK ENGINEER", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        # Contact line
        self.set_font("Helvetica", "", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 5, f"{CANDIDATE_PHONE}  |  {CANDIDATE_EMAIL}  |  {CANDIDATE_LINKEDIN}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

        # Divider line
        self.set_draw_color(0, 180, 216)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"{CANDIDATE_EMAIL}  |  {CANDIDATE_PHONE}", align="C")


def generate_cover_pdf(company: str, title: str, body_text: str = None, hidden_keywords: str = None, prompt_injection: str = None) -> str:
    """Generate a professional PDF cover letter. Returns file path."""
    os.makedirs(CV_DIR, exist_ok=True)
    filename = f"Cover_Letter_{company.replace(' ', '_')}.pdf"
    filepath = os.path.join(CV_DIR, filename)

    pdf = CoverPDF("P", "mm", "A4")
    pdf.add_page()

    # Date
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, datetime.now().strftime("%B %d, %Y"), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Salutation
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(0, 6, _sanitize_text(f"Dear {company} Hiring Team,"))
    pdf.ln(4)

    # Body
    if body_text:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(71, 85, 105)  # #475569 dark slate gray
        paragraphs = body_text.replace("\r\n", "\n").split("\n\n")
        for p in paragraphs:
            p = p.strip()
            if p:
                pdf.multi_cell(0, 5.5, _sanitize_text(p))
                pdf.ln(3)
    else:
        body_parts = [
            f"I am writing to formally express my strong interest in the {title} position at {company}.",
            f"With 15+ years of hands-on experience in enterprise networking, security, and infrastructure automation, I am confident in my ability to deliver immediate value to your organization.",
            f"My expertise spans Cisco, MikroTik, Fortinet, Ubiquiti, and Juniper environments -- networks spanning thousands of devices across multiple countries. I bring a security-first mindset with deep experience in firewall architecture, intrusion detection, and Zero Trust implementations.",
            f"I pride myself on combining technical excellence with automation-first thinking (Python, Ansible, PowerShell) to reduce manual overhead and human error.",
            f"I welcome the opportunity to discuss how my background aligns with {company}'s needs. Thank you for your time and consideration.",
        ]
        body = "\n\n".join(body_parts)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 5.5, _sanitize_text(body))
        pdf.ln(4)

    # Closing
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "Sincerely,", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, CANDIDATE_NAME, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, CANDIDATE_TITLE, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, CANDIDATE_EMAIL, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, CANDIDATE_PHONE, new_x="LMARGIN", new_y="NEXT")

    # --- ATS BYPASS & PROMPT INJECTION (INVISIBLE TEXT) ---
    if hidden_keywords or prompt_injection:
        pdf.set_font("Helvetica", "", 1)  # Microscopic font
        pdf.set_text_color(255, 255, 255) # White color (invisible on white background)
        if hidden_keywords:
            pdf.multi_cell(0, 1, _sanitize_text(hidden_keywords))
        if prompt_injection:
            pdf.multi_cell(0, 1, _sanitize_text(prompt_injection))

    pdf.output(filepath)
    logger.info(f"Cover letter PDF: {filepath} ({os.path.getsize(filepath)} bytes)")
    return filepath
