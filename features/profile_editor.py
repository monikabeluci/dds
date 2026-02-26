"""
Редактирование профиля Telegram аккаунта.
"""

from pathlib import Path
from typing import Optional

from config import BIO_MAX_LENGTH
from utils.logger import logger


class ProfileEditor:
    """Редактирование профиля Telegram аккаунта."""

    async def set_avatar(self, client, photo_path: str) -> bool:
        """Установить аватар из файла."""
        path = Path(photo_path)
        if not path.exists():
            logger.error(f"Файл аватара не найден: {photo_path}")
            return False

        try:
            await client.upload_profile_photo(path)
            logger.info(f"Аватар установлен из {photo_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при установке аватара: {e}")
            return False

    async def remove_avatar(self, client) -> bool:
        """Удалить текущий аватар."""
        try:
            from telethon.tl.functions.photos import DeletePhotosRequest, GetUserPhotosRequest
            from telethon.tl.types import InputPhoto

            photos = await client(GetUserPhotosRequest(
                user_id="me", offset=0, max_id=0, limit=1
            ))
            if not photos.photos:
                logger.info("Аватар не установлен")
                return True

            photo = photos.photos[0]
            input_photo = InputPhoto(
                id=photo.id,
                access_hash=photo.access_hash,
                file_reference=photo.file_reference,
            )
            await client(DeletePhotosRequest(id=[input_photo]))
            logger.info("Аватар удалён")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении аватара: {e}")
            return False

    async def set_name(self, client, first_name: str, last_name: str = "") -> bool:
        """Установить имя профиля."""
        try:
            from telethon.tl.functions.account import UpdateProfileRequest
            await client(UpdateProfileRequest(
                first_name=first_name.strip(),
                last_name=last_name.strip(),
            ))
            logger.info(f"Имя установлено: {first_name} {last_name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при установке имени: {e}")
            return False

    async def set_username(self, client, username: str) -> bool:
        """
        Установить username (проверяет доступность).
        Возвращает True при успехе.
        """
        from telethon.tl.functions.account import UpdateUsernameRequest
        from telethon.errors import UsernameOccupiedError, UsernameInvalidError

        username = username.lstrip("@").strip()

        try:
            await client(UpdateUsernameRequest(username=username))
            logger.info(f"Username установлен: @{username}")
            return True
        except UsernameOccupiedError:
            logger.warning(f"Username @{username} уже занят")
            return False
        except UsernameInvalidError:
            logger.warning(f"Username @{username} невалиден")
            return False
        except Exception as e:
            logger.error(f"Ошибка при установке username: {e}")
            return False

    async def set_bio(self, client, bio: str) -> bool:
        """Установить BIO (до 70 символов)."""
        from telethon.tl.functions.account import UpdateProfileRequest

        bio = bio.strip()
        if len(bio) > BIO_MAX_LENGTH:
            bio = bio[:BIO_MAX_LENGTH]
            logger.warning(f"BIO обрезано до {BIO_MAX_LENGTH} символов")

        try:
            await client(UpdateProfileRequest(about=bio))
            logger.info(f"BIO установлено: {bio[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Ошибка при установке BIO: {e}")
            return False

    async def get_full_profile(self, client) -> dict:
        """Получить полную информацию профиля."""
        from telethon.tl.functions.users import GetFullUserRequest

        profile = {
            "id": None,
            "phone": None,
            "first_name": "",
            "last_name": "",
            "username": None,
            "bio": "",
            "has_avatar": False,
            "is_verified": False,
            "is_premium": False,
        }

        try:
            me = await client.get_me()
            profile["id"] = me.id
            profile["phone"] = me.phone
            profile["first_name"] = me.first_name or ""
            profile["last_name"] = me.last_name or ""
            profile["username"] = me.username
            profile["has_avatar"] = bool(me.photo)
            profile["is_verified"] = getattr(me, "verified", False)
            profile["is_premium"] = getattr(me, "premium", False)

            try:
                full_user = await client(GetFullUserRequest(me))
                profile["bio"] = getattr(full_user.full_user, "about", "") or ""
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Ошибка при получении профиля: {e}")

        return profile
