import logging
import re
from typing import Dict, Optional
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class ShadowNetwork:
    """
    The Shadow Network Protocol.
    Hunts down the exact HR Manager/Recruiter for a target company via DuckDuckGo,
    extracts their name, guesses their corporate email, and crafts a hyper-personalized outreach.
    """
    
    def __init__(self):
        self.ddgs = DDGS()
        
    def hunt_hr_manager(self, company_name: str, location: str = "") -> Optional[Dict]:
        """Search for HR managers at the target company."""
        if not company_name:
            return None
            
        logger.info(f"[SHADOW] Initiating HR hunt for: {company_name}")
        query = f'site:linkedin.com/in/ "Talent Acquisition" OR "Recruiter" OR "HR Manager" "{company_name}" {location}'
        
        try:
            results = list(self.ddgs.text(query, max_results=3))
            if not results:
                logger.warning(f"[SHADOW] No HR managers found for {company_name}")
                return None
                
            best_match = results[0]
            title_text = best_match.get('title', '')
            
            # Extract name from LinkedIn title (e.g. "John Doe - HR Manager - Google | LinkedIn")
            name_part = title_text.split('-')[0].strip()
            name_part = name_part.replace('| LinkedIn', '').strip()
            
            # Guess email (first.last@company.com)
            name_tokens = name_part.split(' ')
            if len(name_tokens) >= 2:
                first = name_tokens[0].lower()
                last = name_tokens[-1].lower()
                domain = re.sub(r'[^a-z0-9]', '', company_name.lower()) + '.com'
                guessed_email = f"{first}.{last}@{domain}"
            else:
                guessed_email = ""
                
            hr_data = {
                "hr_name": name_part,
                "hr_linkedin": best_match.get('href', ''),
                "guessed_email": guessed_email,
                "confidence": 85 if guessed_email else 40
            }
            logger.info(f"[SHADOW] Hunt successful: Found {name_part} ({guessed_email})")
            return hr_data
            
        except Exception as e:
            logger.error(f"[SHADOW] Hunt failed: {e}")
            return None
            
    def craft_shadow_message(self, hr_data: Dict, job_title: str) -> str:
        """Craft a direct message to the hunted HR manager."""
        name = hr_data.get('hr_name', 'Hiring Manager').split(' ')[0]
        return (
            f"Hi {name},\n\n"
            f"I recently submitted my application for the {job_title} position at your company. "
            f"I know you receive hundreds of applications through the portal, so I wanted to reach out directly to express my high interest.\n\n"
            f"I have exactly the background needed to hit the ground running. I've attached my CV for your direct review.\n\n"
            f"Looking forward to speaking with you.\n\n"
            f"Best regards,"
        )
