import subprocess
import os

os.environ['DISABLE_SQLALCHEMY_CEXT_RUNTIME'] = '1'

print("Running all patched tests...")
res = subprocess.run(
    [
        r"test_env\Scripts\python.exe",
        "-c",
        "import os; os.environ['DISABLE_SQLALCHEMY_CEXT_RUNTIME'] = '1'; import sys; sys.path.insert(0, r'c:\\Users\\samde\\Desktop\\📂 Folders & Projects\\cv sam new ma3 kimi\\test_env\\Lib\\site-packages'); sys.path.insert(1, r'c:\\Users\\samde\\Desktop\\📂 Folders & Projects\\cv sam new ma3 kimi'); import pytest; sys.exit(pytest.main(['-v']))"
    ],
    capture_output=True,
    text=True,
    encoding="utf-8"
)

log_path = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_challenger_overdrive_v8_2\pytest_all_patched.log"
with open(log_path, "w", encoding="utf-8") as f:
    f.write("STDOUT:\n")
    f.write(res.stdout)
    f.write("\n\nSTDERR:\n")
    f.write(res.stderr)

print(f"Tests finished with exit code {res.returncode}")
lines = res.stdout.splitlines()
summary_lines = [l for l in lines if "passed" in l or "failed" in l or "collected" in l or "====" in l]
print("\n--- Test Run Summary ---")
for sl in summary_lines[-5:]:
    print(sl)
