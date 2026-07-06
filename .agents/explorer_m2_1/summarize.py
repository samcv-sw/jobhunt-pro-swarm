import json
import os
import sys

# Configure stdout and stderr to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

raw_json = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_1\audit_raw.json"
out_md = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_1\analysis.md"

with open(raw_json, "r", encoding="utf-8") as f:
    data = json.load(f)

markdown = []
markdown.append("# Arabic HTML Templates Deep Content & Visual Audit Report")
markdown.append(f"\n**Audit Date**: 2026-07-06")
markdown.append("\n## Executive Summary\n")
markdown.append("This audit performs a deep analysis of 14 key Arabic HTML templates in the `web/templates/` folder against the global system rules and user specifications. The parameters evaluated include:")
markdown.append("1. **Placeholder text detection** (e.g., TODO, Lorem Ipsum, Coming soon, محتوى قريباً).")
markdown.append("2. **Visual theme alignment** (Dark gradient backgrounds, premium glassmorphism card styles).")
markdown.append("3. **Interactions** (Presence of hover:transform and hover:box-shadow on buttons/links).")
markdown.append("4. **Arabic Typography rules** (Use of Cairo/Tajawal, min 16px font-size, line-height 1.6-2.0, absolute absence of letter-spacing).")
markdown.append("5. **Form field internationalization** (Presence of `dir=\"auto\"` on all inputs, select, and textarea elements).")
markdown.append("6. **RTL layout compatibility** (Use of CSS Logical Properties instead of physical properties like margin-left/padding-right).")

markdown.append("\n---")
markdown.append("\n## High-Level Matrix\n")
markdown.append("| Template File | Dark Gradient BG | Glassmorphism | Buttons Hover | Typo Style (Min 16px) | Typo (No Letter-Spacing) | Form Input `dir=\"auto\"` | Logical CSS | Placeholders |")
markdown.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

for filename, report in data.items():
    if not report.get("exists", False):
        markdown.append(f"| `{filename}` | *Not Found* | - | - | - | - | - | - | - |")
        continue
    
    # BG status
    bg_ok = "✅ Yes" if (report["dark_gradient_bg"]["classes"] or report["dark_gradient_bg"]["style_vars"]) else "❌ No"
    
    # Glassmorphism
    glass_ok = "✅ Yes" if report["glassmorphism_cards"] else "❌ No"
    
    # Buttons hover
    btn_ok = "✅ All OK" if not report["buttons_hover"] else f"❌ {len(report['buttons_hover'])} missing"
    
    # Typography Font-Size
    typo_size = "✅ All >=16px" if not report["typography"]["size_violations"] else f"❌ {len(report['typography']['size_violations'])} under 16px"
    
    # Typography Letter-spacing
    typo_spacing = "✅ OK" if not report["typography"]["letter_spacing_violations"] else f"❌ {len(report['typography']['letter_spacing_violations'])} violations"
    
    # Form input dir="auto"
    input_ok = "✅ All OK" if not report["inputs_dir_auto"] else f"❌ {len(report['inputs_dir_auto'])} missing"
    
    # Physical CSS
    phys_ok = "✅ Logical" if not report["physical_properties"] else f"❌ {len(report['physical_properties'])} physical"
    
    # Placeholders
    placeholders_ok = "✅ None" if not report["placeholders"] else f"⚠️ {len(report['placeholders'])} found"
    
    markdown.append(f"| `{filename}` | {bg_ok} | {glass_ok} | {btn_ok} | {typo_size} | {typo_spacing} | {input_ok} | {phys_ok} | {placeholders_ok} |")

markdown.append("\n---")
markdown.append("\n## Detailed Template Audits\n")

