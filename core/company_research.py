import logging
import json
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None
import config

logger = logging.getLogger(__name__)

class CompanyResearch:
    def __init__(self):
        pass

    def research(self, company_name):
        info = {"company": company_name, "info": "", "news": "", "culture": "", "salary": "", "glassdoor": "", "linkedin": "", "career_page": ""}
        if not DDGS:
            return info

        try:
            with DDGS() as ddgs:
                try:
                    results = ddgs.text(f"{company_name} company overview about us", max_results=5)
                    info['info'] = ' | '.join([r.get('body', '')[:200] for r in results if r.get('body')])
                except Exception as e:
                    logger.warning(f"Research failed for {company_name}: {e}")

                try:
                    results = ddgs.text(f"{company_name} recent news 2024 2025", max_results=5)
                    info['news'] = ' | '.join([r.get('body', '')[:200] for r in results if r.get('body')])
                except Exception as e:
                    logger.warning(f"News research failed for {company_name}: {e}")

                try:
                    results = ddgs.text(f"{company_name} company culture work environment employee reviews", max_results=5)
                    info['culture'] = ' | '.join([r.get('body', '')[:200] for r in results if r.get('body')])
                except Exception as e:
                    logger.warning(f"Culture research failed for {company_name}: {e}")

                try:
                    results = ddgs.text(f"{company_name} network engineer salary range compensation", max_results=3)
                    info['salary'] = ' | '.join([r.get('body', '')[:200] for r in results if r.get('body')])
                except Exception as e:
                    logger.warning(f"Salary research failed for {company_name}: {e}")

                try:
                    results = ddgs.text(f"{company_name} glassdoor reviews rating", max_results=3)
                    info['glassdoor'] = ' | '.join([r.get('body', '')[:200] for r in results if r.get('body')])
                except Exception as e:
                    logger.warning(f"Glassdoor research failed for {company_name}: {e}")

                try:
                    results = ddgs.text(f"{company_name} linkedin company page careers", max_results=3)
                    for r in results:
                        url = r.get('href', '')
                        if 'linkedin.com/company' in url:
                            info['linkedin'] = url
                            break
                except Exception as e:
                    logger.warning(f"LinkedIn research failed for {company_name}: {e}")

                try:
                    results = ddgs.text(f"{company_name} careers page jobs apply", max_results=3)
                    for r in results:
                        url = r.get('href', '')
                        if 'career' in url.lower() or 'jobs' in url.lower():
                            info['career_page'] = url
                            break
                except Exception as e:
                    logger.warning(f"Career page research failed for {company_name}: {e}")
        except Exception as e:
            logger.error(f"DDGS context manager failed: {e}")

        return info

    def get_icebreakers(self, company_info):
        breakers = []
        company = company_info.get('company', 'your company')
        if company_info.get('info'):
            breakers.append(f"I have been following {company}'s recent developments and am impressed by your growth trajectory.")
        if company_info.get('news'):
            breakers.append(f"Your latest initiatives demonstrate exactly the kind of innovation I want to be part of.")
        if company_info.get('culture'):
            breakers.append(f"{company}'s commitment to excellence aligns perfectly with my professional values.")
        return breakers[:3]
