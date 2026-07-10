import re

file_path = "web/static/css/cyberpunk.css"

with open(file_path, "r", encoding="utf-8") as f:
    css = f.read()

# 1. width -> inline-size, max-width -> max-inline-size, min-width -> min-inline-size
css = re.sub(r'\bwidth:', 'inline-size:', css)
css = re.sub(r'\bmax-width:', 'max-inline-size:', css)
css = re.sub(r'\bmin-width:', 'min-inline-size:', css)

# 2. height -> block-size, max-height -> max-block-size, min-height -> min-block-size
css = re.sub(r'\bheight:', 'block-size:', css)
css = re.sub(r'\bmax-height:', 'max-block-size:', css)
css = re.sub(r'\bmin-height:', 'min-block-size:', css)

# 3. left/right/top/bottom -> inset-inline-start/end, inset-block-start/end
css = re.sub(r'\bleft:', 'inset-inline-start:', css)
css = re.sub(r'\bright:', 'inset-inline-end:', css)
css = re.sub(r'\btop:', 'inset-block-start:', css)
css = re.sub(r'\bbottom:', 'inset-block-end:', css)

# 4. padding
css = re.sub(r'\bpadding-left:', 'padding-inline-start:', css)
css = re.sub(r'\bpadding-right:', 'padding-inline-end:', css)
css = re.sub(r'\bpadding-top:', 'padding-block-start:', css)
css = re.sub(r'\bpadding-bottom:', 'padding-block-end:', css)

# 5. margin
css = re.sub(r'\bmargin-left:', 'margin-inline-start:', css)
css = re.sub(r'\bmargin-right:', 'margin-inline-end:', css)
css = re.sub(r'\bmargin-top:', 'margin-block-start:', css)
css = re.sub(r'\bmargin-bottom:', 'margin-block-end:', css)

# 6. border
css = re.sub(r'\bborder-left:', 'border-inline-start:', css)
css = re.sub(r'\bborder-right:', 'border-inline-end:', css)
css = re.sub(r'\bborder-top:', 'border-block-start:', css)
css = re.sub(r'\bborder-bottom:', 'border-block-end:', css)

# 7. Add Glassmorphism Noise & inner borders
css = css.replace('backdrop-filter:blur(10px)', 'backdrop-filter:blur(20px) contrast(120%) brightness(110%)')
css = css.replace('-webkit-backdrop-filter:blur(10px)', '-webkit-backdrop-filter:blur(20px) contrast(120%) brightness(110%)')

# Premium Glassmorphism inner shadow on cards
css = css.replace('.card, [class*="card"], [class*="panel"], [class*="box"]{', '.card, [class*="card"], [class*="panel"], [class*="box"]{box-shadow:inset 0 1px 0 rgba(255,255,255,0.1), 0 4px 20px rgba(0, 0, 0, 0.4) !important; ')

# 8. Add Directional Transform Utility
css += "\n.dir-icon { transform: scaleX(var(--text-x-direction, 1)); }\n"
css += "[dir='rtl'] { --text-x-direction: -1; }\n"
css += "[dir='ltr'] { --text-x-direction: 1; }\n"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(css)

logger.debug("CSS Refactored successfully.")
