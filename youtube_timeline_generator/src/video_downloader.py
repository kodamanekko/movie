"""
YouTube動画情報取得モジュール
yt-dlpを使用して動画のメタデータを取得
"""

import yt_dlp
from pathlib import Path
from loguru import logger
from datetime import timedelta


class VideoDownloader:
    def __init__(self, temp_dir: str):
        self.temp_dir = Path(temp_dir)
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
    
    def get_video_info(self, url: str) -> dict:
        """
        YouTube動画の情報を取得
        
        Args:
            url: YouTube動画のURL
            
        Returns:
            動画情報の辞書
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # 必要な情報を抽出
                duration = info.get('duration', 0)
                video_info = {
                    'url': url,
                    'title': info.get('title', 'Unknown Title'),
                    'channel': info.get('channel', 'Unknown Channel'),
                    'duration': duration,
                    'duration_string': self._format_duration(duration),
                    'description': info.get('description', ''),
                    'upload_date': info.get('upload_date', ''),
                    'video_id': info.get('id', ''),
                }
                
                return video_info
                
        except Exception as e:
            logger.error(f"動画情報の取得に失敗しました: {str(e)}")
            raise
    
    def _format_duration(self, seconds: int) -> str:
        """
        秒数を時:分:秒形式に変換
        
        Args:
            seconds: 秒数
            
        Returns:
            フォーマットされた時間文字列
        """
        if seconds == 0:
            return "00:00"
            
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds = td.seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"