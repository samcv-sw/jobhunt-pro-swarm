import os

base_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\test_env\Lib\site-packages"

targets = [
    os.path.join(base_dir, "_cffi_backend.cp312-win_amd64.pyd"),
    os.path.join(base_dir, "sqlalchemy", "cyextension", "collections.cp312-win_amd64.pyd"),
    os.path.join(base_dir, "sqlalchemy", "cyextension", "immutabledict.cp312-win_amd64.pyd"),
    os.path.join(base_dir, "sqlalchemy", "cyextension", "processors.cp312-win_amd64.pyd"),
    os.path.join(base_dir, "sqlalchemy", "cyextension", "resultproxy.cp312-win_amd64.pyd"),
    os.path.join(base_dir, "sqlalchemy", "cyextension", "util.cp312-win_amd64.pyd"),
]

for t in targets:
    if os.path.exists(t):
        bak = t + ".bak"
        if os.path.exists(bak):
            os.remove(bak)
        os.rename(t, bak)
        logger.debug(f"Renamed: {t} -> .bak")
    else:
        logger.debug(f"Already renamed or not found: {t}")
