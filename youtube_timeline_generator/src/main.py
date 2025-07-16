#!/usr/bin/env python3
"""
YouTube Timeline Generator
技術系/エンタメ動画のタイムライン自動生成ツール
"""

import click
import sys
from pathlib import Path
from loguru import logger
from datetime import datetime

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.video_downloader import VideoDownloader
from src.audio_extractor import AudioExtractor
from src.speech_recognizer import SpeechRecognizer
from src.section_detector import SectionDetector
from src.timeline_writer import TimelineWriter
from src.audio_analyzer import AudioAnalyzer
from src.event_detector import EventDetector
from src.entertainment_detector import EntertainmentDetector

# ログ設定
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
logger.add("logs/app_{time:YYYY-MM-DD}.log", rotation="1 day", retention="7 days", level="DEBUG")


@click.command()
@click.argument('youtube_url')
@click.option('--mode', '-m', type=click.Choice(['tech', 'entertainment']), default='tech', 
              help='処理モード: tech(技術系) / entertainment(エンタメ系)')
@click.option('--output-dir', '-o', default='output', help='出力ディレクトリ')
@click.option('--temp-dir', '-t', default='temp', help='一時ファイルディレクトリ')
@click.option('--language', '-l', default='ja', help='音声認識の言語 (ja/en)')
@click.option('--volume-threshold', default=1.5, help='音量閾値倍率（エンタメモード用）')
@click.option('--verbose', '-v', is_flag=True, help='詳細ログを表示')
def main(youtube_url, mode, output_dir, temp_dir, language, volume_threshold, verbose):
    """
    YouTube動画からタイムラインを自動生成します。
    
    YOUTUBE_URL: 処理対象のYouTube動画URL
    """
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # ディレクトリの作成
    Path(output_dir).mkdir(exist_ok=True)
    Path(temp_dir).mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    logger.info(f"処理開始: {youtube_url}")
    logger.info(f"モード: {mode}")
    
    try:
        # 1. 動画情報の取得
        logger.info("動画情報を取得中...")
        downloader = VideoDownloader(temp_dir)
        video_info = downloader.get_video_info(youtube_url)
        logger.info(f"動画タイトル: {video_info['title']}")
        logger.info(f"動画時間: {video_info['duration_string']}")
        
        # 2. 音声の抽出
        logger.info("音声を抽出中...")
        extractor = AudioExtractor(temp_dir)
        audio_path = extractor.extract_audio(youtube_url, video_info)
        
        if mode == 'tech':
            # 技術系モード：音声認識ベース
            sections = process_tech_mode(audio_path, language)
        else:
            # エンタメモード：音声特徴ベース
            sections = process_entertainment_mode(audio_path, volume_threshold)
        
        # 5. タイムライン出力
        logger.info("タイムラインを生成中...")
        writer = TimelineWriter(output_dir)
        output_path = writer.write_timeline(video_info, sections, mode=mode)
        
        logger.success(f"完了! タイムラインを保存しました: {output_path}")
        
        # 一時ファイルの削除（オプション）
        if not verbose and audio_path.exists():
            audio_path.unlink()
            
    except KeyboardInterrupt:
        logger.warning("処理が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        if verbose:
            logger.exception("詳細なエラー情報:")
        sys.exit(1)


def process_tech_mode(audio_path: Path, language: str) -> list:
    """技術系モードの処理"""
    # 3. 音声認識
    logger.info("音声認識を実行中... (これには時間がかかります)")
    recognizer = SpeechRecognizer(language)
    transcription = recognizer.transcribe(audio_path)
    
    # 4. セクション検出
    logger.info("セクションを検出中...")
    detector = SectionDetector()
    sections = detector.detect_sections(transcription)
    
    return sections


def process_entertainment_mode(audio_path: Path, volume_threshold: float) -> list:
    """エンタメモードの処理"""
    # 3. 音声解析
    logger.info("音声特徴を解析中...")
    analyzer = AudioAnalyzer()
    analysis = analyzer.analyze_audio(audio_path)
    
    # 4. 音声認識（軽量版）
    logger.info("音声認識を実行中（内容把握用）...")
    recognizer = SpeechRecognizer('ja')
    transcription = recognizer.transcribe(audio_path)
    
    # 5. イベント検出
    logger.info("イベントを検出中...")
    all_events = []
    
    # 音量ベースのイベント
    volume_peaks = analyzer.detect_volume_peaks(analysis, volume_threshold)
    all_events.extend(volume_peaks)
    logger.info(f"  音量ピーク: {len(volume_peaks)}個")
    
    surprises = analyzer.detect_silence_to_loud(analysis)
    all_events.extend(surprises)
    logger.info(f"  サプライズ: {len(surprises)}個")
    
    sustained = analyzer.detect_sustained_high_volume(analysis)
    all_events.extend(sustained)
    logger.info(f"  持続的盛り上がり: {len(sustained)}個")
    
    # パターンベースのイベント
    event_detector = EventDetector()
    
    laughter = event_detector.detect_laughter(analysis)
    all_events.extend(laughter)
    logger.info(f"  笑い声: {len(laughter)}個")
    
    applause = event_detector.detect_applause(analysis)
    all_events.extend(applause)
    logger.info(f"  拍手: {len(applause)}個")
    
    cheering = event_detector.detect_cheering(analysis)
    all_events.extend(cheering)
    logger.info(f"  歓声: {len(cheering)}個")
    
    # 6. セクション生成（トランスクリプション付き）
    logger.info("ハイライトセクションを生成中...")
    entertainment_detector = EntertainmentDetector()
    sections = entertainment_detector.detect_sections(all_events, transcription)
    
    return sections


if __name__ == "__main__":
    main()