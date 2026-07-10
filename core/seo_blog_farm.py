"""
JobHunt Pro - SEO Blog Farm v1.0
Auto-generates SEO-optimized blog posts using Groq AI.
Publishes to /blog/ for organic traffic growth.

Target keywords:
  - auto apply to jobs, AI job application, apply to jobs automatically
  - job application bot, best job search tools, automated job applications
  - AI cover letter generator, job search automation
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────
POSTS_PER_DAY = 8  # publish max 8/day (natural cadence)
POSTS_DIR = None
BLOG_DATA = None

# Keyword clusters with target URLs
KEYWORD_CLUSTERS = [
    {
        "primary": "auto apply to jobs",
        "title": "How to Auto-Apply to Jobs: The Complete 2026 Guide",
        "slug": "auto-apply-to-jobs-guide",
        "topics": ["automation", "job search", "AI tools", "productivity"],
        "cta": "Try JobHunt Pro — auto-apply to 1,000+ jobs",
    },
    {
        "primary": "AI job application",
        "title": "AI Job Applications: How Artificial Intelligence Is Changing Job Hunting",
        "slug": "ai-job-applications-guide",
        "topics": ["AI", "automation", "job search", "future of work"],
        "cta": "Start your AI-powered job search",
    },
    {
        "primary": "automated job applications",
        "title": "Automated Job Applications 2026: Apply to 1000s While You Sleep",
        "slug": "automated-job-applications",
        "topics": ["automation", "productivity", "career growth"],
        "cta": "Automate your job search today",
    },
    {
        "primary": "best job search tools",
        "title": "15 Best Job Search Tools in 2026 (Free & Paid)",
        "slug": "best-job-search-tools-2026",
        "topics": ["tools", "reviews", "comparisons"],
        "cta": "Try the #1 AI job application tool",
    },
    {
        "primary": "AI cover letter generator",
        "title": "AI Cover Letter Generator: Write Perfect Letters in Seconds",
        "slug": "ai-cover-letter-generator",
        "topics": ["AI", "cover letters", "writing tips"],
        "cta": "Generate your cover letter with AI",
    },
    {
        "primary": "how to apply to 100 jobs fast",
        "title": "How to Apply to 100+ Jobs in One Day (Without Burnout)",
        "slug": "apply-to-100-jobs-fast",
        "topics": ["productivity", "job search", "tips"],
        "cta": "Apply to 100 jobs in 10 minutes",
    },
    {
        "primary": "job application bot",
        "title": "Job Application Bots: The Smart Way to Job Hunt in 2026",
        "slug": "job-application-bots",
        "topics": ["automation", "tools", "technology"],
        "cta": "Try the most advanced job application bot",
    },
    {
        "primary": "job search automation",
        "title": "Job Search Automation: Your 24/7 AI Recruiter",
        "slug": "job-search-automation",
        "topics": ["automation", "career", "technology"],
        "cta": "Automate your job search now",
    },
    {
        "primary": "apply to multiple jobs at once",
        "title": "How to Apply to Multiple Jobs at Once (Batch Apply Guide)",
        "slug": "apply-to-multiple-jobs-at-once",
        "topics": ["productivity", "job search", "tips"],
        "cta": "Batch-apply with AI",
    },
    {
        "primary": "job search tips 2026",
        "title": "50 Game-Changing Job Search Tips for 2026",
        "slug": "job-search-tips-2026",
        "topics": ["tips", "career", "best practices"],
        "cta": "Supercharge your job search",
    },
]


def init(data_dir: str | None = None):
    """Initialize blog farm."""
    global POSTS_DIR, BLOG_DATA
    if data_dir:
        POSTS_DIR = Path(data_dir) / "blog"
    else:
        POSTS_DIR = Path(__file__).parent.parent / "data" / "blog"
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    BLOG_DATA = POSTS_DIR / "posts.json"
    if not BLOG_DATA.exists():
        with open(BLOG_DATA, "w") as f:
            json.dump([], f)

    logger.info(f"BlogFarm initialized at {POSTS_DIR}")


def generate_post(cluster: dict, groq_key: str = None) -> dict | None:
    """Generate a single blog post using Groq AI."""
    if groq_key is None:
        groq_key = os.getenv("GROQ_API_KEY", "")

    if not groq_key:
        logger.warning("No Groq API key — using template-based generation")
        return _template_post(cluster)

    try:
        import requests

        prompt = f"""Write an SEO-optimized blog post for the keyword: "{cluster["primary"]}".

