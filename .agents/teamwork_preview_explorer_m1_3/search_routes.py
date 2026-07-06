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
    for r in app.routes:
        if 'login' in r.path or 'register' in r.path or 'pricing' in r.path or 'privacy' in r.path or 'terms' in r.path:
            print(f"Path: {r.path} | Type: {type(r)}")
except Exception as e:
    import traceback
    traceback.print_exc()
