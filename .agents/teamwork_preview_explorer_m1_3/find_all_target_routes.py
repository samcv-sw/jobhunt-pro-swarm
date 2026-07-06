import os
import sys

# Set env variables needed to load app_v2
os.environ['JWT_SECRET_KEY'] = 'test_secret'
os.environ['SECRET_KEY'] = 'test_secret'

# Add root folder to python path so web package can be imported
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(root)

try:
    from web.app_v2 import app
    from fastapi.routing import APIRoute
    import inspect
    
    def print_routes(app_or_router, prefix=""):
        for route in app_or_router.routes:
            if isinstance(route, APIRoute):
                full_path = prefix + route.path
                if any(t in full_path for t in ('login', 'register', 'pricing', 'privacy', 'terms')):
                    func = route.endpoint
                    file = inspect.getsourcefile(func)
                    if file:
                        file = os.path.relpath(file, root)
                    line = inspect.getsourcelines(func)[1]
                    out_str = f"Path: {full_path} -> Func: {func.__name__} in {file}:{line}"
                    print(out_str.encode('ascii', errors='replace').decode('ascii'))
            elif hasattr(route, "routes"):
                # Nested router
                print_routes(route, prefix + (getattr(route, "path", "") or ""))
            elif hasattr(route, "app") and hasattr(route.app, "routes"):
                # Sub-app or mount
                print_routes(route.app, prefix + route.path)

    print("--- TARGTET ROUTE SEARCH START ---")
    print_routes(app)
    print("--- TARGTET ROUTE SEARCH END ---")
except Exception as e:
    import traceback
    traceback.print_exc()
