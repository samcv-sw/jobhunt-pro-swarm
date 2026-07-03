import os
import sys

# Reconfigure stdout to support printing emojis on Windows
sys.stdout.reconfigure(encoding='utf-8')

templates_dir = "web/templates"
files = [f for f in os.listdir(templates_dir) if f.endswith(".html")]

print("Scanning templates for sidebar navigation...")

for filename in files:
    filepath = os.path.join(templates_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if this file has a sidebar navigation structure
    if 'href="/wallet"' in content or 'href="/new-campaign"' in content:
        print(f"\n- Found sidebar in: {filename}")
        
        if 'href="/services"' in content:
            print("  [INFO] Already has Services link!")
            continue
            
        # Let's find an insertion point:
        # We can look for '<a href="/wallet"' and insert the new link right before it
        lines = content.splitlines()
        inserted = False
        for idx, line in enumerate(lines):
            if 'href="/wallet"' in line:
                # Get the indentation of this line
                indent = len(line) - len(line.lstrip())
                
                # Check if it has a class="active" or similar, we just insert a standard link
                lines.insert(idx, ' ' * indent + '<a href="/services">💎 Premium Services</a>')
                inserted = True
                print(f"  [SUCCESS] Injected Premium Services link before /wallet line in {filename}")
                break
        
        if inserted:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        else:
            print("  [WARNING] Could not find insertion point!")

print("\nSync completed successfully!")
