# coding: utf-8
import asyncio
import os
import random
import json
import hashlib
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from config import API_ID, API_HASH, SESSIONS_FOLDER, ANTIBAN
from database import AccountDatabase
from account_checker import AccountChecker, AccountStatus, AccountCheckResult
from proxy_manager import ProxyManager
from spammer import SafeSpammer
from warmer import AccountWarmer
from parser import ChatParser
from dm_spammer import DMSpammer
from inbox import InboxManager
from license_manager import LicenseManager
from advanced_spammer import AdvancedSpammer
from auto_responder import AutoResponder

def check_license_startup():
    lm = LicenseManager()
    ADMIN_CODE = "SM$2024#ADM!N_X9k@Master"
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 60)
    print("   SPAMMONSTER v4.0")
    print("=" * 60)
    print(f"\n   HWID: {lm.hwid}")
    admin_file = ".admin"
    if os.path.exists(admin_file):
        try:
            with open(admin_file, "r") as f:
                if f.read().strip() == hashlib.sha512((ADMIN_CODE + lm.hwid).encode()).hexdigest():
                    print("\n   [ADMIN] Access: Unlimited")
                    input("\n   [Enter]...")
                    return True
        except: pass
    valid, result = lm.check_license()
    if valid:
        lm.show_license_info()
        input("\n   [Enter]...")
        return True
    print("\n   License not found!" if result == "NO_LICENSE" else f"\n   {result}")
    print("\n" + "-" * 60)
    key = input("\n   Key: ").strip()
    if not key: return False
    if key == ADMIN_CODE:
        try:
            with open(admin_file, "w") as f:
                f.write(hashlib.sha512((ADMIN_CODE + lm.hwid).encode()).hexdigest())
        except: pass
        print("\n   [ADMIN] Activated!")
        input("\n   [Enter]...")
        return True
    valid, result = lm.activate(key)
    if valid:
        print("\n   License activated!")
        input("\n   [Enter]...")
        return True
    print(f"\n   Error: {result}")
    input("\n   [Enter]...")
    return False

db = AccountDatabase()
proxy_manager = ProxyManager()
checker = AccountChecker()
warmer = AccountWarmer()
parser = ChatParser()
dm_spammer = DMSpammer()
inbox_manager = InboxManager()
advanced_spammer = AdvancedSpammer()
auto_responder = AutoResponder()
SETTINGS_FILE = "settings.json"
current_lang = "en"

LANG = {
"en": {
    "title": "SPAMMONSTER v4.0", "accounts": "Accounts", "ready": "Ready", "score": "Score",
    "menu": "\n[1] Check accounts\n[2] Quick check\n[3] Spam to chats (PRO)\n[4] Spam to DM\n[5] Parse members\n[6] Warm up\n[7] Join chat\n[8] Inbox\n[9] Auto-responder\n[10] Statistics\n[11] Settings\n[12] Proxy\n[13] Cleanup\n[14] Create session\n[15] Language\n[0] Exit\n",
    "choice": "Choice", "use_proxy": "Use proxy? [y/n]", "no_sessions": "No sessions",
    "found_sessions": "Found", "connected": "Connected", "no_accounts": "No accounts",
    "chat_input": "Chat", "msg_source": "[1] Text [2] File", "message": "Message",
    "start_confirm": "[1] START [0] Cancel", "phone": "Phone", "done": "Done", "error": "Error",
    "delete_bad": "Delete bad", "save_good": "Save good", "cancel": "Cancel", "back": "Back",
    "saved": "Saved", "minimum": "Min", "maximum": "Max", "joined": "Joined",
},
"ru": {
    "title": "SPAMMONSTER v4.0", "accounts": "Аккаунты", "ready": "Готовы", "score": "Рейтинг",
    "menu": "\n[1] Проверка аккаунтов\n[2] Быстрая проверка\n[3] Рассылка по чатам (PRO)\n[4] Рассылка в ЛС\n[5] Парсер участников\n[6] Прогрев аккаунтов\n[7] Вступить в чат\n[8] Входящие (Inbox)\n[9] Автоответчик\n[10] Статистика\n[11] Настройки\n[12] Прокси\n[13] Очистка\n[14] Создать сессию\n[15] Язык\n[0] Выход\n",
    "choice": "Выбор", "use_proxy": "Использовать прокси? [y/n]", "no_sessions": "Нет сессий",
    "found_sessions": "Найдено", "connected": "Подключено", "no_accounts": "Нет аккаунтов",
    "chat_input": "Чат", "msg_source": "[1] Текст [2] Файл", "message": "Сообщение",
    "start_confirm": "[1] СТАРТ [0] Отмена", "phone": "Телефон", "done": "Готово", "error": "Ошибка",
    "delete_bad": "Удалить плохие", "save_good": "Сохранить", "cancel": "Отмена", "back": "Назад",
    "saved": "Сохранено", "minimum": "Мин", "maximum": "Макс", "joined": "Вступили",
},
"sr": {
    "title": "SPAMMONSTER v4.0", "accounts": "Nalozi", "ready": "Spremno", "score": "Score",
    "menu": "\n[1] Provera\n[2] Brza provera\n[3] Spam u chat\n[4] Spam u DM\n[5] Parser\n[6] Zagrevanje\n[7] Join chat\n[8] Inbox\n[9] Auto-odgovor\n[10] Statistika\n[11] Podesavanja\n[12] Proxy\n[13] Ciscenje\n[14] Kreiraj sesiju\n[15] Jezik\n[0] Izlaz\n",
    "choice": "Izbor", "use_proxy": "Proxy? [y/n]", "no_sessions": "Nema sesija",
    "found_sessions": "Nadjeno", "connected": "Povezano", "no_accounts": "Nema naloga",
    "chat_input": "Chat", "msg_source": "[1] Tekst [2] Fajl", "message": "Poruka",
    "start_confirm": "[1] START [0] Otkazi", "phone": "Telefon", "done": "Gotovo", "error": "Greska",
    "delete_bad": "Obrisi", "save_good": "Sacuvaj", "cancel": "Otkazi", "back": "Nazad",
    "saved": "Sacuvano", "minimum": "Min", "maximum": "Max", "joined": "Pridruzeno",
}}

