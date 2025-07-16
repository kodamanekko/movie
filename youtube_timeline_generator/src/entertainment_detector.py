"""
エンターテインメント動画用セクション検出モジュール
音声特徴とイベントを統合してハイライトセクションを生成
"""

from typing import List, Dict
from loguru import logger
from datetime import timedelta
import numpy as np


class EntertainmentDetector:
    def __init__(self):
        # イベントタイプごとの重要度
        self.event_weights = {
            'volume_peak': 1.0,
            'surprise': 1.5,
            'sustained_high_volume': 1.2,
            'laughter': 1.3,
            'applause': 1.4,
            'cheering': 1.2
        }
        
        # イベントタイプごとの絵文字
        self.event_emojis = {
            'volume_peak': '🔊',
            'surprise': '😱',
            'sustained_high_volume': '🔥',
            'laughter': '😂',
            'applause': '👏',
            'cheering': '🎉',
            'mixed': '🎊'
        }
        
    def detect_sections(self, all_events: List[Dict], transcription: Dict = None,
                       min_gap: float = 10.0, merge_threshold: float = 5.0) -> List[Dict]:
        """
        検出されたイベントからセクションを生成
        
        Args:
            all_events: 全てのイベントリスト
            transcription: 音声認識結果（オプション）
            min_gap: セクション間の最小間隔（秒）
            merge_threshold: イベント統合の時間閾値（秒）
            
        Returns:
            ハイライトセクションのリスト
        """
        if not all_events:
            return []
        
        # イベントを時間順にソート
        sorted_events = sorted(all_events, key=lambda x: x['time'])
        
        # 近接イベントを統合
        merged_events = self._merge_nearby_events(sorted_events, merge_threshold)
        
        # セクションを生成
        sections = self._create_sections(merged_events, min_gap)
        
        # 音声認識結果から内容を追加
        if transcription:
            sections = self._add_content_from_transcription(sections, transcription)
        
        # セクションに優先度を付与
        sections = self._prioritize_sections(sections)
        
        logger.info(f"検出されたハイライトセクション数: {len(sections)}")
        return sections
    
    def _merge_nearby_events(self, events: List[Dict], threshold: float) -> List[Dict]:
        """近接するイベントを統合"""
        if not events:
            return []
        
        merged = []
        current_group = [events[0]]
        
        for i in range(1, len(events)):
            # 前のイベントとの時間差
            time_diff = events[i]['time'] - events[i-1]['time']
            
            if time_diff <= threshold:
                # 近接している場合はグループに追加
                current_group.append(events[i])
            else:
                # 離れている場合は新しいグループを開始
                merged.append(self._merge_event_group(current_group))
                current_group = [events[i]]
        
        # 最後のグループを追加
        if current_group:
            merged.append(self._merge_event_group(current_group))
        
        return merged
    
    def _merge_event_group(self, events: List[Dict]) -> Dict:
        """イベントグループを1つのイベントに統合"""
        if len(events) == 1:
            return events[0]
        
        # 開始時刻は最初のイベント
        start_time = events[0]['time']
        
        # イベントタイプを集計
        event_types = [e['type'] for e in events]
        unique_types = list(set(event_types))
        
        # 最も重要なイベントタイプを選択
        if len(unique_types) == 1:
            main_type = unique_types[0]
        else:
            # 複数のタイプがある場合
            main_type = 'mixed'
        
        # 強度の計算（重み付き平均）
        total_intensity = 0
        total_weight = 0
        for event in events:
            weight = self.event_weights.get(event['type'], 1.0)
            intensity = event.get('intensity', 1.0)
            total_intensity += intensity * weight
            total_weight += weight
        
        avg_intensity = total_intensity / total_weight if total_weight > 0 else 1.0
        
        # 説明文の生成
        if main_type == 'mixed':
            type_counts = {}
            for t in event_types:
                type_counts[t] = type_counts.get(t, 0) + 1
            
            descriptions = []
            for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                if count > 1:
                    descriptions.append(f"{self._get_type_name(t)}×{count}")
                else:
                    descriptions.append(self._get_type_name(t))
            
            description = "複合イベント（" + "、".join(descriptions[:3]) + "）"
        else:
            description = self._get_type_name(main_type)
        
        return {
            'time': start_time,
            'type': main_type,
            'intensity': avg_intensity,
            'description': description,
            'event_count': len(events)
        }
    
    def _create_sections(self, events: List[Dict], min_gap: float) -> List[Dict]:
        """イベントからセクションを生成"""
        sections = []
        
        for event in events:
            section = {
                'start_time': event['time'],
                'start_time_str': self._format_time(event['time']),
                'title': self._create_section_title(event),
                'type': event['type'],
                'intensity': event.get('intensity', 1.0),
                'event_count': event.get('event_count', 1)
            }
            sections.append(section)
        
        return sections
    
    def _create_section_title(self, event: Dict) -> str:
        """セクションのタイトルを生成"""
        emoji = self.event_emojis.get(event['type'], '📍')
        description = event.get('description', '')
        
        # 強度に基づいて修飾語を追加
        intensity = event.get('intensity', 1.0)
        if intensity > 2.0:
            prefix = "大"
        elif intensity > 1.5:
            prefix = ""
        else:
            prefix = "小"
        
        if prefix and not description.startswith('複合'):
            title = f"{emoji} {prefix}{description}"
        else:
            title = f"{emoji} {description}"
        
        return title
    
    def _prioritize_sections(self, sections: List[Dict]) -> List[Dict]:
        """セクションに優先度スコアを付与してソート"""
        for section in sections:
            # 優先度スコアの計算
            type_weight = self.event_weights.get(section['type'], 1.0)
            intensity = section.get('intensity', 1.0)
            event_count = section.get('event_count', 1)
            
            # スコア = タイプの重み × 強度 × イベント数の対数
            priority_score = type_weight * intensity * (1 + np.log(event_count))
            section['priority_score'] = priority_score
        
        # 時間順にソート（優先度は補助情報として保持）
        return sorted(sections, key=lambda x: x['start_time'])
    
    def _get_type_name(self, event_type: str) -> str:
        """イベントタイプの日本語名を取得"""
        type_names = {
            'volume_peak': '音量ピーク',
            'surprise': 'サプライズ',
            'sustained_high_volume': '持続的盛り上がり',
            'laughter': '笑い声',
            'applause': '拍手',
            'cheering': '歓声'
        }
        return type_names.get(event_type, event_type)
    
    def _format_time(self, seconds: float) -> str:
        """秒数を MM:SS または HH:MM:SS 形式に変換"""
        td = timedelta(seconds=int(seconds))
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds = td.seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _add_content_from_transcription(self, sections: List[Dict], transcription: Dict) -> List[Dict]:
        """音声認識結果から各セクションの内容を追加"""
        segments = transcription.get('segments', [])
        if not segments:
            return sections
        
        for section in sections:
            section_time = section['start_time']
            
            # セクション時刻に最も近いセグメントを探す
            closest_segment = None
            min_time_diff = float('inf')
            
            for segment in segments:
                time_diff = abs(segment['start'] - section_time)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_segment = segment
            
            # 前後のセグメントも含めて内容を取得
            if closest_segment:
                content_segments = []
                segment_idx = segments.index(closest_segment)
                
                # 前後3セグメント（約10-15秒分）を取得
                start_idx = max(0, segment_idx - 1)
                end_idx = min(len(segments), segment_idx + 3)
                
                for i in range(start_idx, end_idx):
                    if abs(segments[i]['start'] - section_time) <= 15:  # 15秒以内
                        content_segments.append(segments[i]['text'])
                
                # 内容を結合して要約
                full_text = ' '.join(content_segments)
                summary = self._summarize_content(full_text)
                
                # タイトルに内容を追加
                section['content'] = summary
                section['full_text'] = full_text[:200] + '...' if len(full_text) > 200 else full_text
        
        return sections
    
    def _summarize_content(self, text: str, max_length: int = 30) -> str:
        """テキストを要約（キーワード抽出）"""
        if not text:
            return ""
        
        # 簡易的なキーワード抽出
        # 句読点で分割
        sentences = text.replace('。', '。\n').replace('、', '、\n').split('\n')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return text[:max_length]
        
        # 最初の意味のある文を使用
        for sentence in sentences:
            if len(sentence) > 5:  # 短すぎる文は除外
                if len(sentence) <= max_length:
                    return sentence
                else:
                    return sentence[:max_length-3] + '...'
        
        return sentences[0][:max_length-3] + '...' if sentences else ""