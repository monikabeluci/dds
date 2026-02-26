# coding: utf-8
import asyncio
import os
import json
from datetime import datetime
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, ChannelParticipantsRecent
from telethon.errors import FloodWaitError, ChatAdminRequiredError

PARSED_FOLDER = "parsed"

class ChatParser:
    def __init__(self):
        if not os.path.exists(PARSED_FOLDER):
            os.makedirs(PARSED_FOLDER)
        self.parsed_users = []
    
    async def parse_chat(self, client, chat_link, limit=1000, active_only=False):
        print(f"\n🔍 Парсинг: {chat_link}")
        print("-" * 50)
        
        self.parsed_users = []
        
        try:
            if "+" in chat_link or "joinchat" in chat_link:
                print("❌ Приватные чаты не поддерживаются для парсинга")
                return []
            
            entity = await client.get_entity(chat_link)
            
            if hasattr(entity, 'title'):
                print(f"📢 Чат: {entity.title}")
            if hasattr(entity, 'participants_count'):
                print(f"👥 Участников: {entity.participants_count}")
            
            print(f"\n⏳ Парсинг до {limit} участников...")
            
            offset = 0
            total = 0
            
            while total < limit:
                try:
                    participants = await client(GetParticipantsRequest(
                        channel=entity,
                        filter=ChannelParticipantsRecent() if active_only else ChannelParticipantsSearch(''),
                        offset=offset,
                        limit=min(200, limit - total),
                        hash=0
                    ))
                    
                    if not participants.users:
                        break
                    
                    for user in participants.users:
                        if user.bot:
                            continue
                        if not user.username and not user.phone:
                            continue
                        
                        user_data = {
                            'id': user.id,
                            'username': user.username or '',
                            'first_name': user.first_name or '',
                            'last_name': user.last_name or '',
                            'phone': user.phone or '',
                            'is_premium': getattr(user, 'premium', False),
                            'has_photo': user.photo is not None
                        }
                        
                        if user_data not in self.parsed_users:
                            self.parsed_users.append(user_data)
                            total += 1
                            
                            if total % 50 == 0:
                                print(f"   Собрано: {total}")
                    
                    offset += len(participants.users)
                    await asyncio.sleep(1)
                    
                    if len(participants.users) < 200:
                        break
                        
                except FloodWaitError as e:
                    print(f"⏳ Flood: ждём {e.seconds}s")
                    await asyncio.sleep(e.seconds + 10)
                except ChatAdminRequiredError:
                    print("❌ Нужны права админа для парсинга")
                    break
                except Exception as e:
                    print(f"⚠️ {str(e)[:50]}")
                    break
            
            print(f"""
╔═══════════════════════════════════════════════════╗
║            ПАРСИНГ ЗАВЕРШЁН                      ║
╠═══════════════════════════════════════════════════╣
║  👥 Всего собрано:     {len(self.parsed_users):<6}                   ║
║  📧 С username:        {len([u for u in self.parsed_users if u['username']]):<6}                   ║
║  ⭐ Premium:           {len([u for u in self.parsed_users if u['is_premium']]):<6}                   ║
╚═══════════════════════════════════════════════════╝
            """)
            
            return self.parsed_users
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return []
    
    def save_to_file(self, filename=None, format='txt'):
        if not self.parsed_users:
            print("❌ Нет данных для сохранения")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parsed_{timestamp}"
        
        filepath = os.path.join(PARSED_FOLDER, f"{filename}.{format}")
        
        if format == 'txt':
            with open(filepath, 'w', encoding='utf-8') as f:
                for user in self.parsed_users:
                    if user['username']:
                        f.write(f"@{user['username']}\n")
                    elif user['id']:
                        f.write(f"{user['id']}\n")
        
        elif format == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.parsed_users, f, indent=2, ensure_ascii=False)
        
        elif format == 'csv':
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("id,username,first_name,last_name,phone,is_premium\n")
                for user in self.parsed_users:
                    f.write(f"{user['id']},{user['username']},{user['first_name']},{user['last_name']},{user['phone']},{user['is_premium']}\n")
        
        print(f"✅ Сохранено: {filepath}")
        return filepath
    
    def load_from_file(self, filepath):
        self.parsed_users = []
        
        try:
            if filepath.endswith('.json'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.parsed_users = json.load(f)
            
            elif filepath.endswith('.txt'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('@'):
                            self.parsed_users.append({'username': line[1:], 'id': 0})
                        elif line.isdigit():
                            self.parsed_users.append({'username': '', 'id': int(line)})
            
            print(f"✅ Загружено: {len(self.parsed_users)} пользователей")
            return self.parsed_users
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return []
    
    def get_users(self):
        return self.parsed_users
    
    def filter_premium(self):
        self.parsed_users = [u for u in self.parsed_users if u.get('is_premium')]
        print(f"✅ Отфильтровано: {len(self.parsed_users)} premium")
        return self.parsed_users
    
    def filter_with_username(self):
        self.parsed_users = [u for u in self.parsed_users if u.get('username')]
        print(f"✅ Отфильтровано: {len(self.parsed_users)} с username")
        return self.parsed_users