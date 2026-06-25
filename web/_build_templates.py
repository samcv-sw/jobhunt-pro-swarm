"""
BUILD-QUICK-WINS: Update dashboard_v2.html with rich job cards
"""
import os

DASHBOARD_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'dashboard_v2.html')

with open(DASHBOARD_HTML, 'r', encoding='utf-8') as f:
    content = f.read()

# ===== Change 1: Add rich job card CSS before the closing </style> =====
rich_css = '''
/* Rich Job Cards (spy-report quick wins #1, #2, #4) */
.job-card-grid{display:flex;flex-direction:column;gap:12px;}
.job-card-rich{
  background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);
  border-radius:16px;padding:16px 20px;transition:all .25s;
  display:flex;align-items:center;gap:16px;flex-wrap:wrap;position:relative;
}
.job-card-rich:hover{
  border-color:rgba(59,130,246,.25);background:rgba(59,130,246,.03);
  transform:translateX(4px);box-shadow:0 4px 24px rgba(59,130,246,.08);
}
.jc-logo{
  width:44px;height:44px;border-radius:10px;flex-shrink:0;
  background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);
  display:flex;align-items:center;justify-content:center;overflow:hidden;
}
.jc-logo img{width:100%;height:100%;object-fit:contain;padding:4px;}
.jc-logo .logo-fallback{font-size:18px;font-weight:800;color:#3b82f6;text-transform:uppercase;}
.jc-info{flex:1;min-width:180px;}
.jc-company{font-size:15px;font-weight:700;color:#e2e8f0;margin-bottom:2px;}
.jc-title{font-size:13px;color:#94a3b8;margin-bottom:4px;}
.jc-meta{display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:10px;color:#52525b;}
.jc-meta-item{
  display:inline-flex;align-items:center;gap:4px;padding:2px 8px;
  background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.05);
  border-radius:20px;font-weight:600;white-space:nowrap;
}
.jc-salary{
  display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0;min-width:140px;
}
.jc-salary-amt{font-size:14px;font-weight:700;font-family:monospace;}
.jc-salary-amt.high{color:#22c55e;}
.jc-salary-amt.medium{color:#fbbf24;}
.jc-salary-amt.entry{color:#94a3b8;}
.jc-bonus{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;}
.jc-bonus.yes{color:#22c55e;}
.jc-bonus.no{color:#52525b;}
.jc-score{
  display:flex;flex-direction:column;align-items:center;gap:2px;flex-shrink:0;min-width:58px;
}
.jc-score-num{
  font-size:20px;font-weight:900;font-family:monospace;letter-spacing:-.5px;
}
.jc-score-num.high{color:#22c55e;}
.jc-score-num.med{color:#fbbf24;}
.jc-score-num.low{color:#ef4444;}
.jc-score-label{font-size:8px;color:#52525b;text-transform:uppercase;letter-spacing:1px;}
.jc-time{font-size:10px;color:#52525b;white-space:nowrap;text-align:right;min-width:60px;}
.jc-actions{display:flex;align-items:center;gap:8px;flex-shrink:0;}
@media(max-width:768px){
  .job-card-rich{flex-direction:column;align-items:flex-start;gap:10px;padding:14px;}
  .jc-salary{flex-direction:row;align-items:center;gap:10px;}
  .jc-score{flex-direction:row;gap:6px;}
  .jc-actions{align-self:stretch;justify-content:flex-end;}
}
'''

style_close = content.rfind('</style>')
content = content[:style_close] + rich_css + content[style_close:]
print("+ Added rich job card CSS")

# ===== Change 2: Replace the pipeline table with rich job cards =====
old_table = '''    {% if pipeline_emails %}
    <div class="table-wrapper">
      <table class="table">
        <thead><tr><th>Company</th><th>Job Title</th><th>Stage</th><th>Action</th></tr></thead>
        <tbody>
          {% for email in pipeline_emails[:10] %}
          {% set stage = email.pipeline_stage or 'discovered' %}
          <tr>
            <td style="font-weight:600;">{{ email.company_name }}</td>
            <td style="color:#94a3b8;">{{ email.job_title }}</td>
            <td><span class="badge-pill ps-{{ stage }}">{{ stage|replace('_',' ')|title }}</span></td>
            <td>
              {% set sidx = ['discovered','applied','followed_up','interview','offer'].index(stage) if stage in ['discovered','applied','followed_up','interview','offer'] else 4 %}
              {% if sidx < 4 %}
              <button class="btn btn-sm advance-btn" data-id="{{ email.id }}" data-stage="{{ stage }}" style="background:linear-gradient(135deg,#3b82f6,#6366f1);padding:5px 12px;font-size:11px;">Advance &rarr;</button>
              {% else %}<span style="color:#4ade80;font-size:12px;">&#x2705; Complete</span>{% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="empty-state">
      <p>No applications tracked yet. Start a campaign to populate your pipeline!</p>
      <a href="/new-campaign" class="btn btn-sm">&#x1F680; Start Campaign</a>
    </div>
    {% endif %}'''

