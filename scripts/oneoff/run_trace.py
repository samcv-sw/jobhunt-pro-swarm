import subprocess

res = subprocess.run(
    [r"test_env\Scripts\python.exe", "-v", "test_sqlalchemy.py"],
    capture_output=True,
    text=True,
    encoding="utf-8"
)

with open("import_trace.log", "w", encoding="utf-8") as f:
    f.write("STDOUT:\n")
    f.write(res.stdout)
    f.write("\n\nSTDERR:\n")
    f.write(res.stderr)

logger.debug("Trace written to import_trace.log")
