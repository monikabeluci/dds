# coding: utf-8
with open("main.py", "r", encoding="utf-8") as f:
    code = f.read()

old_ru = '''"ru": {
    "title": "SPAMMONSTER v4.0", "accounts": "Akkaunty", "ready": "Gotovo", "score": "Score",
    "menu": "\\n[1] Proverka\\n[2] Bystraya proverka\\n[3] Spam v chaty\\n[4] Spam v LS\\n[5] Parser\\n[6] Progrev\\n[7] Join chat\\n[8] Inbox\\n[9] Avtootvetchik\\n[10] Statistika\\n[11] Nastrojki\\n[12] Proxy\\n[13] Ochistka\\n[14] Sozdat sessiyu\\n[15] Yazyk\\n[0] Vyhod\\n",
    "choice": "Vybor", "use_proxy": "Proxy? [y/n]", "no_sessions": "Net sessij",
    "found_sessions": "Najdeno", "connected": "Podklucheno", "no_accounts": "Net akkauntov",
    "chat_input": "Chat", "msg_source": "[1] Tekst [2] Fajl", "message": "Soobshenie",
    "start_confirm": "[1] START [0] Otmena", "phone": "Telefon", "done": "Gotovo", "error": "Oshibka",
    "delete_bad": "Udalit", "save_good": "Sohranit", "cancel": "Otmena", "back": "Nazad",
    "saved": "Sohraneno", "minimum": "Min", "maximum": "Max", "joined": "Vstupili",
},'''

new_ru = '''"ru": {
    "title": "SPAMMONSTER v4.0", "accounts": "\u0410\u043a\u043a\u0430\u0443\u043d\u0442\u044b", "ready": "\u0413\u043e\u0442\u043e\u0432\u044b", "score": "\u0420\u0435\u0439\u0442\u0438\u043d\u0433",
    "menu": "\\n[1] \u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0430\u043a\u043a\u0430\u0443\u043d\u0442\u043e\u0432\\n[2] \u0411\u044b\u0441\u0442\u0440\u0430\u044f \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430\\n[3] \u0420\u0430\u0441\u0441\u044b\u043b\u043a\u0430 \u043f\u043e \u0447\u0430\u0442\u0430\u043c (PRO)\\n[4] \u0420\u0430\u0441\u0441\u044b\u043b\u043a\u0430 \u0432 \u041b\u0421\\n[5] \u041f\u0430\u0440\u0441\u0435\u0440 \u0443\u0447\u0430\u0441\u0442\u043d\u0438\u043a\u043e\u0432\\n[6] \u041f\u0440\u043e\u0433\u0440\u0435\u0432 \u0430\u043a\u043a\u0430\u0443\u043d\u0442\u043e\u0432\\n[7] \u0412\u0441\u0442\u0443\u043f\u0438\u0442\u044c \u0432 \u0447\u0430\u0442\\n[8] \u0412\u0445\u043e\u0434\u044f\u0449\u0438\u0435 (Inbox)\\n[9] \u0410\u0432\u0442\u043e\u043e\u0442\u0432\u0435\u0442\u0447\u0438\u043a\\n[10] \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430\\n[11] \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438\\n[12] \u041f\u0440\u043e\u043a\u0441\u0438\\n[13] \u041e\u0447\u0438\u0441\u0442\u043a\u0430\\n[14] \u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0441\u0435\u0441\u0441\u0438\u044e\\n[15] \u042f\u0437\u044b\u043a\\n[0] \u0412\u044b\u0445\u043e\u0434\\n",
    "choice": "\u0412\u044b\u0431\u043e\u0440", "use_proxy": "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c \u043f\u0440\u043e\u043a\u0441\u0438? [y/n]", "no_sessions": "\u041d\u0435\u0442 \u0441\u0435\u0441\u0441\u0438\u0439",
    "found_sessions": "\u041d\u0430\u0439\u0434\u0435\u043d\u043e", "connected": "\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u043e", "no_accounts": "\u041d\u0435\u0442 \u0430\u043a\u043a\u0430\u0443\u043d\u0442\u043e\u0432",
    "chat_input": "\u0427\u0430\u0442", "msg_source": "[1] \u0422\u0435\u043a\u0441\u0442 [2] \u0424\u0430\u0439\u043b", "message": "\u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435",
    "start_confirm": "[1] \u0421\u0422\u0410\u0420\u0422 [0] \u041e\u0442\u043c\u0435\u043d\u0430", "phone": "\u0422\u0435\u043b\u0435\u0444\u043e\u043d", "done": "\u0413\u043e\u0442\u043e\u0432\u043e", "error": "\u041e\u0448\u0438\u0431\u043a\u0430",
    "delete_bad": "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u043b\u043e\u0445\u0438\u0435", "save_good": "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", "cancel": "\u041e\u0442\u043c\u0435\u043d\u0430", "back": "\u041d\u0430\u0437\u0430\u0434",
    "saved": "\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e", "minimum": "\u041c\u0438\u043d", "maximum": "\u041c\u0430\u043a\u0441", "joined": "\u0412\u0441\u0442\u0443\u043f\u0438\u043b\u0438",
},'''

if old_ru in code:
    code = code.replace(old_ru, new_ru)
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("DONE! Russian language fixed!")
else:
    print("Not found, trying decode...")

# Verify
with open("main.py", "r", encoding="utf-8") as f:
    test = f.read()
    if "\u0410\u043a\u043a\u0430\u0443\u043d\u0442\u044b" in test:
        print("Verification: OK - Cyrillic is in file!")