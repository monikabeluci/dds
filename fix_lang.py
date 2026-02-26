with open("main.py", "r", encoding="utf-8") as f:
    code = f.read()

old = 'elif ch == "0": db.close(); break'
new = '''elif ch == "15":
            print("\\n[1] English\\n[2] Russian\\n[3] Serbian")
            l = input("Choice: ").strip()
            global current_lang
            if l == "2": current_lang = "ru"
            elif l == "3": current_lang = "sr"
            else: current_lang = "en"
            print("OK!")
            input("[Enter]...")
        elif ch == "0": db.close(); break'''

code = code.replace(old, new)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("DONE!")
