with open("main.py", "r", encoding="utf-8") as f:
    code = f.read()

# Find LANG dictionary and add ru and sr
old_lang = '''"en": {
    "title": "SPAMMONSTER v4.0",'''

new_lang = '''"en": {
    "title": "SPAMMONSTER v4.0",
    "accounts": "Accounts", "ready": "Ready", "score": "Score",
    "menu": "\\n[1] Check accounts\\n[2] Quick check\\n[3] Spam to chats (PRO)\\n[4] Spam to DM\\n[5] Parse members\\n[6] Warm up\\n[7] Join chat\\n[8] Inbox\\n[9] Auto-responder\\n[10] Statistics\\n[11] Settings\\n[12] Proxy\\n[13] Cleanup\\n[14] Create session\\n[15] Language\\n[0] Exit\\n",
    "choice": "Choice", "use_proxy": "Use proxy? [y/n]", "no_sessions": "No sessions",
    "found_sessions": "Found", "connected": "Connected", "no_accounts": "No accounts",
    "chat_input": "Chat", "msg_source": "[1] Text [2] File", "message": "Message",
    "start_confirm": "[1] START [0] Cancel", "phone": "Phone", "done": "Done", "error": "Error",
    "delete_bad": "Delete bad", "save_good": "Save good", "cancel": "Cancel", "back": "Back",
    "saved": "Saved", "minimum": "Min", "maximum": "Max", "joined": "Joined",
},
"ru": {
    "title": "SPAMMONSTER v4.0",
    "accounts": "Akkaunty", "ready": "Gotovo", "score": "Score",
    "menu": "\\n[1] Proverka akk\\n[2] Bystraya proverka\\n[3] Spam v chaty (PRO)\\n[4] Spam v LS\\n[5] Parser\\n[6] Progrev\\n[7] Join chat\\n[8] Inbox\\n[9] Avtootvetchik\\n[10] Statistika\\n[11] Nastrojki\\n[12] Proxy\\n[13] Ochistka\\n[14] Sozdat sessiyu\\n[15] Yazyk\\n[0] Vyhod\\n",
    "choice": "Vybor", "use_proxy": "Ispolzovat proxy? [y/n]", "no_sessions": "Net sessij",
    "found_sessions": "Najdeno", "connected": "Podklucheno", "no_accounts": "Net akkauntov",
    "chat_input": "Chat", "msg_source": "[1] Tekst [2] Fajl", "message": "Soobshenie",
    "start_confirm": "[1] START [0] Otmena", "phone": "Telefon", "done": "Gotovo", "error": "Oshibka",
    "delete_bad": "Udalit plohie", "save_good": "Sohranit horoshie", "cancel": "Otmena", "back": "Nazad",
    "saved": "Sohraneno", "minimum": "Min", "maximum": "Max", "joined": "Vstupili",
},
"sr": {
    "title": "SPAMMONSTER v4.0",
    "accounts": "Nalozi", "ready": "Spremno", "score": "Score",
    "menu": "\\n[1] Provera naloga\\n[2] Brza provera\\n[3] Spam u chat (PRO)\\n[4] Spam u DM\\n[5] Parser\\n[6] Zagrevanje\\n[7] Join chat\\n[8] Inbox\\n[9] Auto-odgovor\\n[10] Statistika\\n[11] Podesavanja\\n[12] Proxy\\n[13] Ciscenje\\n[14] Kreiraj sesiju\\n[15] Jezik\\n[0] Izlaz\\n",
    "choice": "Izbor", "use_proxy": "Koristi proxy? [y/n]", "no_sessions": "Nema sesija",
    "found_sessions": "Nadjeno", "connected": "Povezano", "no_accounts": "Nema naloga",
    "chat_input": "Chat", "msg_source": "[1] Tekst [2] Fajl", "message": "Poruka",
    "start_confirm": "[1] START [0] Otkazi", "phone": "Telefon", "done": "Gotovo", "error": "Greska",
    "delete_bad": "Obrisi lose", "save_good": "Sacuvaj dobre", "cancel": "Otkazi", "back": "Nazad",
    "saved": "Sacuvano", "minimum": "Min", "maximum": "Max", "joined": "Pridruzeno",
},
}'''

