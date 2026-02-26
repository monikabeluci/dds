import os
import json
import sqlite3
from datetime import datetime

class AccountDatabase:
    def __init__(self, db_path="accounts.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            phone TEXT,
            username TEXT,
            first_name TEXT,
            status TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            is_authorized INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            can_send_messages INTEGER DEFAULT 1,
            has_username INTEGER DEFAULT 0,
            has_photo INTEGER DEFAULT 0,
            has_bio INTEGER DEFAULT 0,
            has_2fa INTEGER DEFAULT 0,
            profile_completeness INTEGER DEFAULT 0,
            account_age_days INTEGER DEFAULT 0,
            dialogs_count INTEGER DEFAULT 0,
            contacts_count INTEGER DEFAULT 0,
            days_since_active INTEGER DEFAULT 999,
            spam_bot_check TEXT DEFAULT 'unknown',
            messages_sent_total INTEGER DEFAULT 0,
            messages_sent_today INTEGER DEFAULT 0,
            last_message_date TEXT,
            last_check_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            issues TEXT,
            warnings TEXT,
            recommendations TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS deleted_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            user_id INTEGER,
            phone TEXT,
            reason TEXT,
            deleted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_status TEXT,
            last_score INTEGER
        )''')
        self.conn.commit()
    
    def save_account(self, result):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        status_value = result.status.value if hasattr(result.status, 'value') else str(result.status)
        cursor.execute('''INSERT INTO accounts (session_name, user_id, phone, username, first_name, status, score, is_authorized, is_banned, can_send_messages, has_username, last_check_date, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_name) DO UPDATE SET
            user_id=?, phone=?, username=?, first_name=?, status=?, score=?, is_authorized=?, is_banned=?, can_send_messages=?, has_username=?, last_check_date=?, updated_at=?''',
            (result.session_name, result.user_id, result.phone, result.username, result.first_name, status_value, result.score, int(result.is_authorized), int(result.is_banned), int(result.can_send_messages), int(result.has_username), now, now,
             result.user_id, result.phone, result.username, result.first_name, status_value, result.score, int(result.is_authorized), int(result.is_banned), int(result.can_send_messages), int(result.has_username), now, now))
        self.conn.commit()
        return True
    
    def delete_account(self, session_name, reason="unknown"):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, phone, status, score FROM accounts WHERE session_name = ?", (session_name,))
        row = cursor.fetchone()
        if row:
            cursor.execute("INSERT INTO deleted_accounts (session_name, user_id, phone, reason, last_status, last_score) VALUES (?, ?, ?, ?, ?, ?)",
                (session_name, row['user_id'], row['phone'], reason, row['status'], row['score']))
        cursor.execute("DELETE FROM accounts WHERE session_name = ?", (session_name,))
        self.conn.commit()
        return True
    
    def get_suitable_accounts(self, min_score=40):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE score >= ? AND can_send_messages = 1 AND is_banned = 0 ORDER BY score DESC", (min_score,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_accounts(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM accounts ORDER BY score DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_accounts_by_status(self, status):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE status = ?", (status,))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_message_stats(self, session_name):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("UPDATE accounts SET messages_sent_total = messages_sent_total + 1, messages_sent_today = messages_sent_today + 1, last_message_date = ?, updated_at = ? WHERE session_name = ?", (now, now, session_name))
        self.conn.commit()
    
    def get_statistics(self):
        cursor = self.conn.cursor()
        stats = {}
        cursor.execute("SELECT COUNT(*) as total FROM accounts")
        stats['total'] = cursor.fetchone()['total']
        cursor.execute("SELECT AVG(score) as avg_score FROM accounts WHERE score > 0")
        row = cursor.fetchone()
        stats['avg_score'] = round(row['avg_score'], 1) if row['avg_score'] else 0
        cursor.execute("SELECT COUNT(*) as ready FROM accounts WHERE can_send_messages = 1 AND is_banned = 0 AND score >= 40")
        stats['ready'] = cursor.fetchone()['ready']
        cursor.execute("SELECT SUM(messages_sent_total) as total_sent FROM accounts")
        row = cursor.fetchone()
        stats['total_messages_sent'] = row['total_sent'] or 0
        cursor.execute("SELECT COUNT(*) as deleted FROM deleted_accounts")
        stats['deleted'] = cursor.fetchone()['deleted']
        stats['by_status'] = {}
        return stats
    
    def vacuum(self):
        self.conn.execute("VACUUM")
    
    def close(self):
        if self.conn:
            self.conn.close()