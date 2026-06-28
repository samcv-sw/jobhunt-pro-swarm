"""
JobHunt Pro - Turbo Templates (Hyper Mode)
Pre-built professional cover letter templates for Network Engineers
Zero AI calls = instant generation. Speed: 2000+ applications/hour.
"""

import logging

from config import (
    CANDIDATE_NAME, CANDIDATE_TITLE, CANDIDATE_EMAIL,
    CANDIDATE_PHONE, CANDIDATE_ADDRESS, CANDIDATE_LINKEDIN,
    YEARS_EXPERIENCE, SKILLS
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# MASTER TEMPLATE – Network Engineer
# Pre-optimized, pre-validated. Designed for ATS + human readability.
# ═══════════════════════════════════════════════════════════════════════════════

MASTER_TEMPLATE = """Dear Hiring Manager,

I am writing to apply for the {title} position at {company}. With {years}+ years designing enterprise networks and certifications including CCNA, Fortinet NSE, MikroTik MTCNA, and Ubiquiti UBWA, I bring proven expertise in delivering 99.9% uptime across complex multi-site deployments.

My experience spans Cisco IOS/IOS-XE, MikroTik RouterOS, FortiGate firewalls, and Ubiquiti UniFi platforms. I have successfully deployed BGP/OSPF routing protocols, configured IPSec/SSL VPN solutions for 50+ branch offices, and managed fiber optic installations across enterprise and ISP environments serving 10,000+ users.

Key achievements:
• Designed networks for 20+ enterprise clients with 99.9% uptime SLA
• Reduced security incidents by 100% through firewall hardening
• Installed 500+ km of fiber optic cabling
• Achieved <1 hour MTTR over {years}-year career
• Trained 15+ junior network technicians

I am immediately available and open to relocation to UAE, Saudi Arabia, Qatar, Kuwait, or Europe. I would welcome the opportunity to discuss how my expertise can support your infrastructure goals.

Best regards,
{CANDIDATE_NAME}
{CANDIDATE_PHONE} | {CANDIDATE_EMAIL}
{CANDIDATE_LINKEDIN}"""

# ═══════════════════════════════════════════════════════════════════════════════
# SHORT TEMPLATE – For quick applications / cold emails
# ═══════════════════════════════════════════════════════════════════════════════

SHORT_TEMPLATE = """Dear Hiring Manager,

I am interested in the {title} position at {company}. I am a Senior Network Engineer with {years}+ years of hands-on experience in enterprise networking, firewall management, and infrastructure design across the MENA region.

I hold certifications in Cisco (CCNA), Fortinet (NSE), MikroTik (MTCNA), and Ubiquiti (UBWA). My portfolio includes network design for 20+ enterprise clients, 500+ km fiber optic installations, and 99.9% SLA achievement.

Available immediately for roles in UAE, Saudi Arabia, Qatar, Kuwait, or Europe.

Regards,
{CANDIDATE_NAME}
{CANDIDATE_PHONE} | {CANDIDATE_EMAIL}"""

# ═══════════════════════════════════════════════════════════════════════════════
# THEMATIC TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES = {
    "default": MASTER_TEMPLATE,
    "short": SHORT_TEMPLATE,
    "cisco": """Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}. As a Cisco-certified networking professional with {years}+ years of experience, I have extensive hands-on expertise with Cisco IOS/IOS-XE, Catalyst and Nexus switches, ASR/ISR routers, and Cisco DNA Center.

Throughout my career, I have designed, deployed, and managed large-scale Cisco-based networks supporting 10,000+ users across multi-site enterprise environments. My experience includes configuring OSPF, BGP, EIGRP, MPLS, and implementing QoS policies for converged networks.

Key Cisco-specific achievements:
• Upgraded core switching/routing infrastructure for 10+ enterprise clients
• Reduced network downtime by 95% through proactive monitoring and Cisco DNA Assurance
• Led migration from legacy Catalyst to Nexus 9000 series platform

I am immediately available and welcome the opportunity to discuss how my Cisco expertise aligns with {company}'s networking needs.

Best regards,
{CANDIDATE_NAME}
{CANDIDATE_PHONE} | {CANDIDATE_EMAIL}""",

    "mikrotik": """Dear Hiring Manager,

I am applying for the {title} position at {company}. I am a MikroTik Certified professional (MTCNA, MTCRE) with deep expertise in RouterOS, RouterBOARD hardware, and large-scale MikroTik deployments across ISP and enterprise environments.

My experience includes:
• Deploying and managing 200+ MikroTik devices including CCR, RB, and Cloud Core Router series
• Configuring BGP/OSPF/MPLS on MikroTik platforms for service providers
• Implementing bandwidth management, hotspot, PPPoE, VLAN, and firewall rules
• Load balancing across multiple WAN links using MikroTik PCC and ECMP

Available immediately. I look forward to discussing how I can contribute to {company}.

Regards,
{CANDIDATE_NAME}
{CANDIDATE_PHONE} | {CANDIDATE_EMAIL}""",

    "fortinet": """Dear Hiring Manager,

I am writing to apply for the {title} position at {company}. As a Fortinet NSE-certified security professional with {years}+ years in network security, I specialize in FortiGate firewall deployment, FortiManager/FortiAnalyzer management, and multi-layered security architecture.

Key Fortinet experience:
• Deployed 50+ FortiGate firewalls across enterprise and branch offices
• Configured IPSec and SSL VPN solutions for 50+ remote sites
• Implemented FortiGate security policies, IDS/IPS, web filtering, and application control
• Reduced security incidents by 100% through comprehensive firewall hardening

I am immediately available and would welcome the opportunity to strengthen {company}'s security posture.

Best regards,
{CANDIDATE_NAME}
{CANDIDATE_PHONE} | {CANDIDATE_EMAIL}""",

    "security": """Dear Hiring Manager,

I am applying for the {title} role at {company}. With {years}+ years in network security and certifications from Fortinet (NSE), Cisco (CCNA Security), and CompTIA (Security+), I bring comprehensive security expertise.

My security portfolio includes firewall administration, VPN deployment, IDS/IPS, SIEM configuration, vulnerability assessment, and security policy development. I have successfully hardened networks for 20+ enterprise clients across banking, telecom, and government sectors.

Available immediately. I look forward to discussing how I can enhance {company}'s security infrastructure.

Regards,
{CANDIDATE_NAME}
{CANDIDATE_PHONE} | {CANDIDATE_EMAIL}""",

    "infrastructure": """Dear Hiring Manager,

I am interested in the {title} position at {company}. I am an experienced IT Infrastructure Engineer with {years}+ years of hands-on experience in network design, server management, data center operations, and cloud integration across the MENA region.

My infrastructure experience includes fiber optic cabling (500+ km deployed), data center buildouts, structured cabling, server room design, UPS sizing, and cooling infrastructure planning. I have managed end-to-end infrastructure projects for 20+ enterprise clients.

Available immediately for roles in UAE, Saudi Arabia, Qatar, Kuwait, or Lebanon.

Regards,
{CANDIDATE_NAME}
{CANDIDATE_PHONE} | {CANDIDATE_EMAIL}""",

    "telecom": """Dear Hiring Manager,

I am applying for the {title} position at {company}. With {years}+ years in telecommunications and ISP networking, I have extensive experience in fiber optic deployment, last-mile connectivity, MPLS/IP core networks, and ISP-grade infrastructure.

Key telecom achievements:
• Managed fiber optic installations totaling 500+ km
• Designed and deployed ISP core networks with BGP/OSPF/MPLS
• Implemented QoS and traffic shaping for 10,000+ subscriber environments
• Configured MikroTik and Cisco platforms for service provider networks

Available immediately. I look forward to discussing how I can support {company}'s telecom infrastructure.

Regards,
{CANDIDATE_NAME}
{CANDIDATE_PHONE} | {CANDIDATE_EMAIL}""",
}

# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE SELECTOR – Choose best template based on job title
# ═══════════════════════════════════════════════════════════════════════════════

def detect_template_key(title: str) -> str:
    """Detect the best template key based on job title keywords."""
    title_lower = title.lower()
    if any(kw in title_lower for kw in ["security", "firewall", "cyber", "fortinet", "nse"]):
        return "fortinet" if any(kw in title_lower for kw in ["fortinet", "nse"]) else "security"
    if any(kw in title_lower for kw in ["mikrotik", "routeros", "mtcna"]):
        return "mikrotik"
    if any(kw in title_lower for kw in ["cisco", "ccna", "ccnp", "ccie", "catalyst", "nexus"]):
        return "cisco"
    if any(kw in title_lower for kw in ["telecom", "telecommunication", "isp", "fiber", "service provider"]):
        return "telecom"
    if any(kw in title_lower for kw in ["infrastructure", "data center", "datacenter", "cabling"]):
        return "infrastructure"
    if any(kw in title_lower for kw in ["short", "quick", "fast", "cold"]):
        return "short"
    return "default"


def get_letter(title: str, company: str, template_key: str = None) -> str:
    """Generate a cover letter from the best matching template.
    
    Args:
        title: Job title
        company: Company name
        template_key: Optional explicit template key. Auto-detected if None.
    
    Returns:
        Formatted cover letter string. Falls back to master template on error.
    """
    if not title:
        title = "Network Engineer"
    if not company:
        company = "your company"

    if template_key is None:
        template_key = detect_template_key(title)

    template = TEMPLATES.get(template_key, MASTER_TEMPLATE)

    format_kwargs = {
        "title": title,
        "company": company,
        "years": YEARS_EXPERIENCE,
        "CANDIDATE_NAME": CANDIDATE_NAME,
        "CANDIDATE_TITLE": CANDIDATE_TITLE,
        "CANDIDATE_EMAIL": CANDIDATE_EMAIL,
        "CANDIDATE_PHONE": CANDIDATE_PHONE,
        "CANDIDATE_ADDRESS": CANDIDATE_ADDRESS,
        "CANDIDATE_LINKEDIN": CANDIDATE_LINKEDIN,
    }

    try:
        return template.format(**format_kwargs)
    except KeyError as e:
        logger.warning(f"[turbo_templates] Template '{template_key}' has unknown key {e}, falling back to MASTER_TEMPLATE")
        try:
            return MASTER_TEMPLATE.format(**format_kwargs)
        except Exception as ex:
            logger.error(f"[turbo_templates] MASTER_TEMPLATE also failed: {ex}")
            return f"Dear Hiring Manager,\n\nI am applying for the {title} position at {company}.\n\nBest regards,\n{CANDIDATE_NAME}"
    except Exception as e:
        logger.error(f"[turbo_templates] Unexpected error generating letter: {e}", exc_info=True)
        return f"Dear Hiring Manager,\n\nI am applying for the {title} position at {company}.\n\nBest regards,\n{CANDIDATE_NAME}"


def batch_generate(jobs: list) -> list:
    """Generate cover letters for a batch of jobs.
    
    Args:
        jobs: List of dicts with 'title' and 'company' keys
    
    Returns:
        List of dicts with original data + generated letter. Failed jobs are skipped.
    """
    result = []
    for job in jobs:
        try:
            title = job.get("title", "Network Engineer") or "Network Engineer"
            company = job.get("company", "Company") or "Company"
            result.append({
                **job,
                "letter": get_letter(title, company),
                "template_key": detect_template_key(title),
            })
        except Exception as e:
            logger.error(f"[turbo_templates] Failed to generate letter for job {job.get('company', 'unknown')}: {e}")
            # Include the job without a letter rather than dropping it entirely
            result.append({**job, "letter": "", "template_key": "default"})
    return result
