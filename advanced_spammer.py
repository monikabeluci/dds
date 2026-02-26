# coding: utf-8
import asyncio
import random
import os
import json
import re
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, GetHistoryRequest
from telethon.tl.types import InputMediaUploadedPhoto, InputMediaUploadedDocument
from telethon.errors import (
    FloodWaitError, ChatWriteForbiddenError, UserBannedInChannelError,
    ChannelPrivateError, ChatAdminRequiredError, SlowModeWaitError,
    UserNotParticipantError, InviteHashExpiredError
)
from spintax import Spintax, apply_templates

spintax = Spintax()

LOGS_FOLDER = "logs"
CHATS_FOLDER = "chats"

class AdvancedSpammer:
    def __init__(self):
        self.stats = {
            'sent': 0,
            'failed': 0,
            'flood': 0,
            'banned': 0,
            'joined': 0,
            'skipped': 0
        }
        self.logs = []
        self.premium_emoji_pattern = re.compile(r'<emoji id="(\d+)">')
        
        if not os.path.exists(LOGS_FOLDER):
            os.makedirs(LOGS_FOLDER)
        if not os.path.exists(CHATS_FOLDER):
            os.makedirs(CHATS_FOLDER)
    
    def count_premium_emoji(self, text):
        """Подсчёт Premium-эмодзи"""
        return len(self.premium_emoji_pattern.findall(text))
    
    def format_text(self, text):
        """Применить форматирование"""
        # Спинтакс
        text = apply_templates(text)
        text = spintax.spin(text)
        return text
    
    def preview_message(self, text, media_path=None):
        """Предпросмотр сообщения"""
        print("\n" + "=" * 60)
        print("ПРЕДПРОСМОТР СООБЩЕНИЯ")
        print("=" * 60)
        
        formatted = self.format_text(text)
        premium_count = self.count_premium_emoji(text)
        
        print(f"\nТекст ({len(formatted)} символов):")
        print("-" * 40)
        print(formatted)
        print("-" * 40)
        
        if premium_count > 0:
            print(f"\nPremium-эмодзи: {premium_count}")
        
        if media_path:
            if os.path.exists(media_path):
                size = os.path.getsize(media_path) / 1024 / 1024
                print(f"\nМедиа: {media_path} ({size:.2f} MB)")
            else:
                print(f"\nМедиа: {media_path} (файл не найден!)")
        
        print("\n" + "=" * 60)
        
        # Показать варианты спинтакса
        print("\nВарианты спинтакса:")
        for i in range(3):
            variant = self.format_text(text)
            print(f"  {i+1}. {variant[:80]}...")
        
        return formatted
    
    async def check_chat_filters(self, client, chat_entity):
        """Проверка фильтров чата"""
        filters = {
            'can_send': True,
            'slow_mode': 0,
            'is_muted': False,
            'has_captcha': False,
            'requires_subscription': False,
            'auto_delete': 0
        }
        
        try:
            # Проверяем права
            if hasattr(chat_entity, 'default_banned_rights'):
                rights = chat_entity.default_banned_rights
                if rights and rights.send_messages:
                    filters['can_send'] = False
            
            # Slow mode
            if hasattr(chat_entity, 'slowmode_enabled') and chat_entity.slowmode_enabled:
                if hasattr(chat_entity, 'slowmode_seconds'):
                    filters['slow_mode'] = chat_entity.slowmode_seconds
            
            # Auto-delete
            if hasattr(chat_entity, 'ttl_period') and chat_entity.ttl_period:
                filters['auto_delete'] = chat_entity.ttl_period
            
        except Exception as e:
            pass
        
        return filters
    
    async def join_chat_safe(self, client, chat, delay_after=30):
        """Безопасное вступление в чат"""
        try:
            if "+" in chat or "joinchat" in chat:
                hash_part = chat.split("/")[-1].replace("+", "")
                await client(ImportChatInviteRequest(hash_part))
            else:
                chat_clean = chat.replace("https://t.me/", "").replace("@", "")
                await client(JoinChannelRequest(chat_clean))
            
            self.stats['joined'] += 1
            self.log(f"JOIN: {chat}")
            
            if delay_after > 0:
                await asyncio.sleep(delay_after)
            
            return True
            
        except FloodWaitError as e:
            self.log(f"JOIN FLOOD: {chat} - {e.seconds}s")
            await asyncio.sleep(e.seconds + 10)
            return False
        except InviteHashExpiredError:
            self.log(f"JOIN EXPIRED: {chat}")
            return False
        except Exception as e:
            self.log(f"JOIN ERROR: {chat} - {str(e)[:30]}")
            return False
    
    async def send_message_advanced(self, client, chat, text, media_path=None, 
                                     parse_mode='md', reply_to=None):
        """Отправка сообщения с медиа и форматированием"""
        try:
            entity = await client.get_entity(chat)
            
            # Проверяем фильтры
            filters = await self.check_chat_filters(client, entity)
            
            if not filters['can_send']:
                self.log(f"SKIP (no rights): {chat}")
                self.stats['skipped'] += 1
                return False, "no_rights"
            
            if filters['slow_mode'] > 0:
                self.log(f"SLOW MODE: {chat} - {filters['slow_mode']}s")
                await asyncio.sleep(filters['slow_mode'])
            
            # Форматируем текст
            formatted_text = self.format_text(text)
            
            # Отправляем
            if media_path and os.path.exists(media_path):
                ext = os.path.splitext(media_path)[1].lower()
                
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    await client.send_file(
                        entity, 
                        media_path, 
                        caption=formatted_text,
                        parse_mode=parse_mode
                    )
                elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                    await client.send_file(
                        entity,
                        media_path,
                        caption=formatted_text,
                        parse_mode=parse_mode,
                        supports_streaming=True
                    )
                else:
                    await client.send_file(
                        entity,
                        media_path,
                        caption=formatted_text,
                        parse_mode=parse_mode
                    )
            else:
                await client.send_message(
                    entity,
                    formatted_text,
                    parse_mode=parse_mode,
                    reply_to=reply_to
                )
            
            self.stats['sent'] += 1
            self.log(f"SENT: {chat}")
            return True, "sent"
            
        except FloodWaitError as e:
            self.stats['flood'] += 1
            self.log(f"FLOOD: {chat} - {e.seconds}s")
            return False, f"flood_{e.seconds}"
        
        except SlowModeWaitError as e:
            self.log(f"SLOW: {chat} - {e.seconds}s")
            await asyncio.sleep(e.seconds)
            return False, "slow_mode"
        
        except ChatWriteForbiddenError:
            self.stats['banned'] += 1
            self.log(f"FORBIDDEN: {chat}")
            return False, "forbidden"
        
        except UserBannedInChannelError:
            self.stats['banned'] += 1
            self.log(f"BANNED: {chat}")
            return False, "banned"
        
        except UserNotParticipantError:
            self.log(f"NOT MEMBER: {chat}")
            return False, "not_member"
        
        except ChannelPrivateError:
            self.log(f"PRIVATE: {chat}")
            return False, "private"
        
        except Exception as e:
            self.stats['failed'] += 1
            self.log(f"ERROR: {chat} - {str(e)[:40]}")
            return False, str(e)
    
    def load_chats_from_file(self, filepath):
        """Загрузка чатов из файла"""
        chats = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        chats.append(line)
        except:
            pass
        return chats
    
    async def get_chats_from_account(self, client, limit=100):
        """Получить чаты из аккаунта"""
        chats = []
        try:
            dialogs = await client.get_dialogs(limit=limit)
            for dialog in dialogs:
                if dialog.is_group or dialog.is_channel:
                    if hasattr(dialog.entity, 'username') and dialog.entity.username:
                        chats.append(f"@{dialog.entity.username}")
                    else:
                        chats.append(str(dialog.entity.id))
        except:
            pass
        return chats
    
    def log(self, message):
        """Добавить лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def save_logs(self):
        """Сохранить логи"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(LOGS_FOLDER, f"spam_log_{timestamp}.txt")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"SPAMMONSTER LOG - {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Sent: {self.stats['sent']}\n")
            f.write(f"Failed: {self.stats['failed']}\n")
            f.write(f"Flood: {self.stats['flood']}\n")
            f.write(f"Banned: {self.stats['banned']}\n")
            f.write(f"Joined: {self.stats['joined']}\n")
            f.write(f"Skipped: {self.stats['skipped']}\n")
            f.write("\n" + "=" * 60 + "\n\n")
            
            for log in self.logs:
                f.write(log + "\n")
        
        print(f"\nЛоги сохранены: {filepath}")
        return filepath
    
    async def mass_spam(self, clients, chats, text, media_path=None,
                        delay_between_chats=30, delay_between_cycles=300,
                        delay_join=60, cycles=1, auto_join=True,
                        rotate_accounts=True):
        """
        Массовая рассылка по чатам
        
        clients: dict {session_name: client}
        chats: list of chat links/usernames
        text: message text (supports spintax)
        media_path: path to media file (optional)
        delay_between_chats: seconds between each chat
        delay_between_cycles: seconds between cycles
        delay_join: seconds after joining chat
        cycles: number of cycles (None = infinite)
        auto_join: automatically join chats
        rotate_accounts: use different accounts for each message
        """
        
        self.stats = {
            'sent': 0, 'failed': 0, 'flood': 0,
            'banned': 0, 'joined': 0, 'skipped': 0
        }
        self.logs = []
        
        print("\n" + "=" * 60)
        print("ЗАПУСК МАССОВОЙ РАССЫЛКИ")
        print("=" * 60)
        print(f"Аккаунтов: {len(clients)}")
        print(f"Чатов: {len(chats)}")
        print(f"Циклов: {cycles if cycles else 'бесконечно'}")
        print(f"Задержка между чатами: {delay_between_chats}s")
        print(f"Задержка между циклами: {delay_between_cycles}s")
        print(f"Авто-вступление: {'Да' if auto_join else 'Нет'}")
        print("=" * 60)
        
        clients_list = list(clients.items())
        current_client_idx = 0
        
        cycle = 0
        while cycles is None or cycle < cycles:
            cycle += 1
            self.log(f"\n--- ЦИКЛ {cycle} ---")
            
            for chat in chats:
                # Выбор аккаунта
                if rotate_accounts:
                    current_client_idx = (current_client_idx + 1) % len(clients_list)
                
                session_name, client = clients_list[current_client_idx]
                
                self.log(f"\n[{session_name[:15]}] -> {chat}")
                
                # Проверяем членство и вступаем
                if auto_join:
                    try:
                        entity = await client.get_entity(chat)
                    except UserNotParticipantError:
                        self.log(f"Вступаем в {chat}...")
                        joined = await self.join_chat_safe(client, chat, delay_join)
                        if not joined:
                            continue
                    except Exception as e:
                        # Пробуем вступить
                        joined = await self.join_chat_safe(client, chat, delay_join)
                        if not joined:
                            continue
                
                # Отправляем
                success, result = await self.send_message_advanced(
                    client, chat, text, media_path
                )
                
                if result.startswith("flood_"):
                    wait_time = int(result.split("_")[1])
                    if wait_time > 300:
                        self.log(f"Долгий flood ({wait_time}s), меняем аккаунт")
                        continue
                    await asyncio.sleep(wait_time + 10)
                
                # Задержка между чатами
                delay = delay_between_chats + random.randint(-10, 10)
                await asyncio.sleep(max(10, delay))
            
            # Задержка между циклами
            if cycles is None or cycle < cycles:
                self.log(f"\nПауза между циклами: {delay_between_cycles}s")
                await asyncio.sleep(delay_between_cycles)
        
        # Итоги
        print(f"""
{'=' * 60}
                РАССЫЛКА ЗАВЕРШЕНА
{'=' * 60}
  Отправлено:    {self.stats['sent']}
  Ошибок:        {self.stats['failed']}
  Flood:         {self.stats['flood']}
  Забанено:      {self.stats['banned']}
  Вступили:      {self.stats['joined']}
  Пропущено:     {self.stats['skipped']}
{'=' * 60}
        """)
        
        self.save_logs()
        return self.stats


class PostBotSpammer:
    """Отправка через @PostBot"""
    
    def __init__(self):
        self.postbot_username = "PostBot"
    
    async def send_via_postbot(self, client, chat, text, media_path=None):
        """Отправка через PostBot"""
        try:
            # Находим PostBot
            postbot = await client.get_entity(self.postbot_username)
            
            # Отправляем команду
            await client.send_message(postbot, f"/post {chat}")
            await asyncio.sleep(2)
            
            # Отправляем контент
            if media_path and os.path.exists(media_path):
                await client.send_file(postbot, media_path, caption=text)
            else:
                await client.send_message(postbot, text)
            
            await asyncio.sleep(2)
            
            # Подтверждаем
            await client.send_message(postbot, "/confirm")
            
            return True
            
        except Exception as e:
            print(f"PostBot error: {e}")
            return False