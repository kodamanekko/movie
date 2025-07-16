"""
セクション検出モジュール
音声認識結果から話題の切り替わりを検出
"""

from typing import List, Dict
from loguru import logger
import re
from datetime import timedelta


class SectionDetector:
    def __init__(self):
        # セクション開始を示すキーワードパターン
        self.section_keywords = [
            # 日本語パターン
            r'次は',
            r'続いて',
            r'それでは',
            r'ここから',
            r'まず',
            r'最初に',
            r'次に',
            r'最後に',
            r'では.*について',
            r'.*の説明',
            r'.*を見て',
            r'実際に',
            r'デモ',
            r'例として',
            r'まとめ',
            # 英語パターン
            r'next',
            r'now',
            r'let\'s',
            r'first',
            r'finally',
            r'in this section',
            r'moving on',
        ]
        
        # セクション境界の最小間隔（秒）
        self.min_section_duration = 30
        
    def detect_sections(self, transcription: Dict) -> List[Dict]:
        """
        音声認識結果からセクションを検出
        
        Args:
            transcription: 音声認識結果
            
        Returns:
            検出されたセクションのリスト
        """
        segments = transcription.get('segments', [])
        if not segments:
            return []
        
        sections = []
        current_section = None
        
        for i, segment in enumerate(segments):
            text = segment['text']
            start_time = segment['start']
            
            # セクション開始の検出
            if self._is_section_start(text):
                # 前のセクションとの間隔をチェック
                if current_section is None or (start_time - current_section['start']) >= self.min_section_duration:
                    # 新しいセクションを開始
                    if current_section:
                        sections.append(current_section)
                    
                    current_section = {
                        'start': start_time,
                        'title': self._extract_section_title(text, segments[i:i+3]),
                        'segments': [segment]
                    }
                else:
                    # 間隔が短い場合は現在のセクションに追加
                    if current_section:
                        current_section['segments'].append(segment)
            else:
                # 現在のセクションに追加
                if current_section:
                    current_section['segments'].append(segment)
                elif not sections:
                    # 最初のセクションがない場合は作成
                    current_section = {
                        'start': 0,
                        'title': 'イントロダクション',
                        'segments': [segment]
                    }
        
        # 最後のセクションを追加
        if current_section:
            sections.append(current_section)
        
        # セクションが見つからない場合の処理
        if not sections and segments:
            sections = self._create_time_based_sections(segments)
        
        logger.info(f"検出されたセクション数: {len(sections)}")
        return self._format_sections(sections)
    
    def _is_section_start(self, text: str) -> bool:
        """テキストがセクションの開始を示すかチェック"""
        text_lower = text.lower()
        for pattern in self.section_keywords:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _extract_section_title(self, text: str, next_segments: List[Dict]) -> str:
        """セクションタイトルを抽出"""
        # 最初の文から抽出
        title = text.strip()
        
        # 長すぎる場合は短縮
        if len(title) > 30:
            # 句読点で区切る
            for delimiter in ['。', '、', ',', '.']:
                if delimiter in title:
                    title = title.split(delimiter)[0]
                    break
            
            # それでも長い場合は切り詰め
            if len(title) > 30:
                title = title[:27] + '...'
        
        return title
    
    def _create_time_based_sections(self, segments: List[Dict]) -> List[Dict]:
        """時間ベースでセクションを作成（フォールバック）"""
        sections = []
        section_duration = 300  # 5分ごと
        
        current_section = {
            'start': 0,
            'title': 'セクション 1',
            'segments': []
        }
        section_num = 1
        
        for segment in segments:
            if segment['start'] - current_section['start'] >= section_duration:
                sections.append(current_section)
                section_num += 1
                current_section = {
                    'start': segment['start'],
                    'title': f'セクション {section_num}',
                    'segments': [segment]
                }
            else:
                current_section['segments'].append(segment)
        
        if current_section['segments']:
            sections.append(current_section)
        
        return sections
    
    def _format_sections(self, sections: List[Dict]) -> List[Dict]:
        """セクション情報をフォーマット"""
        formatted_sections = []
        
        for section in sections:
            formatted_sections.append({
                'start_time': section['start'],
                'start_time_str': self._format_time(section['start']),
                'title': section['title'],
                'text': ' '.join([s['text'] for s in section['segments']])
            })
        
        return formatted_sections
    
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