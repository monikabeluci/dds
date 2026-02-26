#!/usr/bin/env python3
"""
Telegram Multi-Account Manager CLI
Parser, Inviter, and Sender modules
"""
import argparse
import asyncio
import os
import sys

# Add telegram-manager to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'telegram-manager'))


def get_client(account_name: str = None):
    """Get Telethon client for account"""
    try:
        from telethon import TelegramClient
        api_id = int(os.environ.get('TELEGRAM_API_ID', '0'))
        api_hash = os.environ.get('TELEGRAM_API_HASH', '')
        session = account_name or 'default'
        return TelegramClient(session, api_id, api_hash)
    except ImportError:
        print("Error: telethon not installed. Run: pip install telethon")
        sys.exit(1)


# ─────────────────────── PARSER COMMANDS ───────────────────────

async def cmd_parse_chat(args):
    from parser.chat_parser import ChatParser
    from parser.export import ParserExporter

    client = get_client(getattr(args, 'account', None))
    async with client:
        parser = ChatParser(client, args.account or 'default')
        users = await parser.parse(
            chat_ids=args.chats,
            limit_per_chat=getattr(args, 'limit', None),
            only_admins=getattr(args, 'admins', False),
            aggressive=getattr(args, 'aggressive', False),
        )
        exporter = ParserExporter()
        output = args.output
        if output.endswith('.csv'):
            exporter.export_csv(users, output)
        elif output.endswith('.json'):
            exporter.export_json(users, output)
        else:
            exporter.export_txt(users, output)
        print(f"✅ Parsed {len(users)} users → {output}")
        print(f"   Stats: {parser.stats}")


async def cmd_parse_comments(args):
    from parser.comments_parser import CommentsParser
    from parser.export import ParserExporter

    client = get_client(getattr(args, 'account', None))
    async with client:
        parser = CommentsParser(client, args.account or 'default')
        users = await parser.parse(
            channel=args.channel,
            posts_limit=getattr(args, 'posts_limit', 100),
        )
        exporter = ParserExporter()
        output = args.output
        if output.endswith('.csv'):
            exporter.export_csv(users, output)
        else:
            exporter.export_txt(users, output)
        print(f"✅ Parsed {len(users)} users from comments → {output}")


async def cmd_parse_contacts(args):
    from parser.contacts_parser import ContactsParser
    from parser.export import ParserExporter

    client = get_client(getattr(args, 'account', None))
    async with client:
        parser = ContactsParser(client, args.account or 'default')
        users = await parser.parse()
        exporter = ParserExporter()
        exporter.export_txt(users, args.output)
        print(f"✅ Parsed {len(users)} contacts → {args.output}")


async def cmd_parse_gifts(args):
    from parser.gifts_parser import GiftsParser
    from parser.export import ParserExporter

    client = get_client(getattr(args, 'account', None))
    async with client:
        parser = GiftsParser(client, args.account or 'default')
        users = await parser.parse(
            chat=args.channel,
            gift_type=getattr(args, 'type', 'all'),
        )
        exporter = ParserExporter()
        exporter.export_txt(users, args.output)
        print(f"✅ Parsed {len(users)} gift users → {args.output}")


async def cmd_parse_messages(args):
    from parser.messages_parser import MessagesParser
    from parser.export import ParserExporter

    keywords = None
    if getattr(args, 'keywords', None):
        keywords = [k.strip() for k in args.keywords.split(',')]

    client = get_client(getattr(args, 'account', None))
    async with client:
        parser = MessagesParser(client, args.account or 'default')
        users = await parser.parse(
            chat=args.chat,
            keywords=keywords,
        )
        exporter = ParserExporter()
        exporter.export_txt(users, args.output)
        print(f"✅ Parsed {len(users)} users from messages → {args.output}")


