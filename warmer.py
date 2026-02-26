import asyncio
import random
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.errors import FloodWaitError

class AccountWarmer:
    def __init__(self):
        self.public_channels = [
            'telegram', 'durov', 'tchannel', 'worldnews',
            'music', 'movies', 'books', 'travel'
        ]
        self.actions_done = {}
    
    async def warm_account(self, client, session_name, days=7, intensity='medium'):
        print(f"\n🔥 Прогрев: {session_name}")
        print("-" * 40)
        
        self.actions_done[session_name] = {
            'messages_read': 0,
            'channels_joined': 0,
            'reactions': 0,
            'profile_updates': 0
        }
        
        actions_per_day = {'low': 5, 'medium': 15, 'high': 30}
        total_actions = actions_per_day.get(intensity, 15) * days
        
        try:
            me = await client.get_me()
            print(f"👤 Аккаунт: {me.first_name}")
            
            # 1. Читаем существующие диалоги
            print("\n📖 Читаю диалоги...")
            dialogs = await client.get_dialogs(limit=20)
            for dialog in dialogs[:10]:
                try:
                    await client.send_read_acknowledge(dialog.entity)
                    self.actions_done[session_name]['messages_read'] += 1
                    await asyncio.sleep(random.uniform(1, 3))
                except:
                    pass
            print(f"   Прочитано: {self.actions_done[session_name]['messages_read']} диалогов")
            
            # 2. Вступаем в публичные каналы
            print("\n📢 Вступаю в каналы...")
            channels_to_join = random.sample(self.public_channels, min(3, len(self.public_channels)))
            for channel in channels_to_join:
                try:
                    await client(JoinChannelRequest(channel))
                    self.actions_done[session_name]['channels_joined'] += 1
                    print(f"   + @{channel}")
                    await asyncio.sleep(random.uniform(5, 15))
                except FloodWaitError as e:
                    print(f"   ⏳ Flood: ждём {e.seconds}s")
                    await asyncio.sleep(e.seconds + 10)
                except Exception as e:
                    print(f"   - @{channel}: {str(e)[:20]}")
            
            # 3. Читаем историю каналов
            print("\n📜 Читаю историю каналов...")
            for dialog in dialogs:
                if hasattr(dialog.entity, 'broadcast') and dialog.entity.broadcast:
                    try:
                        history = await client(GetHistoryRequest(
                            peer=dialog.entity,
                            limit=20,
                            offset_date=None,
                            offset_id=0,
                            max_id=0,
                            min_id=0,
                            add_offset=0,
                            hash=0
                        ))
                        self.actions_done[session_name]['messages_read'] += len(history.messages)
                        await asyncio.sleep(random.uniform(2, 5))
                    except:
                        pass
            
            # 4. Обновляем профиль (опционально)
            if random.random() > 0.7:
                print("\n✏️ Обновляю профиль...")
                bios = [
                    "Life is good ✨", "Just living 🌍", "Hello world 👋",
                    "🎵 Music lover", "📚 Reader", "✈️ Traveler",
                    "☕ Coffee addict", "🎮 Gamer", "📸 Photographer"
                ]
                try:
                    await client(UpdateProfileRequest(about=random.choice(bios)))
                    self.actions_done[session_name]['profile_updates'] += 1
                    print("   ✅ Bio обновлено")
                except:
                    pass
            
            # Итоги
            print(f"""
╔═══════════════════════════════════════╗
║       ПРОГРЕВ ЗАВЕРШЁН               ║
╠═══════════════════════════════════════╣
║  📖 Прочитано сообщений: {self.actions_done[session_name]['messages_read']:<5}       ║
║  📢 Вступил в каналы:    {self.actions_done[session_name]['channels_joined']:<5}       ║
║  ✏️ Обновлений профиля:  {self.actions_done[session_name]['profile_updates']:<5}       ║
╚═══════════════════════════════════════╝
            """)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    async def warm_all(self, clients, days=7, intensity='medium'):
        print("\n" + "=" * 50)
        print("🔥 МАССОВЫЙ ПРОГРЕВ АККАУНТОВ")
        print("=" * 50)
        print(f"Аккаунтов: {len(clients)}")
        print(f"Дней прогрева: {days}")
        print(f"Интенсивность: {intensity}")
        
        success = 0
        for session_name, client in clients.items():
            result = await self.warm_account(client, session_name, days, intensity)
            if result:
                success += 1
            await asyncio.sleep(random.uniform(30, 60))
        
        print(f"\n✅ Прогрето: {success}/{len(clients)}")
        return success