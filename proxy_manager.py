import os
import json
import socket
import asyncio
from typing import Optional, Dict, List

PROXY_FILE = "proxies.json"

COUNTRY_CODES = {
    '7': 'RU', '77': 'KZ', '375': 'BY', '380': 'UA', '381': 'RS',
    '382': 'ME', '385': 'HR', '386': 'SI', '387': 'BA', '389': 'MK',
    '1': 'US', '44': 'GB', '49': 'DE', '33': 'FR', '39': 'IT',
    '34': 'ES', '31': 'NL', '48': 'PL', '90': 'TR', '971': 'AE',
    '966': 'SA', '91': 'IN', '86': 'CN', '81': 'JP', '82': 'KR',
    '62': 'ID', '60': 'MY', '65': 'SG', '66': 'TH', '84': 'VN',
    '55': 'BR', '52': 'MX', '54': 'AR', '57': 'CO',
}

COUNTRY_NAMES = {
    'RU': 'Россия', 'KZ': 'Казахстан', 'BY': 'Беларусь', 'UA': 'Украина',
    'RS': 'Сербия', 'ME': 'Черногория', 'HR': 'Хорватия', 'SI': 'Словения',
    'BA': 'Босния', 'MK': 'Македония', 'US': 'США', 'GB': 'Великобритания',
    'DE': 'Германия', 'FR': 'Франция', 'IT': 'Италия', 'ES': 'Испания',
    'NL': 'Нидерланды', 'PL': 'Польша', 'TR': 'Турция', 'AE': 'ОАЭ',
    'SA': 'Сауд. Аравия', 'IN': 'Индия', 'CN': 'Китай', 'JP': 'Япония',
    'KR': 'Юж. Корея', 'ID': 'Индонезия', 'MY': 'Малайзия', 'SG': 'Сингапур',
    'TH': 'Таиланд', 'VN': 'Вьетнам', 'BR': 'Бразилия', 'MX': 'Мексика',
    'AR': 'Аргентина', 'CO': 'Колумбия',
}

class ProxyManager:
    def __init__(self):
        self.proxies = {}
        self.account_proxies = {}
        self.load()
    
    def load(self):
        if os.path.exists(PROXY_FILE):
            try:
                with open(PROXY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.proxies = data.get('proxies', {})
                    self.account_proxies = data.get('account_proxies', {})
            except:
                pass
    
    def save(self):
        with open(PROXY_FILE, 'w', encoding='utf-8') as f:
            json.dump({'proxies': self.proxies, 'account_proxies': self.account_proxies}, f, indent=2)
    
    def parse_proxy(self, proxy_str):
        proxy_str = proxy_str.strip()
        if not proxy_str:
            return None
        
        proxy_type = 'socks5'
        for prefix in ['http://', 'https://', 'socks5://', 'socks4://']:
            if proxy_str.startswith(prefix):
                proxy_type = prefix.replace('://', '').replace('https', 'http')
                proxy_str = proxy_str[len(prefix):]
                break
        
        username, password = None, None
        
        if '@' in proxy_str:
            auth, proxy_str = proxy_str.rsplit('@', 1)
            if ':' in auth:
                username, password = auth.split(':', 1)
        
        parts = proxy_str.split(':')
        if len(parts) == 2:
            host, port = parts
        elif len(parts) == 4:
            host, port, username, password = parts
        else:
            return None
        
        try:
            port = int(port)
        except:
            return None
        
        return {'type': proxy_type, 'host': host, 'port': port, 'username': username, 'password': password}
    
    def add_proxy(self, name, proxy_str, country=''):
        parsed = self.parse_proxy(proxy_str)
        if not parsed:
            return False
        parsed['country'] = country.upper()
        parsed['raw'] = proxy_str
        self.proxies[name] = parsed
        self.save()
        return True
    
    def remove_proxy(self, name):
        if name in self.proxies:
            del self.proxies[name]
            for acc in list(self.account_proxies.keys()):
                if self.account_proxies[acc] == name:
                    del self.account_proxies[acc]
            self.save()
            return True
        return False
    
    def assign_proxy_to_account(self, session_name, proxy_name):
        if proxy_name and proxy_name not in self.proxies:
            return False
        if proxy_name:
            self.account_proxies[session_name] = proxy_name
        elif session_name in self.account_proxies:
            del self.account_proxies[session_name]
        self.save()
        return True
    
    def get_proxy_for_account(self, session_name):
        proxy_name = self.account_proxies.get(session_name)
        if proxy_name and proxy_name in self.proxies:
            return self.proxies[proxy_name]
        return None
    
    def get_proxy_for_telethon(self, session_name=None):
        if not session_name:
            return None
        proxy = self.get_proxy_for_account(session_name)
        if not proxy:
            return None
        try:
            import socks
            proxy_types = {'socks5': socks.SOCKS5, 'socks4': socks.SOCKS4, 'http': socks.HTTP}
            return (proxy_types.get(proxy['type'], socks.SOCKS5), proxy['host'], proxy['port'], True, proxy.get('username'), proxy.get('password'))
        except:
            return None
    
    def get_country_from_phone(self, phone):
        phone = phone.replace('+', '').replace(' ', '').replace('-', '')
        for code_len in [3, 2, 1]:
            code = phone[:code_len]
            if code in COUNTRY_CODES:
                return COUNTRY_CODES[code]
        return ''
    
    def auto_assign_by_country(self, session_name, phone):
        country = self.get_country_from_phone(phone)
        if not country:
            return False
        for pname, pdata in self.proxies.items():
            if pdata.get('country') == country:
                self.account_proxies[session_name] = pname
                self.save()
                return True
        return False
    
    async def check_proxy(self, proxy_data, timeout=10):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((proxy_data['host'], proxy_data['port']))
            sock.close()
            return result == 0
        except:
            return False
    
    async def check_all_proxies(self):
        results = {}
        for name, data in self.proxies.items():
            print(f"Проверка {name}...", end=" ")
            is_alive = await self.check_proxy(data)
            results[name] = is_alive
            print("OK" if is_alive else "DEAD")
        return results
    
    def list_proxies(self):
        result = []
        for name, data in self.proxies.items():
            assigned = [acc for acc, pn in self.account_proxies.items() if pn == name]
            result.append({
                'name': name, 'type': data['type'], 'host': data['host'], 'port': data['port'],
                'country': data.get('country', ''), 'country_name': COUNTRY_NAMES.get(data.get('country', ''), ''),
                'assigned_to': assigned
            })
        return result
    
    def print_status(self):
        proxies = self.list_proxies()
        if not proxies:
            print("\nНет добавленных прокси")
            return
        print("\n" + "=" * 60)
        print("СПИСОК ПРОКСИ")
        print("=" * 60)
        for p in proxies:
            country = f"[{p['country']}]" if p['country'] else "[??]"
            assigned = ", ".join(p['assigned_to']) if p['assigned_to'] else "не назначен"
            print(f"\n  {p['name']}")
            print(f"   Тип: {p['type'].upper()}")
            print(f"   Адрес: {p['host']}:{p['port']}")
            print(f"   Страна: {country} {p['country_name']}")
            print(f"   Аккаунты: {assigned}")
        print("=" * 60)