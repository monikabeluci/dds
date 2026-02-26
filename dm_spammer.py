import asyncio
import random
import os
import json
from datetime import datetime
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, PeerFloodError
from spintax import Spintax, apply_templates

spintax = Spintax()
DM_STATS_FILE = "dm_stats.json"

class DMSpammer:
    def __init__(self):
        self.stats = {'sent': 0, 'failed': 0, 'flood': 0, 'privacy': 0}
        self.sent_to = []
        self.load_sent()
    
    def load_sent(self):
        if os.path.exists(DM_STATS_FILE):
            try:
                with open(DM_STATS_FILE, 'r') as f:
                    data = json.load(f)
                    self.sent_to = data.get('sent_to', [])
            except:
                pass
    
    def save_sent(self):
        with open(DM_STATS_FILE, 'w') as f:
            json.dump({'sent_to': self.sent_to}, f)
    
    def process_message(self, message):
        message = apply_templates(message)
        message = spintax.spin(message)
        return message
    
    async def send_dm(self, client, user, message, session_name=""):
        try:
            if isinstance(user, dict):
                target = user.get('username') or user.get('id')
            else:
                target = user
            
            if str(target) in self.sent_to:
                return 'skip'
            
            entity = await client.get_entity(target)
            processed_msg = self.process_message(message)
            await client.send_message(entity, processed_msg)
            
            self.sent_to.append(str(target))
            self.save_sent()
            self.stats['sent'] += 1
            
            return 'sent'
            
        except UserPrivacyRestrictedError:
            self.stats['privacy'] += 1
            return 'privacy'
        
        except PeerFloodError:
            self.stats['flood'] += 1
            return 'flood'
        
        except FloodWaitError as e:
            self.stats['flood'] += 1
            return f'flood_{e.seconds}'
        
        except Exception as e:
            self.stats['failed'] += 1
            return f'error: {str(e)[:30]}'
    
    async def mass_dm(self, clients, users, messages, delay_min=60, delay_max=180, daily_limit=20):
        print("\n" + "=" * 60)
        print("РАССЫЛКА В ЛИЧНЫЕ СООБЩЕНИЯ")
        print("=" * 60)
        print(f"Аккаунтов: {len(clients)}")
        print(f"Получателей: {len(users)}")
        print(f"Сообщений: {len(messages)}")
        print(f"Задержка: {delay_min}-{delay_max} ��ек")
        print(f"Лимит в день: {daily_limit}")
        print(f"Спинтакс: Включён")
        print("=" * 60)
        
        self.stats = {'sent': 0, 'failed': 0, 'flood': 0, 'privacy': 0}
        
        clients_list = list(clients.items())
        account_counts = {name: 0 for name, _ in clients_list}
        
        user_index = 0
        
        while user_index < len(users):
            for session_name, client in clients_list:
                if user_index >= len(users):
                    break
                
                if account_counts[session_name] >= daily_limit:
                    continue
                
                user = users[user_index]
                message = random.choice(messages)
                
                if isinstance(user, dict):
                    display = user.get('username') or user.get('id')
                else:
                    display = user
                
                print(f"\n[{session_name[:15]}] -> {display}")
                
                result = await self.send_dm(client, user, message, session_name)
                
                if result == 'sent':
                    print(f"   ✅ Отправлено!")
                    account_counts[session_name] += 1
                    user_index += 1
                    
                    delay = random.randint(delay_min, delay_max)
                    print(f"   Ждём {delay} сек...")
                    await asyncio.sleep(delay)
                
                elif result == 'skip':
                    print(f"   Уже отправляли")
                    user_index += 1
                
                elif result == 'privacy':
                    print(f"   Приватность")
                    user_index += 1
                
                elif result == 'flood':
                    print(f"   Flood! Меняем аккаунт...")
                    await asyncio.sleep(30)
                
                elif result.startswith('flood_'):
                    wait = int(result.split('_')[1])
                    print(f"   Flood {wait}s! Меняем аккаунт...")
                    await asyncio.sleep(30)
                
                else:
                    print(f"   {result}")
                    user_index += 1
            
            if all(count >= daily_limit for count in account_counts.values()):
                print("\nВсе аккаунты достигли лимита!")
                break
        
        print(f"""
============================================================
              РАССЫЛКА ЗАВЕРШЕНА
============================================================
  Отправлено:        {self.stats['sent']}
  Приватность:       {self.stats['privacy']}
  Flood:             {self.stats['flood']}
  Ошибки:            {self.stats['failed']}
============================================================
        """)
        
        return self.stats
    
    def clear_history(self):
        self.sent_to = []
        self.save_sent()
        print("История очищена")
    
    def get_stats(self):
        return self.stats