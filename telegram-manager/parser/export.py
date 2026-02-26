import csv
import json
import os
from typing import List

from .base_parser import ParsedUser


class ParserExporter:
    """Export parsing results"""

    def export_txt(
        self,
        users: List[ParsedUser],
        filepath: str,
        format: str = "username",
    ) -> None:
        """
        Export to TXT.
        format: "username", "id", "phone", "full"
        """
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        lines = []
        for user in users:
            if format == "username":
                value = f"@{user.username}" if user.username else str(user.user_id)
            elif format == "id":
                value = str(user.user_id)
            elif format == "phone":
                value = user.phone or str(user.user_id)
            elif format == "full":
                parts = [str(user.user_id)]
                if user.username:
                    parts.append(f"@{user.username}")
                if user.first_name:
                    parts.append(user.first_name)
                if user.last_name:
                    parts.append(user.last_name)
                if user.phone:
                    parts.append(user.phone)
                value = ' | '.join(parts)
            else:
                value = str(user.user_id)
            lines.append(value)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def export_csv(self, users: List[ParsedUser], filepath: str) -> None:
        """Export to CSV with all fields"""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        fieldnames = [
            'user_id', 'username', 'first_name', 'last_name',
            'phone', 'bio', 'is_premium', 'is_bot', 'is_verified',
            'last_online', 'source', 'source_id', 'parsed_at',
        ]
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for user in users:
                writer.writerow({
                    'user_id': user.user_id,
                    'username': user.username or '',
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'phone': user.phone or '',
                    'bio': user.bio or '',
                    'is_premium': user.is_premium,
                    'is_bot': user.is_bot,
                    'is_verified': user.is_verified,
                    'last_online': user.last_online.isoformat() if user.last_online else '',
                    'source': user.source,
                    'source_id': user.source_id or '',
                    'parsed_at': user.parsed_at.isoformat(),
                })

    def export_json(self, users: List[ParsedUser], filepath: str) -> None:
        """Export to JSON"""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        data = []
        for user in users:
            data.append({
                'user_id': user.user_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'bio': user.bio,
                'is_premium': user.is_premium,
                'is_bot': user.is_bot,
                'is_verified': user.is_verified,
                'last_online': user.last_online.isoformat() if user.last_online else None,
                'source': user.source,
                'source_id': user.source_id,
                'parsed_at': user.parsed_at.isoformat(),
            })
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def merge_bases(
        self,
        filepaths: List[str],
        output: str,
        deduplicate: bool = True,
    ) -> int:
        """Merge multiple bases into one"""
        entries: List[str] = []
        for fp in filepaths:
            if not os.path.exists(fp):
                continue
            with open(fp, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(line)

        if deduplicate:
            seen = set()
            unique: List[str] = []
            for entry in entries:
                if entry not in seen:
                    seen.add(entry)
                    unique.append(entry)
            entries = unique

        os.makedirs(os.path.dirname(output) if os.path.dirname(output) else '.', exist_ok=True)
        with open(output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(entries))
        return len(entries)
