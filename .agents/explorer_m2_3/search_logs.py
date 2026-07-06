import re

LOG_FILE = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\_pa_server.log"
OUTPUT_FILE = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_3\log_audit.txt"

def main():
    errors = []
    warnings = set()
    tracebacks = 0
    in_traceback = False
    traceback_lines = []
    
    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "Traceback (most recent call last):" in line:
                tracebacks += 1
                in_traceback = True
                traceback_lines = [line]
                continue
            
            if in_traceback:
                traceback_lines.append(line)
                if not line.startswith(" ") and not line.startswith("  ") and not line.strip().startswith("File "):
                    in_traceback = False
                    errors.append("".join(traceback_lines))
                continue
            
            if " - ERROR - " in line or " - CRITICAL - " in line:
                errors.append(line.strip())
            elif " - WARNING - " in line:
                m = re.search(r"- WARNING -\s*(.*)$", line)
                if m:
                    warnings.add(m.group(1).strip())
                    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(f"Total Tracebacks: {tracebacks}\n")
        out.write(f"Total Unique Warnings: {len(warnings)}\n")
        out.write(f"Total Error/Critical Logs: {len(errors)}\n\n")
        
        out.write("--- Unique Warnings ---\n")
        for w in sorted(list(warnings)):
            out.write(f"- {w}\n")
            
        out.write("\n--- Error Logs / Tracebacks ---\n")
        for e in errors:
            out.write(f"=== ERROR EVENT ===\n{e}\n\n")

if __name__ == "__main__":
    main()
