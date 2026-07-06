import os
import sys

# Set env variables needed to load app
os.environ['JWT_SECRET_KEY'] = 'test_secret'
os.environ['SECRET_KEY'] = 'test_secret'

# Add root folder to python path so web package can be imported
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(root)

try:
    from web.app import app
    from fastapi.routing import APIRoute
    
    def get_routes(app_or_router, prefix=""):
        paths = []
        for route in app_or_router.routes:
            if isinstance(route, APIRoute):
                paths.append(prefix + route.path)
            elif hasattr(route, "routes"):
                # Nested router
                paths.extend(get_routes(route, prefix + (getattr(route, "path", "") or "")))
            elif hasattr(route, "app") and hasattr(route.app, "routes"):
                # Sub-app or mount
                paths.extend(get_routes(route.app, prefix + route.path))
            else:
                # Other types
                path = getattr(route, "path", None)
                if path:
                    paths.append(prefix + path)
                else:
                    print(f"Skipped route: {type(route)}")
        return paths

    all_paths = get_routes(app)
    routes = sorted(list(set(all_paths)))
    print("--- ROUTES LIST START ---")
    for r in routes:
        print(r)
    print("--- ROUTES LIST END ---")
except Exception as e:
    import traceback
    traceback.print_exc()
