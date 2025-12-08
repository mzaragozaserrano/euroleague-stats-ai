import re

# Test cases
sqls = [
    "WHERE g.season = '2022'",
    "WHERE season = '2022'",
    "WHERE g.season = 2022",
    "WHERE season = 2022",
]

for sql in sqls:
    fixed = re.sub(r"season\s*=\s*'20[012]\d'", "season IN (2024, 2025)", sql, flags=re.IGNORECASE)
    fixed = re.sub(r"season\s*=\s*20[012]\d\b", "season IN (2024, 2025)", fixed, flags=re.IGNORECASE)
    print(f"Original: {sql}")
    print(f"Fixed:    {fixed}")
    print()

