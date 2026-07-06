import os
import re
from html.parser import HTMLParser

TARGET_FILES = [
    "index_v3.html", "pricing_v3.html", "for_employers.html", "trust.html",
    "services_v2.html", "faq.html", "contact.html", "dashboard_v3.html",
    "upload_cv_v2.html", "ats_scorer.html", "resume_tailor.html",
    "wallet.html", "war_room.html", "battle_station.html"
]

TEMPLATES_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\en"

class TemplateAuditor(HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.inputs_without_dir = [] # list of (tag, line_no, attrs)
        self.style_tags = []         # list of style contents
        self.elements_with_inline_style = [] # (tag, line_no, style_val)
        self.elements_with_classes = []      # (tag, line_no, class_list)
        self.elements_with_physical_attrs = [] # (tag, line_no, attr_name, attr_val)
        self.buttons_and_btn_links = []      # (tag, line_no, text, classes, inline_style)
        self.current_tag = None
        self.current_line = 1
        self.in_style = False
        self.style_buffer = []

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_line = self.getpos()[0]
        attrs_dict = dict(attrs)
        
        # Track style tags
        if tag == "style":
            self.in_style = True
            self.style_buffer = []

        # Check form inputs for dir="auto"
        if tag in ["input", "textarea", "select"]:
            # Check type of input
            input_type = attrs_dict.get("type", "").lower()
            # Ignore hidden inputs or checkbox/radio where dir is not relevant, but let's check text-like inputs
            if tag == "input" and input_type in ["hidden", "checkbox", "radio", "submit", "button", "file", "image"]:
                pass
            else:
                if "dir" not in attrs_dict or attrs_dict["dir"] != "auto":
                    self.inputs_without_dir.append((tag, self.current_line, attrs_dict))

        # Check inline styles
        if "style" in attrs_dict:
            self.elements_with_inline_style.append((tag, self.current_line, attrs_dict["style"]))

        # Check classes
        if "class" in attrs_dict:
            classes = attrs_dict["class"].split()
            self.elements_with_classes.append((tag, self.current_line, classes))
            
            # Identify buttons and links styled as buttons
            is_button = tag == "button" or (tag == "a" and any("btn" in c or "button" in c for c in classes))
            if is_button:
                self.buttons_and_btn_links.append((tag, self.current_line, classes, attrs_dict.get("style", "")))
        elif tag == "button":
            self.buttons_and_btn_links.append((tag, self.current_line, [], attrs_dict.get("style", "")))

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
            self.style_tags.append("".join(self.style_buffer))
            self.style_buffer = []

    def handle_data(self, data):
        if self.in_style:
            self.style_buffer.append(data)

def audit_file(filepath, filename):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Placeholders
    placeholders = []
    # Search for lorem, todo, coming soon
    placeholder_regex = re.compile(r"\b(lorem\s+ipsum|todo|coming\s+soon)\b", re.IGNORECASE)
    for m in placeholder_regex.finditer(content):
        # get line number
        line_no = content.count("\n", 0, m.start()) + 1
        placeholders.append((m.group(0), line_no))

    # Parse HTML
    parser = TemplateAuditor(filename)
    parser.feed(content)

    # 2. Check for physical properties in inline styles or style tags
    physical_in_styles = []
    # Check style tags
    physical_style_regex = re.compile(r"\b(margin-left|margin-right|padding-left|padding-right|left|right|float|text-align)\s*:", re.IGNORECASE)
    for style_content in parser.style_tags:
        for m in physical_style_regex.finditer(style_content):
            # approximate line location inside style tags (or just list the match)
            physical_in_styles.append((m.group(1), "in <style> block"))

    # Check inline styles
    for tag, line, style_val in parser.elements_with_inline_style:
        matches = physical_style_regex.findall(style_val)
        if matches:
            for match in matches:
                physical_in_styles.append((f"{tag} style contains '{match}'", f"line {line}"))

    # 3. Check for physical Tailwind utility classes
    # e.g., ml-, mr-, pl-, pr-, left-, right-, text-left, text-right, text-justify, float-left, float-right
    # Let's be careful about right- or left- classes like border-right etc.
    # Tailwind classes of interest:
    # Margin: ml-, mr-, -ml-, -mr-
    # Padding: pl-, pr-
    # Inset: left-, right-, -left-, -right-
    # Alignment: text-left, text-right
    # Float: float-left, float-right
    # Border: border-l-, border-r-
    # Rounded: rounded-l-, rounded-r-, rounded-tl-, rounded-tr-, rounded-bl-, rounded-br-
    # Transform: translate-x- (which is physical, though maybe acceptable but let's note it)
    physical_tailwind_classes = []
    physical_tw_pattern = re.compile(r"^-?(ml|mr|pl|pr|left|right|text-left|text-right|float-left|float-right|border-l|border-r|rounded-l|rounded-r)-\w+$")
    
    for tag, line, classes in parser.elements_with_classes:
        for c in classes:
            if physical_tw_pattern.match(c):
                physical_tailwind_classes.append((c, tag, line))

    # 4. Check typography and font-size
    # Look for inline style font-family or font-size
    font_issues = []
    # We want to identify font sizes under 16px (e.g. text-xs, text-sm, or inline font-size: < 16px)
    font_size_inline_pattern = re.compile(r"font-size\s*:\s*(\d+)px", re.IGNORECASE)
    for tag, line, style_val in parser.elements_with_inline_style:
        # Check inline font-size
        for val in font_size_inline_pattern.findall(style_val):
            size = int(val)
            if size < 16:
                font_issues.append((f"inline font-size {size}px (below 16px)", tag, line))
        # Check inline font-family (if any)
        if "font-family" in style_val:
            if not ("inter" in style_val.lower() or "outfit" in style_val.lower() or "sans-serif" in style_val.lower()):
                font_issues.append((f"inline font-family '{style_val}' is not Inter/Outfit", tag, line))

    # Check style tags for font size < 16px or font family not Inter/Outfit
    for style_content in parser.style_tags:
        for val in font_size_inline_pattern.findall(style_content):
            size = int(val)
            if size < 16:
                font_issues.append((f"style block font-size {size}px (below 16px)", "style", "style tag"))
        # font family in style tags
        ff_matches = re.findall(r"font-family\s*:\s*([^;}\n]+)", style_content, re.IGNORECASE)
        for ff in ff_matches:
            if not ("inter" in ff.lower() or "outfit" in ff.lower() or "inherit" in ff.lower() or "sans-serif" in ff.lower()):
                font_issues.append((f"style block font-family '{ff.strip()}' is not Inter/Outfit", "style", "style tag"))

    # Check Tailwind classes for small text
    small_tw_classes = ["text-xs", "text-sm", "text-[10px]", "text-[11px]", "text-[12px]", "text-[13px]", "text-[14px]", "text-[15px]"]
    for tag, line, classes in parser.elements_with_classes:
        for c in classes:
            if c in small_tw_classes:
                font_issues.append((f"Tailwind class '{c}' (below 16px)", tag, line))

    # 5. Check if dark gradient background and glassmorphism styles exist
    # Let's look for background gradient classes: e.g. bg-gradient-to-r, bg-gradient-to-b, bg-slate-950, etc.
    # or background styles in CSS.
    # Let's look for glassmorphism classes: e.g. glass, bg-white/5, backdrop-blur-, bg-opacity-, etc.
    has_gradient_bg = False
    has_glass_card = False
    
    # Check if "glass" class or custom card class is used
    glass_terms = ["glass", "backdrop-blur", "bg-opacity", "backdrop-filter"]
    gradient_terms = ["bg-gradient", "from-", "to-", "linear-gradient", "radial-gradient"]
    
    for tag, line, classes in parser.elements_with_classes:
        for c in classes:
            if any(gt in c for gt in gradient_terms):
                has_gradient_bg = True
            if any(gt in c for gt in glass_terms):
                has_glass_card = True
                
    # Also check inline styles and style blocks
    for style_content in parser.style_tags + [style_val for _, _, style_val in parser.elements_with_inline_style]:
        if any(gt in style_content for gt in gradient_terms):
            has_gradient_bg = True
        if any(gt in style_content for gt in glass_terms):
            has_glass_card = True

    # 6. Check hover transform and hover shadow for buttons/links
    hover_issues = []
    for tag, line, classes, inline_style in parser.buttons_and_btn_links:
        # Check classes for hover:transform (or hover:scale- or hover:-translate-y-)
        # and hover:shadow (or hover:box-shadow)
        has_hover_transform = False
        has_hover_shadow = False
        
        # Check Tailwind class hover states
        for c in classes:
            if c.startswith("hover:") and ("transform" in c or "scale" in c or "translate" in c or "shadow" in c):
                if "shadow" in c:
                    has_hover_shadow = True
                else:
                    has_hover_transform = True
                    
        # Check inline styles or classnames for explicit hover state rules
        # Let's inspect classes for hover rules. Often, custom classes like `.btn` or `.btn-submit` have transitions defined in CSS.
        # Let's check if the class list has a class that is defined in the style block.
        # Let's look inside style blocks for hover styles for this tag or class.
        for c in classes:
            # check style tags for .classname:hover
            pattern = re.compile(r"\." + re.escape(c) + r"\s*:hover\s*\{([^}]+)\}", re.IGNORECASE)
            for style_content in parser.style_tags:
                for match in pattern.finditer(style_content):
                    hover_rules = match.group(1)
                    if "transform" in hover_rules or "translate" in hover_rules or "scale" in hover_rules:
                        has_hover_transform = True
                    if "box-shadow" in hover_rules or "shadow" in hover_rules:
                        has_hover_shadow = True

        # Check tag name:hover in style blocks
        tag_hover_pattern = re.compile(tag + r"\s*:hover\s*\{([^}]+)\}", re.IGNORECASE)
        for style_content in parser.style_tags:
            for match in tag_hover_pattern.finditer(style_content):
                hover_rules = match.group(1)
                if "transform" in hover_rules or "translate" in hover_rules or "scale" in hover_rules:
                    has_hover_transform = True
                if "box-shadow" in hover_rules or "shadow" in hover_rules:
                    has_hover_shadow = True

        # Check if the class is button/btn and it's using global transition (which is ok, but we need to check if hover styles exist)
        if not (has_hover_transform and has_hover_shadow):
            missing = []
            if not has_hover_transform:
                missing.append("hover:transform")
            if not has_hover_shadow:
                missing.append("hover:box-shadow")
            hover_issues.append((f"Button/Link is missing {', '.join(missing)}", tag, line, classes))

    return {
        "placeholders": placeholders,
        "inputs_without_dir": parser.inputs_without_dir,
        "physical_in_styles": physical_in_styles,
        "physical_tailwind_classes": physical_tailwind_classes,
        "font_issues": font_issues,
        "has_gradient_bg": has_gradient_bg,
        "has_glass_card": has_glass_card,
        "hover_issues": hover_issues
    }

def main():
    results = {}
    for filename in TARGET_FILES:
        filepath = os.path.join(TEMPLATES_DIR, filename)
        if not os.path.exists(filepath):
            results[filename] = {"error": "File does not exist"}
            continue
        try:
            results[filename] = audit_file(filepath, filename)
        except Exception as e:
            results[filename] = {"error": str(e)}

    # Write summary to file
    report_path = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_2\raw_audit_report.txt"
    with open(report_path, "w", encoding="utf-8") as out:
        for filename, res in results.items():
            out.write(f"=== {filename} ===\n")
            if "error" in res:
                out.write(f"Error: {res['error']}\n\n")
                continue
            
            out.write(f"Placeholders: {len(res['placeholders'])} found\n")
            for text, line in res["placeholders"]:
                out.write(f"  - '{text}' at line {line}\n")
                
            out.write(f"Inputs without dir='auto': {len(res['inputs_without_dir'])} found\n")
            for tag, line, attrs in res["inputs_without_dir"]:
                out.write(f"  - <{tag}> at line {line} (id: {attrs.get('id', 'N/A')}, name: {attrs.get('name', 'N/A')})\n")

            out.write(f"Physical CSS properties in styles: {len(res['physical_in_styles'])} found\n")
            for desc, loc in res["physical_in_styles"]:
                out.write(f"  - {desc} ({loc})\n")

            out.write(f"Physical Tailwind classes: {len(res['physical_tailwind_classes'])} found\n")
            for c, tag, line in res["physical_tailwind_classes"]:
                out.write(f"  - Class '{c}' in <{tag}> at line {line}\n")

            out.write(f"Typography/Font size issues: {len(res['font_issues'])} found\n")
            for issue, tag, line in res["font_issues"]:
                out.write(f"  - {issue} in <{tag}> at line {line}\n")

            out.write(f"Has Gradient BG: {res['has_gradient_bg']}, Has Glass Card: {res['has_glass_card']}\n")
            
            out.write(f"Buttons/Links with missing hover styles: {len(res['hover_issues'])} found\n")
            for desc, tag, line, classes in res["hover_issues"]:
                out.write(f"  - {desc} in <{tag}> at line {line} (classes: {classes})\n")
            out.write("\n")

if __name__ == "__main__":
    main()
