"""
SpamMonster - Конфигурация
"""

API_ID = 36727770
API_HASH = "c878cc12870b29d5a9a5670b0e43abd8"

SESSIONS_FOLDER = "sessions"
PROXIES_FILE = "proxies.txt"

ANTIBAN = {
    "min_interval": 45,
    "max_interval": 120,
    "account_delay_min": 30,
    "account_delay_max": 90,
    "round_pause_min": 300,
    "round_pause_max": 600,
    "messages_per_hour": 8,
    "messages_per_day": 50,
    "work_hours_start": 8,
    "work_hours_end": 23,
    "floodwait_multiplier": 1.5,
    "max_floodwait": 3600,
    "warmup_actions": 5,
    "warmup_delay": 3,
    "typing_enabled": True,
    "typing_duration_min": 2,
    "typing_duration_max": 8,
}

EMOJI_POOL = ["👋", "🔥", "💪", "✨", "🚀", "💯", "👍", "😊", "🎯", "⭐"]
INVISIBLE_CHARS = ["\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"]