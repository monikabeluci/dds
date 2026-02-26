import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime, timedelta

class AccountStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MEDIUM = "medium"
    BAD = "bad"
    BANNED = "banned"
    DEAD = "dead"
    UNAUTHORIZED = "unauthorized"

@dataclass
class AccountCheckResult:
    session_name: str
    user_id: int = 0
    phone: str = ""
    username: str = ""
    first_name: str = ""
    is_authorized: bool = False
    is_banned: bool = False
    status: AccountStatus = AccountStatus.BAD
    score: int = 0
    score_details: Dict[str, int] = field(default_factory=dict)
    score_reasons: List[str] = field(default_factory=list)
    can_send_messages: bool = False
    has_username: bool = False
    has_photo: bool = False
    has_bio: bool = False
    has_2fa: bool = False
    profile_completeness: int = 0
    account_age_days: int = 0
    dialogs_count: int = 0
    contacts_count: int = 0
    days_since_active: int = 999
    spam_bot_status: str = "unknown"
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class AccountChecker:
    def __init__(self):
        self.results = {}
    
    async def check_account(self, client, session_name):
        result = AccountCheckResult(session_name=session_name)
        result.score_details = {}
        result.score_reasons = []
        
        try:
            if not client.is_connected():
                await client.connect()
            
            if not await client.is_user_authorized():
                result.status = AccountStatus.UNAUTHORIZED
                result.issues.append("Not authorized")
                result.score_reasons.append("[-] Не авторизован")
                return result
            
            result.is_authorized = True
            me = await client.get_me()
            result.user_id = me.id
            result.phone = me.phone or ""
            result.username = me.username or ""
            result.first_name = me.first_name or ""
            result.has_username = bool(me.username)
            
            if hasattr(me, 'photo') and me.photo:
                result.has_photo = True
            
            if hasattr(me, 'scam') and me.scam:
                result.is_banned = True
                result.status = AccountStatus.BANNED
                result.issues.append("SCAM flag")
                result.score_reasons.append("[-100] Аккаунт помечен как SCAM")
                return result
            
            if hasattr(me, 'fake') and me.fake:
                result.is_banned = True
                result.status = AccountStatus.BANNED
                result.issues.append("FAKE flag")
                result.score_reasons.append("[-100] Аккаунт помечен как FAKE")
                return result
            
            score = 0
            
            # Username check
            if result.has_username:
                score += 15
                result.score_details['username'] = 15
                result.score_reasons.append("[+15] Есть username")
            else:
                result.score_details['username'] = 0
                result.score_reasons.append("[+0] Нет username")
                result.recommendations.append("Добавьте username")
            
            # Photo check
            if result.has_photo:
                score += 15
                result.score_details['photo'] = 15
                result.score_reasons.append("[+15] Есть фото профиля")
            else:
                result.score_details['photo'] = 0
                result.score_reasons.append("[+0] Нет фото профиля")
                result.recommendations.append("Добавьте фото профиля")
            
            # Bio check
            try:
                full = await client.get_entity(me.id)
                if hasattr(full, 'about') and full.about:
                    result.has_bio = True
                    score += 10
                    result.score_details['bio'] = 10
                    result.score_reasons.append("[+10] Есть bio/описание")
                else:
                    result.score_details['bio'] = 0
                    result.score_reasons.append("[+0] Нет bio/описания")
                    result.recommendations.append("Добавьте описание профиля")
            except:
                result.score_details['bio'] = 0
                result.score_reasons.append("[+0] Не удалось проверить bio")
            
            # Dialogs check
            try:
                dialogs = await client.get_dialogs(limit=100)
                result.dialogs_count = len(dialogs)
                if result.dialogs_count >= 50:
                    score += 15
                    result.score_details['dialogs'] = 15
                    result.score_reasons.append(f"[+15] Много диалогов ({result.dialogs_count})")
                elif result.dialogs_count >= 20:
                    score += 10
                    result.score_details['dialogs'] = 10
                    result.score_reasons.append(f"[+10] Средне диалогов ({result.dialogs_count})")
                elif result.dialogs_count >= 5:
                    score += 5
                    result.score_details['dialogs'] = 5
                    result.score_reasons.append(f"[+5] Мало диалогов ({result.dialogs_count})")
                else:
                    result.score_details['dialogs'] = 0
                    result.score_reasons.append(f"[+0] Очень мало диалогов ({result.dialogs_count})")
                    result.recommendations.append("Добавьте больше диалогов")
            except:
                result.score_details['dialogs'] = 0
                result.score_reasons.append("[+0] Не удалось проверить диалоги")
            
            # SpamBot check
            try:
                spambot = await client.get_entity("@SpamBot")
                await client.send_message(spambot, "/start")
                await asyncio.sleep(2)
                msgs = await client.get_messages(spambot, limit=1)
                
                if msgs:
                    text = msgs[0].text.lower()
                    if "ограничен" in text or "limited" in text:
                        result.spam_bot_status = "limited"
                        result.can_send_messages = False
                        score -= 30
                        result.score_details['spambot'] = -30
                        result.score_reasons.append("[-30] SpamBot: ОГРАНИЧЕН!")
                        result.issues.append("SpamBot: ограничен")
                    elif "свободен" in text or "free" in text or "good" in text or "нет ограничений" in text:
                        result.spam_bot_status = "clean"
                        result.can_send_messages = True
                        score += 25
                        result.score_details['spambot'] = 25
                        result.score_reasons.append("[+25] SpamBot: чистый аккаунт")
                    else:
                        result.spam_bot_status = "unknown"
                        result.can_send_messages = True
                        score += 10
                        result.score_details['spambot'] = 10
                        result.score_reasons.append("[+10] SpamBot: статус неясен")
            except Exception as e:
                result.spam_bot_status = "error"
                result.can_send_messages = True
                result.score_details['spambot'] = 0
                result.score_reasons.append("[+0] Не удалось проверить SpamBot")
            
            # Account age (estimate from user_id)
            try:
                if me.id < 100000000:
                    result.account_age_days = 2000
                    score += 20
                    result.score_details['age'] = 20
                    result.score_reasons.append("[+20] Очень старый аккаунт")
                elif me.id < 500000000:
                    result.account_age_days = 1000
                    score += 15
                    result.score_details['age'] = 15
                    result.score_reasons.append("[+15] Старый аккаунт")
                elif me.id < 1500000000:
                    result.account_age_days = 365
                    score += 10
                    result.score_details['age'] = 10
                    result.score_reasons.append("[+10] Средний возраст аккаунта")
                elif me.id < 5000000000:
                    result.account_age_days = 180
                    score += 5
                    result.score_details['age'] = 5
                    result.score_reasons.append("[+5] Относительно новый аккаунт")
                else:
                    result.account_age_days = 30
                    result.score_details['age'] = 0
                    result.score_reasons.append("[+0] Новый аккаунт")
                    result.warnings.append("Новый аккаунт - выше риск бана")
            except:
                result.score_details['age'] = 0
                result.score_reasons.append("[+0] Не удалось определить возраст")
            
            # Final score
            result.score = max(0, min(100, score))
            
            # Status based on score
            if result.score >= 80:
                result.status = AccountStatus.EXCELLENT
            elif result.score >= 60:
                result.status = AccountStatus.GOOD
            elif result.score >= 40:
                result.status = AccountStatus.MEDIUM
            else:
                result.status = AccountStatus.BAD
            
            if not result.can_send_messages:
                result.status = AccountStatus.BAD
            
            # Completeness
            complete = 0
            if result.has_username: complete += 25
            if result.has_photo: complete += 25
            if result.has_bio: complete += 25
            if result.dialogs_count >= 10: complete += 25
            result.profile_completeness = complete
            
        except Exception as e:
            result.status = AccountStatus.DEAD
            result.issues.append(f"Error: {str(e)[:50]}")
            result.score_reasons.append(f"[ERROR] {str(e)[:50]}")
        
        return result
    
    async def check_all(self, clients):
        self.results = {}
        total = len(clients)
        
        for i, (session_name, client) in enumerate(clients.items(), 1):
            print(f"\n[{i}/{total}] Проверка: {session_name}")
            print("-" * 40)
            
            result = await self.check_account(client, session_name)
            self.results[session_name] = result
            
            # Status emoji
            status_emoji = {
                AccountStatus.EXCELLENT: "🟢",
                AccountStatus.GOOD: "🟡",
                AccountStatus.MEDIUM: "🟠",
                AccountStatus.BAD: "🔴",
                AccountStatus.BANNED: "⛔",
                AccountStatus.DEAD: "💀",
                AccountStatus.UNAUTHORIZED: "🔒"
            }
            
            emoji = status_emoji.get(result.status, "❓")
            print(f"{emoji} Статус: {result.status.value.upper()}")
            print(f"📊 Рейтинг: {result.score}/100")
            
            # Print score breakdown
            print("\n📋 Детали рейтинга:")
            for reason in result.score_reasons:
                print(f"   {reason}")
            
            if result.issues:
                print(f"\n❌ Проблемы:")
                for issue in result.issues:
                    print(f"   • {issue}")
            
            if result.recommendations:
                print(f"\n💡 Рекомендации:")
                for rec in result.recommendations:
                    print(f"   • {rec}")
            
            await asyncio.sleep(1)
        
        return self.results
    
    def print_summary(self):
        if not self.results:
            return
        
        counts = {
            'excellent': 0, 'good': 0, 'medium': 0,
            'bad': 0, 'banned': 0, 'dead': 0, 'unauthorized': 0
        }
        
        for result in self.results.values():
            counts[result.status.value] += 1
        
        ready = counts['excellent'] + counts['good'] + counts['medium']
        
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                  РЕЗУЛЬТАТЫ ПРОВЕРКИ                      ║
╠═══════════════════════════════════════════════════════════╣
║  🟢 Отличные (80-100):       {counts['excellent']:<3}                        ║
║  🟡 Хорошие (60-79):         {counts['good']:<3}                        ║
║  🟠 Средние (40-59):         {counts['medium']:<3}                        ║
║  🔴 Плохие (0-39):           {counts['bad']:<3}                        ║
║  ⛔ Забанены:                {counts['banned']:<3}                        ║
║  💀 Мёртвые:                 {counts['dead']:<3}                        ║
║  🔒 Не авторизованы:         {counts['unauthorized']:<3}                        ║
╠═══════════════════════════════════════════════════════════╣
║  ✅ Готовы к работе:         {ready:<3}                        ║
╚═══════════════════════════════════════════════════════════╝
        """)