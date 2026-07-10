import io
import logging
import re

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


def clean_xml_for_reportlab(text: str) -> str:
    """
    Cleans up HTML/Markdown text to make it fully compliant with ReportLab's Paragraph XML parser.
    Escapes unescaped special characters, cleans up markdown tags, and preserves valid HTML tags.
    """
    if not text:
        return ""

    # 1. First, convert markdown bold (**text**) to <b>text</b> globally
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    # 2. Convert markdown italic (*text*) to <i>text</i> globally
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)

    # 3. Escape ampersands, but avoid double-escaping already escaped ones
    # We match '&' only if it's not part of an existing entity like &amp;, &lt;, &gt;, &quot;, &apos;
    text = re.sub(r"&(?!([a-zA-Z0-9]+|#[0-9]+|#x[0-9a-fA-F]+);)", "&amp;", text)

    # 4. Preserve valid ReportLab XML tags by placeholder-ing them to avoid escaping them.
    # Allowed tags: b, i, u, font, br, link, a, and their closing counterparts.
    valid_tag_pattern = re.compile(
        r"(</?(?:b|i|u|a|link|font|br)(?:\s+[^>]*?)?/?>)", re.IGNORECASE
    )

    placeholders = []

    def save_tag(match):
        placeholders.append(match.group(1))
        return f"___TAG_PLACEHOLDER_{len(placeholders) - 1}___"

    text = valid_tag_pattern.sub(save_tag, text)

    # 5. Escape any remaining stray '<' and '>' to prevent XML parsing errors
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    # 6. Restore the valid tags
    for idx, tag in enumerate(placeholders):
        text = text.replace(f"___TAG_PLACEHOLDER_{idx}___", tag)

    return text


def generate_cover_letter_pdf(text: str, applicant_name: str = "Sam Salameh") -> bytes:
    """
    Generates a professional PDF version of the cover letter using ReportLab.
    Returns the PDF as raw bytes.
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            spaceAfter=12,
            alignment=TA_LEFT,
        )

        header_style = ParagraphStyle(
            "Header",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            spaceAfter=20,
        )

        elements = []

        # Add basic header
        elements.append(Paragraph(f"<b>{applicant_name}</b>", header_style))
        elements.append(Paragraph("Senior Network Engineer", body_style))
        elements.append(Spacer(1, 20))

        # Process the text body
        # Convert newlines to ReportLab paragraph tags or separate Paragraph objects
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if para:
                # Clean up XML tags for ReportLab safety
                clean_para = clean_xml_for_reportlab(para)
                elements.append(Paragraph(clean_para, body_style))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to disk
        import os
        import time

        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "generated"
        )
        os.makedirs(output_dir, exist_ok=True)
        filename = (
            f"Cover_Letter_{applicant_name.replace(' ', '_')}_{int(time.time())}.pdf"
        )
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        logger.info(f"Generated PDF for {applicant_name} at {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return None
