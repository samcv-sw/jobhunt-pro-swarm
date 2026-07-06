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
    
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path in ('/login', '/register', '/pricing', '/privacy', '/terms'):
            func = route.endpoint
            file = inspect.getsourcefile(func)
            # Make path relative to root to avoid emoji encoding issues
            if file:
                file = os.path.relpath(file, root)
            line = inspect.getsourcelines(func)[1]
            out_str = f"Path: {route.path} -> Func: {func.__name__} in {file}:{line}"
            print(out_str.encode('ascii', errors='replace').decode('ascii'))
except Exception as e:
    import traceback
    traceback.print_exc()
