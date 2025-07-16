"""
音声特徴抽出モジュール
エンタメ動画の音声解析とイベント検出
"""

import numpy as np
import librosa
import scipy.signal
from pathlib import Path
from loguru import logger
from typing import List, Dict, Tuple
import soundfile as sf


class AudioAnalyzer:
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.frame_length = 2048
        self.hop_length = 512
        
    def analyze_audio(self, audio_path: Path) -> Dict:
        """
        音声ファイルを解析して特徴量を抽出
        
        Args:
            audio_path: 音声ファイルのパス
            
        Returns:
            解析結果の辞書
        """
        try:
            # 音声データの読み込み
            logger.info("音声データを読み込み中...")
            audio_data, sr = librosa.load(str(audio_path), sr=self.sample_rate)
            duration = len(audio_data) / sr
            
            # 各種特徴量の抽出
            logger.info("音声特徴を解析中...")
            
            # RMSエネルギー（音量）
            rms = librosa.feature.rms(y=audio_data, frame_length=self.frame_length, 
                                      hop_length=self.hop_length)[0]
            
            # スペクトラルセントロイド（音の明るさ）
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_data, sr=sr, hop_length=self.hop_length)[0]
            
            # ゼロ交差率（音の粗さ、ノイズ性）
            zcr = librosa.feature.zero_crossing_rate(
                audio_data, frame_length=self.frame_length, hop_length=self.hop_length)[0]
            
            # テンポとビート
            tempo, beats = librosa.beat.beat_track(y=audio_data, sr=sr, hop_length=self.hop_length)
            
            # 時間軸の作成
            times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=self.hop_length)
            
            analysis_result = {
                'duration': duration,
                'sample_rate': sr,
                'times': times,
                'rms': rms,
                'spectral_centroids': spectral_centroids,
                'zero_crossing_rate': zcr,
                'tempo': tempo,
                'beats': beats,
                'audio_data': audio_data
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"音声解析に失敗しました: {str(e)}")
            raise
    
    def detect_volume_peaks(self, analysis: Dict, threshold_multiplier: float = 1.5,
                           min_duration: float = 2.0) -> List[Dict]:
        """
        音量のピークを検出
        
        Args:
            analysis: 解析結果
            threshold_multiplier: 平均音量の何倍を閾値とするか
            min_duration: ピークとみなす最小持続時間
            
        Returns:
            ピークイベントのリスト
        """
        rms = analysis['rms']
        times = analysis['times']
        
        # 平均と標準偏差を計算
        mean_rms = np.mean(rms)
        std_rms = np.std(rms)
        threshold = mean_rms + (threshold_multiplier * std_rms)
        
        # ピークの検出
        peaks, properties = scipy.signal.find_peaks(
            rms, 
            height=threshold,
            distance=int(min_duration * analysis['sample_rate'] / self.hop_length)
        )
        
        volume_events = []
        for peak_idx in peaks:
            # ピークの強度を計算
            peak_intensity = (rms[peak_idx] - mean_rms) / std_rms
            
            event = {
                'time': times[peak_idx],
                'type': 'volume_peak',
                'intensity': float(peak_intensity),
                'description': self._get_volume_description(peak_intensity)
            }
            volume_events.append(event)
        
        return volume_events
    
    def detect_silence_to_loud(self, analysis: Dict, silence_threshold: float = 0.01,
                              loud_threshold: float = 0.1, max_gap: float = 1.0) -> List[Dict]:
        """
        静寂から急激な音量上昇を検出（サプライズ、驚き）
        
        Args:
            analysis: 解析結果
            silence_threshold: 静寂とみなす閾値
            loud_threshold: 大音量とみなす閾値
            max_gap: 静寂と大音量の最大間隔（秒）
            
        Returns:
            サプライズイベントのリスト
        """
        rms = analysis['rms']
        times = analysis['times']
        
        surprise_events = []
        
        # 静寂区間を検出
        silence_mask = rms < silence_threshold
        
        for i in range(1, len(rms)):
            # 静寂から大音量への変化を検出
            if (i > 0 and silence_mask[i-1] and rms[i] > loud_threshold):
                # 前の数フレームが静寂だったか確認
                lookback = min(i, int(max_gap * analysis['sample_rate'] / self.hop_length))
                if np.mean(rms[max(0, i-lookback):i]) < silence_threshold * 2:
                    event = {
                        'time': times[i],
                        'type': 'surprise',
                        'intensity': float(rms[i] / silence_threshold),
                        'description': '静寂からの急激な音量上昇'
                    }
                    surprise_events.append(event)
        
        return surprise_events
    
    def detect_sustained_high_volume(self, analysis: Dict, threshold_multiplier: float = 1.3,
                                   min_duration: float = 5.0) -> List[Dict]:
        """
        持続的な高音量区間を検出（アクションシーン、盛り上がり）
        
        Args:
            analysis: 解析結果
            threshold_multiplier: 平均音量の何倍を閾値とするか
            min_duration: 最小持続時間
            
        Returns:
            持続的高音量イベントのリスト
        """
        rms = analysis['rms']
        times = analysis['times']
        
        mean_rms = np.mean(rms)
        threshold = mean_rms * threshold_multiplier
        
        # 高音量区間を検出
        high_volume_mask = rms > threshold
        
        sustained_events = []
        start_idx = None
        
        for i in range(len(high_volume_mask)):
            if high_volume_mask[i] and start_idx is None:
                start_idx = i
            elif not high_volume_mask[i] and start_idx is not None:
                # 区間の終了
                duration = times[i] - times[start_idx]
                if duration >= min_duration:
                    event = {
                        'time': times[start_idx],
                        'type': 'sustained_high_volume',
                        'duration': float(duration),
                        'intensity': float(np.mean(rms[start_idx:i]) / mean_rms),
                        'description': f'持続的な盛り上がり（{duration:.1f}秒間）'
                    }
                    sustained_events.append(event)
                start_idx = None
        
        return sustained_events
    
    def _get_volume_description(self, intensity: float) -> str:
        """音量の強度に基づいた説明を生成"""
        if intensity > 3.0:
            return "非常に大きな音量ピーク"
        elif intensity > 2.0:
            return "大きな音量ピーク"
        elif intensity > 1.5:
            return "音量の盛り上がり"
        else:
            return "軽い音量上昇"