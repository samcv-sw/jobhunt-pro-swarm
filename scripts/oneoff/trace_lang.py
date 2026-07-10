import os
import requests

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'

# Ensure the /lang route works correctly in PythonAnywhere caching/Cloudflare
# We might need to make sure the app processes the cookie properly. Let's trace.
logger.debug('Tracing /lang behavior on PA...')