for filename, report in data.items():
    if not report.get("exists", False):
        markdown.append(f"### `{filename}` (NOT FOUND)\n")
        continue
        
    markdown.append(f"### `{filename}`\n")
    
    # 1. Placeholders
    markdown.append("#### 1. Placeholder Text")
    if report["placeholders"]:
        markdown.append("The following placeholder texts/attributes were detected:")
        for idx, line in report["placeholders"]:
            markdown.append(f"- **Line {idx}**: `{line}`")
    else:
        markdown.append("- ✅ No placeholder texts or standard 'TODO'/'Lorem Ipsum' markers were found.")
    markdown.append("")
    
    # 2. Dark Gradient Background and Glassmorphism Card Style
    markdown.append("#### 2. Visual Theme & Style")
    # Background
    if report["dark_gradient_bg"]["classes"] or report["dark_gradient_bg"]["style_vars"]:
        markdown.append("- **Dark Gradient Background**: Detected. ")
        if report["dark_gradient_bg"]["classes"]:
            markdown.append(f"  - Classes: `{report['dark_gradient_bg']['classes']}`")
        if report["dark_gradient_bg"]["style_vars"]:
            markdown.append(f"  - Styles: `{report['dark_gradient_bg']['style_vars']}`")
    else:
        markdown.append("- ❌ **Dark Gradient Background**: Not explicitly declared in body classes or standard variables.")
        
    # Glassmorphism
    if report["glassmorphism_cards"]:
        markdown.append("- **Glassmorphism Card Style**: Detected. ")
        markdown.append(f"  - Verified selectors/classes on lines: {', '.join(str(x[0]) for x in report['glassmorphism_cards'][:5])}" + ("..." if len(report['glassmorphism_cards']) > 5 else ""))
    else:
        markdown.append("- ❌ **Glassmorphism Card Style**: Not explicitly detected via classes (`backdrop-blur`, `bg-white/`, `glass`).")
    markdown.append("")
    
    # 3. Hover effects on buttons & links
    markdown.append("#### 3. Button/Link Hover Interactions")
    if report["buttons_hover"]:
        markdown.append(f"- ❌ {len(report['buttons_hover'])} buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:")
        for idx, tag, status in report["buttons_hover"][:10]:
            transform_str = "has transform" if status["has_hover_transform"] else "missing transform"
            shadow_str = "has shadow" if status["has_hover_shadow"] else "missing shadow"
            markdown.append(f"  - **Line {idx}**: `{tag}` ({transform_str}, {shadow_str})")
        if len(report["buttons_hover"]) > 10:
            markdown.append(f"  - ... and {len(report['buttons_hover']) - 10} more buttons.")
    else:
        markdown.append("- ✅ All detected button/link elements properly declare hover transform and shadow classes.")
    markdown.append("")
    
    # 4. Arabic Typography
    markdown.append("#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)")
    # Font Families
    families = report["typography"]["font_families"]
    styles_str = ", ".join(families["styles"]) if families["styles"] else "None (inherits)"
    classes_str = ", ".join(families["classes"]) if families["classes"] else "None (inherits)"
    markdown.append(f"- **Font Families**: Styles: `{styles_str}` | Classes: `{classes_str}`")
    
    # Size violations
    if report["typography"]["size_violations"]:
        markdown.append(f"- ❌ **Font-Size Violations** ({len(report['typography']['size_violations'])} instances where font size < 16px on Arabic content):")
        for idx, line in report["typography"]["size_violations"][:5]:
            markdown.append(f"  - **Line {idx}**: `{line}`")
        if len(report["typography"]["size_violations"]) > 5:
            markdown.append(f"  - ... and {len(report['typography']['size_violations']) - 5} more size violations.")
    else:
        markdown.append("- ✅ No font-size violations found (all Arabic content is >= 16px).")
        
    # Height violations
    if report["typography"]["height_violations"]:
        markdown.append(f"- ❌ **Line-Height Violations** ({len(report['typography']['height_violations'])} instances where line height is < 1.6 on Arabic content):")
        for idx, line in report["typography"]["height_violations"][:5]:
            markdown.append(f"  - **Line {idx}**: `{line}`")
        if len(report["typography"]["height_violations"]) > 5:
            markdown.append(f"  - ... and {len(report['typography']['height_violations']) - 5} more height violations.")
    else:
        markdown.append("- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).")
        
    # Letter spacing violations
    if report["typography"]["letter_spacing_violations"]:
        markdown.append(f"- ❌ **Letter-Spacing Violations** ({len(report['typography']['letter_spacing_violations'])} instances where letter-spacing/tracking classes are used on Arabic text):")
        for idx, line in report["typography"]["letter_spacing_violations"][:10]:
            markdown.append(f"  - **Line {idx}**: `{line}`")
        if len(report["typography"]["letter_spacing_violations"]) > 10:
            markdown.append(f"  - ... and {len(report['typography']['letter_spacing_violations']) - 10} more letter-spacing violations.")
    else:
        markdown.append("- ✅ No letter-spacing/tracking classes detected on Arabic text elements.")
    markdown.append("")
    
    # 5. Form inputs dir="auto"
    markdown.append("#### 5. Form Inputs `dir=\"auto\"` Alignment")
    if report["inputs_dir_auto"]:
        markdown.append(f"- ❌ **Missing `dir=\"auto\"`** on {len(report['inputs_dir_auto'])} input/select/textarea elements:")
        for idx, tag in report["inputs_dir_auto"]:
            markdown.append(f"  - **Line {idx}**: `{tag}`")
    else:
        markdown.append("- ✅ All inputs, textareas, and selects correctly define `dir=\"auto\"`.")
    markdown.append("")
    
    # 6. Logical CSS Properties
    markdown.append("#### 6. Layout Properties (Logical CSS vs Physical Layout)")
    if report["physical_properties"]:
        markdown.append(f"- ❌ **Physical CSS Properties** detected ({len(report['physical_properties'])} instances):")
        for idx, line, matches in report["physical_properties"][:10]:
            markdown.append(f"  - **Line {idx}**: `{line}` (Matched: `{matches}`)")
        if len(report["physical_properties"]) > 10:
            markdown.append(f"  - ... and {len(report['physical_properties']) - 10} more physical property uses.")
    else:
        markdown.append("- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.")
    markdown.append("\n---\n")

with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(markdown))

print("Markdown summary report written successfully.")
