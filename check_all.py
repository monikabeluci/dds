print('=' * 60)
print('FULL SYSTEM CHECK')
print('=' * 60)

errors = []
ok = []

try:
    from config import API_ID, API_HASH, SESSIONS_FOLDER, ANTIBAN
    ok.append('config.py')
except Exception as e:
    errors.append(f'config.py: {e}')

try:
    from database import AccountDatabase
    db = AccountDatabase()
    stats = db.get_statistics()
    ok.append(f'database.py (accounts: {stats["total"]})')
except Exception as e:
    errors.append(f'database.py: {e}')

try:
    from account_checker import AccountChecker, AccountStatus, AccountCheckResult
    ok.append('account_checker.py')
except Exception as e:
    errors.append(f'account_checker.py: {e}')

try:
    from proxy_manager import ProxyManager
    ok.append('proxy_manager.py')
except Exception as e:
    errors.append(f'proxy_manager.py: {e}')

try:
    from spammer import SafeSpammer
    ok.append('spammer.py')
except Exception as e:
    errors.append(f'spammer.py: {e}')

try:
    from warmer import AccountWarmer
    ok.append('warmer.py')
except Exception as e:
    errors.append(f'warmer.py: {e}')

try:
    from parser import ChatParser
    ok.append('parser.py')
except Exception as e:
    errors.append(f'parser.py: {e}')

try:
    from dm_spammer import DMSpammer
    ok.append('dm_spammer.py')
except Exception as e:
    errors.append(f'dm_spammer.py: {e}')

try:
    from inbox import InboxManager
    ok.append('inbox.py')
except Exception as e:
    errors.append(f'inbox.py: {e}')

try:
    from license_manager import LicenseManager
    lm = LicenseManager()
    ok.append(f'license_manager.py (HWID: {lm.hwid[:8]}...)')
except Exception as e:
    errors.append(f'license_manager.py: {e}')

try:
    from advanced_spammer import AdvancedSpammer
    ok.append('advanced_spammer.py')
except Exception as e:
    errors.append(f'advanced_spammer.py: {e}')

try:
    from auto_responder import AutoResponder
    ok.append('auto_responder.py')
except Exception as e:
    errors.append(f'auto_responder.py: {e}')

try:
    from spintax import Spintax
    sp = Spintax()
    test = sp.spin('{Hello|Hi} {World|There}')
    ok.append(f'spintax.py (test: {test})')
except Exception as e:
    errors.append(f'spintax.py: {e}')

try:
    import main
    ok.append('main.py')
except Exception as e:
    errors.append(f'main.py: {e}')

try:
    from telethon import TelegramClient
    ok.append('telethon')
except Exception as e:
    errors.append(f'telethon: {e}')

print()
print('OK:')
for item in ok:
    print(f'  [+] {item}')

if errors:
    print()
    print('ERRORS:')
    for item in errors:
        print(f'  [-] {item}')

print()
print('=' * 60)
print(f'RESULT: {len(ok)}/15 modules OK')
if len(ok) == 15:
    print('ALL SYSTEMS READY!')
else:
    print(f'FIX {len(errors)} errors')
print('=' * 60)