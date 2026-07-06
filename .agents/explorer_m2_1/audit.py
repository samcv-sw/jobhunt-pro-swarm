import os
import re
import sys

# Configure stdout and stderr to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

TEMPLATES_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"
TARGET_FILES = [
    "index_v3.html", "pricing_v3.html", "for_employers.html", "trust.html",
    "services_v2.html", "faq.html", "contact.html", "dashboard_v3.html",
    "upload_cv_v2.html", "ats_scorer.html", "resume_tailor.html", "wallet.html",
    "war_room.html", "battle_station.html"
]

def check_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    filename = os.path.basename(file_path)
    report = {
        "filename": filename,
        "exists": True,
        "placeholders": [],
        "dark_gradient_bg": None,
        "glassmorphism_cards": [],
        "buttons_hover": [],
        "typography": {
            "font_families": [],
            "size_violations": [],
            "height_violations": [],
            "letter_spacing_violations": []
        },
        "inputs_dir_auto": [],
        "physical_properties": []
    }
    
    # 1. Placeholders
    # Look for "Lorem Ipsum", "TODO", "Coming soon", "محتوى قريباً", "قريباً", "placeholder"
    placeholder_patterns = [
        r"lorem\s+ipsum", r"todo", r"coming\s+soon", r"محتوى\s+قريباً", 
        r"قريباً\s+جداً", r"placeholder"
    ]
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        for pattern in placeholder_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Clean up line for report
                report["placeholders"].append((idx, line.strip()))
                break
                
    # 2. Dark gradient background & Premium glassmorphism
    # Check for body background or classes
    bg_classes = re.findall(r"class=\"[^\"]*bg-gradient[^\"]*\"", content)
    bg_style = re.findall(r"background\s*:\s*var\(--bg\)", content) or re.findall(r"background-image\s*:\s*linear-gradient", content)
    report["dark_gradient_bg"] = {
        "classes": bg_classes,
        "style_vars": bg_style
    }
    
    # Glassmorphism: backdrop-blur, bg-white/5, border-white/10, etc.
    glass_patterns = [r"backdrop-blur", r"bg-white/\d+", r"border-white/\d+", r"bg-opacity-\d+", r"glass"]
    for idx, line in enumerate(lines, 1):
        found = []
        for gp in glass_patterns:
            if re.search(gp, line):
                found.append(gp)
        if found:
            report["glassmorphism_cards"].append((idx, line.strip(), found))

    # 3. Buttons/links hover:transform & hover:box-shadow
    # Look for button tag or a tag with button classes
    button_regex = re.compile(r"<button\b[^>]*>|<a\b[^>]*class=\"[^\"]*(?:btn|button)[^\"]*\"[^>]*>", re.IGNORECASE)
    for idx, line in enumerate(lines, 1):
        match = button_regex.search(line)
        if match:
            # Check if this button line or adjacent classes have hover:transform / hover:scale / hover:shadow
            tag = match.group(0)
            has_hover_transform = any(x in tag for x in ["hover:scale", "hover:translate", "hover:-translate-y", "hover:transform", "duration-", "transition-"])
            has_hover_shadow = any(x in tag for x in ["hover:shadow", "hover:box-shadow", "hover:glow"])
            
            # Check if there is inline custom style or class
            if not (has_hover_transform and has_hover_shadow):
                report["buttons_hover"].append((idx, tag.strip(), {
                    "has_hover_transform": has_hover_transform,
                    "has_hover_shadow": has_hover_shadow
                }))

    # 4. Typography
    # Font families in style blocks or classes
    fonts_found = re.findall(r"font-family\s*:\s*([^;\}]+)", content)
    font_classes = re.findall(r"class=\"[^\"]*(font-cairo|font-tajawal|font-ibm)[^\"]*\"", content)
    report["typography"]["font_families"] = {
        "styles": list(set(fonts_found)),
        "classes": list(set(font_classes))
    }
    
    # Typography details: min 16px (violators: text-xs (12px), text-sm (14px)), line-height 1.6 to 2.0, letter-spacing (violators: tracking-)
    for idx, line in enumerate(lines, 1):
        # Font-size violations (Arabic text has text-xs or text-sm)
        # We look for text-xs or text-sm in elements with Arabic characters
        if re.search(r"[\u0600-\u06FF]", line):
            if re.search(r"\btext-(xs|sm)\b", line) or re.search(r"font-size\s*:\s*(?:1[0-5]px|1\.[0-4]rem|[0-9]px)", line):
                report["typography"]["size_violations"].append((idx, line.strip()))
            
            # Line-height violations: check for leading-none, leading-tight, leading-snug, leading-normal (all < 1.6)
            if re.search(r"\bleading-(none|tight|snug|normal)\b", line) or re.search(r"line-height\s*:\s*(?:1\.[0-5]\b|[0-9]px|100%|110%|120%|130%|140%|150%)", line):
                report["typography"]["height_violations"].append((idx, line.strip()))
                
            # Letter spacing violation: tracking- (letter-spacing is not allowed in Arabic)
            if re.search(r"\btracking-", line) or re.search(r"letter-spacing\s*:", line):
                report["typography"]["letter_spacing_violations"].append((idx, line.strip()))

    # 5. Form inputs dir="auto"
    input_regex = re.compile(r"<(input|textarea|select)\b[^>]*>", re.IGNORECASE)
    for idx, line in enumerate(lines, 1):
        for match in input_regex.finditer(line):
            tag = match.group(0)
            # Skip hidden inputs or buttons
            if 'type="hidden"' in tag or 'type="submit"' in tag or 'type="button"' in tag or 'type="checkbox"' in tag or 'type="radio"' in tag:
                continue
            if 'dir="auto"' not in tag and 'dir=\'auto\'' not in tag:
                report["inputs_dir_auto"].append((idx, tag.strip()))

    # 6. Physical CSS properties vs logical properties
    # Physical: ml-, mr-, pl-, pr-, left-, right-, space-x-, inset-l, inset-r, margin-left, margin-right, padding-left, padding-right, left:, right:
    # Exclude matches like border-left or bg-left or text-left (which are sometimes acceptable or different context, but let's highlight physical layouts)
    physical_patterns = [
        r"\b(?:ml|mr|pl|pr|left|right)-\d+",
        r"\b(?:ml|mr|pl|pr|left|right)-\[",
        r"\b(?:margin|padding)-(?:left|right)\b",
        r"\b(?:left|right)\s*:\s*[^;\}]+",
    ]
    for idx, line in enumerate(lines, 1):
        found_phys = []
        for p in physical_patterns:
            matches = re.findall(p, line)
            if matches:
                found_phys.extend(matches)
        if found_phys:
            report["physical_properties"].append((idx, line.strip(), found_phys))
            
    return report

def main():
    import json
    results = {}
    for filename in TARGET_FILES:
        path = os.path.join(TEMPLATES_DIR, filename)
        if os.path.exists(path):
            results[filename] = check_file(path)
        else:
            results[filename] = {"exists": False, "filename": filename}
            
    # Save the raw results JSON
    out_json = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_1\audit_raw.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Audit completed successfully. Output written to JSON file.")

if __name__ == "__main__":
    main()
