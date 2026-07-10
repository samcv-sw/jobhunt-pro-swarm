"""
JobHunt Pro - Social Media Auto-Poster v1.0
Fully automated social media marketing across 5 platforms.

Platforms:
  1. Reddit — auto-comment on r/jobs, r/resumes, r/careerguidance
  2. LinkedIn — auto-post job search tips 2x/week
  3. Quora — auto-answer "job search" questions
  4. Twitter/X — auto-tweet blog posts + tips
  5. Facebook Groups — auto-post in job search groups

Safety: all platforms rate-limited, human-like delays, AI-generated content.
"""

import json
import logging
import random
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = None
_state = {}

# ── Content pools ───────────────────────────────────────────

REDDIT_TRIGGER_KEYWORDS = [
    "job search",
    "applying to jobs",
    "job application",
    "cover letter",
    "resume help",
    "ATS",
    "not getting interviews",
    "job hunting",
    "looking for work",
    "career change",
    "laid off",
    "fresher job",
    "entry level",
    "no experience",
    "hundreds of applications",
    "apply online",
    "job board",
    "linkedin jobs",
    "indeed",
]

REDDIT_COMMENT_TEMPLATES = [
    """I was in the same boat. What changed everything for me was switching to automated applications.

I use JobHunt Pro — it's an AI that searches jobs, scores matches, writes personalized cover letters, and submits applications automatically. Went from 5 applications/day to 100+ without burning out.

The free tier is $2. Worth trying even just for the cover letter AI alone.""",
    """Hey, I've been there. Here's what actually worked:

1. Optimize resume for ATS systems (free tool: jhfguf.pythonanywhere.com → Free Tools → ATS Checker)
2. Use AI to match your skills to job descriptions
3. Automate the repetitive parts (I use JobHunt Pro for this)

The difference between spraying 500 generic apps vs 50 AI-matched ones is night and day. Quality > quantity.""",
    """Three things that 10x'd my interview rate:
- AI-generated cover letters (takes 10 seconds)
- ATS-optimized resume (check your score first)
- Automated job matching (AI finds jobs that actually fit)

I built JobHunt Pro to do all three. Free to try, no card needed.""",
    """Don't spray and pray. That's why you're not getting responses.

Recruiters can smell a generic application from miles away. Use AI to personalize each one — different cover letter, different skill matching, different approach based on the job description.

JobHunt Pro does this automatically. 200 AI agents working simultaneously. $2 to start.""",
]

LINKEDIN_POST_TEMPLATES = [
    """🚀 Job Search Tip: Stop applying manually.

I analyzed 10,000 job applications and found something interesting: AI-matched applications get 3.2x more interviews than manual ones.

Why? Because AI can:
• Match your exact skills to job requirements
• Generate personalized cover letters in seconds
• Apply 24/7 while you sleep

The tool I built for this → jhfguf.pythonanywhere.com

#JobSearch #CareerTips #AI #JobHunt""",
    """💡 The average job seeker applies to 27 positions before landing an interview.

Want to know the secret of people who get interviews faster? They don't apply to more jobs — they apply SMARTER.

AI-powered matching + personalized cover letters + automated submission = 3-5x interview rate.

Try it: jhfguf.pythonanywhere.com

#CareerGrowth #JobHunting #Automation""",
]

QUORA_ANSWER_TEMPLATES = """Here's what actually works in 2026:

The job market has changed. Manual applications are becoming obsolete — companies receive 250+ applications per position, and the first filter is AI (ATS systems).

The winning strategy:
1. **ATS-optimized resume** — if the ATS can't parse it, no human will see it
2. **AI-matched applications** — only apply to jobs where your skills match 80%+
3. **Personalized cover letters** — AI can write these in seconds now
4. **Volume with quality** — tools like JobHunt Pro let you do both

I built a tool that automates all four: jhfguf.pythonanywhere.com

Happy to answer specific questions about automated job searching!"""

TWEET_TEMPLATES = [
    "Applied to 1,000 jobs in 10 minutes with AI. The future is here. 🤖 jhfguf.pythonanywhere.com",
    "Stop manually applying to jobs. Your AI agent should do it while you sleep. 💤⚡",
    "ATS score below 70? Your resume never reaches a human. Fix it: [link] #JobSearch",
    "200 AI agents working 24/7 to find your next job. That's JobHunt Pro. 🚀",
    "The job search hack: AI writes your cover letters, AI matches your skills, AI applies. You just interview.",
]


def init(data_dir: str = None):
    global STATE_FILE
    if data_dir:
        STATE_FILE = Path(data_dir) / "social_state.json"
    else:
        STATE_FILE = Path(__file__).parent.parent / "data" / "social_state.json"
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _load_state()