def t(key): return LANG[current_lang].get(key, key)
def clear(): os.system("cls" if os.name == "nt" else "clear")
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f: ANTIBAN.update(json.load(f))
        except: pass
def save_settings():
    with open(SETTINGS_FILE, "w") as f: json.dump(ANTIBAN, f)

def banner():
    clear()
    stats = db.get_statistics()
    print("=" * 60)
    print(f"   {t('title')}   |   {'[ADMIN]' if os.path.exists('.admin') else ''}")
    print("=" * 60)
    print(f"   {t('accounts')}: {stats['total']}  |  {t('ready')}: {stats['ready']}  |  {t('score')}: {stats['avg_score']:.1f}")
    print("=" * 60)

async def connect_sessions(use_proxy=False):
    if not os.path.exists(SESSIONS_FOLDER): os.makedirs(SESSIONS_FOLDER)
    sessions = [f[:-8] for f in os.listdir(SESSIONS_FOLDER) if f.endswith(".session")]
    if not sessions:
        print(t("no_sessions"))
        return {}
    print(f"{t('found_sessions')}: {len(sessions)}")
    clients = {}
    for sname in sessions:
        spath = os.path.join(SESSIONS_FOLDER, sname)
        proxy = proxy_manager.get_proxy_for_telethon(sname) if use_proxy else None
        client = TelegramClient(spath, API_ID, API_HASH, proxy=proxy)
        try:
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                print(f"+ {me.first_name}")
                clients[sname] = client
            else: await client.disconnect()
        except Exception as e: print(f"- {sname}: {str(e)[:30]}")
        await asyncio.sleep(0.5)
    print(f"{t('connected')}: {len(clients)}")
    return clients

async def full_check():
    clear()
    use_proxy = input(f"{t('use_proxy')}: ").lower() == "y"
    clients = await connect_sessions(use_proxy)
    if not clients: input("[Enter]..."); return
    results = await checker.check_all(clients)
    checker.print_summary()
    for c in clients.values():
        try: await c.disconnect()
        except: pass
    input("[Enter]...")

async def quick_check():
    clear()
    use_proxy = input(f"{t('use_proxy')}: ").lower() == "y"
    clients = await connect_sessions(use_proxy)
    if not clients: input("[Enter]..."); return
    for sname, client in clients.items():
        try:
            me = await client.get_me()
            print(f"OK {me.first_name}")
            db.save_account(AccountCheckResult(session_name=sname, user_id=me.id, username=me.username, first_name=me.first_name, is_authorized=True, status=AccountStatus.GOOD, score=60, can_send_messages=True, has_username=bool(me.username)))
        except: print(f"ERR {sname}")
    for c in clients.values():
        try: await c.disconnect()
        except: pass
    input("[Enter]...")

