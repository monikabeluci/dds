import os
import json
import hashlib
import uuid
import datetime
import base64

LICENSE_FILE = "license.key"

class LicenseManager:
    def __init__(self):
        self.hwid = self.get_hwid()
        self.license_data = None
    
    def get_hwid(self):
        try:
            import platform
            raw = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)])
            raw += f"-{mac}"
            hwid = hashlib.sha256(raw.encode()).hexdigest()[:32].upper()
            return hwid
        except:
            return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:32].upper()
    
    def generate_key(self, hwid, days=30, plan="standard"):
        expire_date = datetime.datetime.now() + datetime.timedelta(days=days)
        
        data = {
            "hwid": hwid,
            "plan": plan,
            "expire": expire_date.strftime("%Y-%m-%d"),
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        secret = "SpamMonster_Secret_Key_2024"
        sign_data = f"{data['hwid']}{data['plan']}{data['expire']}{secret}"
        signature = hashlib.sha256(sign_data.encode()).hexdigest()[:16]
        data["signature"] = signature
        
        json_str = json.dumps(data)
        key = base64.b64encode(json_str.encode()).decode()
        formatted_key = "-".join([key[i:i+8] for i in range(0, len(key), 8)])
        
        return formatted_key
    
    def verify_key(self, key):
        try:
            clean_key = key.replace("-", "").replace(" ", "").replace("\n", "")
            json_str = base64.b64decode(clean_key.encode()).decode()
            data = json.loads(json_str)
            
            secret = "SpamMonster_Secret_Key_2024"
            sign_data = f"{data['hwid']}{data['plan']}{data['expire']}{secret}"
            expected_sig = hashlib.sha256(sign_data.encode()).hexdigest()[:16]
            
            if data.get("signature") != expected_sig:
                return False, "Неверный ключ"
            
            if data.get("hwid") != self.hwid and data.get("hwid") != "UNIVERSAL":
                return False, f"Ключ для другого компьютера\nВаш HWID: {self.hwid}"
            
            expire = datetime.datetime.strptime(data["expire"], "%Y-%m-%d")
            if datetime.datetime.now() > expire:
                days_expired = (datetime.datetime.now() - expire).days
                return False, f"Ключ истёк {days_expired} дней назад"
            
            self.license_data = data
            return True, data
            
        except Exception as e:
            return False, f"Ошибка проверки: {str(e)}"
    
    def save_license(self, key):
        with open(LICENSE_FILE, "w") as f:
            f.write(key)
    
    def load_license(self):
        if os.path.exists(LICENSE_FILE):
            with open(LICENSE_FILE, "r") as f:
                return f.read().strip()
        return None
    
    def get_days_left(self):
        if not self.license_data:
            return 0
        expire = datetime.datetime.strptime(self.license_data["expire"], "%Y-%m-%d")
        delta = expire - datetime.datetime.now()
        return max(0, delta.days)
    
    def get_plan(self):
        if not self.license_data:
            return "none"
        return self.license_data.get("plan", "standard")
    
    def check_license(self):
        key = self.load_license()
        
        if not key:
            return False, "NO_LICENSE"
        
        valid, result = self.verify_key(key)
        
        if not valid:
            return False, result
        
        return True, result
    
    def activate(self, key):
        valid, result = self.verify_key(key)
        
        if valid:
            self.save_license(key)
            return True, result
        
        return False, result
    
    def show_license_info(self):
        if not self.license_data:
            print("\n  Лицензия: Не активирована")
            return
        
        days = self.get_days_left()
        plan = self.get_plan()
        expire = self.license_data.get("expire", "?")
        
        plan_names = {
            "trial": "Пробный",
            "standard": "Стандарт",
            "premium": "Премиум",
            "unlimited": "Безлимитный"
        }
        
        print(f"""
  Лицензия: {plan_names.get(plan, plan)}
  Истекает: {expire}
  Осталось: {days} дней
        """)


def admin_generate_key():
    lm = LicenseManager()
    
    print("\n" + "=" * 60)
    print("   ГЕНЕРАТОР КЛЮЧЕЙ (АДМИН)")
    print("=" * 60)
    print(f"\nВаш HWID: {lm.hwid}")
    
    print("\nВведите HWID клиента (или UNIVERSAL для любого ПК):")
    hwid = input(": ").strip().upper()
    if not hwid:
        hwid = "UNIVERSAL"
    
    print("\nСрок действия (дней):")
    print("[1] 7 дней")
    print("[2] 30 дней")
    print("[3] 90 дней")
    print("[4] 365 дней")
    print("[5] Своё значение")
    
    choice = input(": ").strip()
    days_map = {"1": 7, "2": 30, "3": 90, "4": 365}
    
    if choice in days_map:
        days = days_map[choice]
    elif choice == "5":
        days = int(input("Дней: ").strip())
    else:
        days = 30
    
    print("\nПлан:")
    print("[1] trial - Пробный")
    print("[2] standard - Стандарт")
    print("[3] premium - Премиум")
    print("[4] unlimited - Безлимитный")
    
    plan_choice = input(": ").strip()
    plans = {"1": "trial", "2": "standard", "3": "premium", "4": "unlimited"}
    plan = plans.get(plan_choice, "standard")
    
    key = lm.generate_key(hwid, days, plan)
    
    print("\n" + "=" * 60)
    print("   СГЕНЕРИРОВАННЫЙ КЛЮЧ")
    print("=" * 60)
    print(f"\nHWID: {hwid}")
    print(f"План: {plan}")
    print(f"Срок: {days} дней")
    print(f"\nКлюч:\n{key}")
    print("\n" + "=" * 60)
    
    save = input("\nСохранить в файл? [y/n]: ").lower()
    if save == 'y':
        filename = f"key_{hwid[:8]}_{days}d.txt"
        with open(filename, "w") as f:
            f.write(f"HWID: {hwid}\n")
            f.write(f"План: {plan}\n")
            f.write(f"Срок: {days} дней\n")
            f.write(f"\nКлюч:\n{key}\n")
        print(f"Сохранено: {filename}")


if __name__ == "__main__":
    admin_generate_key()