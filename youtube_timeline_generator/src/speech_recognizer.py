"""
音声認識モジュール
OpenAI Whisperを使用して音声をテキストに変換
"""

import whisper
from pathlib import Path
from loguru import logger
from typing import Dict, List
import torch


class SpeechRecognizer:
    def __init__(self, language: str = 'ja'):
        self.language = language
        self.model = None
        
    def transcribe(self, audio_path: Path) -> Dict:
        """
        音声ファイルをテキストに変換
        
        Args:
            audio_path: 音声ファイルのパス
            
        Returns:
            変換結果の辞書（segments含む）
        """
        try:
            # モデルのロード（初回のみ）
            if self.model is None:
                logger.info("Whisperモデルをロード中...")
                # GPUが利用可能か確認
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"使用デバイス: {device}")
                
                # baseモデルを使用（精度とスピードのバランス）
                self.model = whisper.load_model("base", device=device)
            
            # 音声認識実行
            logger.info("音声認識を実行中...")
            result = self.model.transcribe(
                str(audio_path),
                language=self.language,
                verbose=False,
                task="transcribe"
            )
            
            # セグメント情報を整理
            segments = []
            for segment in result['segments']:
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip(),
                    'id': segment['id']
                })
            
            transcription = {
                'text': result['text'],
                'segments': segments,
                'language': result.get('language', self.language)
            }
            
            logger.info(f"音声認識完了: {len(segments)}セグメント")
            return transcription
            
        except Exception as e:
            logger.error(f"音声認識に失敗しました: {str(e)}")
            raise
    
    def get_segments_with_timestamps(self, transcription: Dict) -> List[Dict]:
        """
        タイムスタンプ付きのセグメントリストを取得
        
        Args:
            transcription: 音声認識結果
            
        Returns:
            タイムスタンプ付きセグメントのリスト
        """
        return transcription.get('segments', [])