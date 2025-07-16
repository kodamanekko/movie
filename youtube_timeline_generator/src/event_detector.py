"""
イベント検出モジュール
笑い声、拍手、歓声などの特定の音声パターンを検出
"""

import numpy as np
import librosa
from scipy import signal
from loguru import logger
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


class EventDetector:
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.frame_length = 2048
        self.hop_length = 512
        
    def detect_laughter(self, analysis: Dict, confidence_threshold: float = 0.7) -> List[Dict]:
        """
        笑い声を検出
        笑い声の特徴：
        - 中高周波数帯域（300-800Hz）の周期的な変動
        - 短い破裂音の連続
        - 特徴的なスペクトラルパターン
        
        Args:
            analysis: 音声解析結果
            confidence_threshold: 検出信頼度の閾値
            
        Returns:
            笑い声イベントのリスト
        """
        audio_data = analysis['audio_data']
        times = analysis['times']
        
        # スペクトログラムの計算
        D = librosa.stft(audio_data, n_fft=self.frame_length, hop_length=self.hop_length)
        magnitude = np.abs(D)
        
        # 周波数ビンの計算
        freqs = librosa.fft_frequencies(sr=self.sample_rate, n_fft=self.frame_length)
        
        # 笑い声の特徴的な周波数帯域（300-800Hz）
        laugh_freq_range = (300, 800)
        freq_mask = (freqs >= laugh_freq_range[0]) & (freqs <= laugh_freq_range[1])
        
        # 該当周波数帯域のエネルギー
        laugh_band_energy = np.mean(magnitude[freq_mask, :], axis=0)
        
        # エネルギーの変動を計算（笑い声は周期的）
        energy_diff = np.diff(laugh_band_energy)
        
        # ゼロ交差率（笑い声は高い）
        zcr = analysis['zero_crossing_rate']
        
        # 笑い声の可能性スコアを計算
        laugh_score = self._calculate_laughter_score(laugh_band_energy, energy_diff, zcr)
        
        # 閾値を超える区間を検出
        laugh_events = []
        is_laughing = False
        start_idx = None
        
        for i in range(len(laugh_score)):
            if laugh_score[i] > confidence_threshold and not is_laughing:
                is_laughing = True
                start_idx = i
            elif laugh_score[i] <= confidence_threshold and is_laughing:
                is_laughing = False
                if start_idx is not None and i - start_idx > 10:  # 最小フレーム数
                    # フレームインデックスを時間インデックスに変換
                    time_idx = min(int(start_idx * len(times) / len(laugh_score)), len(times) - 1)
                    
                    event = {
                        'time': times[time_idx],
                        'type': 'laughter',
                        'confidence': float(np.mean(laugh_score[start_idx:i])),
                        'duration': float((i - start_idx) * self.hop_length / self.sample_rate),
                        'description': '笑い声'
                    }
                    laugh_events.append(event)
        
        return laugh_events
    
    def detect_applause(self, analysis: Dict, min_duration: float = 1.0) -> List[Dict]:
        """
        拍手を検出
        拍手の特徴：
        - 広帯域ノイズ
        - 短い衝撃音の連続
        - 高いゼロ交差率
        
        Args:
            analysis: 音声解析結果
            min_duration: 最小持続時間
            
        Returns:
            拍手イベントのリスト
        """
        audio_data = analysis['audio_data']
        times = analysis['times']
        zcr = analysis['zero_crossing_rate']
        
        # スペクトラルフラットネス（拍手は高い値）
        spectral_flatness = librosa.feature.spectral_flatness(
            y=audio_data, n_fft=self.frame_length, hop_length=self.hop_length)[0]
        
        # 拍手の特徴スコア
        # 高いゼロ交差率 + 高いスペクトラルフラットネス
        applause_score = self._normalize(zcr) * self._normalize(spectral_flatness)
        
        # 移動平均でスムージング
        window_size = int(0.5 * self.sample_rate / self.hop_length)  # 0.5秒窓
        applause_score_smooth = np.convolve(applause_score, np.ones(window_size)/window_size, 'same')
        
        # 閾値の設定（平均 + 2標準偏差）
        threshold = np.mean(applause_score_smooth) + 2 * np.std(applause_score_smooth)
        
        # 拍手区間の検出
        applause_events = []
        is_applause = False
        start_idx = None
        
        for i in range(len(applause_score_smooth)):
            if applause_score_smooth[i] > threshold and not is_applause:
                is_applause = True
                start_idx = i
            elif applause_score_smooth[i] <= threshold and is_applause:
                is_applause = False
                if start_idx is not None:
                    duration = (i - start_idx) * self.hop_length / self.sample_rate
                    if duration >= min_duration:
                        # フレームインデックスを時間インデックスに変換
                        time_idx = min(int(start_idx * len(times) / len(applause_score_smooth)), len(times) - 1)
                        
                        event = {
                            'time': times[time_idx],
                            'type': 'applause',
                            'duration': float(duration),
                            'intensity': float(np.mean(applause_score_smooth[start_idx:i])),
                            'description': f'拍手（{duration:.1f}秒間）'
                        }
                        applause_events.append(event)
        
        return applause_events
    
    def detect_cheering(self, analysis: Dict, min_duration: float = 1.5) -> List[Dict]:
        """
        歓声・叫び声を検出
        歓声の特徴：
        - 高い周波数成分
        - 持続的な高エネルギー
        - 高いスペクトラルセントロイド
        
        Args:
            analysis: 音声解析結果
            min_duration: 最小持続時間
            
        Returns:
            歓声イベントのリスト
        """
        spectral_centroids = analysis['spectral_centroids']
        rms = analysis['rms']
        times = analysis['times']
        
        # 正規化
        centroids_norm = self._normalize(spectral_centroids)
        rms_norm = self._normalize(rms)
        
        # 歓声スコア：高い周波数成分 + 高いエネルギー
        cheer_score = centroids_norm * rms_norm
        
        # 閾値（平均 + 1.5標準偏差）
        threshold = np.mean(cheer_score) + 1.5 * np.std(cheer_score)
        
        # 歓声区間の検出
        cheer_events = []
        is_cheering = False
        start_idx = None
        
        for i in range(len(cheer_score)):
            if cheer_score[i] > threshold and not is_cheering:
                is_cheering = True
                start_idx = i
            elif cheer_score[i] <= threshold and is_cheering:
                is_cheering = False
                if start_idx is not None:
                    duration = (i - start_idx) * self.hop_length / self.sample_rate
                    if duration >= min_duration:
                        event = {
                            'time': times[start_idx],
                            'type': 'cheering',
                            'duration': float(duration),
                            'intensity': float(np.mean(cheer_score[start_idx:i])),
                            'description': f'歓声・叫び声（{duration:.1f}秒間）'
                        }
                        cheer_events.append(event)
        
        return cheer_events
    
    def _calculate_laughter_score(self, energy: np.ndarray, energy_diff: np.ndarray, 
                                 zcr: np.ndarray) -> np.ndarray:
        """笑い声の可能性スコアを計算"""
        # エネルギーの周期的変動
        energy_var = np.convolve(np.abs(energy_diff), np.ones(10)/10, 'same')
        
        # 各特徴量を正規化
        energy_norm = self._normalize(energy)
        energy_var_norm = self._normalize(energy_var[:-1])  # diffで1要素減るため
        zcr_norm = self._normalize(zcr)
        
        # 長さを合わせる
        min_len = min(len(energy_norm), len(energy_var_norm), len(zcr_norm))
        
        # スコアの計算（重み付き平均）
        score = (0.3 * energy_norm[:min_len] + 
                0.4 * energy_var_norm[:min_len] + 
                0.3 * zcr_norm[:min_len])
        
        return score
    
    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """データを0-1に正規化"""
        if len(data) == 0:
            return data
        min_val = np.min(data)
        max_val = np.max(data)
        if max_val - min_val > 0:
            return (data - min_val) / (max_val - min_val)
        return np.zeros_like(data)