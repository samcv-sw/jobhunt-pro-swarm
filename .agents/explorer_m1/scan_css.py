import os
import re
import json

css_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css"
files = [f for f in os.listdir(css_dir) if f.endswith(".css")]

report = {}

# Physical properties regex: property followed by colon
physical_props_rx = re.compile(r"\b(margin-left|margin-right|padding-left|padding-right|left|right|width|height)\s*:", re.IGNORECASE)

# Font size regex: e.g., font-size: 12px or font-size:0.8rem
font_size_rx = re.compile(r"\bfont-size\s*:\s*([^;}]+)", re.IGNORECASE)

# Line height regex
line_height_rx = re.compile(r"\bline-height\s*:\s*([^;}]+)", re.IGNORECASE)

# Letter spacing regex
letter_spacing_rx = re.compile(r"\bletter-spacing\s*:\s*([^;}]+)", re.IGNORECASE)

# Font family regex
font_family_rx = re.compile(r"\bfont-family\s*:\s*([^;}]+)", re.IGNORECASE)

# Glassmorphism/Micro-animation markers
backdrop_filter_rx = re.compile(r"\bbackdrop-filter\s*:", re.IGNORECASE)
saturate_rx = re.compile(r"\bsaturate\s*\(", re.IGNORECASE)
transparent_border_rx = re.compile(r"\bborder\s*:\s*[^;}]*(rgba|hsla|transparent)", re.IGNORECASE)
animation_rx = re.compile(r"\banimation\s*:", re.IGNORECASE)
keyframes_rx = re.compile(r"@keyframes\b", re.IGNORECASE)
transition_rx = re.compile(r"\btransition\s*:", re.IGNORECASE)

# RTL selectors
rtl_selector_rx = re.compile(r"(\[dir\s*=\s*[\"']?rtl[\"']?\]|\.rtl|\:lang\(ar\))", re.IGNORECASE)

