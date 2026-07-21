"""
Autonomous Social Outreach Agent - JobHunt Pro God-Tier Module
Automates recruiter cold outreach across LinkedIn, WhatsApp & Email with auto-booking calendar hooks.
"""

from typing import Dict, List, Any
import urllib.parse


class AutonomousSocialOutreach:
    def __init__(self):
        self.supported_platforms = ["linkedin", "whatsapp", "email"]

    def generate_outreach_campaign(
        self, recruiter_name: str, company: str, target_role: str, platform: str = "linkedin", calendar_link: str = "https://calendly.com/candidate/interview"
    ) -> Dict[str, Any]:
        """Generate tailored cold outreach message payload."""
        plat = platform.lower()
        if plat not in self.supported_platforms:
            plat = "linkedin"

        encoded_cal = urllib.parse.quote(calendar_link)

        if plat == "whatsapp":
            message = (
                f"Hi {recruiter_name}, saw you're hiring for {target_role} at {company}. "
                f"I bring extensive experience delivering high-performance backend systems. "
                f"Would love to connect briefly! You can grab a slot directly on my calendar: {calendar_link}"
            )
            deep_link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(message)}"
        elif plat == "email":
            subject = f"Application / Experienced {target_role} - {recruiter_name}"
            message = (
                f"Hi {recruiter_name},\n\n"
                f"I noticed the open {target_role} role at {company} and wanted to reach out directly.\n"
                f"I specialize in scalable software engineering and automated pipeline optimization. "
                f"I've attached my ATS-optimized resume for your review.\n\n"
                f"If you have 10 minutes this week, feel free to book a chat directly: {calendar_link}\n\n"
                f"Best regards,\nCandidate"
            )
            deep_link = f"mailto:recruiter@{company.lower().replace(' ', '')}.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(message)}"
        else:
            # LinkedIn
            message = (
                f"Hi {recruiter_name}, hope you're having a great week! "
                f"I saw that {company} is scaling its team for the {target_role} position. "
                f"I'd love to share how my background in building high-throughput systems aligns with your team goals. "
                f"Looking forward to connecting!"
            )
            deep_link = f"https://www.linkedin.com/in/search?keywords={urllib.parse.quote(recruiter_name + ' ' + company)}"

        return {
            "success": True,
            "platform": plat,
            "recruiter_name": recruiter_name,
            "company": company,
            "target_role": target_role,
            "message": message,
            "deep_link": deep_link,
            "calendar_link": calendar_link
        }


social_outreach = AutonomousSocialOutreach()
