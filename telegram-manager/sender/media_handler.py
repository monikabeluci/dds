import os
import shutil
from typing import List, Optional, Tuple


class MediaHandler:
    """Handle media files for sending"""

    def __init__(self):
        self.supported_images = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        self.supported_videos = ['.mp4', '.avi', '.mov', '.mkv']
        self.supported_docs = ['.pdf', '.doc', '.docx', '.txt', '.zip']

    def validate_media(self, filepath: str) -> Tuple[bool, str]:
        """Validate media file"""
        if not os.path.exists(filepath):
            return False, f"File not found: {filepath}"

        ext = os.path.splitext(filepath)[1].lower()
        all_supported = self.supported_images + self.supported_videos + self.supported_docs

        if ext not in all_supported:
            return False, f"Unsupported file type: {ext}"

        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if size_mb > 2000:
            return False, f"File too large: {size_mb:.1f}MB"

        return True, "OK"

    def resize_image(self, filepath: str, max_size: int = 1280) -> str:
        """Resize image"""
        try:
            from PIL import Image
            img = Image.open(filepath)
            if max(img.size) <= max_size:
                return filepath

            ratio = max_size / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

            base, ext = os.path.splitext(filepath)
            output_path = f"{base}_resized{ext}"
            img.save(output_path)
            return output_path
        except ImportError:
            return filepath
        except Exception:
            return filepath

    def compress_video(self, filepath: str, max_size_mb: int = 50) -> str:
        """Compress video"""
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if size_mb <= max_size_mb:
            return filepath

        try:
            import subprocess
            base, ext = os.path.splitext(filepath)
            output_path = f"{base}_compressed.mp4"
            subprocess.run([
                'ffmpeg', '-i', filepath,
                '-vcodec', 'libx264', '-crf', '28',
                '-preset', 'fast', '-y', output_path
            ], capture_output=True, check=True)
            return output_path
        except Exception:
            return filepath

    def create_thumbnail(self, video_path: str) -> str:
        """Create video thumbnail"""
        try:
            import subprocess
            base, _ = os.path.splitext(video_path)
            thumbnail_path = f"{base}_thumb.jpg"
            subprocess.run([
                'ffmpeg', '-i', video_path,
                '-vframes', '1', '-an',
                '-s', '320x240', '-y', thumbnail_path
            ], capture_output=True, check=True)
            return thumbnail_path
        except Exception:
            return ""
