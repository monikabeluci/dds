"""
SpamMonster - Антибан система
"""

import random
import re
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from config import ANTIBAN, EMOJI_POOL, INVISIBLE_CHARS


class AntiBanSystem:
    def __init__(self):
        self.message_count = defaultdict(lambda: {"hour": 0, "day": 0, "last_reset_hour": None, "last_reset_day": None})
        self.last_message_time = {}
        self.floodwait_until = {}
        self.account_errors = defaultdict(int)
    
    def get_random_interval(self):
        base = random.randint(ANTIBAN["min_interval"], ANTIBAN["max_interval"])
        jitter = random.uniform(0.1, 2.5)
        return base + jitter
    
    def get_account_delay(self):
        return random.randint(ANTIBAN["account_delay_min"], ANTIBAN["account_delay_max"])
    
    def get_round_pause(self):
        return random.randint(ANTIBAN["round_pause_min"], ANTIBAN["round_pause_max"])
    
    def get_typing_duration(self):
        return random.uniform(ANTIBAN["typing_duration_min"], ANTIBAN["typing_duration_max"])
    
    def check_limits(self, account_id):
        stats = self.message_count[account_id]
        now = datetime.now()
        
        if stats["last_reset_hour"] is None or now.hour != stats["last_reset_hour"]:
            stats["hour"] = 0
            stats["last_reset_hour"] = now.hour
        
        if stats["last_reset_day"] is None or now.date() != stats["last_reset_day"]:
            stats["day"] = 0
            stats["last_reset_day"] = now.date()
        
        if stats["hour"] >= ANTIBAN["messages_per_hour"]:
            return False, f"Лимит в час ({ANTIBAN['messages_per_hour']})"
        
        if stats["day"] >= ANTIBAN["messages_per_day"]:
            return False, f"Лимит в день ({ANTIBAN['messages_per_day']})"
        
        return True, "OK"
    
    def increment_counter(self, account_id):
        self.message_count[account_id]["hour"] += 1
        self.message_count[account_id]["day"] += 1
        self.last_message_time[account_id] = datetime.now()
    
    def is_working_hours(self):
        hour = datetime.now().hour
        return ANTIBAN["work_hours_start"] <= hour < ANTIBAN["work_hours_end"]
    
    def get_sleep_until_work(self):
        now = datetime.now()
        if now.hour >= ANTIBAN["work_hours_end"]:
            next_start = now.replace(hour=ANTIBAN["work_hours_start"], minute=0, second=0) + timedelta(days=1)
        else:
            next_start = now.replace(hour=ANTIBAN["work_hours_start"], minute=0, second=0)
        return (next_start - now).total_seconds()
    
    def handle_floodwait(self, account_id, seconds):
        wait_time = min(seconds * ANTIBAN["floodwait_multiplier"], ANTIBAN["max_floodwait"])
        self.floodwait_until[account_id] = datetime.now() + timedelta(seconds=wait_time)
        self.account_errors[account_id] += 1
        return wait_time
    
    def is_in_floodwait(self, account_id):
        if account_id not in self.floodwait_until:
            return False
        return datetime.now() < self.floodwait_until[account_id]
    
    def get_floodwait_remaining(self, account_id):
        if account_id not in self.floodwait_until:
            return 0
        remaining = (self.floodwait_until[account_id] - datetime.now()).total_seconds()
        return max(0, remaining)
    
    def get_available_accounts(self, all_accounts):
        available = []
        for account_id, client in all_accounts:
            if self.is_in_floodwait(account_id):
                continue
            can_send, _ = self.check_limits(account_id)
            if not can_send:
                continue
            if self.account_errors[account_id] >= 5:
                continue
            available.append((account_id, client))
        random.shuffle(available)
        return available


class TextSpinner:
    @staticmethod
    def spin(text):
        pattern = r'\{([^}]+)\}'
        def replace_spin(match):
            options = match.group(1).split('|')
            return random.choice(options)
        return re.sub(pattern, replace_spin, text)
    
    @staticmethod
    def add_invisible_char(text):
        char = random.choice(INVISIBLE_CHARS)
        position = random.randint(0, len(text))
        return text[:position] + char + text[position:]
    
    @staticmethod
    def add_random_emoji(text):
        if random.random() < 0.5:
            emoji = random.choice(EMOJI_POOL)
            return f"{text} {emoji}"
        return text
    
    @staticmethod
    def make_unique(text):
        text = TextSpinner.spin(text)
        text = TextSpinner.add_random_emoji(text)
        text = TextSpinner.add_invisible_char(text)
        return text


class AccountWarmer:
    @staticmethod
    async def warmup(client, actions=None):
        if actions is None:
            actions = ANTIBAN["warmup_actions"]
        
        me = await client.get_me()
        print(f"🌡️ Прогрев: {me.first_name}...")
        
        try:
            await client.get_dialogs(limit=20)
            await asyncio.sleep(random.uniform(2, 4))
        except:
            pass
        
        try:
            from telethon.tl.functions.contacts import GetContactsRequest
            await client(GetContactsRequest(hash=0))
            await asyncio.sleep(random.uniform(1, 3))
        except:
            pass
        
        try:
            from telethon.tl.functions.account import UpdateStatusRequest
            await client(UpdateStatusRequest(offline=False))
        except:
            pass
        
        print(f"✅ Прогрев {me.first_name} завершён")