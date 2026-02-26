"""
Telegram Multi-Account Manager CLI
Точка входа для управления Telegram аккаунтами
"""

import asyncio
import argparse
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def build_parser() -> argparse.ArgumentParser:
    """Создать парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Telegram Multi-Account Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python main.py add-account --phone +79001234567 --name main_acc
  python main.py validate-all
  python main.py warmup --account main_acc --intensity normal --duration 60
  python main.py send --account main_acc --groups-file data/groups.txt --message-file data/messages.txt
  python main.py profile --account main_acc
  python main.py setup-2fa --account main_acc --password "MyPass123"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Команда")

    # ── Управление аккаунтами ──────────────────────────────────────────────
    add_acc = subparsers.add_parser("add-account", help="Добавить новый аккаунт")
    add_acc.add_argument("--phone", required=True, help="Номер телефона (+79001234567)")
    add_acc.add_argument("--name", help="Имя аккаунта (по умолчанию — номер телефона)")
    add_acc.add_argument("--password", help="Пароль 2FA (если установлен)")
    add_acc.add_argument("--auto-code", action="store_true", help="Автоматически получить код входа")

    rm_acc = subparsers.add_parser("remove-account", help="Удалить аккаунт")
    rm_acc.add_argument("--account", required=True, help="Имя аккаунта")

    subparsers.add_parser("list-accounts", help="Список всех аккаунтов")

    # ── Валидация ──────────────────────────────────────────────────────────
    validate = subparsers.add_parser("validate", help="Проверить аккаунт(ы)")
    validate.add_argument("--account", required=True, help="Имя аккаунта или 'all'")

    subparsers.add_parser("validate-all", help="Проверить все аккаунты")

    # ── Прогрев ───────────────────────────────────────────────────────────
    warmup = subparsers.add_parser("warmup", help="Запустить прогрев аккаунта")
    warmup.add_argument("--account", required=True, help="Имя аккаунта")
    warmup.add_argument("--intensity", choices=["light", "normal", "intensive"],
                        default="normal", help="Интенсивность прогрева")
    warmup.add_argument("--duration", type=int, default=30, help="Продолжительность в минутах")

    warmup_sched = subparsers.add_parser("warmup-schedule", help="Запланировать прогрев на N дней")
    warmup_sched.add_argument("--account", required=True, help="Имя аккаунта или 'all'")
    warmup_sched.add_argument("--days", type=int, default=7, help="Количество дней")
    warmup_sched.add_argument("--intensity", choices=["light", "normal", "intensive"],
                               default="normal", help="Интенсивность прогрева")

    # ── Рассылка ──────────────────────────────────────────────────────────
    send = subparsers.add_parser("send", help="Отправить сообщение в группы")
    send.add_argument("--account", required=True, help="Имя аккаунта или 'all'")
    send.add_argument("--groups-file", help="Файл со списком групп")
    send.add_argument("--message-file", help="Файл с шаблонами сообщений")
    send.add_argument("--message", help="Текст сообщения (альтернатива --message-file)")
    send.add_argument("--delay-min", type=int, help="Минимальная задержка между отправками (сек)")
    send.add_argument("--delay-max", type=int, help="Максимальная задержка между отправками (сек)")
    send.add_argument("--validate-before", action="store_true",
                      help="Валидировать аккаунт перед рассылкой")
    send.add_argument("--dry-run", action="store_true",
                      help="Симуляция (без реальной отправки)")

    list_groups = subparsers.add_parser("list-groups", help="Показать группы аккаунта")
    list_groups.add_argument("--account", required=True, help="Имя аккаунта")

    # ── Профиль ──────────────────────────────────────────────────────────
    profile = subparsers.add_parser("profile", help="Показать полную информацию об аккаунте")
    profile.add_argument("--account", required=True, help="Имя аккаунта")

    set_avatar = subparsers.add_parser("set-avatar", help="Установить аватар")
    set_avatar.add_argument("--account", required=True, help="Имя аккаунта")
    set_avatar.add_argument("--photo", required=True, help="Путь к файлу фото")

    set_name = subparsers.add_parser("set-name", help="Установить имя")
    set_name.add_argument("--account", required=True, help="Имя аккаунта")
    set_name.add_argument("--first-name", required=True, help="Имя")
    set_name.add_argument("--last-name", default="", help="Фамилия")

    set_username = subparsers.add_parser("set-username", help="Установить username")
    set_username.add_argument("--account", required=True, help="Имя аккаунта")
    set_username.add_argument("--username", required=True, help="Новый username")

    set_bio = subparsers.add_parser("set-bio", help="Установить BIO")
    set_bio.add_argument("--account", required=True, help="Имя аккаунта")
    set_bio.add_argument("--bio", required=True, help="Текст BIO (до 70 символов)")

    gen_username = subparsers.add_parser("generate-username", help="Сгенерировать доступные username")
    gen_username.add_argument("--account", required=True, help="Имя аккаунта")
    gen_username.add_argument("--base", help="Базовое слово для генерации")
    gen_username.add_argument("--count", type=int, default=10, help="Количество вариантов")

    # ── Безопасность ─────────────────────────────────────────────────────
    setup_2fa = subparsers.add_parser("setup-2fa", help="Установить 2FA")
    setup_2fa.add_argument("--account", required=True, help="Имя аккаунта")
    setup_2fa.add_argument("--password", required=True, help="Пароль 2FA")
    setup_2fa.add_argument("--hint", default="", help="Подсказка к паролю")

    remove_2fa = subparsers.add_parser("remove-2fa", help="Удалить 2FA")
    remove_2fa.add_argument("--account", required=True, help="Имя аккаунта")
    remove_2fa.add_argument("--password", required=True, help="Текущий пароль 2FA")

    term_sessions = subparsers.add_parser("terminate-sessions",
                                          help="Закрыть все другие сессии")
    term_sessions.add_argument("--account", required=True, help="Имя аккаунта")

    show_sessions = subparsers.add_parser("show-sessions", help="Показать активные сессии")
    show_sessions.add_argument("--account", required=True, help="Имя аккаунта")

    return parser


# ── Обработчики команд ────────────────────────────────────────────────────

async def cmd_add_account(args):
    from core.account_manager import AccountManager
    manager = AccountManager()
    await manager.add_account(
        phone=args.phone,
        account_name=args.name or "",
        password=args.password,
        auto_code=args.auto_code,
    )


async def cmd_remove_account(args):
    from core.account_manager import AccountManager
    manager = AccountManager()
    await manager.remove_account(args.account)


def cmd_list_accounts(args):
    from rich.console import Console
    from rich.table import Table
    from core.account_manager import AccountManager

    console = Console()
    manager = AccountManager()
    accounts = manager.list_accounts_info()

    if not accounts:
        console.print("[yellow]Нет добавленных аккаунтов[/yellow]")
        return

    table = Table(title="Аккаунты", show_header=True, header_style="bold cyan")
    table.add_column("Имя", style="bold")
    table.add_column("Телефон")
    table.add_column("Имя пользователя")
    table.add_column("Username")

    for acc in accounts:
        name = f"{acc.get('first_name', '')} {acc.get('last_name', '')}".strip() or "—"
        table.add_row(
            acc["name"],
            acc.get("phone", "—"),
            name,
            f"@{acc['username']}" if acc.get("username") else "—",
        )

    console.print(table)


async def cmd_validate(args):
    from rich.console import Console
    console = Console()

    account_names = _resolve_accounts(args.account)
    if not account_names:
        console.print("[red]Аккаунты не найдены[/red]")
        return

    for account_name in account_names:
        await _validate_and_print(account_name, console)


async def cmd_validate_all(args):
    from rich.console import Console
    from utils.helpers import list_accounts
    console = Console()

    accounts = list_accounts()
    if not accounts:
        console.print("[yellow]Нет добавленных аккаунтов[/yellow]")
        return

    for account_name in accounts:
        await _validate_and_print(account_name, console)


async def _validate_and_print(account_name: str, console):
    from rich.panel import Panel
    from rich.table import Table
    from core.account_manager import AccountManager
    from core.validator import AccountValidator, AccountStatus

    manager = AccountManager()
    validator = AccountValidator()

    client = manager.create_client(account_name)
    try:
        async with client:
            result = await validator.validate_account(client, account_name)
    except Exception as e:
        console.print(f"[red]Ошибка при подключении к аккаунту {account_name}: {e}[/red]")
        return

    status = result["status"]
    rating = result["rating"]
    emoji = AccountStatus.emoji(status)
    suitable = "✅ ДА" if result["suitable_for_sending"] else "❌ НЕТ"

    # Строим таблицу с деталями
    details = result["details"]
    detail_lines = [
        f"📱 Телефон подтверждён: {'✅' if details['phone_verified'] else '❌'}",
        f"👤 Username: {'✅' if details['has_username'] else '❌'}",
        f"🖼  Аватар: {'✅' if details['has_avatar'] else '❌'}",
        f"📝 BIO: {'✅' if details['has_bio'] else '❌'}",
        f"🔐 2FA: {'✅' if details['has_2fa'] else '❌'}",
        f"📅 Возраст: {details['account_age_days']} дней",
        f"💬 Диалогов: {details['dialogs_count']}",
        f"👥 Контактов: {details['contacts_count']}",
        f"🤖 SpamBot: {details['spam_bot_status']}",
    ]

    reasons_text = "\n".join(f" • {r}" for r in result["reasons"]) if result["reasons"] else " • —"
    recs_text = "\n".join(f" • {r}" for r in result["recommendations"]) if result["recommendations"] else " • —"

    content = (
        f"Статус: {emoji} {status.upper()}\n"
        f"Рейтинг: {rating}/100\n"
        f"Пригоден для рассылки: {suitable}\n"
        f"\n{'─' * 50}\n"
        f"Детали профиля:\n"
        + "\n".join(detail_lines)
        + f"\n{'─' * 50}\n"
        f"Причины рейтинга:\n{reasons_text}\n"
        f"{'─' * 50}\n"
        f"Рекомендации:\n{recs_text}"
    )

    status_color = {
        AccountStatus.EXCELLENT: "green",
        AccountStatus.GOOD: "green",
        AccountStatus.WARNING: "yellow",
        AccountStatus.RESTRICTED: "red",
        AccountStatus.BANNED: "red",
        AccountStatus.INVALID: "red",
    }.get(status, "white")

    console.print(Panel(
        content,
        title=f"[bold]Аккаунт: {account_name}[/bold]",
        border_style=status_color,
        expand=False,
    ))


async def cmd_warmup(args):
    from rich.console import Console
    from core.account_manager import AccountManager
    from features.warmup import AccountWarmer

    console = Console()
    manager = AccountManager()
    warmer = AccountWarmer()

    account_names = _resolve_accounts(args.account)
    if not account_names:
        console.print("[red]Аккаунты не найдены[/red]")
        return

    for account_name in account_names:
        console.print(f"[bold cyan]Прогрев аккаунта: {account_name}[/bold cyan]")
        client = manager.create_client(account_name)
        async with client:
            stats = await warmer.warmup_account(
                client,
                account_name,
                intensity=args.intensity,
                duration_minutes=args.duration,
            )
        console.print(
            f"[green]✓ Прогрев завершён: выполнено {stats['actions_performed']} действий[/green]"
        )


async def cmd_warmup_schedule(args):
    from rich.console import Console
    from core.account_manager import AccountManager
    from features.warmup import AccountWarmer

    console = Console()
    manager = AccountManager()
    warmer = AccountWarmer()

    account_names = _resolve_accounts(args.account)
    if not account_names:
        console.print("[red]Аккаунты не найдены[/red]")
        return

    await warmer.schedule_warmup(
        accounts=account_names,
        client_factory=manager.create_client,
        days=args.days,
        intensity=args.intensity,
    )


async def cmd_send(args):
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from core.account_manager import AccountManager
    from core.sender import Sender
    from core.validator import AccountValidator, AccountStatus
    from utils.helpers import parse_groups_file, parse_messages_file

    console = Console()
    manager = AccountManager()
    sender = Sender()

    account_names = _resolve_accounts(args.account)
    if not account_names:
        console.print("[red]Аккаунты не найдены[/red]")
        return

    # Загружаем группы
    groups = parse_groups_file(args.groups_file) if args.groups_file else parse_groups_file()
    if not groups:
        console.print("[red]Список групп пуст. Укажите --groups-file или заполните data/groups.txt[/red]")
        return

    # Загружаем сообщения
    if args.message:
        messages = [args.message]
    else:
        messages = parse_messages_file(args.message_file) if args.message_file else parse_messages_file()
    if not messages:
        console.print("[red]Нет сообщений для рассылки. Укажите --message или --message-file[/red]")
        return

    console.print(f"[bold]Рассылка: {len(groups)} групп, {len(account_names)} аккаунт(ов)[/bold]")
    if args.dry_run:
        console.print("[yellow]Режим DRY RUN — сообщения не отправляются[/yellow]")

    total_stats = {"sent": 0, "failed": 0, "skipped": 0}

    for account_name in account_names:
        client = manager.create_client(account_name)
        async with client:
            # Валидация перед отправкой
            if args.validate_before:
                validator = AccountValidator()
                result = await validator.validate_account(client, account_name)
                if not result["suitable_for_sending"]:
                    console.print(
                        f"[yellow]⚠ Аккаунт {account_name} не пригоден для рассылки "
                        f"(рейтинг: {result['rating']}/100) — пропускаем[/yellow]"
                    )
                    continue

            console.print(f"  Отправка с аккаунта [bold]{account_name}[/bold]...")

            stats = await sender.send_to_groups(
                client,
                account_name,
                groups=groups,
                messages=messages,
                delay_min=args.delay_min,
                delay_max=args.delay_max,
                dry_run=args.dry_run,
            )

        console.print(
            f"  [green]✓[/green] {account_name}: отправлено {stats['sent']}, "
            f"ошибок {stats['failed']}, пропущено {stats['skipped']}"
        )
        for err in stats["errors"]:
            console.print(f"    [red]✗[/red] {err}")

        total_stats["sent"] += stats["sent"]
        total_stats["failed"] += stats["failed"]
        total_stats["skipped"] += stats["skipped"]

    console.print(
        f"\n[bold]Итого:[/bold] отправлено {total_stats['sent']}, "
        f"ошибок {total_stats['failed']}, пропущено {total_stats['skipped']}"
    )


async def cmd_list_groups(args):
    from rich.console import Console
    from rich.table import Table
    from core.account_manager import AccountManager
    from core.sender import Sender

    console = Console()
    manager = AccountManager()
    sender = Sender()

    client = manager.create_client(args.account)
    async with client:
        groups = await sender.get_account_groups(client)

    if not groups:
        console.print(f"[yellow]Групп не найдено для аккаунта {args.account}[/yellow]")
        return

    table = Table(title=f"Группы аккаунта: {args.account}", show_header=True,
                  header_style="bold cyan")
    table.add_column("Название")
    table.add_column("Username")
    table.add_column("Тип")
    table.add_column("Участников", justify="right")

    for g in groups:
        table.add_row(
            g["title"] or "—",
            f"@{g['username']}" if g["username"] else "—",
            g["type"],
            str(g["members_count"]),
        )

    console.print(table)


async def cmd_profile(args):
    from rich.console import Console
    from rich.panel import Panel
    from core.account_manager import AccountManager
    from features.profile_editor import ProfileEditor

    console = Console()
    manager = AccountManager()
    editor = ProfileEditor()

    client = manager.create_client(args.account)
    async with client:
        profile = await editor.get_full_profile(client)

    lines = [
        f"ID: {profile['id']}",
        f"Телефон: {profile['phone']}",
        f"Имя: {profile['first_name']} {profile['last_name']}".strip(),
        f"Username: @{profile['username']}" if profile["username"] else "Username: —",
        f"BIO: {profile['bio'] or '—'}",
        f"Аватар: {'✅' if profile['has_avatar'] else '❌'}",
        f"Верифицирован: {'✅' if profile['is_verified'] else '❌'}",
        f"Premium: {'✅' if profile['is_premium'] else '❌'}",
    ]

    console.print(Panel(
        "\n".join(lines),
        title=f"[bold]Профиль: {args.account}[/bold]",
        border_style="cyan",
    ))


async def cmd_set_avatar(args):
    from rich.console import Console
    from core.account_manager import AccountManager
    from features.profile_editor import ProfileEditor

    console = Console()
    manager = AccountManager()
    editor = ProfileEditor()

    client = manager.create_client(args.account)
    async with client:
        success = await editor.set_avatar(client, args.photo)

    if success:
        console.print(f"[green]✓ Аватар установлен для {args.account}[/green]")
    else:
        console.print(f"[red]✗ Не удалось установить аватар[/red]")


async def cmd_set_name(args):
    from rich.console import Console
    from core.account_manager import AccountManager
    from features.profile_editor import ProfileEditor

    console = Console()
    manager = AccountManager()
    editor = ProfileEditor()

    client = manager.create_client(args.account)
    async with client:
        success = await editor.set_name(client, args.first_name, args.last_name)

    if success:
        console.print(f"[green]✓ Имя установлено: {args.first_name} {args.last_name}[/green]")
    else:
        console.print(f"[red]✗ Не удалось установить имя[/red]")


async def cmd_set_username(args):
    from rich.console import Console
    from core.account_manager import AccountManager
    from features.profile_editor import ProfileEditor

    console = Console()
    manager = AccountManager()
    editor = ProfileEditor()

    client = manager.create_client(args.account)
    async with client:
        success = await editor.set_username(client, args.username)

    if success:
        console.print(f"[green]✓ Username @{args.username} установлен[/green]")
    else:
        console.print(f"[red]✗ Не удалось установить username @{args.username}[/red]")


async def cmd_set_bio(args):
    from rich.console import Console
    from core.account_manager import AccountManager
    from features.profile_editor import ProfileEditor

    console = Console()
    manager = AccountManager()
    editor = ProfileEditor()

    client = manager.create_client(args.account)
    async with client:
        success = await editor.set_bio(client, args.bio)

    if success:
        console.print(f"[green]✓ BIO установлено[/green]")
    else:
        console.print(f"[red]✗ Не удалось установить BIO[/red]")


async def cmd_generate_username(args):
    from rich.console import Console
    from rich.table import Table
    from core.account_manager import AccountManager
    from features.username_generator import UsernameGenerator

    console = Console()
    manager = AccountManager()
    generator = UsernameGenerator()

    console.print(f"[bold]Генерация username для аккаунта {args.account}...[/bold]")

    client = manager.create_client(args.account)
    async with client:
        available = await generator.generate_available_username(
            client, base_name=args.base, count=args.count
        )

    if not available:
        console.print("[yellow]Не найдено доступных username[/yellow]")
        return

    table = Table(title="Доступные username", show_header=True, header_style="bold green")
    table.add_column("№", justify="right")
    table.add_column("Username")

    for i, username in enumerate(available, 1):
        table.add_row(str(i), f"@{username}")

    console.print(table)


async def cmd_setup_2fa(args):
    from rich.console import Console
    from core.account_manager import AccountManager
    from features.security import SecurityManager

    console = Console()
    manager = AccountManager()
    security = SecurityManager()

    client = manager.create_client(args.account)
    async with client:
        success = await security.setup_2fa(client, args.password, hint=args.hint)

    if success:
        console.print(f"[green]✓ 2FA установлена для {args.account}[/green]")
    else:
        console.print(f"[red]✗ Не удалось установить 2FA[/red]")


async def cmd_remove_2fa(args):
    from rich.console import Console
    from core.account_manager import AccountManager
    from features.security import SecurityManager

    console = Console()
    manager = AccountManager()
    security = SecurityManager()

    client = manager.create_client(args.account)
    async with client:
        success = await security.remove_2fa(client, args.password)

    if success:
        console.print(f"[green]✓ 2FA удалена для {args.account}[/green]")
    else:
        console.print(f"[red]✗ Не удалось удалить 2FA[/red]")


async def cmd_terminate_sessions(args):
    from rich.console import Console
    from rich.prompt import Confirm
    from core.account_manager import AccountManager
    from features.security import SecurityManager

    console = Console()
    manager = AccountManager()
    security = SecurityManager()

    if not Confirm.ask(f"Закрыть все другие сессии для {args.account}?"):
        return

    client = manager.create_client(args.account)
    async with client:
        success = await security.terminate_all_sessions(client)

    if success:
        console.print(f"[green]✓ Все другие сессии закрыты для {args.account}[/green]")
    else:
        console.print(f"[red]✗ Ошибка при закрытии сессий[/red]")


async def cmd_show_sessions(args):
    from rich.console import Console
    from rich.table import Table
    from datetime import datetime
    from core.account_manager import AccountManager
    from features.security import SecurityManager

    console = Console()
    manager = AccountManager()
    security = SecurityManager()

    client = manager.create_client(args.account)
    async with client:
        sessions = await security.get_active_sessions(client)

    if not sessions:
        console.print(f"[yellow]Нет активных сессий для {args.account}[/yellow]")
        return

    table = Table(
        title=f"Активные сессии: {args.account}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Устройство")
    table.add_column("Приложение")
    table.add_column("IP")
    table.add_column("Страна")
    table.add_column("Последняя активность")
    table.add_column("Текущая")

    for s in sessions:
        device = f"{s.get('device_model', '—')} ({s.get('platform', '—')})"
        app = f"{s.get('app_name', '—')} {s.get('app_version', '')}".strip()
        last_active = s.get("date_active")
        if isinstance(last_active, int):
            last_active = datetime.fromtimestamp(last_active).strftime("%Y-%m-%d %H:%M")
        else:
            last_active = str(last_active) if last_active else "—"
        is_current = "✅" if s.get("current") else ""

        table.add_row(device, app, s.get("ip", "—"), s.get("country", "—"), last_active, is_current)

    console.print(table)


# ── Вспомогательные функции ───────────────────────────────────────────────

def _resolve_accounts(account_arg: str) -> list[str]:
    """Разрешить имя аккаунта: 'all' → список всех аккаунтов."""
    from utils.helpers import list_accounts, account_exists
    if account_arg == "all":
        return list_accounts()
    if account_exists(account_arg):
        return [account_arg]
    return []


# ── Точка входа ───────────────────────────────────────────────────────────

def main():
    from rich.console import Console
    console = Console()

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Маппинг команд на обработчики
    async_commands = {
        "add-account": cmd_add_account,
        "remove-account": cmd_remove_account,
        "validate": cmd_validate,
        "validate-all": cmd_validate_all,
        "warmup": cmd_warmup,
        "warmup-schedule": cmd_warmup_schedule,
        "send": cmd_send,
        "list-groups": cmd_list_groups,
        "profile": cmd_profile,
        "set-avatar": cmd_set_avatar,
        "set-name": cmd_set_name,
        "set-username": cmd_set_username,
        "set-bio": cmd_set_bio,
        "generate-username": cmd_generate_username,
        "setup-2fa": cmd_setup_2fa,
        "remove-2fa": cmd_remove_2fa,
        "terminate-sessions": cmd_terminate_sessions,
        "show-sessions": cmd_show_sessions,
    }
    sync_commands = {
        "list-accounts": cmd_list_accounts,
    }

    if args.command in sync_commands:
        sync_commands[args.command](args)
    elif args.command in async_commands:
        try:
            asyncio.run(async_commands[args.command](args))
        except KeyboardInterrupt:
            console.print("\n[yellow]Прервано пользователем[/yellow]")
        except Exception as e:
            console.print(f"[red]Ошибка: {e}[/red]")
            raise
    else:
        console.print(f"[red]Неизвестная команда: {args.command}[/red]")
        parser.print_help()


if __name__ == "__main__":
    main()
