# ==============================================================================
# PYTHONANYWHERE WSGI CONFIGURATION SCRIPT FOR JOBHUNT PRO
# ==============================================================================
# Copy this entire file's content into your PythonAnywhere WSGI configuration file.
# You can find it in the Web tab -> "WSGI configuration file".
# It usually looks like: /var/www/jhfguf_pythonanywhere_com_wsgi.py
# ==============================================================================

import sys
import os

# 1. ADD YOUR PROJECT DIRECTORY TO THE PATH
# Replace '/home/jhfguf/jobhunt-pro-swarm/web' with the actual path 
# where your app_v2.py file is located on PythonAnywhere.
project_home = '/home/jhfguf/jobhunt-pro-swarm/web'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 2. SET ENVIRONMENT VARIABLES (Optional but recommended)
os.environ['SECRET_KEY'] = 'YOUR_SUPER_SECRET_KEY'
# os.environ['SUPABASE_MODE'] = '1'
# os.environ['DATABASE_URL'] = 'postgres://your_neon_url_here'

# 3. IMPORT THE WSGI APP FROM APP_V2
# Our code uses a2wsgi to bridge FastAPI to WSGI via the `wsgi_app` variable.

# DONE! PythonAnywhere will now route all traffic to FastAPI correctly.
