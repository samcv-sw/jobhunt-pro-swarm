import re

with open("web/templates/pricing_v3.html", "r", encoding="utf-8") as f:
    content = f.read()

tokens = """
:root {
  /* Design Tokens */
  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-4: 32px;
  --space-5: 48px;
  --space-6: 64px;
  --space-8: 96px;
  --space-10: 128px;
  
  --text-main: #ffffff;
  --text-secondary: #e2e8f0;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  
  --accent-primary: #6366f1;
  --accent-primary-dim: rgba(99, 102, 241, 0.1);
  --accent-secondary: #a855f7;
  --accent-danger: #ef4444;
  --accent-success: #10b981;
  
  --bg-card: rgba(30, 41, 59, 0.7);
  --border-glass: rgba(255, 255, 255, 0.1);
  --border-glass-hover: rgba(255, 255, 255, 0.2);
  
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  
  --font-mono: 'Courier New', Courier, monospace;
  
  --shadow-lg: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
  --shadow-glow-primary: 0 0 20px rgba(99, 102, 241, 0.4);
  
  --transition-fast: 0.2s ease;
  --transition-base: 0.3s ease;
}
"""

if "--space-3:" not in content:
    content = content.replace("/* ── Animations ── */", tokens + "\n/* ── Animations ── */")

with open("web/templates/pricing_v3.html", "w", encoding="utf-8") as f:
    f.write(content)