Title: {cluster["title"]}
Topics: {", ".join(cluster.get("topics", []))}

Guidelines:
- 800-1200 words
- Use H2 and H3 subheadings
- Include practical tips and actionable advice
- Naturally mention "JobHunt Pro" 2-3 times (it's an AI-powered auto job application tool)
- Include a CTA at the end: "{cluster.get("cta", "Try JobHunt Pro today")}"
- Write in a helpful, blog-style voice (not salesy)
- Include 3-5 bullet points where appropriate
- Add internal link suggestion as [internal_link]

Output in this JSON format:
{{
  "title": "exact title",
  "meta_description": "155-char SEO meta description",
  "content": "full HTML blog post with <h2>, <h3>, <p>, <ul>, <li> tags",
  "internal_link_text": "short text to link from other posts",
  "word_count": 950
}}"""

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2500,
            },
            timeout=60,
        )

        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            # Extract JSON
            m = re.search(r"\{.*\}", content, re.DOTALL)
            if m:
                post = json.loads(m.group())
                post["slug"] = cluster["slug"]
                post["primary_keyword"] = cluster["primary"]
                post["topics"] = cluster.get("topics", [])
                post["published"] = False
                post["created_at"] = datetime.utcnow().isoformat()
                post["published_at"] = None
                logger.info(
                    f"Generated: {post['title']} ({post.get('word_count', '?')} words)"
                )
                return post
        else:
            logger.warning(f"Groq API error {r.status_code}: {r.text[:200]}")

    except Exception as e:
        logger.error(f"Blog generation failed: {e}")

    # Fallback
    return _template_post(cluster)


def _template_post(cluster: dict) -> dict:
    """Generate a template-based blog post (no API needed)."""
    kw = cluster["primary"]
    title = cluster["title"]
    slug = cluster["slug"]
    topics = cluster.get("topics", [])
    cluster.get("cta", "Try JobHunt Pro today")

    content = f"""<h2>Why {title.split(":")[0] if ":" in title else kw.title()} Matters in 2026</h2>

<p>The job market in 2026 is more competitive than ever. With hundreds of applicants per position, standing out requires more than just a good resume — it requires strategy, speed, and the right tools.</p>

<p>Whether you're a recent graduate, a career changer, or a seasoned professional looking for your next opportunity, mastering <strong>{kw}</strong> can dramatically improve your results.</p>

<h2>Key Strategies for Success</h2>

<p>Here are the most effective approaches to {kw}:</p>

<ul>
    <li><strong>Automate repetitive tasks</strong> — The average job seeker spends 3-4 hours per day on manual applications. Automation tools like <a href="https://jhfguf.pythonanywhere.com">JobHunt Pro</a> can reduce this to minutes.</li>
    <li><strong>Target the right jobs</strong> — AI-powered matching ensures you only apply to positions that actually fit your skills.</li>
    <li><strong>Personalize at scale</strong> — Modern AI can generate customized cover letters for each application.</li>
    <li><strong>Track everything</strong> — Keep records of applications, responses, and interviews to optimize your approach.</li>
</ul>

<h2>The Power of AI in Job Applications</h2>

<p>Artificial intelligence has transformed how we search and apply for jobs. Tools like <strong>JobHunt Pro</strong> use 200+ AI agents working simultaneously to search job boards, score matches, write personalized cover letters, and submit applications — all automatically.</p>

<p>The result? Users report 3-5x more interview invitations within the first week.</p>

<h2>Common Mistakes to Avoid</h2>

<ul>
    <li><strong>Spraying and praying</strong> — Applying to everything without matching skills to requirements</li>
    <li><strong>Generic cover letters</strong> — Recruiters can spot a template from miles away</li>
    <li><strong>Poor time management</strong> — Spending too much time on low-quality leads</li>
    <li><strong>Ignoring follow-ups</strong> — The fortune is in the follow-up</li>
</ul>

<h2>Getting Started Today</h2>

<p>Here's your action plan for mastering {kw}:</p>

<ol>
    <li>Optimize your resume for ATS systems</li>
    <li>Set up automated job alerts on multiple platforms</li>
    <li>Use AI tools to streamline your application process</li>
    <li>Track your metrics and adjust your strategy weekly</li>
</ol>

<h2>Why Choose JobHunt Pro?</h2>

<p><a href="https://jhfguf.pythonanywhere.com">JobHunt Pro</a> is the most advanced AI job application platform available. With features like BanShield™ anti-detection, multi-platform job search, and AI-generated cover letters, it's designed to maximize your interview rate while minimizing your effort.</p>

<p><strong>Start your free trial today → <a href="https://jhfguf.pythonanywhere.com">JobHunt Pro</a></strong></p>

<p><em>Tags: {", ".join(topics)}, {kw}</em></p>"""

    meta = f"Master {kw} with our complete 2026 guide. AI-powered tools, expert strategies, and actionable tips to land more interviews. Start today."

    return {
        "title": title,
        "slug": slug,
        "meta_description": meta[:160],
        "primary_keyword": kw,
        "topics": topics,
        "content": content,
        "internal_link_text": f"Learn more about {kw}",
        "word_count": len(content.split()),
        "published": False,
        "created_at": datetime.utcnow().isoformat(),
        "published_at": None,
    }


def generate_all(groq_key: str = None) -> int:
    """Generate all blog posts. Returns count generated."""
    posts = _load_posts()
    existing_slugs = {p["slug"] for p in posts}
    generated = 0

    for cluster in KEYWORD_CLUSTERS:
        if cluster["slug"] in existing_slugs:
            continue

        try:
            post = generate_post(cluster, groq_key)
            if post:
                posts.append(post)
                generated += 1
                logger.info(f"  ✓ {post['title'][:60]}")
                time.sleep(2)  # rate limit between API calls
        except Exception as e:
            logger.error(f"Failed {cluster['slug']}: {e}")

    if generated:
        _save_posts(posts)

    return generated


def publish_post(slug: str) -> bool:
    """Mark a post as published."""
    posts = _load_posts()
    for p in posts:
        if p["slug"] == slug:
            p["published"] = True
            p["published_at"] = datetime.utcnow().isoformat()
            _save_posts(posts)
            logger.info(f"Published: {slug}")
            return True
    return False


def get_posts(
    published_only: bool = True, limit: int = None, offset: int = 0
) -> list[dict]:
    """Get blog posts, optionally filtered."""
    posts = _load_posts()
    if published_only:
        posts = [p for p in posts if p.get("published")]

    posts.sort(
        key=lambda x: x.get("published_at", x.get("created_at", "")), reverse=True
    )

    if offset:
        posts = posts[offset:]
    if limit:
        posts = posts[:limit]

    return posts


def get_post(slug: str) -> dict | None:
    """Get a single post by slug."""
    posts = _load_posts()
    for p in posts:
        if p["slug"] == slug:
            return p
    return None


def _load_posts() -> list[dict]:
    """Load all posts from JSON."""
    if BLOG_DATA and BLOG_DATA.exists():
        try:
            with open(BLOG_DATA, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_posts(posts: list[dict]):
    """Save posts to JSON."""
    if BLOG_DATA:
        with open(BLOG_DATA, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, ensure_ascii=False, default=str)


def get_stats() -> dict:
    """Blog farm statistics."""
    posts = _load_posts()
    published = [p for p in posts if p.get("published")]
    return {
        "total_posts": len(posts),
        "published": len(published),
        "drafts": len(posts) - len(published),
        "total_words": sum(p.get("word_count", 0) for p in posts),
        "last_post": published[-1]["published_at"] if published else None,
    }