# Also fix the LANG definition to include all languages
old_lang_def = '''LANG = {"en": {
    "title": "SPAMMONSTER v4.0", "accounts": "Accounts", "ready": "Ready", "score": "Score",
    "menu": "\\n[1] Check accounts\\n[2] Quick check\\n[3] Spam to chats (PRO)\\n[4] Spam to DM\\n[5] Parse members\\n[6] Warm up\\n[7] Join chat\\n[8] Inbox\\n[9] Auto-responder\\n[10] Statistics\\n[11] Settings\\n[12] Proxy\\n[13] Cleanup\\n[14] Create session\\n[15] Language\\n[0] Exit\\n",
    "choice": "Choice", "use_proxy": "Use proxy? [y/n]", "no_sessions": "No sessions",
    "found_sessions": "Found", "connected": "Connected", "no_accounts": "No accounts",
    "chat_input": "Chat", "msg_source": "[1] Text [2] File", "message": "Message",
    "start_confirm": "[1] START [0] Cancel", "phone": "Phone", "done": "Done", "error": "Error",
    "delete_bad": "Delete bad", "save_good": "Save good", "cancel": "Cancel", "back": "Back",
    "saved": "Saved", "minimum": "Min", "maximum": "Max", "joined": "Joined",
}}'''

new_lang_def = '''LANG = {
"en": {
    "title": "SPAMMONSTER v4.0", "accounts": "Accounts", "ready": "Ready", "score": "Score",
    "menu": "\\n[1] Check accounts\\n[2] Quick check\\n[3] Spam to chats (PRO)\\n[4] Spam to DM\\n[5] Parse members\\n[6] Warm up\\n[7] Join chat\\n[8] Inbox\\n[9] Auto-responder\\n[10] Statistics\\n[11] Settings\\n[12] Proxy\\n[13] Cleanup\\n[14] Create session\\n[15] Language\\n[0] Exit\\n",
    "choice": "Choice", "use_proxy": "Use proxy? [y/n]", "no_sessions": "No sessions",
    "found_sessions": "Found", "connected": "Connected", "no_accounts": "No accounts",
    "chat_input": "Chat", "msg_source": "[1] Text [2] File", "message": "Message",
    "start_confirm": "[1] START [0] Cancel", "phone": "Phone", "done": "Done", "error": "Error",
    "delete_bad": "Delete bad", "save_good": "Save good", "cancel": "Cancel", "back": "Back",
    "saved": "Saved", "minimum": "Min", "maximum": "Max", "joined": "Joined",
},
"ru": {
    "title": "SPAMMONSTER v4.0", "accounts": "Akkaunty", "ready": "Gotovo", "score": "Score",
    "menu": "\\n[1] Proverka\\n[2] Bystraya proverka\\n[3] Spam v chaty\\n[4] Spam v LS\\n[5] Parser\\n[6] Progrev\\n[7] Join chat\\n[8] Inbox\\n[9] Avtootvetchik\\n[10] Statistika\\n[11] Nastrojki\\n[12] Proxy\\n[13] Ochistka\\n[14] Sozdat sessiyu\\n[15] Yazyk\\n[0] Vyhod\\n",
    "choice": "Vybor", "use_proxy": "Proxy? [y/n]", "no_sessions": "Net sessij",
    "found_sessions": "Najdeno", "connected": "Podklucheno", "no_accounts": "Net akkauntov",
    "chat_input": "Chat", "msg_source": "[1] Tekst [2] Fajl", "message": "Soobshenie",
    "start_confirm": "[1] START [0] Otmena", "phone": "Telefon", "done": "Gotovo", "error": "Oshibka",
    "delete_bad": "Udalit", "save_good": "Sohranit", "cancel": "Otmena", "back": "Nazad",
    "saved": "Sohraneno", "minimum": "Min", "maximum": "Max", "joined": "Vstupili",
},
"sr": {
    "title": "SPAMMONSTER v4.0", "accounts": "Nalozi", "ready": "Spremno", "score": "Score",
    "menu": "\\n[1] Provera\\n[2] Brza provera\\n[3] Spam u chat\\n[4] Spam u DM\\n[5] Parser\\n[6] Zagrevanje\\n[7] Join chat\\n[8] Inbox\\n[9] Auto-odgovor\\n[10] Statistika\\n[11] Podesavanja\\n[12] Proxy\\n[13] Ciscenje\\n[14] Kreiraj sesiju\\n[15] Jezik\\n[0] Izlaz\\n",
    "choice": "Izbor", "use_proxy": "Proxy? [y/n]", "no_sessions": "Nema sesija",
    "found_sessions": "Nadjeno", "connected": "Povezano", "no_accounts": "Nema naloga",
    "chat_input": "Chat", "msg_source": "[1] Tekst [2] Fajl", "message": "Poruka",
    "start_confirm": "[1] START [0] Otkazi", "phone": "Telefon", "done": "Gotovo", "error": "Greska",
    "delete_bad": "Obrisi", "save_good": "Sacuvaj", "cancel": "Otkazi", "back": "Nazad",
    "saved": "Sacuvano", "minimum": "Min", "maximum": "Max", "joined": "Pridruzeno",
}}'''

if old_lang_def in code:
    code = code.replace(old_lang_def, new_lang_def)
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("DONE! Languages added.")
else:
    print("Manual fix needed - LANG not found as expected")