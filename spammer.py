# coding: utf-8
import asyncio
import random
from datetime import datetime
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, UserBannedInChannelError
from config import ANTIBAN
from spintax import Spintax, apply_templates

spintax = Spintax()

class SafeSpammer:
    def __init__(self, clients):
        self.clients = clients
        self.stats = {'sent': 0, 'failed': 0, 'flood': 0}
        self.account_stats = {}
        for uid, client in clients:
            self.account_stats[uid] = {'sent_hour': 0, 'sent_day': 0, 'last_send': None, 'floods': 0}
    
    def is_work_hours(self):
        hour = datetime.now().hour
        return ANTIBAN['work_hours_start'] <= hour < ANTIBAN['work_hours_end']
    
    def can_send(self, uid):
        stats = self.account_stats[uid]
        if stats['sent_hour'] >= ANTIBAN['messages_per_hour']:
            return False
        if stats['sent_day'] >= ANTIBAN['messages_per_day']:
            return False
        if stats['floods'] >= 3:
            return False
        return True
    
    def get_delay(self):
        return random.randint(ANTIBAN['min_interval'], ANTIBAN['max_interval'])
    
    def get_account_delay(self):
        return random.randint(ANTIBAN['account_delay_min'], ANTIBAN['account_delay_max'])
    
    def process_message(self, message):
        message = apply_templates(message)
        message = spintax.spin(message)
        return message
    
    async def send_message(self, client, uid, chat, message):
        if not self.can_send(uid):
            return False
        
        try:
            processed_msg = self.process_message(message)
            await client.send_message(chat, processed_msg)
            
            self.stats['sent'] += 1
            self.account_stats[uid]['sent_hour'] += 1
            self.account_stats[uid]['sent_day'] += 1
            self.account_stats[uid]['last_send'] = datetime.now()
            
            print(f"✅ [{uid}] Отправлено: {processed_msg[:50]}...")
            return True
            
        except FloodWaitError as e:
            self.stats['flood'] += 1
            self.account_stats[uid]['floods'] += 1
            print(f"⏳ [{uid}] Flood: {e.seconds}s")
            await asyncio.sleep(e.seconds + 10)
            return False
            
        except ChatWriteForbiddenError:
            print(f"🚫 [{uid}] Нет прав писать")
            self.stats['failed'] += 1
            return False
            
        except UserBannedInChannelError:
            print(f"⛔ [{uid}] Забанен в чате")
            self.stats['failed'] += 1
            return False
            
        except Exception as e:
            print(f"❌ [{uid}] {str(e)[:40]}")
            self.stats['failed'] += 1
            return False
    
    async def start_safe_spam(self, chat, messages, rounds=None, warmup=True):
        print("\n" + "=" * 60)
        print("ЗАПУСК РАССЫЛКИ")
        print("=" * 60)
        print(f"Чат: {chat}")
        print(f"Аккаунтов: {len(self.clients)}")
        print(f"Сообщений: {len(messages)}")
        print(f"Кругов: {rounds or 'бесконечно'}")
        print(f"Спинтакс: Включён")
        print("=" * 60)
        
        if warmup:
            print("\nПрогрев...")
            await asyncio.sleep(random.randint(5, 15))
        
        round_num = 0
        while rounds is None or round_num < rounds:
            round_num += 1
            print(f"\n--- КРУГ {round_num} ---")
            
            if not self.is_work_hours():
                print("Не рабочие часы. Ждём...")
                await asyncio.sleep(300)
                continue
            
            for uid, client in self.clients:
                if not self.can_send(uid):
                    print(f"[{uid}] Лимит исчерпан")
                    continue
                
                message = random.choice(messages)
                await self.send_message(client, uid, chat, message)
                
                delay = self.get_account_delay()
                print(f"Ждём {delay}s...")
                await asyncio.sleep(delay)
            
            delay = self.get_delay()
            print(f"\nПауза между кругами: {delay}s")
            await asyncio.sleep(delay)
        
        self.print_stats()
    
    def print_stats(self):
        print(f"""
============================================================
                  СТАТИСТИКА РАССЫЛКИ
============================================================
  Отправлено:        {self.stats['sent']}
  Ошибок:            {self.stats['failed']}
  Flood:             {self.stats['flood']}
============================================================
        """)