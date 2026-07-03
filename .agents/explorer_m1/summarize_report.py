import json
import os

report_path = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1\scan_report.json"
with open(report_path, "r", encoding="utf-8") as f:
    report = json.load(f)

summary = []

summary.append("# SUMMARY OF CSS STYLE AUDIT\n")

# 1. Physical properties
summary.append("## 1. Physical Layout Properties Analysis")
total_phys = 0
phys_by_file = {}
phys_by_prop = {}

for filename, data in report.items():
    instances = data.get("physical_instances", [])
    if not instances:
        continue
    phys_by_file[filename] = len(instances)
    for inst in instances:
        p = inst["property"]
        phys_by_prop[p] = phys_by_prop.get(p, 0) + 1
        total_phys += 1

summary.append(f"Total Physical Directional/Size Property Instances: {total_phys}")
summary.append("\n### Instances by File:")
for f, count in sorted(phys_by_file.items(), key=lambda x: x[1], reverse=True):
    summary.append(f"- `{f}`: {count} instances")

summary.append("\n### Instances by Property Type:")
for p, count in sorted(phys_by_prop.items(), key=lambda x: x[1], reverse=True):
    summary.append(f"- `{p}`: {count} instances")

# Show specific physical direction properties (margin-left, margin-right, padding-left, padding-right, left, right)
direction_props = ["margin-left", "margin-right", "padding-left", "padding-right", "left", "right"]
summary.append("\n### Physical Directional Properties (excluding width/height):")
dir_count = 0
for filename, data in report.items():
    instances = data.get("physical_instances", [])
    file_instances = [inst for inst in instances if inst["property"] in direction_props]
    if file_instances:
        summary.append(f"\n#### `{filename}` ({len(file_instances)} instances):")
        for inst in file_instances:
            dir_count += 1
            summary.append(f"  - Selector: `{inst['selector']}` | `{inst['property']}: {inst['value']}` (Line: {inst['line']})")
summary.append(f"\nTotal Physical Directional Properties: {dir_count}")

# 2. Fonts, Font-sizes, Line-heights, Letter-spacing
summary.append("\n## 2. Typography Audit")

# Cairo, Tajawal, IBM Plex Arabic references
fonts_ref = {
    "Cairo": [],
    "IBM Plex Arabic": [],
    "Tajawal": []
}
all_imported = []
for filename, data in report.items():
    if data.get("cairo_ref"):
        fonts_ref["Cairo"].append(filename)
    if data.get("ibm_ref"):
        fonts_ref["IBM Plex Arabic"].append(filename)
    if data.get("tajawal_ref"):
        fonts_ref["Tajawal"].append(filename)
    if data.get("imported_fonts"):
        all_imported.extend(data["imported_fonts"])

summary.append("\n### Font References:")
for font, files in fonts_ref.items():
    if files:
        summary.append(f"- **{font}**: Referenced in {len(files)} files: {', '.join(f'`{x}`' for x in files)}")
    else:
        summary.append(f"- **{font}**: NOT referenced in any stylesheet.")

if all_imported:
    summary.append("\n### Imported Fonts (@import):")
    for imp in set(all_imported):
        summary.append(f"- `{imp}`")

# Font sizes under 14px
fs_under_14 = []
for filename, data in report.items():
    instances = data.get("font_sizes_under_14", [])
    if instances:
        fs_under_14.append((filename, instances))

summary.append(f"\n### Font Sizes Under 14px ({sum(len(x[1]) for x in fs_under_14)} instances):")
for filename, insts in fs_under_14:
    summary.append(f"\n#### `{filename}`:")
    for inst in insts[:15]: # Show first 15 to avoid massive output
        summary.append(f"  - Selector: `{inst['selector']}` | `font-size: {inst['value']}` (Line: {inst['line']})")
    if len(insts) > 15:
        summary.append(f"  - ... and {len(insts)-15} more instances.")

# Line heights outside 1.6-2.0
lh_outside = []
for filename, data in report.items():
    instances = data.get("line_heights_outside", [])
    if instances:
        lh_outside.append((filename, instances))

