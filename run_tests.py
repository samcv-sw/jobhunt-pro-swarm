import sys
import os
import traceback

# Set UTF-8 encoding for stdout
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

print("Starting debug test runner...")

try:
    # Add local paths
    sys.path.insert(0, r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\test_env\Lib\site-packages")
    sys.path.insert(1, r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi")
    
    print("Paths set. Importing pytest...")
    import pytest
    print("pytest imported successfully.")
    
    print("Importing backend.main...")
    import backend.main
    print("backend.main imported successfully.")
    
    print("Running pytest.main...")
    exit_code = pytest.main(["-v"])
    print(f"pytest.main finished with exit code: {exit_code}")
    sys.exit(exit_code)
except Exception as e:
    print("An exception occurred during imports/run:")
    traceback.print_exc()
    sys.exit(2)
