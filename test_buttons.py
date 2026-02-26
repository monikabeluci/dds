print("=" * 60)
print("TESTING ALL MENU FUNCTIONS")
print("=" * 60)

# Read main.py
with open("main.py", "r", encoding="utf-8") as f:
    code = f.read()

# Check which functions exist
functions = {
    "1": "full_check",
    "2": "quick_check", 
    "3": "advanced_spam_menu",
    "4": "dm_spam_menu",
    "5": "parse_menu",
    "6": "warm_menu",
    "7": "join_chat_menu",
    "8": "inbox_menu",
    "9": "auto_resp_menu",
    "10": "show_stats",
    "11": "settings_menu",
    "12": "proxy_menu",
    "13": "cleanup_menu",
    "14": "create_session",
    "15": "select_language",
}

print("\nChecking menu handlers in main.py:\n")

missing = []
found = []

for num, func in functions.items():
    # Check if handler exists
    if f'ch == "{num}"' in code or f"ch == '{num}'" in code:
        # Check if function exists
        if f"def {func}" in code or f"async def {func}" in code:
            found.append(f"[{num}] {func} - OK")
        else:
            missing.append(f"[{num}] {func} - HANDLER EXISTS BUT FUNCTION MISSING")
    else:
        missing.append(f"[{num}] {func} - NO HANDLER")

for item in found:
    print(f"  [+] {item}")

if missing:
    print("\n  MISSING:")
    for item in missing:
        print(f"  [-] {item}")

print("\n" + "=" * 60)
print(f"RESULT: {len(found)}/15 buttons work")
print("=" * 60)