async def advanced_spam_menu():
    clear()
    print("SPAM TO CHATS (PRO)")
    use_proxy = input(f"{t('use_proxy')}: ").lower() == "y"
    clients = await connect_sessions(use_proxy)
    if not clients: input("[Enter]..."); return
    print("\n[1] From account\n[2] From file\n[3] Manual")
    src = input(f"{t('choice')}: ").strip()
    chats = []
    if src == "1":
        chats = await advanced_spammer.get_chats_from_account(list(clients.values())[0])
        print(f"Found: {len(chats)}")
    elif src == "2":
        if not os.path.exists("chats"): os.makedirs("chats")
        files = [f for f in os.listdir("chats") if f.endswith(".txt")]
        for i, f in enumerate(files, 1): print(f"[{i}] {f}")
        if files:
            idx = input("Number: ").strip()
            if idx.isdigit() and 0 < int(idx) <= len(files):
                chats = advanced_spammer.load_chats_from_file(os.path.join("chats", files[int(idx)-1]))
    elif src == "3":
        print("Enter chats (empty=done):")
        while True:
            c = input(": ").strip()
            if not c: break
            chats.append(c)
    if not chats:
        for c in clients.values(): await c.disconnect()
        return
    print(f"\nChats: {len(chats)}")
    msg = input(f"{t('message')}: ").strip()
    if not msg:
        for c in clients.values(): await c.disconnect()
        return
    if input(f"\n{t('start_confirm')}: ").strip() != "1":
        for c in clients.values(): await c.disconnect()
        return
    await advanced_spammer.mass_spam(clients, chats, msg)
    for c in clients.values():
        try: await c.disconnect()
        except: pass
    input("[Enter]...")

async def dm_spam_menu():
    clear()
    print("SPAM TO DM")
    if os.path.exists("parsed"):
        files = [f for f in os.listdir("parsed") if f.endswith((".txt", ".json"))]
        for i, f in enumerate(files, 1): print(f"[{i}] {f}")
        if files:
            idx = input("Number: ").strip()
            if idx.isdigit() and 0 < int(idx) <= len(files):
                parser.load_from_file(os.path.join("parsed", files[int(idx)-1]))
    users = parser.get_users()
    if not users: print("No users"); input("[Enter]..."); return
    print(f"Users: {len(users)}")
    msg = input(f"{t('message')}: ").strip()
    if not msg: return
    use_proxy = input(f"{t('use_proxy')}: ").lower() == "y"
    clients = await connect_sessions(use_proxy)
    if clients:
        await dm_spammer.mass_dm(clients, users, [msg])
        for c in clients.values(): await c.disconnect()
    input("[Enter]...")

async def parse_menu():
    clear()
    use_proxy = input(f"{t('use_proxy')}: ").lower() == "y"
    clients = await connect_sessions(use_proxy)
    if not clients: input("[Enter]..."); return
    chat = input(f"{t('chat_input')}: ").strip()
    if chat:
        users = await parser.parse_chat(list(clients.values())[0], chat, 1000)
        if users:
            print(f"Parsed: {len(users)}")
            fmt = input("[1] TXT [2] JSON [3] CSV: ").strip()
            if fmt in ["1","2","3"]: parser.save_to_file(format=["txt","json","csv"][int(fmt)-1])
    for c in clients.values(): await c.disconnect()
    input("[Enter]...")

async def warm_menu():
    clear()
    use_proxy = input(f"{t('use_proxy')}: ").lower() == "y"
    clients = await connect_sessions(use_proxy)
    if not clients: input("[Enter]..."); return
    await warmer.warm_all(clients, 7, "medium")
    for c in clients.values(): await c.disconnect()
    input("[Enter]...")

async def join_chat_menu():
    clear()
    suitable = db.get_suitable_accounts(min_score=40)
    if not suitable: print(t("no_accounts")); input("[Enter]..."); return
    chat = input(f"{t('chat_input')}: ").strip()
    if not chat: return
    use_proxy = input(f"{t('use_proxy')}: ").lower() == "y"
    success = 0
    for acc in suitable:
        client = TelegramClient(os.path.join(SESSIONS_FOLDER, acc["session_name"]), API_ID, API_HASH, proxy=proxy_manager.get_proxy_for_telethon(acc["session_name"]) if use_proxy else None)
        try:
            await client.connect()
            if await client.is_user_authorized():
                if "+" in chat: await client(ImportChatInviteRequest(chat.split("/")[-1].replace("+","")))
                else: await client(JoinChannelRequest(chat))
                print(f"+ {acc['session_name']}")
                success += 1
        except Exception as e: print(f"- {str(e)[:30]}")
        finally: await client.disconnect()
        await asyncio.sleep(random.randint(30,60))
    print(f"\n{t('joined')}: {success}/{len(suitable)}")
    input("[Enter]...")

