# coding: utf-8
import asyncio
import os
import json
from datetime import datetime
from telethon import events
from telethon.tl.types import User
from spintax import Spintax, apply_templates

spintax = Spintax()

RESPONDER_FILE = "auto_responder.json"
RESPONDED_FILE = "responded_users.json"

class AutoResponder:
    def __init__(self):
        self.is_running = False
        self.settings = {
            'enabled': False,
            'reply_once': True,
            'delay_min': 5,
            'delay_max': 30,
            'only_private': True,
            'ignore_bots': True,
            'ignore_groups': True,
            'work_hours_start': 0,
            'work_hours_end': 24,
            'message': 'Привет! Спасибо за сообщение. Отвечу в ближайшее время.',
            'media_path': None,
            'keywords': [],
            'blacklist': [],
            'whitelist': []
        }
        self.responded_users = {}
        self.stats = {
            'total_received': 0,
            'total_responded': 0,
            'skipped': 0
        }
        self.handlers = {}
        self.load_settings()
        self.load_responded()
    
    def load_settings(self):
        if os.path.exists(RESPONDER_FILE):
            try:
                with open(RESPONDER_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.settings.update(saved)
            except:
                pass
    
    def save_settings(self):
        with open(RESPONDER_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
    
    def load_responded(self):
        if os.path.exists(RESPONDED_FILE):
            try:
                with open(RESPONDED_FILE, 'r', encoding='utf-8') as f:
                    self.responded_users = json.load(f)
            except:
                pass
    
    def save_responded(self):
        with open(RESPONDED_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.responded_users, f, indent=2)
    
    def is_work_hours(self):
        hour = datetime.now().hour
        return self.settings['work_hours_start'] <= hour < self.settings['work_hours_end']
    
    def should_respond(self, user_id, username, message_text):
        """Проверка нужно ли отвечать"""
        
        # Проверка рабочих часов
        if not self.is_work_hours():
            return False, "not_work_hours"
        
        # Проверка reply_once
        if self.settings['reply_once']:
            user_key = str(user_id)
            if user_key in self.responded_users:
                return False, "already_responded"
        
        # Проверка blacklist
        if username and username.lower() in [b.lower() for b in self.settings['blacklist']]:
            return False, "blacklisted"
        
        if str(user_id) in self.settings['blacklist']:
            return False, "blacklisted"
        
        # Проверка whitelist (если не пустой - только для них)
        if self.settings['whitelist']:
            in_whitelist = False
            if username and username.lower() in [w.lower() for w in self.settings['whitelist']]:
                in_whitelist = True
            if str(user_id) in self.settings['whitelist']:
                in_whitelist = True
            if not in_whitelist:
                return False, "not_in_whitelist"
        
        # Проверка ключевых слов
        if self.settings['keywords']:
            found = False
            text_lower = message_text.lower()
            for keyword in self.settings['keywords']:
                if keyword.lower() in text_lower:
                    found = True
                    break
            if not found:
                return False, "no_keywords"
        
        return True, "ok"
    
    def format_response(self):
        """Форматирование ответа со спинтаксом"""
        text = self.settings['message']
        text = apply_templates(text)
        text = spintax.spin(text)
        return text
    
    async def send_response(self, client, event, session_name):
        """Отправка ответа"""
        import random
        
        try:
            sender = await event.get_sender()
            
            if not sender:
                return False
            
            # Игнорируем ботов
            if self.settings['ignore_bots'] and getattr(sender, 'bot', False):
                return False
            
            user_id = sender.id
            username = getattr(sender, 'username', '') or ''
            first_name = getattr(sender, 'first_name', '') or ''
            message_text = event.message.text or ''
            
            # Проверяем нужно ли отвечать
            should, reason = self.should_respond(user_id, username, message_text)
            
            if not should:
                self.stats['skipped'] += 1
                return False
            
            # Задержка перед ответом
            delay = random.randint(self.settings['delay_min'], self.settings['delay_max'])
            await asyncio.sleep(delay)
            
            # Форматируем ответ
            response_text = self.format_response()
            
            # Персонализация
            response_text = response_text.replace('{name}', first_name)
            response_text = response_text.replace('{username}', f'@{username}' if username else first_name)
            
            # Отправляем
            media_path = self.settings.get('media_path')
            
            if media_path and os.path.exists(media_path):
                await client.send_file(
                    sender.id,
                    media_path,
                    caption=response_text,
                    parse_mode='md'
                )
            else:
                await client.send_message(
                    sender.id,
                    response_text,
                    parse_mode='md'
                )
            
            # Записываем что ответили
            self.responded_users[str(user_id)] = {
                'username': username,
                'first_name': first_name,
                'responded_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'session': session_name
            }
            self.save_responded()
            
            self.stats['total_responded'] += 1
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{session_name}] -> {first_name} (@{username}): Ответ отправлен")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] {str(e)[:50]}")
            return False
    
    async def start(self, clients):
        """Запуск автоответчика"""
        if self.is_running:
            print("Автоответчик уже запущен!")
            return
        
        self.is_running = True
        self.settings['enabled'] = True
        self.save_settings()
        
        print("\n" + "=" * 60)
        print("   АВТООТВЕТЧИК ЗАПУЩЕН")
        print("=" * 60)
        print(f"   Аккаунтов: {len(clients)}")
        print(f"   Ответ один раз: {'Да' if self.settings['reply_once'] else 'Нет'}")
        print(f"   Задержка: {self.settings['delay_min']}-{self.settings['delay_max']} сек")
        print(f"   Рабочие часы: {self.settings['work_hours_start']}:00-{self.settings['work_hours_end']}:00")
        if self.settings['keywords']:
            print(f"   Ключевые слова: {', '.join(self.settings['keywords'])}")
        if self.settings['media_path']:
            print(f"   Медиа: {self.settings['media_path']}")
        print("=" * 60)
        print("\n   Нажмите Ctrl+C для остановки\n")
        
        # Регистрируем обработчики для каждого клиента
        for session_name, client in clients.items():
            
            @client.on(events.NewMessage(incoming=True))
            async def handler(event, c=client, s=session_name):
                if not self.is_running:
                    return
                
                # Только личные сообщения
                if self.settings['only_private'] and not event.is_private:
                    return
                
                # Игнорируем группы
                if self.settings['ignore_groups'] and (event.is_group or event.is_channel):
                    return
                
                self.stats['total_received'] += 1
                await self.send_response(c, event, s)
            
            self.handlers[session_name] = handler
        
        # Держим соединение
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    
    def stop(self):
        """Остановка автоответчика"""
        self.is_running = False
        self.settings['enabled'] = False
        self.save_settings()
        self.handlers = {}  # Очистка handlers
        
        print("\n" + "=" * 60)
        print("   АВТООТВЕТЧИК ОСТАНОВЛЕН")
        print("=" * 60)
        print(f"   Получено сообщений: {self.stats['total_received']}")
        print(f"   Отправлено ответов: {self.stats['total_responded']}")
        print(f"   Пропущено: {self.stats['skipped']}")
        print("=" * 60)
    
    def clear_responded(self):
        """Очистить список отвеченных"""
        self.responded_users = {}
        self.save_responded()
        print("История ответов очищена!")
    
    def add_to_blacklist(self, user):
        """Добавить в черный список"""
        if user not in self.settings['blacklist']:
            self.settings['blacklist'].append(user)
            self.save_settings()
    
    def remove_from_blacklist(self, user):
        """Удалить из черного списка"""
        if user in self.settings['blacklist']:
            self.settings['blacklist'].remove(user)
            self.save_settings()
    
    def add_keyword(self, keyword):
        """Добавить ключевое слово"""
        if keyword not in self.settings['keywords']:
            self.settings['keywords'].append(keyword)
            self.save_settings()
    
    def remove_keyword(self, keyword):
        """Удалить ключевое слово"""
        if keyword in self.settings['keywords']:
            self.settings['keywords'].remove(keyword)
            self.save_settings()
    
    def print_settings(self):
        """Показать текущие настройки"""
        print(f"""
{'=' * 60}
   НАСТРОЙКИ АВТООТВЕТЧИКА
{'=' * 60}

   Статус: {'ВКЛЮЧЕН' if self.settings['enabled'] else 'ВЫКЛЮЧЕН'}
   
   Ответ один раз: {'Да' if self.settings['reply_once'] else 'Нет'}
   Задержка: {self.settings['delay_min']}-{self.settings['delay_max']} сек
   Только ЛС: {'Да' if self.settings['only_private'] else 'Нет'}
   Игнорировать ботов: {'Да' if self.settings['ignore_bots'] else 'Нет'}
   Рабочие часы: {self.settings['work_hours_start']}:00-{self.settings['work_hours_end']}:00
   
   Сообщение:
   {self.settings['message'][:100]}{'...' if len(self.settings['message']) > 100 else ''}
   
   Медиа: {self.settings['media_path'] or 'Нет'}
   
   Ключевые слова: {', '.join(self.settings['keywords']) if self.settings['keywords'] else 'Все сообщения'}
   Черный список: {len(self.settings['blacklist'])} пользователей
   Белый список: {len(self.settings['whitelist'])} пользователей
   
   Уже ответили: {len(self.responded_users)} пользователям
{'=' * 60}
        """)
    
    def preview_response(self):
        """Предпросмотр ответа"""
        print("\n" + "=" * 60)
        print("   ПРЕДПРОСМОТР ОТВЕТА")
        print("=" * 60)
        
        print("\nВарианты ответа (спинтакс):")
        for i in range(5):
            response = self.format_response()
            response = response.replace('{name}', 'Иван')
            response = response.replace('{username}', '@user123')
            print(f"\n{i+1}. {response}")
        
        if self.settings['media_path']:
            print(f"\n+ Медиа: {self.settings['media_path']}")
        
        print("\n" + "=" * 60)