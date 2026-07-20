import os
import re

TARGET_DIR = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

# CSS physical property mapping
CSS_REPLACEMENTS = {
    r"\bmargin-left\b": "margin-inline-start",
    r"\bmargin-right\b": "margin-inline-end",
    r"\bpadding-left\b": "padding-inline-start",
    r"\bpadding-right\b": "padding-inline-end",
    r"\bleft\s*:\s*": "inset-inline-start: ",
    r"\bright\s*:\s*": "inset-inline-end: ",
}

def translate_tailwind_class(cls_name: str) -> str:
    """Translate physical Tailwind classes to logical RTL classes."""
    # Pattern to handle screen breakpoints (e.g. md:, lg:) and negative positions (e.g. -ml-2)
    pattern = r"^([a-z0-9:-]*?)(-?)(ml|mr|pl|pr|left|right)-(.+)$"
    match = re.match(pattern, cls_name)
    if not match:
        return cls_name
    
    prefix, neg, prop, value = match.groups()
    
    # Map physical properties to logical
    prop_map = {
        "ml": "ms",
        "mr": "me",
        "pl": "ps",
        "pr": "pe",
        "left": "start",
        "right": "end"
    }
    
    new_prop = prop_map[prop]
    return f"{prefix}{neg}{new_prop}-{value}"

def refactor_classes(class_str: str) -> str:
    """Refactor class string by converting physical classes to logical ones."""
    classes = class_str.split()
    new_classes = [translate_tailwind_class(c) for c in classes]
    return " ".join(new_classes)

def process_content(content: str) -> str:
    # 1. Enforce CSS Logical Properties in inline style attributes and <style> blocks
    for pattern, replacement in CSS_REPLACEMENTS.items():
        content = re.sub(pattern, replacement, content)
    
    # 2. Translate physical Tailwind CSS classes
    def class_replacer(match):
        classes = match.group(2)
        refactored = refactor_classes(classes)
        return f'{match.group(1)}class="{refactored}"'

    content = re.sub(r'(\s)class="([^"]*)"', class_replacer, content)

    # 3. Form fields auto dir="auto"
    content = re.sub(r'<input([^>]*?)(?<!dir="auto")([^>]*?)>', lambda m: f'<input{m.group(1)}{m.group(2)} dir="auto">' if 'dir=' not in m.group(0) else m.group(0), content)
    content = re.sub(r'<textarea([^>]*?)(?<!dir="auto")([^>]*?)>', lambda m: f'<textarea{m.group(1)}{m.group(2)} dir="auto">' if 'dir=' not in m.group(0) else m.group(0), content)

    # 4. Flip directional icons
    def replace_icon(match):
        tag = match.group(1)
        if 'transform:' in tag or 'scaleX' in tag:
            return tag
        style_match = re.search(r'style\s*=\s*"([^"]*)"', tag)
        if style_match:
            style_val = style_match.group(1)
            new_style_val = style_val.rstrip('; ') + '; transform: scaleX(var(--text-x-direction, 1));'
            return tag.replace(style_match.group(0), f'style="{new_style_val}"')
        else:
            if tag.endswith('/>'):
                return tag[:-2] + ' style="transform: scaleX(var(--text-x-direction, 1));"/>'
            elif tag.endswith('>'):
                return tag[:-1] + ' style="transform: scaleX(var(--text-x-direction, 1));">'
            return tag

    content = re.sub(r'(<i[^>]*class="[^"]*(?:right|left|forward|backward|chevron)[^"]*"[^>]*>)', replace_icon, content)

    # 5. Arabic Typographic Guidelines font stack injection
    font_stack = "'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif"
    
    # If standard font declarations are found, verify Arabic typography guidelines
    def font_family_replacer(match):
        declaration = match.group(0)
        # Ensure Arabic font stack is prepended
        if 'Cairo' not in declaration and 'Tajawal' not in declaration:
            return f"font-family: {font_stack}, {match.group(1)}"
        return declaration

    content = re.sub(r'font-family\s*:\s*([^;]+)', font_family_replacer, content)
    
    # Enforce minimum font-size of 14px in styles
    def font_size_replacer(match):
        size_str = match.group(1)
        try:
            size_val = int(re.search(r'\d+', size_str).group(0))
            if size_val < 14:
                return "font-size: 14px"
        except:
            pass
        return match.group(0)

    content = re.sub(r'font-size\s*:\s*(\d+px)', font_size_replacer, content)

    # Remove letter-spacing from styles (as it breaks Arabic readability)
    content = re.sub(r'letter-spacing\s*:[^;]+;?', '', content)

    return content

def main():
    count = 0
    for root, _, files in os.walk(TARGET_DIR):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                try:
                    with open(path, encoding="utf-8") as f:
                        original = f.read()
                    
                    modified = process_content(original)
                    
                    if original != modified:
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(modified)
                        count += 1
                        print(f"[Refactored] {os.path.relpath(path, TARGET_DIR)}")
                except Exception as e:
                    print(f"[Error] Failed to process {file}: {e}")
                    
    print(f"\nSuccessfully refactored {count} files.")

if __name__ == "__main__":
    main()