summary.append(f"\n### Line Heights Outside 1.6-2.0 ({sum(len(x[1]) for x in lh_outside)} instances):")
for filename, insts in lh_outside:
    summary.append(f"\n#### `{filename}`:")
    for inst in insts[:15]:
        summary.append(f"  - Selector: `{inst['selector']}` | `line-height: {inst['value']}` (Line: {inst['line']})")
    if len(insts) > 15:
        summary.append(f"  - ... and {len(insts)-15} more instances.")

# Letter spacings applied to Arabic
ls_instances = []
for filename, data in report.items():
    instances = data.get("letter_spacings", [])
    if instances:
        ls_instances.append((filename, instances))

summary.append(f"\n### Letter Spacings ({sum(len(x[1]) for x in ls_instances)} instances):")
for filename, insts in ls_instances:
    summary.append(f"\n#### `{filename}`:")
    for inst in insts:
        summary.append(f"  - Selector: `{inst['selector']}` | `letter-spacing: {inst['value']}` (Line: {inst['line']})")

# 3. RTL Classes/Rules Hardcoded and Counterparts
summary.append("\n## 3. RTL Configuration & Overrides")
rtl_rules = []
for filename, data in report.items():
    instances = data.get("rtl_selectors", [])
    if instances:
        rtl_rules.append((filename, instances))

summary.append(f"### Explicit RTL Selectors/Rules ({sum(len(x[1]) for x in rtl_rules)} instances):")
for filename, insts in rtl_rules:
    summary.append(f"\n#### `{filename}`:")
    for inst in insts[:15]:
        summary.append(f"  - Selector: `{inst['selector']}` | declaration: `{inst['declaration']}` (Line: {inst['line']})")

# Counterparts
summary.append("\n### CSS File Counterparts (Physical vs RTL override files):")
css_files = sorted(report.keys())
rtl_counterparts = {}
non_rtl_files = []
for f in css_files:
    if f.endswith("-rtl.css"):
        base = f.replace("-rtl.css", ".css")
        if base in css_files:
            rtl_counterparts[base] = f
        else:
            rtl_counterparts[f] = None
    elif not f.endswith("-rtl.css") and (f.replace(".css", "-rtl.css") not in css_files):
        non_rtl_files.append(f)

for base, rtl in sorted(rtl_counterparts.items()):
    summary.append(f"- `{base}` <-> `{rtl}`")
if non_rtl_files:
    summary.append("\nFiles without direct `-rtl.css` counterparts:")
    for f in non_rtl_files:
        summary.append(f"- `{f}`")

# 4. Glassmorphism and Micro-animations
summary.append("\n## 4. Glassmorphism & Micro-animations")
glass_inst = []
for filename, data in report.items():
    instances = data.get("glassmorphism", [])
    if instances:
        glass_inst.append((filename, instances))

summary.append(f"\n### Glassmorphism Selectors ({sum(len(x[1]) for x in glass_inst)} instances):")
for filename, insts in glass_inst:
    summary.append(f"\n#### `{filename}`:")
    for inst in insts[:15]:
        summary.append(f"  - Selector: `{inst['selector']}` | declaration: `{inst['declaration']}` (Line: {inst['line']})")

anim_inst = []
for filename, data in report.items():
    instances = data.get("animations", [])
    kf = data.get("keyframes", [])
    if instances or kf:
        anim_inst.append((filename, instances, kf))

summary.append(f"\n### Micro-animations, Keyframes & Transitions:")
for filename, insts, kfs in anim_inst:
    summary.append(f"\n#### `{filename}`:")
    if kfs:
        summary.append("  *Keyframes:*")
        for kf in kfs:
            summary.append(f"    - Line {kf['line']}: `{kf['content']}`")
    if insts:
        summary.append("  *Transitions/Transforms/Animations:*")
        for inst in insts[:15]:
            summary.append(f"    - Selector: `{inst['selector']}` | declaration: `{inst['declaration']}` (Line: {inst['line']})")

with open(r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1\summary_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(summary))

print("Summary generated successfully!")
