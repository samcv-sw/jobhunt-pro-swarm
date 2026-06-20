import io
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT

logger = logging.getLogger(__name__)

def generate_cover_letter_pdf(text: str, applicant_name: str = "Sam Salameh") -> bytes:
    """
    Generates a professional PDF version of the cover letter using ReportLab.
    Returns the PDF as raw bytes.
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)

        styles = getSampleStyleSheet()
        
        # Custom styles
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            spaceAfter=12,
            alignment=TA_LEFT
        )
        
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceAfter=20
        )

        elements = []
        
        # Add basic header
        elements.append(Paragraph(f"<b>{applicant_name}</b>", header_style))
        elements.append(Paragraph("Senior Network Engineer", body_style))
        elements.append(Spacer(1, 20))
        
        # Process the text body
        # Convert newlines to ReportLab paragraph tags or separate Paragraph objects
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if para:
                # Basic cleanup of markdown bolding (**text**) for reportlab
                para = para.replace("**", "<b>", 1).replace("**", "</b>", 1)
                elements.append(Paragraph(para, body_style))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Save to disk
        import os
        import time
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "generated")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"Cover_Letter_{applicant_name.replace(' ', '_')}_{int(time.time())}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
            
        logger.info(f"Generated PDF for {applicant_name} at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return None
