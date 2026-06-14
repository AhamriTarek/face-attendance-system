import re

path = r"D:\PFE\PFE - TOP - real one\templates\absence_total.html"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix ANY variation of week.date_fin split across lines
fixed = re.sub(
    r'\{\{\s*week\.date_debut\s*\}\}\s*[–\-]\s*\{\{\s*week\.date_fin\s*\}\}',
    r'{{ week.date_debut }}-{{ week.date_fin }}',
    content,
    flags=re.DOTALL
)

# Also fix if date_fin tag itself is split like {{ \n week.date_fin }}
fixed = re.sub(
    r'\{\{\s*\n\s*week\.date_fin\s*\}\}',
    r'{{ week.date_fin }}',
    fixed
)

# Also fix date_debut split
fixed = re.sub(
    r'\{\{\s*\n\s*week\.date_debut\s*\}\}',
    r'{{ week.date_debut }}',
    fixed
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(fixed)

print("DONE. Lines containing date_fin:")
for i, line in enumerate(fixed.split('\n'), 1):
    if 'date_fin' in line or 'date_debut' in line:
        print(f"  Line {i}: {repr(line)}")
