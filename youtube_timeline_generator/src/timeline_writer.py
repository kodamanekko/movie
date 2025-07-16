"""
タイムライン出力モジュール
検出されたセクション情報をテキストファイルに出力
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict
from loguru import logger
import re


class TimelineWriter:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        
    def write_timeline(self, video_info: Dict, sections: List[Dict], mode: str = 'tech') -> Path:
        """
        タイムラインをテキストファイルに出力
        
        Args:
            video_info: 動画情報
            sections: セクション情報のリスト
            mode: 出力モード ('tech' or 'entertainment')
            
        Returns:
            出力ファイルのパス
        """
        # ファイル名を生成（動画IDまたはタイトルから）
        video_id = video_info.get('video_id', '')
        title = self._sanitize_filename(video_info.get('title', 'timeline'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        mode_suffix = "_entertainment" if mode == "entertainment" else "_tech"
        if video_id:
            filename = f"{video_id}{mode_suffix}_{timestamp}.txt"
        else:
            filename = f"{title}{mode_suffix}_{timestamp}.txt"
        
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # ヘッダー情報
                if mode == 'entertainment':
                    f.write("エンターテインメント動画タイムライン\n")
                else:
                    f.write("YouTube動画タイムライン\n")
                f.write("=" * 50 + "\n")
                f.write(f"URL: {video_info.get('url', 'N/A')}\n")
                f.write(f"タイトル: {video_info.get('title', 'N/A')}\n")
                f.write(f"チャンネル: {video_info.get('channel', 'N/A')}\n")
                f.write(f"総再生時間: {video_info.get('duration_string', 'N/A')}\n")
                f.write(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"モード: {'エンタメ' if mode == 'entertainment' else '技術系'}\n")
                f.write("\n")
                
                # タイムライン
                if mode == 'entertainment':
                    f.write("ハイライトタイムライン\n")
                else:
                    f.write("タイムライン\n")
                f.write("=" * 50 + "\n")
                
                if sections:
                    for section in sections:
                        line = f"{section['start_time_str']} - {section['title']}"
                        # エンタメモードで内容がある場合は追加
                        if mode == 'entertainment' and section.get('content'):
                            line += f"「{section['content']}」"
                        f.write(line + "\n")
                else:
                    f.write("セクションが検出されませんでした。\n")
                
                # 詳細セクション（技術系モードのみ）
                if mode == 'tech' and sections and len(sections) > 0:
                    f.write("\n")
                    f.write("詳細\n")
                    f.write("=" * 50 + "\n")
                    
                    for i, section in enumerate(sections, 1):
                        f.write(f"\n[{i}] {section['start_time_str']} - {section['title']}\n")
                        # テキストの最初の100文字を表示
                        preview_text = section.get('text', '')[:100]
                        if preview_text:
                            f.write(f"    {preview_text}...\n")
                
                # エンタメモードの追加情報
                elif mode == 'entertainment' and sections:
                    f.write("\n")
                    f.write("イベント統計\n")
                    f.write("=" * 50 + "\n")
                    
                    # イベントタイプ別の統計
                    type_counts = {}
                    for section in sections:
                        event_type = section.get('type', 'unknown')
                        type_counts[event_type] = type_counts.get(event_type, 0) + 1
                    
                    for event_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                        type_name = self._get_event_type_name(event_type)
                        f.write(f"  {type_name}: {count}個\n")
            
            logger.info(f"タイムライン出力完了: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"タイムライン出力に失敗しました: {str(e)}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名として使用できない文字を除去"""
        # Windowsで使用できない文字を置換
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # 長すぎる場合は切り詰め
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        return sanitized.strip()
    
    def _get_event_type_name(self, event_type: str) -> str:
        """イベントタイプの日本語名を取得"""
        type_names = {
            'volume_peak': '音量ピーク',
            'surprise': 'サプライズ',
            'sustained_high_volume': '持続的盛り上がり',
            'laughter': '笑い声',
            'applause': '拍手',
            'cheering': '歓声',
            'mixed': '複合イベント'
        }
        return type_names.get(event_type, event_type)