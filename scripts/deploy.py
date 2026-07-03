#!/usr/bin/env python3
import sys
import subprocess
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="JobHunt Pro Consolidated Deploy Script")
    parser.add_argument("--safe", action="store_true", help="Run safe deploy")
    parser.add_argument("--quick", action="store_true", help="Run quick deploy")
    parser.add_argument("--retry", action="store_true", help="Run quick deploy with retry")
    
    args = parser.parse_args()
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if args.safe:
        target = "safe_deploy.py"
    elif args.retry:
        target = "quick_deploy_retry.py"
    else:
        target = "quick_deploy.py"
        
    target_path = os.path.join(script_dir, target)
    if not os.path.exists(target_path):
        print(f"Error: {target} not found in root directory.")
        sys.exit(1)
        
    print(f"--- Running {target} ---")
    subprocess.run([sys.executable, target_path], check=True)

if __name__ == "__main__":
    main()
