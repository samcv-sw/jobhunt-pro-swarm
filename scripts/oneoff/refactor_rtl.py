import os
import re

directory = "web/templates"

replacements = {
    r"\bml-": "ms-",
    r"\bmr-": "me-",
    r"\bpl-": "ps-",
    r"\bpr-": "pe-",
    r"\btext-left\b": "text-start",
    r"\btext-right\b": "text-end",
    r"\bleft-": "start-",
    r"\bright-": "end-",
    r"\bborder-l-": "border-s-",
    r"\bborder-r-": "border-e-",
    r"\brounded-l-": "rounded-s-",
    r"\brounded-r-": "rounded-e-",
    r"\brounded-tl-": "rounded-ss-",
    r"\brounded-tr-": "rounded-se-",
    r"\brounded-bl-": "rounded-es-",
    r"\brounded-br-": "rounded-ee-"
}

count = 0
for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = re.sub(old, new, new_content)
                
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1
                logger.debug(f"Updated {path}")

logger.debug(f"Refactored RTL logical properties in {count} templates.")