def parse_css_file(filename):
    filepath = os.path.join(css_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # We also want to locate where rules are defined, but since CSS might be minified (single line),
    # let's analyze line-by-line AND look at the overall content.
    # For minified files, splitting by ';' or '{'/'}' might be better to find blocks.
    # Let's break the CSS into rules/declarations to get better context.
    # A simple CSS parser state machine or splitting by rules:
    
    lines = content.splitlines()
    is_minified = len(lines) < 10 and len(content) > 1000
    
    # If minified, let's prettify/split it by ';' and '{'/'}' for analysis context
    blocks = []
    if is_minified:
        # Simple splitting that preserves structure roughly
        raw_blocks = re.split(r"([{}])", content)
        current_selector = ""
        for i, val in enumerate(raw_blocks):
            val = val.strip()
            if not val:
                continue
            if val == "{":
                if i > 0:
                    current_selector = raw_blocks[i-1].strip()
            elif val == "}":
                pass
            else:
                # This is either a selector or declarations
                if ";" in val or ":" in val:
                    # declarations
                    decls = val.split(";")
                    for decl in decls:
                        decl = decl.strip()
                        if decl:
                            blocks.append({
                                "selector": current_selector,
                                "declaration": decl,
                                "line_num": 1,
                                "raw": f"{current_selector} {{ {decl} }}"
                            })
                else:
                    # selector
                    pass
    else:
        # Not minified, we can do line-by-line analysis and track the current selector
        current_selector = ""
        for line_idx, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            # Simple selector tracking
            if "{" in line:
                current_selector = line.split("{")[0].strip()
            
            # Extract declarations on this line
            decls = line.split(";")
            for decl in decls:
                decl = decl.strip()
                if ":" in decl:
                    # check if this is inside a rule block
                    blocks.append({
                        "selector": current_selector,
                        "declaration": decl,
                        "line_num": line_idx,
                        "raw": line
                    })

    # Let's run checks on blocks
    physical_instances = []
    font_sizes_under_14 = []
    line_heights_outside = []
    letter_spacings = []
    font_families = []
    glassmorphism = []
    animations = []
    rtl_selectors = []
    
    # Check overall content for `@keyframes` or `@import`
    imported_fonts = re.findall(r"@import\s+url\([^)]+\)", content)
    cairo_ref = "cairo" in content.lower()
    ibm_ref = "ibm plex arabic" in content.lower()
    tajawal_ref = "tajawal" in content.lower()
    
    for b in blocks:
        decl = b["declaration"]
        sel = b["selector"]
        line_num = b["line_num"]
        
        # 1. Physical properties
        m = physical_props_rx.search(decl)
        if m:
            prop = m.group(1).lower()
            val = decl.split(":")[1].strip()
            physical_instances.append({
                "selector": sel,
                "property": prop,
                "value": val,
                "line": line_num,
                "raw": b["raw"]
            })
            
        # 2. Font sizes
        m_fs = font_size_rx.search(decl)
        if m_fs:
            fs_val = m_fs.group(1).strip()
            # check if under 14px
            # parse numeric px value
            px_match = re.match(r"^(\d+(?:\.\d+)?)\s*px", fs_val)
            if px_match:
                px_val = float(px_match.group(1))
                if px_val < 14.0:
                    font_sizes_under_14.append({
                        "selector": sel,
                        "value": fs_val,
                        "line": line_num,
                        "raw": b["raw"]
                    })
            else:
                # also report rem/em if they might be < 14px (e.g. < 0.875rem or 0.8rem)
                rem_match = re.match(r"^(\d+(?:\.\d+)?)\s*rem", fs_val)
                if rem_match:
                    rem_val = float(rem_match.group(1))
                    if rem_val < 0.875:
                        font_sizes_under_14.append({
                            "selector": sel,
                            "value": fs_val,
                            "line": line_num,
                            "raw": b["raw"]
                        })
                        
        # 3. Line heights
        m_lh = line_height_rx.search(decl)
        if m_lh:
            lh_val = m_lh.group(1).strip()
            # check if numeric and outside 1.6 to 2.0
            num_match = re.match(r"^(\d+(?:\.\d+)?)$", lh_val)
            if num_match:
                val_num = float(num_match.group(1))
                # Skip resets (like line-height: 1 or 1.2 for headings/icons)
                # But let's flag body/content text if line-height is outside 1.6 - 2.0
                if val_num < 1.6 or val_num > 2.0:
                    line_heights_outside.append({
                        "selector": sel,
                        "value": lh_val,
                        "line": line_num,
                        "raw": b["raw"]
                    })
            else:
                # px values
                px_match = re.match(r"^(\d+(?:\.\d+)?)\s*px", lh_val)
                if px_match:
                    px_val = float(px_match.group(1))
                    # assuming base font is 16px, 1.6 of 16 is 25.6px.
                    # let's list it if it's explicitly px and looks too small or large
                    pass

        # 4. Letter spacing
        m_ls = letter_spacing_rx.search(decl)
        if m_ls:
            ls_val = m_ls.group(1).strip()
            # check if it is applied to Arabic (e.g. selectors that might contain body, p, or ar/rtl)
            # or if it's just letter-spacing in general
            letter_spacings.append({
                "selector": sel,
                "value": ls_val,
                "line": line_num,
                "raw": b["raw"]
            })
            
        # 5. Font families
        m_ff = font_family_rx.search(decl)
        if m_ff:
            ff_val = m_ff.group(1).strip()
            font_families.append({
                "selector": sel,
                "value": ff_val,
                "line": line_num,
                "raw": b["raw"]
            })

        # 6. Glassmorphism
        if backdrop_filter_rx.search(decl) or saturate_rx.search(decl) or transparent_border_rx.search(decl):
            glassmorphism.append({
                "selector": sel,
                "declaration": decl,
                "line": line_num,
                "raw": b["raw"]
            })

        # 7. Animations/Transitions
        if animation_rx.search(decl) or transition_rx.search(decl) or "transform" in decl:
            animations.append({
                "selector": sel,
                "declaration": decl,
                "line": line_num,
                "raw": b["raw"]
            })
            
        # 8. RTL rules/selectors
        if rtl_selector_rx.search(sel):
            rtl_selectors.append({
                "selector": sel,
                "declaration": decl,
                "line": line_num,
                "raw": b["raw"]
            })

    # Find keyframes
    kf_matches = []
    for line_idx, line in enumerate(lines, 1):
        if keyframes_rx.search(line):
            kf_matches.append({
                "line": line_idx,
                "content": line.strip()
            })

    report[filename] = {
        "is_minified": is_minified,
        "cairo_ref": cairo_ref,
        "ibm_ref": ibm_ref,
        "tajawal_ref": tajawal_ref,
        "imported_fonts": imported_fonts,
        "physical_instances": physical_instances,
        "font_sizes_under_14": font_sizes_under_14,
        "line_heights_outside": line_heights_outside,
        "letter_spacings": letter_spacings,
        "font_families": font_families,
        "glassmorphism": glassmorphism,
        "animations": animations,
        "rtl_selectors": rtl_selectors,
        "keyframes": kf_matches
    }

for f in files:
    parse_css_file(f)

# Save result to json
with open(r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1\scan_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("Scan complete! Output written to scan_report.json")
