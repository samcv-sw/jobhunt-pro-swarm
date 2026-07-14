import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
bot_path = os.path.join(cwd, "core", "telegram", "bot.py")

with open(bot_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_function(func_name):
    print(f"=== {func_name} ===")
    found = False
    indent = 0
    for i, line in enumerate(lines):
        if f"async def {func_name}(" in line or f"def {func_name}(" in line:
            found = True
            # print definition and subsequent lines that have more indentation
            print(f"{i+1}: {line.rstrip()}")
            # find indentation of the function body
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if next_line.strip() == "":
                    print(f"{j+1}: {next_line.rstrip()}")
                    j += 1
                    continue
                # check indentation
                current_indent = len(next_line) - len(next_line.lstrip())
                if current_indent > 0:
                    print(f"{j+1}: {next_line.rstrip()}")
                    j += 1
                else:
                    break
            break

print_function("cmd_start")
print_function("cmd_status")
print_function("cmd_pause")