if old_table not in content:
    # Try alternative with different whitespace
    print("WARN: Old table pattern not found exactly, trying fuzzy match...")
    # Fallback: find the if pipeline_emails block
    marker = '{% if pipeline_emails %}'
    marker_idx = content.find(marker)
    # Find matching endif
    depth = 0
    end_idx = None
    for i, ch in enumerate(content[marker_idx:], marker_idx):
        if content[i:i+2] == '{%':
            if 'if' in content[i:i+20]:
                depth += 1
            elif 'endif' in content[i:i+20]:
                depth -= 1
                if depth == 0:
                    end_idx = content.find('%}', i) + 2
                    break

    if end_idx:
        old_block = content[marker_idx:end_idx]
        print(f"Found pipeline block at {marker_idx}-{end_idx} ({len(old_block)} chars)")
    else:
        print("ERROR: Could not find pipeline_emails block!")
        exit(1)
else:
    old_block = old_table

new_rich_cards = '''    {% if pipeline_emails %}
    <div class="job-card-grid">
      {% for email in pipeline_emails[:10] %}
      {% set stage = email.pipeline_stage or 'discovered' %}
      {% set domain = email.company_domain or '' %}
      {% set logo_url = 'https://logo.clearbit.com/' + domain if domain else '' %}
      <div class="job-card-rich">
        <!-- Company Logo -->
        <div class="jc-logo">
          {% if domain %}
          <img src="{{ logo_url }}" alt="{{ email.company_name }}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" loading="lazy">
          {% endif %}
          <span class="logo-fallback" style="{% if domain %}display:none;{% endif %}width:44px;height:44px;justify-content:center;align-items:center;">{{ (email.company_name or '?')[:2] }}</span>
        </div>
        <!-- Job Info -->
        <div class="jc-info">
          <div class="jc-company">{{ email.company_name }}</div>
          <div class="jc-title">{{ email.job_title or 'Untitled Position' }}</div>
          <div class="jc-meta">
            {% if email.industry_sector %}<span class="jc-meta-item">{{ email.industry_sector }}</span>{% endif %}
            {% if email.company_size %}<span class="jc-meta-item">{{ email.company_size }}</span>{% endif %}
            {% if email.funding_stage %}<span class="jc-meta-item">{{ email.funding_stage }}</span>{% endif %}
            {% if email.job_location %}<span class="jc-meta-item">{{ email.job_location }}</span>{% endif %}
          </div>
        </div>
        <!-- Salary -->
        <div class="jc-salary">
          {% if email.salary_display %}
          <span class="jc-salary-amt {{ email.salary_tier or 'entry' }}">{{ email.salary_display }}</span>
          {% endif %}
          {% if email.has_bonus is not none %}
          <span class="jc-bonus {{ 'yes' if email.has_bonus else 'no' }}">{{ 'Bonus Included' if email.has_bonus else 'No Bonus' }}</span>
          {% endif %}
        </div>
        <!-- Match Score -->
        <div class="jc-score">
          {% set ms = email.match_score or 0 %}
          <span class="jc-score-num {{ 'high' if ms >= 80 else 'med' if ms >= 60 else 'low' }}">{{ ms }}%</span>
          <span class="jc-score-label">Match</span>
        </div>
        <!-- Time -->
        <div class="jc-time">{{ email.relative_time or 'Recently' }}<br><span style="font-size:8px;">{{ email.job_location or '' }}</span></div>
        <!-- Stage & Action -->
        <span class="badge-pill ps-{{ stage }}">{{ stage|replace('_',' ')|title }}</span>
        <div class="jc-actions">
          {% set sidx = ['discovered','applied','followed_up','interview','offer'].index(stage) if stage in ['discovered','applied','followed_up','interview','offer'] else 4 %}
          {% if sidx < 4 %}
          <button class="btn btn-sm advance-btn" data-id="{{ email.id }}" data-stage="{{ stage }}" style="background:linear-gradient(135deg,#3b82f6,#6366f1);padding:5px 12px;font-size:11px;">Advance &rarr;</button>
          {% else %}<span style="color:#22c55e;font-size:11px;font-weight:600;">Complete</span>{% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="empty-state">
      <p>No applications tracked yet. Start a campaign to populate your pipeline!</p>
      <a href="/new-campaign" class="btn btn-sm">&#x1F680; Start Campaign</a>
    </div>
    {% endif %}'''

try:
    content = content.replace(old_block, new_rich_cards)
    print("+ Replaced pipeline table with rich job cards")
except Exception as e:
    print(f"ERROR replacing: {e}")

with open(DASHBOARD_HTML, 'w', encoding='utf-8') as f:
    f.write(content)

print("=== dashboard_v2.html updated ===")