async def cmd_parse_bio(args):
    from parser.base_parser import ParsedUser
    from parser.bio_parser import BioParser
    from parser.export import ParserExporter
    from datetime import datetime as _dt, timezone as _tz

    keywords = [k.strip() for k in args.keywords.split(',')]

    # Load input users
    input_users = []
    if os.path.exists(args.input):
        with open(args.input, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    uid = int(line)
                    input_users.append(ParsedUser(
                        user_id=uid, username=None, first_name=None,
                        last_name=None, phone=None, bio=None,
                        is_premium=False, is_bot=False, is_verified=False,
                        last_online=None, source='file', source_id=None,
                        parsed_at=_dt.now(_tz.utc),
                    ))
                except ValueError:
                    username = line.lstrip('@')
                    input_users.append(ParsedUser(
                        user_id=0, username=username, first_name=None,
                        last_name=None, phone=None, bio=None,
                        is_premium=False, is_bot=False, is_verified=False,
                        last_online=None, source='file', source_id=None,
                        parsed_at=_dt.now(_tz.utc),
                    ))

    client = get_client(getattr(args, 'account', None))
    async with client:
        parser = BioParser(client, args.account or 'default')
        users = await parser.parse(
            source_users=input_users,
            keywords=keywords,
            match_mode=getattr(args, 'mode', 'any'),
        )
        exporter = ParserExporter()
        exporter.export_txt(users, args.output)
        print(f"✅ Filtered {len(users)} users by BIO → {args.output}")


async def cmd_parse_merge(args):
    from parser.export import ParserExporter

    exporter = ParserExporter()
    count = exporter.merge_bases(
        filepaths=args.files,
        output=args.output,
        deduplicate=getattr(args, 'dedupe', True),
    )
    print(f"✅ Merged {count} entries → {args.output}")


# ─────────────────────── INVITER COMMANDS ───────────────────────

async def cmd_invite_username(args):
    from inviter.username_inviter import UsernameInviter

    # Load usernames
    usernames = []
    if os.path.exists(args.file):
        with open(args.file, 'r', encoding='utf-8') as f:
            usernames = [line.strip() for line in f if line.strip()]

    client = get_client(getattr(args, 'account', None))
    async with client:
        inviter = UsernameInviter(client, args.account or 'default')

        def progress(current, total, stats):
            print(f"\r  Progress: {current}/{total} | ✅{stats.success} ❌{stats.other_errors}", end='')

        stats = await inviter.invite(
            target_chat=args.target,
            usernames=usernames,
            delay_min=getattr(args, 'delay_min', 30),
            delay_max=getattr(args, 'delay_max', 60),
            batch_size=getattr(args, 'batch_size', 10),
            batch_delay=getattr(args, 'batch_delay', 300),
            on_progress=progress,
        )
        print(f"\n✅ Done! Success: {stats.success}, Errors: {stats.other_errors}")


async def cmd_invite_phone(args):
    from inviter.phone_inviter import PhoneInviter

    phones = []
    if os.path.exists(args.file):
        with open(args.file, 'r', encoding='utf-8') as f:
            phones = [line.strip() for line in f if line.strip()]

    client = get_client(getattr(args, 'account', None))
    async with client:
        inviter = PhoneInviter(client, args.account or 'default')
        stats = await inviter.invite(
            target_chat=args.target,
            phones=phones,
            add_to_contacts=getattr(args, 'add_contacts', True),
        )
        print(f"✅ Done! Success: {stats.success}, Errors: {stats.other_errors}")


async def cmd_invite_admin(args):
    from inviter.admin_inviter import AdminInviter

    users = []
    if os.path.exists(args.file):
        with open(args.file, 'r', encoding='utf-8') as f:
            users = [line.strip() for line in f if line.strip()]

    client = get_client(getattr(args, 'account', None))
    async with client:
        inviter = AdminInviter(client, args.account or 'default')
        stats = await inviter.invite(target_chat=args.target, users=users)
        print(f"✅ Done! Success: {stats.success}, Errors: {stats.other_errors}")


async def cmd_invite_promote(args):
    from inviter.admin_manager import AdminManager

    client = get_client(getattr(args, 'account', None))
    async with client:
        manager = AdminManager(client)
        success = await manager.promote_for_invite(args.chat, args.user)
        if success:
            print(f"✅ Promoted {args.user} as invite admin in {args.chat}")
        else:
            print(f"❌ Failed to promote {args.user}")


async def cmd_invite_check_rights(args):
    from inviter.validators import InviteValidator

    client = get_client(getattr(args, 'account', None))
    async with client:
        validator = InviteValidator(client)
        rights = await validator.check_chat_rights(args.chat)
        print(f"Chat: {args.chat}")
        for key, val in rights.items():
            print(f"  {key}: {val}")


# ─────────────────────── SENDER COMMANDS ───────────────────────

def build_content(args) -> 'MessageContent':
    from sender.base_sender import MessageContent

    text = getattr(args, 'message', None)
    if not text and getattr(args, 'message_file', None):
        if os.path.exists(args.message_file):
            with open(args.message_file, 'r', encoding='utf-8') as f:
                text = f.read()

    return MessageContent(
        text=text,
        photo=getattr(args, 'photo', None),
        video=getattr(args, 'video', None),
        document=getattr(args, 'document', None),
    )


async def cmd_send_contacts(args):
    from sender.contacts_sender import ContactsSender

    content = build_content(args)
    client = get_client(getattr(args, 'account', None))
    async with client:
        sender = ContactsSender(client, args.account or 'default')
        stats = await sender.send(
            content=content,
            only_mutual=getattr(args, 'only_mutual', False),
        )
        print(f"✅ Sent to contacts: {stats.success}/{stats.total}")


async def cmd_send_dialogs(args):
    from sender.dialogs_sender import DialogsSender

    content = build_content(args)
    dialog_types = ['user']
    if getattr(args, 'only_users', False):
        dialog_types = ['user']

    client = get_client(getattr(args, 'account', None))
    async with client:
        sender = DialogsSender(client, args.account or 'default')
        stats = await sender.send(content=content, dialog_types=dialog_types)
        print(f"✅ Sent to dialogs: {stats.success}/{stats.total}")


async def cmd_send_comments(args):
    from sender.comments_sender import CommentsSender

    content = build_content(args)
    client = get_client(getattr(args, 'account', None))
    async with client:
        sender = CommentsSender(client, args.account or 'default')
        stats = await sender.send(
            channels=args.channels,
            content=content,
        )
        print(f"✅ Sent comments: {stats.success}/{stats.total}")


async def cmd_send_dm(args):
    from sender.dm_sender import DMSender

    content = build_content(args)
    usernames = []
    if os.path.exists(args.file):
        with open(args.file, 'r', encoding='utf-8') as f:
            usernames = [line.strip() for line in f if line.strip()]

    client = get_client(getattr(args, 'account', None))
    async with client:
        sender = DMSender(client, args.account or 'default')
        stats = await sender.send(usernames=usernames, content=content)
        print(f"✅ Sent DMs: {stats.success}/{stats.total}")


async def cmd_send_chats(args):
    from sender.chats_sender import ChatsSender

    content = build_content(args)
    chats = []
    if os.path.exists(args.file):
        with open(args.file, 'r', encoding='utf-8') as f:
            chats = [line.strip() for line in f if line.strip()]

    client = get_client(getattr(args, 'account', None))
    async with client:
        sender = ChatsSender(client, args.account or 'default')
        stats = await sender.send(chats=chats, content=content)
        print(f"✅ Sent to chats: {stats.success}/{stats.total}")


async def cmd_send_gifts(args):
    from sender.gifts_sender import GiftsSender

    users = []
    if os.path.exists(args.file):
        with open(args.file, 'r', encoding='utf-8') as f:
            users = [line.strip() for line in f if line.strip()]

    client = get_client(getattr(args, 'account', None))
    async with client:
        sender = GiftsSender(client, args.account or 'default')
        stats = await sender.send_gifts_batch(
            users=users,
            stars_amount=args.stars,
            message=getattr(args, 'message', None),
        )
        print(f"✅ Sent gifts: {stats.success}/{stats.total}")


# ─────────────────────── INTERACTIVE MENU ───────────────────────

def show_menu():
    """Show interactive menu"""
    menu = """
┌────────────────────────────────────────────────────────────┐
│           TELEGRAM MULTI-ACCOUNT MANAGER v2.0              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ══════════════ ПАРСЕР ══════════════                      │
│  1.  👥 Парсинг по чатам                                   │
│  2.  💬 Парсинг по комментариям                            │
│  3.  📱 Парсинг контактов                                  │
│  4.  🎁 Парсинг по подаркам                                │
│  5.  ✉️  Парсинг из сообщений                               │
│  6.  📝 Фильтрация по BIO                                  │
│  7.  🔗 Объединение баз                                    │
│                                                            │
│  ═══════════ ИНВАЙТЕР ═══════════                          │
│  8.  👤 Инвайт по username                                 │
│  9.  📞 Инвайт по телефонам                                │
│  10. ⚡ Инвайт через админку                               │
│  11. 🔧 Назначить инвайт-админа                            │
│  12. 🔍 Проверка прав в чате                               │
│                                                            │
│  ═══════════ РАССЫЛКА ═══════════                          │
│  13. 📱 Рассылка по контактам                              │
│  14. 💭 Рассылка по диалогам                               │
│  15. 💬 Рассылка комментариями                             │
│  16. ✉️  Рассылка в ЛС по базе                              │
│  17. 👥 Рассылка по чатам                                  │
│  18. ⭐ Рассылка подарками (Stars)                         │
│                                                            │
│  0.  ❌ Выход                                               │
│                                                            │
└────────────────────────────────────────────────────────────┘
"""
    print(menu)


async def interactive_menu():
    """Run interactive menu"""
    while True:
        show_menu()
        choice = input("Выберите пункт: ").strip()

        if choice == '0':
            print("Выход...")
            break
        elif choice == '1':
            chats_input = input("Введите чаты (через пробел, @username или ID): ").strip()
            output = input("Файл для сохранения (например, data/parsed/users.txt): ").strip()
            chats = chats_input.split()
            args_obj = type('Args', (), {
                'chats': chats, 'output': output, 'account': None,
                'limit': None, 'admins': False, 'aggressive': False,
            })()
            await cmd_parse_chat(args_obj)
        elif choice == '2':
            channel = input("Канал (@username): ").strip()
            output = input("Файл для сохранения: ").strip()
            args_obj = type('Args', (), {
                'channel': channel, 'output': output, 'account': None,
                'posts_limit': 100,
            })()
            await cmd_parse_comments(args_obj)
        elif choice == '3':
            output = input("Файл для сохранения: ").strip()
            args_obj = type('Args', (), {'output': output, 'account': None})()
            await cmd_parse_contacts(args_obj)
        elif choice == '4':
            channel = input("Канал (@username): ").strip()
            output = input("Файл для сохранения: ").strip()
            args_obj = type('Args', (), {
                'channel': channel, 'output': output, 'account': None, 'type': 'all',
            })()
            await cmd_parse_gifts(args_obj)
        elif choice == '5':
            chat = input("Чат (@username): ").strip()
            keywords_input = input("Ключевые слова (через запятую, пусто = все): ").strip()
            output = input("Файл для сохранения: ").strip()
            args_obj = type('Args', (), {
                'chat': chat, 'output': output, 'account': None,
                'keywords': keywords_input if keywords_input else None,
            })()
            await cmd_parse_messages(args_obj)
        elif choice == '6':
            input_file = input("Файл со списком пользователей: ").strip()
            keywords_input = input("Ключевые слова (через запятую): ").strip()
            output = input("Файл для сохранения: ").strip()
            args_obj = type('Args', (), {
                'input': input_file, 'keywords': keywords_input,
                'output': output, 'account': None, 'mode': 'any',
            })()
            await cmd_parse_bio(args_obj)
        elif choice == '7':
            files_input = input("Файлы для объединения (через пробел): ").strip()
            output = input("Выходной файл: ").strip()
            args_obj = type('Args', (), {
                'files': files_input.split(), 'output': output, 'dedupe': True,
            })()
            await cmd_parse_merge(args_obj)
        elif choice == '8':
            target = input("Целевой чат (@username): ").strip()
            file_path = input("Файл с usernames: ").strip()
            args_obj = type('Args', (), {
                'target': target, 'file': file_path, 'account': None,
                'delay_min': 30, 'delay_max': 60, 'batch_size': 10, 'batch_delay': 300,
            })()
            await cmd_invite_username(args_obj)
        elif choice == '9':
            target = input("Целевой чат (@username): ").strip()
            file_path = input("Файл с телефонами: ").strip()
            args_obj = type('Args', (), {
                'target': target, 'file': file_path, 'account': None,
                'add_contacts': True,
            })()
            await cmd_invite_phone(args_obj)
        elif choice == '10':
            target = input("Целевой чат (@username): ").strip()
            file_path = input("Файл с пользователями: ").strip()
            args_obj = type('Args', (), {
                'target': target, 'file': file_path, 'account': None,
            })()
            await cmd_invite_admin(args_obj)
        elif choice == '11':
            chat = input("Чат (@username): ").strip()
            user = input("Пользователь (@username): ").strip()
            args_obj = type('Args', (), {'chat': chat, 'user': user, 'account': None})()
            await cmd_invite_promote(args_obj)
        elif choice == '12':
            chat = input("Чат (@username): ").strip()
            args_obj = type('Args', (), {'chat': chat, 'account': None})()
            await cmd_invite_check_rights(args_obj)
        elif choice == '13':
            message = input("Сообщение: ").strip()
            args_obj = type('Args', (), {
                'message': message, 'account': None,
                'photo': None, 'video': None, 'document': None,
                'message_file': None, 'only_mutual': False,
            })()
            await cmd_send_contacts(args_obj)
        elif choice == '14':
            message = input("Сообщение: ").strip()
            args_obj = type('Args', (), {
                'message': message, 'account': None,
                'photo': None, 'video': None, 'document': None,
                'message_file': None, 'only_users': True,
            })()
            await cmd_send_dialogs(args_obj)
        elif choice == '15':
            channels_input = input("Каналы (через пробел): ").strip()
            message = input("Сообщение: ").strip()
            args_obj = type('Args', (), {
                'channels': channels_input.split(), 'message': message, 'account': None,
                'photo': None, 'video': None, 'document': None, 'message_file': None,
            })()
            await cmd_send_comments(args_obj)
        elif choice == '16':
            file_path = input("Файл с usernames: ").strip()
            message = input("Сообщение: ").strip()
            args_obj = type('Args', (), {
                'file': file_path, 'message': message, 'account': None,
                'photo': None, 'video': None, 'document': None, 'message_file': None,
            })()
            await cmd_send_dm(args_obj)
        elif choice == '17':
            file_path = input("Файл с чатами: ").strip()
            message = input("Сообщение: ").strip()
            args_obj = type('Args', (), {
                'file': file_path, 'message': message, 'account': None,
                'photo': None, 'video': None, 'document': None, 'message_file': None,
            })()
            await cmd_send_chats(args_obj)
        elif choice == '18':
            file_path = input("Файл с пользователями: ").strip()
            stars_input = input("Количество Stars: ").strip()
            message = input("Сообщение (Enter для пропуска): ").strip()
            args_obj = type('Args', (), {
                'file': file_path, 'stars': int(stars_input),
                'message': message or None, 'account': None,
            })()
            await cmd_send_gifts(args_obj)
        else:
            print("❓ Неверный выбор. Попробуйте снова.")

        input("\nНажмите Enter для продолжения...")


# ─────────────────────── ARGUMENT PARSER ───────────────────────

def build_argument_parser():
    parser = argparse.ArgumentParser(
        description='Telegram Multi-Account Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--account', '-a', help='Account name/session to use')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # ── parse ──
    parse_parser = subparsers.add_parser('parse', help='Parse users')
    parse_sub = parse_parser.add_subparsers(dest='parse_type')

    p_chat = parse_sub.add_parser('chat', help='Parse from chats')
    p_chat.add_argument('--chats', nargs='+', required=True)
    p_chat.add_argument('--output', '-o', required=True)
    p_chat.add_argument('--limit', type=int)
    p_chat.add_argument('--admins', action='store_true')
    p_chat.add_argument('--aggressive', action='store_true')

    p_comments = parse_sub.add_parser('comments', help='Parse from comments')
    p_comments.add_argument('--channel', required=True)
    p_comments.add_argument('--output', '-o', required=True)
    p_comments.add_argument('--posts-limit', dest='posts_limit', type=int, default=100)

    p_contacts = parse_sub.add_parser('contacts', help='Parse contacts')
    p_contacts.add_argument('--output', '-o', required=True)

    p_gifts = parse_sub.add_parser('gifts', help='Parse gift senders')
    p_gifts.add_argument('--channel', required=True)
    p_gifts.add_argument('--output', '-o', required=True)
    p_gifts.add_argument('--type', default='all', choices=['stars', 'premium', 'all'])

    p_messages = parse_sub.add_parser('messages', help='Parse message authors')
    p_messages.add_argument('--chat', required=True)
    p_messages.add_argument('--output', '-o', required=True)
    p_messages.add_argument('--keywords', help='Comma-separated keywords')

    p_bio = parse_sub.add_parser('bio', help='Filter users by BIO keywords')
    p_bio.add_argument('--input', required=True)
    p_bio.add_argument('--keywords', required=True)
    p_bio.add_argument('--output', '-o', required=True)
    p_bio.add_argument('--mode', default='any', choices=['any', 'all', 'exact'])

    p_merge = parse_sub.add_parser('merge', help='Merge bases')
    p_merge.add_argument('--files', nargs='+', required=True)
    p_merge.add_argument('--output', '-o', required=True)
    p_merge.add_argument('--dedupe', action='store_true', default=True)

    # ── invite ──
    invite_parser = subparsers.add_parser('invite', help='Invite users')
    invite_sub = invite_parser.add_subparsers(dest='invite_type')

    i_username = invite_sub.add_parser('username', help='Invite by username')
    i_username.add_argument('--target', required=True)
    i_username.add_argument('--file', required=True)
    i_username.add_argument('--delay-min', dest='delay_min', type=int, default=30)
    i_username.add_argument('--delay-max', dest='delay_max', type=int, default=60)
    i_username.add_argument('--batch-size', dest='batch_size', type=int, default=10)
    i_username.add_argument('--batch-delay', dest='batch_delay', type=int, default=300)

    i_phone = invite_sub.add_parser('phone', help='Invite by phone')
    i_phone.add_argument('--target', required=True)
    i_phone.add_argument('--file', required=True)
    i_phone.add_argument('--add-contacts', dest='add_contacts', action='store_true', default=True)

    i_admin = invite_sub.add_parser('admin', help='Invite via admin rights')
    i_admin.add_argument('--target', required=True)
    i_admin.add_argument('--file', required=True)

    i_promote = invite_sub.add_parser('promote', help='Promote user to invite admin')
    i_promote.add_argument('--chat', required=True)
    i_promote.add_argument('--user', required=True)

    i_check = invite_sub.add_parser('check-rights', help='Check chat rights')
    i_check.add_argument('--chat', required=True)

    # ── send ──
    send_parser = subparsers.add_parser('send', help='Send messages')
    send_sub = send_parser.add_subparsers(dest='send_type')

    def add_message_args(p):
        p.add_argument('--message', '-m', help='Message text')
        p.add_argument('--message-file', dest='message_file', help='Path to message file')
        p.add_argument('--photo', help='Path to photo')
        p.add_argument('--video', help='Path to video')
        p.add_argument('--document', help='Path to document')

    s_contacts = send_sub.add_parser('contacts', help='Send to contacts')
    add_message_args(s_contacts)
    s_contacts.add_argument('--only-mutual', dest='only_mutual', action='store_true')

    s_dialogs = send_sub.add_parser('dialogs', help='Send to dialogs')
    add_message_args(s_dialogs)
    s_dialogs.add_argument('--only-users', dest='only_users', action='store_true')

    s_comments = send_sub.add_parser('comments', help='Send as comments')
    add_message_args(s_comments)
    s_comments.add_argument('--channels', nargs='+', required=True)

    s_dm = send_sub.add_parser('dm', help='Send DMs by username list')
    add_message_args(s_dm)
    s_dm.add_argument('--file', required=True)

    s_chats = send_sub.add_parser('chats', help='Send to chats')
    add_message_args(s_chats)
    s_chats.add_argument('--file', required=True)

    s_gifts = send_sub.add_parser('gifts', help='Send gifts (Stars)')
    s_gifts.add_argument('--file', required=True)
    s_gifts.add_argument('--stars', type=int, required=True)
    s_gifts.add_argument('--message', '-m', help='Gift message')

    # ── menu ──
    subparsers.add_parser('menu', help='Interactive menu')

    return parser


def main():
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.command is None:
        asyncio.run(interactive_menu())
        return

    if args.command == 'menu':
        asyncio.run(interactive_menu())
        return

    if args.command == 'parse':
        handlers = {
            'chat': cmd_parse_chat,
            'comments': cmd_parse_comments,
            'contacts': cmd_parse_contacts,
            'gifts': cmd_parse_gifts,
            'messages': cmd_parse_messages,
            'bio': cmd_parse_bio,
            'merge': cmd_parse_merge,
        }
        handler = handlers.get(args.parse_type)
        if handler:
            asyncio.run(handler(args))
        else:
            parser.print_help()
        return

    if args.command == 'invite':
        handlers = {
            'username': cmd_invite_username,
            'phone': cmd_invite_phone,
            'admin': cmd_invite_admin,
            'promote': cmd_invite_promote,
            'check-rights': cmd_invite_check_rights,
        }
        handler = handlers.get(args.invite_type)
        if handler:
            asyncio.run(handler(args))
        else:
            parser.print_help()
        return

    if args.command == 'send':
        handlers = {
            'contacts': cmd_send_contacts,
            'dialogs': cmd_send_dialogs,
            'comments': cmd_send_comments,
            'dm': cmd_send_dm,
            'chats': cmd_send_chats,
            'gifts': cmd_send_gifts,
        }
        handler = handlers.get(args.send_type)
        if handler:
            asyncio.run(handler(args))
        else:
            parser.print_help()
        return

    parser.print_help()


if __name__ == '__main__':
    main()