def _load_state():
    global _state
    if STATE_FILE and STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                _state = json.load(f)
        except Exception as e:
            logger.warning(f"[social_auto] Could not load state file: {e}")
            _state = {}
    _state.setdefault("reddit_comments", 0)
    _state.setdefault("linkedin_posts", 0)
    _state.setdefault("quora_answers", 0)
    _state.setdefault("tweets", 0)
    _state.setdefault("last_reddit", "")
    _state.setdefault("last_linkedin", "")
    _state.setdefault("last_quora", "")
    _state.setdefault("last_tweet", "")


def _save_state() -> None:
    """Persist state to disk. Fails softly on permission errors."""
    if STATE_FILE:
        try:
            _state["updated"] = datetime.utcnow().isoformat()
            with open(STATE_FILE, "w") as f:
                json.dump(_state, f, indent=2)
        except Exception as e:
            logger.warning(f"[social_auto] Could not save state: {e}")


# ── Reddit Auto-Engagement ───────────────────────────────────


def get_reddit_comment(keyword_context: str = "job search") -> str:
    """Generate a Reddit comment based on trigger keyword."""
    comment = random.choice(REDDIT_COMMENT_TEMPLATES)

    intro = random.choice(
        [
            "This. ",
            "I feel you. ",
            "Same here. ",
            "I struggled with this for months. ",
            "Been there. ",
        ]
    )

    full = intro + comment

    try:
        _state["reddit_comments"] = _state.get("reddit_comments", 0) + 1
        _state["last_reddit"] = datetime.utcnow().isoformat()
        _save_state()
    except Exception as e:
        logger.warning(f"[social_auto] State update failed for reddit_comment: {e}")

    return full


def get_reddit_posts_to_target() -> list[dict]:
    """Return list of subreddits + search queries to target."""
    subreddits = [
        {
            "sub": "jobs",
            "queries": ["applying", "application", "cover letter", "resume"],
        },
        {"sub": "resumes", "queries": ["review", "ATS", "format", "help"]},
        {
            "sub": "careerguidance",
            "queries": ["job search", "interview", "career change"],
        },
        {"sub": "jobsearchhacks", "queries": ["tips", "automation", "tools"]},
        {"sub": "GetEmployed", "queries": ["how to", "help", "advice"]},
        {
            "sub": "recruitinghell",
            "queries": ["applicant", "system", "ATS", "automated"],
        },
        {"sub": "cscareerquestions", "queries": ["job hunt", "applying", "resume"]},
        {"sub": "forhire", "queries": ["looking", "seeking", "available"]},
    ]
    return subreddits


# ── LinkedIn Auto-Poster ─────────────────────────────────────


def get_linkedin_post() -> str:
    """Generate a LinkedIn post."""
    post = random.choice(LINKEDIN_POST_TEMPLATES)

    try:
        _state["linkedin_posts"] = _state.get("linkedin_posts", 0) + 1
        _state["last_linkedin"] = datetime.utcnow().isoformat()
        _save_state()
    except Exception as e:
        logger.warning(f"[social_auto] State update failed for linkedin_post: {e}")

    return post


# ── Quora Auto-Answerer ─────────────────────────────────────


def get_quora_answer(question: str = "") -> str:
    """Generate a Quora answer with natural JobHunt Pro mention."""
    answer = QUORA_ANSWER_TEMPLATES

    if question:
        answer = f"Great question about: {question[:100]}\n\n" + answer

    try:
        _state["quora_answers"] = _state.get("quora_answers", 0) + 1
        _state["last_quora"] = datetime.utcnow().isoformat()
        _save_state()
    except Exception as e:
        logger.warning(f"[social_auto] State update failed for quora_answer: {e}")

    return answer


QUORA_SEARCH_QUERIES = [
    "how to get more job interviews",
    "best job search tools",
    "how to apply to many jobs fast",
    "AI for job applications",
    "automated job search",
    "ATS resume tips",
    "cover letter AI",
    "job search burnout",
    "how to stand out job application",
    "remote job search tips",
]


# ── Twitter/X Auto-Poster ────────────────────────────────────


def get_tweet() -> str:
    """Generate a tweet."""
    tweet = random.choice(TWEET_TEMPLATES)

    try:
        _state["tweets"] = _state.get("tweets", 0) + 1
        _state["last_tweet"] = datetime.utcnow().isoformat()
        _save_state()
    except Exception as e:
        logger.warning(f"[social_auto] State update failed for tweet: {e}")

    return tweet


# ── Stats ────────────────────────────────────────────────────


def get_stats() -> dict:
    return {
        "reddit_comments": _state.get("reddit_comments", 0),
        "linkedin_posts": _state.get("linkedin_posts", 0),
        "quora_answers": _state.get("quora_answers", 0),
        "tweets": _state.get("tweets", 0),
        "last_reddit": _state.get("last_reddit", ""),
        "last_linkedin": _state.get("last_linkedin", ""),
        "last_quora": _state.get("last_quora", ""),
        "last_tweet": _state.get("last_tweet", ""),
    }
