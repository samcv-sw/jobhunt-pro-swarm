import sqlite3
import urllib.request
import os
import json

PA_TOKEN = "874997673d6b9787dc4e3a938dd45a1930f1c85c"
USER = "JHFGUF"
DOMAIN = "jhfguf.pythonanywhere.com"

# PythonAnywhere API has a feature to execute a console command, but it's complex.
# Instead, we upload a small script and run it via PA API consoles endpoint or just run it via my api script.
