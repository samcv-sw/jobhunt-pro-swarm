import re

filepath = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\app_v2.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add imports if not present
if "from web.routers import seo" not in content:
    content = content.replace("from web.routers import auth, dashboard", "from web.routers import auth, dashboard, seo")
    
if "from core.i18n_middleware import I18nMiddleware" not in content:
    content = content.replace("from fastapi import FastAPI, Request", "from fastapi import FastAPI, Request\nfrom core.i18n_middleware import I18nMiddleware")

# Add SEO router
if "app.include_router(seo.router)" not in content:
    content = content.replace("app.include_router(dashboard.router)", "app.include_router(dashboard.router)\napp.include_router(seo.router)")

# Add middleware
if "app.add_middleware(I18nMiddleware)" not in content:
    content = content.replace("app = FastAPI(", "app = FastAPI(\napp.add_middleware(I18nMiddleware)")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Injected SEO router and i18n middleware into app_v2.py")
