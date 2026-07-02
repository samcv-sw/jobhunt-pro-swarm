import os
import re
from pathlib import Path
from bs4 import BeautifulSoup, Comment, Doctype, CData, ProcessingInstruction, Declaration
import html

ROOT_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = ROOT_DIR / "web" / "templates"

CSS_MAPPINGS = [
    (r'\bml-(\d+|auto|px|[-.\drem]+)\b', r'ms-\1'),
    (r'\bmr-(\d+|auto|px|[-.\drem]+)\b', r'me-\1'),
    (r'\bpl-(\d+|px|[-.\drem]+)\b', r'ps-\1'),
    (r'\bpr-(\d+|px|[-.\drem]+)\b', r'pe-\1'),
    (r'\btext-left\b', r'text-start'),
    (r'\btext-right\b', r'text-end'),
    (r'\bleft-(\d+|auto|px|[-.\drem]+)\b', r'start-\1'),
    (r'\bright-(\d+|auto|px|[-.\drem]+)\b', r'end-\1'),
    (r'\brounded-l-([a-z0-9-]+)\b', r'rounded-s-\1'),
    (r'\brounded-r-([a-z0-9-]+)\b', r'rounded-e-\1'),
    (r'\bborder-l-([a-z0-9-]+)\b', r'border-s-\1'),
    (r'\bborder-r-([a-z0-9-]+)\b', r'border-e-\1'),
    (r'\bborder-l\b', r'border-s'),
    (r'\bborder-r\b', r'border-e'),
]

def migrate_css_logical(content: str) -> str:
    for pattern, replacement in CSS_MAPPINGS:
        content = re.sub(pattern, replacement, content)
    return content

def inject_gettext(content: str) -> str:
    soup = BeautifulSoup(content, 'html.parser')
    modified = False
    
    for text_node in soup.find_all(string=True):
        if isinstance(text_node, (Comment, Doctype, CData, ProcessingInstruction, Declaration)):
            continue
            
        parent = text_node.parent
        if parent and parent.name in ['script', 'style', 'code', 'pre']:
            continue
            
        original_text = text_node.string
        stripped = original_text.strip()
        
        if not stripped:
            continue
            
        # Skip if it's already a Jinja template tag or contains braces
        if '{' in stripped or '}' in stripped:
            continue
            
        # Skip if it doesn't contain any letters (e.g. just punctuation, numbers)
        if not re.search(r'[A-Za-z]', stripped):
            continue
            
        # Escape single quotes for Jinja
        escaped_stripped = stripped.replace("'", "\\'")
        
        # We need to preserve the surrounding whitespace that was stripped
        leading_space = original_text[:len(original_text) - len(original_text.lstrip())]
        trailing_space = original_text[len(original_text.rstrip()):]
        
        new_text = f"{leading_space}{{{{ _('{escaped_stripped}') }}}}{trailing_space}"
        text_node.replace_with(new_text)
        modified = True
        
    if modified:
        # We must decode HTML entities because BeautifulSoup will escape the Jinja curly braces sometimes
        # Actually BS4 handles {{ fine, but let's just return the raw string
        return str(soup).replace('&lt;', '<').replace('&gt;', '>')
    return content

def main():
    print(f"Starting DOM Surgery on {TEMPLATES_DIR}")
    count = 0
    
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        # Skip the legacy en folder and backups
        if 'en' in dirs:
            dirs.remove('en')
        if 'templates_backup' in dirs:
            dirs.remove('templates_backup')
            
        for file in files:
            if file.endswith('.html'):
                filepath = Path(root) / file
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Pass 1: CSS Logical Properties
                content = migrate_css_logical(content)
                
                # Pass 2: Inject gettext
                content = inject_gettext(content)
                
                # Unescape some common HTML entities created by BS4 that breaks jinja
                content = html.unescape(content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                count += 1
                
    print(f"DOM Surgery complete. Modified {count} files.")

if __name__ == "__main__":
    main()
