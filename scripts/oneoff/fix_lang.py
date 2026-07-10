import os
import requests

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'

# Let's fix app_v2.py to use request in render_template if passed, so it can resolve language.
app_file = "web/app_v2.py"
with open(app_file, "r", encoding="utf-8") as f:
    content = f.read()

# We need to change render_template to check for request context for language
new_render_template = """
def render_template(name: str, **context):
    \"\"\"Render a Jinja2 template to HTML string, handling undefined variables gracefully.\"\"\"
    try:
        if "VERSION" not in context:
            context["VERSION"] = config.VERSION
            
        # Add language check if request is in context
        request = context.get("request")
        if request:
            lang = request.cookies.get("lang", "ar")
            if lang == "en":
                en_name = f"en/{name}"
                en_path = template_dir / en_name
                if en_path.exists():
                    name = en_name
                    
        t = jinja_env.get_template(name)
        return t.render(**context)
    except jinja2.TemplateNotFound:
        return f"<!-- Template {name} not found -->"
    except Exception as e:
        logger.error(f"Error rendering template {name}: {e}")
        return f"<!-- Error rendering template {name}: {e} -->"
"""

import re
content = re.sub(r'def render_template\(name: str, \*\*context\):.*?return f"<!-- Error rendering template \{name\}: \{e\} -->"', new_render_template.strip(), content, flags=re.DOTALL)

with open(app_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated render_template in app_v2.py locally.")
