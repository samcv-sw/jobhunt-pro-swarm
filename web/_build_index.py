"""
BUILD-QUICK-WINS: Add featured jobs section to index_v3.html
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INDEX_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'index_v3.html')


def build_index() -> None:
    """Builds and updates index_v3.html templates with featured jobs sections."""
    try:
        if not os.path.exists(INDEX_HTML):
            logger.error(f"Template file not found: {INDEX_HTML}")
            sys.exit(1)

        with open(INDEX_HTML, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read template file: {e}")
        sys.exit(1)

    # ===== Add Featured Jobs CSS before closing </style> =====
    featured_css = '''
/* Featured Jobs Section (spy-report quick win #5) */
.featured-jobs{
  position:relative;z-index:10;padding:60px 40px;max-width:1200px;margin:0 auto;
}
.featured-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:32px;}
.fj-card{
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius-xl);
  padding:32px 24px;transition:all var(--transition);position:relative;overflow:hidden;
  display:flex;flex-direction:column;gap:16px;
}
.fj-card::before{
  content:'';position:absolute;top:0;left:0;width:100%;height:3px;
  background:linear-gradient(90deg,var(--cyan),var(--magenta));
  opacity:0;transition:opacity var(--transition);
}
.fj-card:hover{
  transform:translateY(-8px);border-color:rgba(0,240,255,0.25);
  box-shadow:0 20px 50px rgba(0,0,0,0.6),var(--glow-cyan);
}
.fj-card:hover::before{opacity:1}
.fj-badge{
  display:inline-flex;align-items:center;gap:6px;padding:5px 14px;
  background:rgba(255,179,0,0.08);border:1px solid rgba(255,179,0,0.2);
  border-radius:50px;font-size:9px;font-weight:700;color:var(--gold);
  letter-spacing:1.5px;text-transform:uppercase;align-self:flex-start;
}
.fj-company-row{display:flex;align-items:center;gap:12px;}
.fj-logo{
  width:48px;height:48px;border-radius:12px;flex-shrink:0;
  background:rgba(255,255,255,.04);border:1px solid var(--border);
  display:flex;align-items:center;justify-content:center;overflow:hidden;
}
.fj-logo img{width:100%;height:100%;object-fit:contain;padding:5px;}
.fj-logo-fb{font-size:20px;font-weight:800;color:var(--cyan);}
.fj-company-name{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;color:#fff;}
.fj-company-name small{display:block;font-size:10px;color:var(--muted);font-weight:400;margin-top:2px;}
.fj-title{font-size:17px;font-weight:700;color:var(--text);line-height:1.3;}
.fj-salary-row{
  display:flex;align-items:center;gap:8px;
  padding:10px 16px;background:rgba(34,197,94,.06);
  border:1px solid rgba(34,197,94,.15);border-radius:10px;
}
.fj-salary{font-family:monospace;font-size:15px;font-weight:700;color:#22c55e;}
.fj-tags{display:flex;gap:6px;flex-wrap:wrap;}
.fj-tag{
  font-size:10px;padding:4px 10px;border-radius:6px;font-weight:600;white-space:nowrap;
  background:rgba(0,240,255,.06);color:var(--cyan);border:1px solid rgba(0,240,255,.15);
}
.fj-location{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);}
.fj-apply-btn{
  display:block;text-align:center;padding:14px;border-radius:12px;
  background:linear-gradient(135deg,var(--cyan),#00a0cc);color:#000;
  font-weight:700;font-size:14px;text-decoration:none;transition:all var(--transition);
  margin-top:auto;
}
.fj-apply-btn:hover{
  box-shadow:0 6px 25px rgba(0,240,255,0.4);transform:translateY(-2px);
}
@media(max-width:1024px){.featured-grid{grid-template-columns:repeat(2,1fr);}}
@media(max-width:768px){.featured-grid{grid-template-columns:1fr;max-width:400px;margin-inline:auto;}}
'''

    style_close = content.rfind('</style>')
    if style_close != -1:
        content = content[:style_close] + featured_css + content[style_close:]
        logger.info("+ Added featured jobs CSS")

    # ===== Add featured jobs HTML after Trusted By and before How It Works =====
    how_it_works_marker = '<!-- ═══ HOW IT WORKS ═══ -->'
    how_idx = content.find(how_it_works_marker)
    if how_idx == -1:
        logger.error("Could not find How It Works section!")
        sys.exit(1)

    featured_html = '''
<!-- ═══ FEATURED JOBS (spy-report quick win #5) ═══ -->
{% if featured_jobs %}
<section class="featured-jobs">
 <div class="section-header">
  <div class="overline">HOT OPPORTUNITIES</div>
  <h2>Featured <span class="gradient">Jobs</span></h2>
  <p>Hand-picked premium positions in top companies across MENA/GCC. Apply instantly with JobHunt Pro.</p>
 </div>
 <div class="featured-grid">
  {% for job in featured_jobs %}
  <div class="fj-card">
   <span class="fj-badge">&#x2605; Featured</span>
   <div class="fj-company-row">
    <div class="fj-logo">
     <img src="https://logo.clearbit.com/{{ job.domain }}" alt="{{ job.company }}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" loading="lazy">
     <span class="fj-logo-fb" style="display:none;">{{ job.company[:2] }}</span>
    </div>
    <div class="fj-company-name">{{ job.company }}<small>{{ job.location }}</small></div>
   </div>
   <div class="fj-title">{{ job.title }}</div>
   <div class="fj-salary-row">
    <span class="fj-salary">{{ job.salary }}</span>
   </div>
   <div class="fj-tags">
    {% for tag in job.tags %}<span class="fj-tag">{{ tag }}</span>{% endfor %}
   </div>
   <a href="{{ job.url }}" class="fj-apply-btn">&#x1F680; Apply Now</a>
  </div>
  {% endfor %}
 </div>
</section>
{% endif %}
'''

    content = content[:how_idx] + featured_html + '\n' + content[how_idx:]
    logger.info("+ Added featured jobs HTML section")

    try:
        with open(INDEX_HTML, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("=== index_v3.html updated ===")
    except Exception as e:
        logger.error(f"Failed to write template file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_index()
