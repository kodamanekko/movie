"""
音声抽出モジュール
YouTube動画から音声を抽出してMP3形式で保存
"""

import yt_dlp
from pathlib import Path
from loguru import logger
import subprocess
import os


class AudioExtractor:
    def __init__(self, temp_dir: str):
        self.temp_dir = Path(temp_dir)
        
    def extract_audio(self, url: str, video_info: dict) -> Path:
        """
        YouTube動画から音声を抽出
        
        Args:
            url: YouTube動画のURL
            video_info: 動画情報の辞書
            
        Returns:
            抽出した音声ファイルのパス
        """
        video_id = video_info['video_id']
        output_path = self.temp_dir / f"{video_id}.mp3"
        
        # 既に音声ファイルが存在する場合はスキップ
        if output_path.exists():
            logger.info(f"音声ファイルが既に存在します: {output_path}")
            return output_path
        
        # yt-dlpのオプション設定
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.temp_dir / f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            # FFmpegの存在確認
            self._check_ffmpeg()
            
            # 音声をダウンロード・抽出
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("音声をダウンロード中...")
                ydl.download([url])
            
            if not output_path.exists():
                raise FileNotFoundError(f"音声ファイルの生成に失敗しました: {output_path}")
            
            logger.info(f"音声抽出完了: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"音声抽出に失敗しました: {str(e)}")
            raise
    
    def _check_ffmpeg(self):
        """FFmpegがインストールされているか確認"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpegが正しく動作していません")
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpegがインストールされていません。\n"
                "インストール方法:\n"
                "- Windows: https://ffmpeg.org/download.html\n"
                "- Mac: brew install ffmpeg\n"
                "- Linux: sudo apt install ffmpeg"
            )