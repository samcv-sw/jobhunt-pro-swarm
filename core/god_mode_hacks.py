import logging
from typing import Optional

logger = logging.getLogger(__name__)

def inject_stealth_payload(html: str, company: str, job_title: str) -> str:
    """
    🇨🇳 The 'Stealth Payload' (Chinese ATS Hack)
    Injects massive blocks of ATS-friendly keywords as an invisible, zero-opacity
    div. Modern ATS parsers strip HTML but read the raw text. This guarantees
    a near 100% keyword match for screening algorithms.
    """
    logger.info(f"[GOD MODE] Injecting ATS Stealth Payload for {company}")
    
    # Generate generic highly-ranked keywords for the role
    # In a fully scaled app, this would query a database of ATS keywords per job title
    keywords = f"{job_title} {company} Agile Scrum Python CI/CD Docker Kubernetes Leadership Architecture Microservices Cloud AWS Azure GCP Scalability Cross-functional System Design Machine Learning Optimization Performance Strategy Innovation Collaboration Execution Ownership Enterprise Delivery " * 10
    
    stealth_div = f"""
    <div style="width:0px;height:0px;overflow:hidden;opacity:0;font-size:1px;color:#ffffff;display:none;" aria-hidden="true">
        {keywords}
    </div>
    """
    
    # Inject right before the closing body tag, or append if no body tag
    if "</body>" in html:
        return html.replace("</body>", f"{stealth_div}\n</body>")
    return html + stealth_div


def inject_bgp_hijack_spoof(html: str, company: str, ceo_name: str = "CEO") -> str:
    """
    🇷🇺 The 'BGP Hijack' Forward Spoof (Russian/Grey-Hat Hack)
    Spoofs the visual appearance of an internal corporate forward. 
    By faking the Outlook forwarding header, the recipient assumes this email
    was passed down from their CEO or a senior executive, completely bypassing
    their psychological spam filter.
    """
    logger.info(f"[GOD MODE] Injecting BGP Hijack Spoof for {company}")
    
    forward_header = f"""
    <div style="font-family: Calibri, Arial, sans-serif; font-size: 11pt; color: #000000;">
        <p>Please review this candidate. Looks like a strong fit for the open req.</p>
        <p>- {ceo_name}</p>
    </div>
    <div style="border:none;border-top:solid #E1E1E1 1.0pt;padding:3.0pt 0in 0in 0in; margin-top: 15px;">
        <p style="font-family: Calibri, Arial, sans-serif; font-size: 10pt; color: #000000; margin: 0;">
            <b>From:</b> Applicant Tracking System &lt;no-reply@{company.lower().replace(' ', '')}.com&gt;<br>
            <b>Sent:</b> Just now<br>
            <b>To:</b> {ceo_name} &lt;{ceo_name.lower().split()[0]}@{company.lower().replace(' ', '')}.com&gt;<br>
            <b>Subject:</b> Candidate Submission
        </p>
    </div>
    <br>
    """
    
    # We prefix the HTML body with this fake header
    # If the html already has a <body> tag, inject inside it
    if "<body>" in html:
        return html.replace("<body>", f"<body>\n{forward_header}")
    return forward_header + html


def get_bgp_hijack_subject(original_subject: str) -> str:
    """Modifies the subject to look like an internal forward."""
    return f"Fwd: RE: {original_subject}"


def generate_proof_of_work_link(company: str, candidate_name: str) -> str:
    """
    🇺🇸 The 'Pre-Crime' Predictive Pitch (Silicon Valley Hack)
    Generates a dynamic URL that looks incredibly tailored.
    When the user clicks it, they expect a custom audit, which forces them 
    to engage with the candidate's portfolio.
    """
    safe_company = company.lower().replace(" ", "-").replace(".", "")
    safe_name = candidate_name.lower().replace(" ", "")
    return f"https://github.com/{safe_name}/infrastructure-audit-{safe_company}-2026"
