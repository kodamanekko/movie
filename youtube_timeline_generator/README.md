# YouTube Timeline Generator

YouTube動画の内容を自動解析し、タイムラインを生成するツール

## 機能

### 技術系モード (tech)
- Whisperによる高精度音声認識
- 話題の切り替わりを自動検出
- セクションごとのテキスト内容を含む詳細なタイムライン

### エンタメモード (entertainment)
- 音声特徴に基づくハイライト検出
- 笑い声、拍手、歓声の自動検出
- 音量ピークやサプライズシーンの抽出
- 盛り上がりポイントの可視化

## 必要要件

- Python 3.8以上
- FFmpeg（音声処理用）
- 4GB以上のメモリ（Whisper実行用）

## インストール

### 1. リポジトリのクローン
```bash
git clone <repository_url>
cd youtube_timeline_generator
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 3. FFmpegのインストール

#### Windows
1. [FFmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロード
2. 解凍してPATHに追加

#### Mac
```bash
brew install ffmpeg
```

#### Linux
```bash
sudo apt update
sudo apt install ffmpeg
```

## 使い方

### 基本的な使用方法
```bash
# 技術系モード（デフォルト）
python src/main.py <YouTube URL>

# エンタメモード
python src/main.py <YouTube URL> --mode entertainment
```

### オプション
```bash
python src/main.py <YouTube URL> [OPTIONS]

Options:
  -m, --mode TEXT         処理モード tech/entertainment (default: tech)
  -o, --output-dir TEXT   出力ディレクトリ (default: output)
  -t, --temp-dir TEXT     一時ファイルディレクトリ (default: temp)
  -l, --language TEXT     音声認識の言語 ja/en (default: ja) ※techモード用
  --volume-threshold      音量閾値倍率 (default: 1.5) ※entertainmentモード用
  -v, --verbose          詳細ログを表示
  --help                 ヘルプを表示
```

### 使用例

#### 技術系動画
```bash
# プログラミングチュートリアル
python src/main.py https://www.youtube.com/watch?v=xxxxx

# 英語の技術解説
python src/main.py https://www.youtube.com/watch?v=xxxxx -l en

# 詳細ログ付き
python src/main.py https://www.youtube.com/watch?v=xxxxx -v
```

#### エンタメ動画
```bash
# ゲーム実況
python src/main.py https://www.youtube.com/watch?v=xxxxx -m entertainment

# 音量閾値を調整（より多くのピークを検出）
python src/main.py https://www.youtube.com/watch?v=xxxxx -m entertainment --volume-threshold 1.2

# バラエティ番組
python src/main.py https://www.youtube.com/watch?v=xxxxx --mode entertainment
```

## 出力例

### 技術系モード
```
YouTube動画タイムライン
==================================================
URL: https://www.youtube.com/watch?v=xxxxx
タイトル: Python入門講座
チャンネル: Tech Channel
総再生時間: 25:30
生成日時: 2024-01-12 17:30:00
モード: 技術系

タイムライン
==================================================
00:00 - イントロダクション
02:15 - 環境構築の説明
05:30 - 基本概念の解説
08:45 - コーディング開始
12:20 - エラー対処とデバッグ方法
15:00 - 応用例の実装
18:30 - まとめと次回予告
```

### エンタメモード
```
エンターテインメント動画タイムライン
==================================================
URL: https://www.youtube.com/watch?v=xxxxx
タイトル: 【ゲーム実況】恐怖のホラーゲーム
チャンネル: Gaming Channel
総再生時間: 35:20
生成日時: 2024-01-12 17:45:00
モード: エンタメ

ハイライトタイムライン
==================================================
00:45 - 🎉 大きな盛り上がり「すごい！これはヤバい！」
02:30 - 😱 サプライズ（静寂からの急激な音量上昇）「えっ！？マジで！？」
05:15 - 😂 笑い声「それはないでしょ〜」
08:20 - 👏 拍手（3.5秒間）「よくやった！素晴らしい！」
12:45 - 🔥 持続的盛り上がり（15.2秒間）「ここからが本番だ！」
15:30 - 🎊 複合イベント（笑い声、歓声）「やったー！ついに成功！」
18:00 - 😱 大きなサプライズ「うわっ！びっくりした！」
22:15 - 🎉 歓声（5.8秒間）「最高！ありがとう！」

イベント統計
==================================================
  笑い声: 8個
  音量ピーク: 5個
  拍手: 3個
  サプライズ: 3個
  歓声: 2個
```

## ディレクトリ構成

```
youtube_timeline_generator/
├── src/                    # ソースコード
│   ├── main.py            # メインスクリプト
│   ├── video_downloader.py # 動画情報取得
│   ├── audio_extractor.py  # 音声抽出
│   ├── speech_recognizer.py # 音声認識
│   ├── section_detector.py  # セクション検出
│   └── timeline_writer.py   # タイムライン出力
├── tests/                  # テストコード
├── output/                 # 出力ファイル
├── temp/                   # 一時ファイル
├── logs/                   # ログファイル
├── requirements.txt        # 依存関係
└── README.md              # このファイル
```

## 注意事項

- 初回実行時はWhisperモデルのダウンロードに時間がかかります（約140MB）
- 長時間の動画は処理に時間がかかります（60分動画で5-10分程度）
- GPU（CUDA）が利用可能な場合は自動的に使用されます

## トラブルシューティング

### FFmpegが見つからないエラー
FFmpegが正しくインストールされ、PATHに追加されているか確認してください。

### メモリ不足エラー
Whisperの実行には最低4GBのメモリが必要です。他のアプリケーションを終了してから再試行してください。

### 音声認識の精度が低い
- 動画の音質が悪い可能性があります
- 言語設定が正しいか確認してください（-l オプション）

## ライセンス

MIT License