async def inbox_menu():
    clear()
    use_proxy = input(f"{t('use_proxy')}: ").lower() == "y"
    clients = await connect_sessions(use_proxy)
    if not clients: input("[Enter]..."); return
    await inbox_manager.check_all_accounts(clients)
    input("[Enter]...")
    for c in clients.values(): await c.disconnect()

async def auto_resp_menu():
    clear()
    auto_responder.print_settings()
    print("\n[1] Start\n[2] Change message\n[0] Back")
    ch = input(f"{t('choice')}: ").strip()
    if ch == "1":
        use_proxy = input(f"{t('use_proxy')}: ").lower() == "y"
        clients = await connect_sessions(use_proxy)
        if clients:
            try: await auto_responder.start(clients)
            except KeyboardInterrupt: auto_responder.stop()
            for c in clients.values(): await c.disconnect()
    elif ch == "2":
        msg = input("New message: ").strip()
        if msg:
            auto_responder.settings["message"] = msg
            auto_responder.save_settings()
    input("[Enter]...")

def show_stats():
    clear()
    stats = db.get_statistics()
    print(f"Total: {stats['total']}\nReady: {stats['ready']}\nScore: {stats['avg_score']:.1f}\nSent: {stats['total_messages_sent']}")
    input("[Enter]...")

async def settings_menu():
    clear()
    print(f"Interval: {ANTIBAN['min_interval']}-{ANTIBAN['max_interval']}s")
    print(f"Hourly: {ANTIBAN['messages_per_hour']}")
    print(f"Daily: {ANTIBAN['messages_per_day']}")
    input("[Enter]...")

async def proxy_menu():
    clear()
    proxy_manager.print_status()
    print("\n[1] Add\n[2] Remove\n[0] Back")
    ch = input(f"{t('choice')}: ").strip()
    if ch == "1":
        name = input("Name: ").strip()
        proxy = input("Proxy: ").strip()
        country = input("Country: ").strip().upper()
        if name and proxy: proxy_manager.add_proxy(name, proxy, country)
    input("[Enter]...")

async def cleanup_menu():
    clear()
    print("[1] Delete bad\n[2] Optimize DB")
    ch = input(f"{t('choice')}: ").strip()
    if ch == "1":
        for st in ["banned","dead","unauthorized","bad"]:
            for acc in db.get_accounts_by_status(st):
                sf = os.path.join(SESSIONS_FOLDER, f"{acc['session_name']}.session")
                if os.path.exists(sf): os.remove(sf)
                db.delete_account(acc["session_name"], st)
    elif ch == "2": db.vacuum()
    input("[Enter]...")

async def create_session():
    clear()
    if API_ID == 12345678: print("Set API in config.py!"); input("[Enter]..."); return
    phone = input(f"{t('phone')}: ").strip()
    if not phone: return
    client = TelegramClient(os.path.join(SESSIONS_FOLDER, phone.replace("+","").replace(" ","")), API_ID, API_HASH)
    try:
        await client.start(phone)
        me = await client.get_me()
        print(f"{t('done')}: {me.first_name}")
    except Exception as e: print(f"{t('error')}: {e}")
    finally: await client.disconnect()
    input("[Enter]...")

async def main():
    for f in [SESSIONS_FOLDER, "chats", "logs", "parsed"]:
        if not os.path.exists(f): os.makedirs(f)
    load_settings()
    while True:
        banner()
        print(t("menu"))
        ch = input(f"{t('choice')}: ").strip()
        if ch == "1": await full_check()
        elif ch == "2": await quick_check()
        elif ch == "3": await advanced_spam_menu()
        elif ch == "4": await dm_spam_menu()
        elif ch == "5": await parse_menu()
        elif ch == "6": await warm_menu()
        elif ch == "7": await join_chat_menu()
        elif ch == "8": await inbox_menu()
        elif ch == "9": await auto_resp_menu()
        elif ch == "10": show_stats()
        elif ch == "11": await settings_menu()
        elif ch == "12": await proxy_menu()
        elif ch == "13": await cleanup_menu()
        elif ch == "14": await create_session()
        elif ch == "15":
            print("\n[1] English\n[2] Russian\n[3] Serbian")
            l = input("Choice: ").strip()
            global current_lang
            if l == "2": current_lang = "ru"
            elif l == "3": current_lang = "sr"
            else: current_lang = "en"
            print("OK!")
            input("[Enter]...")
        elif ch == "0": db.close(); break

if __name__ == "__main__":
    if check_license_startup(): asyncio.run(main())
