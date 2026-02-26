# coding: utf-8
import asyncio
from datetime import datetime, timedelta

class Inbox:
    def __init__(self):
        self.messages = {}
    
    async def get_unread(self, client, session_name, limit=20):
        unread = []
        
        try:
            dialogs = await client.get_dialogs(limit=50)
            
            for dialog in dialogs:
                if dialog.unread_count > 0:
                    if dialog.is_user:
                        msgs = await client.get_messages(dialog.entity, limit=dialog.unread_count)
                        
                        for msg in msgs:
                            if msg.out:
                                continue
                            
                            unread.append({
                                'dialog_id': dialog.id,
                                'user_id': dialog.entity.id,
                                'username': getattr(dialog.entity, 'username', '') or '',
                                'first_name': getattr(dialog.entity, 'first_name', '') or '',
                                'last_name': getattr(dialog.entity, 'last_name', '') or '',
                                'message_id': msg.id,
                                'text': msg.text or '[медиа]',
                                'date': msg.date,
                                'entity': dialog.entity
                            })
        
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        self.messages[session_name] = unread
        return unread
    
    async def get_recent(self, client, session_name, hours=24, limit=50):
        recent = []
        since = datetime.now() - timedelta(hours=hours)
        
        try:
            dialogs = await client.get_dialogs(limit=50)
            
            for dialog in dialogs:
                if not dialog.is_user:
                    continue
                
                msgs = await client.get_messages(dialog.entity, limit=10)
                
                for msg in msgs:
                    if msg.out:
                        continue
                    
                    if msg.date.replace(tzinfo=None) > since:
                        recent.append({
                            'dialog_id': dialog.id,
                            'user_id': dialog.entity.id,
                            'username': getattr(dialog.entity, 'username', '') or '',
                            'first_name': getattr(dialog.entity, 'first_name', '') or '',
                            'text': msg.text or '[медиа]',
                            'date': msg.date,
                            'unread': not msg.out and dialog.unread_count > 0,
                            'entity': dialog.entity
                        })
                
                if len(recent) >= limit:
                    break
        
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        return recent
    
    async def reply(self, client, entity, message):
        try:
            await client.send_message(entity, message)
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False
    
    async def mark_read(self, client, entity):
        try:
            await client.send_read_acknowledge(entity)
            return True
        except:
            return False
    
    def print_messages(self, messages, session_name):
        if not messages:
            print(f"\n📭 [{session_name}] Нет новых сообщений")
            return
        
        print(f"\n{'='*60}")
        print(f"📬 [{session_name}] Входящие: {len(messages)}")
        print("="*60)
        
        for i, msg in enumerate(messages, 1):
            name = msg['first_name']
            if msg['username']:
                name += f" (@{msg['username']})"
            
            date_str = msg['date'].strftime("%d.%m %H:%M")
            unread = "🔴" if msg.get('unread', True) else "⚪"
            
            print(f"\n{unread} [{i}] От: {name}")
            print(f"   📅 {date_str}")
            print(f"   💬 {msg['text'][:100]}{'...' if len(msg['text']) > 100 else ''}")
        
        print("\n" + "="*60)


class InboxManager:
    def __init__(self):
        self.inbox = Inbox()
        self.current_messages = {}
        self.current_clients = {}
    
    async def check_all_accounts(self, clients):
        print("\n" + "="*60)
        print("📬 ПРОВЕРКА ВХОДЯЩИХ СООБЩЕНИЙ")
        print("="*60)
        
        total_unread = 0
        self.current_clients = clients
        
        for session_name, client in clients.items():
            try:
                me = await client.get_me()
                print(f"\n🔍 Проверка: {me.first_name} ({session_name})")
                
                messages = await self.inbox.get_unread(client, session_name)
                self.current_messages[session_name] = messages
                
                if messages:
                    total_unread += len(messages)
                    self.inbox.print_messages(messages, session_name)
                else:
                    print(f"   📭 Нет новых сообщений")
                    
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
            
            await asyncio.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"📊 Всего непрочитанных: {total_unread}")
        print("="*60)
        
        return total_unread
    
    async def interactive_reply(self, clients):
        self.current_clients = clients
        
        while True:
            all_messages = []
            for session_name, messages in self.current_messages.items():
                for msg in messages:
                    msg['session'] = session_name
                    all_messages.append(msg)
            
            if not all_messages:
                print("\n📭 Нет сообщений для ответа")
                break
            
            print("\n" + "="*60)
            print("📬 ВСЕ ВХОДЯЩИЕ СООБЩЕНИЯ")
            print("="*60)
            
            for i, msg in enumerate(all_messages, 1):
                name = msg['first_name']
                if msg['username']:
                    name += f" (@{msg['username']})"
                
                print(f"\n[{i}] {msg['session'][:15]} <- {name}")
                print(f"    {msg['text'][:80]}{'...' if len(msg['text']) > 80 else ''}")
            
            print(f"\n[0] Выход")
            print("="*60)
            
            choice = input("\nВыберите сообщение для ответа: ").strip()
            
            if choice == "0" or not choice:
                break
            
            if not choice.isdigit() or int(choice) > len(all_messages):
                print("❌ Неверный выбор")
                continue
            
            idx = int(choice) - 1
            selected = all_messages[idx]
            
            print(f"\n{'='*60}")
            print(f"От: {selected['first_name']} (@{selected['username']})")
            print(f"Аккаунт: {selected['session']}")
            print(f"{'='*60}")
            print(f"\n{selected['text']}")
            print(f"\n{'='*60}")
            
            reply_text = input("\n✏️ Ваш ответ (пусто = отмена): ").strip()
            
            if not reply_text:
                continue
            
            client = self.current_clients.get(selected['session'])
            if client:
                success = await self.inbox.reply(client, selected['entity'], reply_text)
                if success:
                    print("✅ Ответ отправлен!")
                    self.current_messages[selected['session']] = [
                        m for m in self.current_messages[selected['session']]
                        if m['message_id'] != selected['message_id']
                    ]
                else:
                    print("❌ Ошибка отправки")
            
            await asyncio.sleep(1)
    
    async def quick_reply_all(self, clients, message):
        count = 0
        
        for session_name, messages in self.current_messages.items():
            client = clients.get(session_name)
            if not client:
                continue
            
            for msg in messages:
                success = await self.inbox.reply(client, msg['entity'], message)
                if success:
                    print(f"✅ [{session_name}] -> {msg['first_name']}")
                    count += 1
                await asyncio.sleep(2)
        
        print(f"\n📤 Отправлено ответов: {count}")
        return count