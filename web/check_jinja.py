import os

import jinja2

env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))
errs = 0
for f in os.listdir("templates"):
    if f.endswith(".html"):
        try:
            env.parse(env.loader.get_source(env, f)[0])
        except Exception as e:
            print(f"Error in {f}: {e}")
            errs += 1
if errs == 0:
    print("All OK")
