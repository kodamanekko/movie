# Windows環境でのFFmpegインストール手順

## 方法1: 手動インストール（推奨）

### 1. FFmpegのダウンロード
1. [FFmpeg公式サイト](https://www.gyan.dev/ffmpeg/builds/)にアクセス
2. "release builds"セクションから「release full」をクリック
3. `ffmpeg-release-full.7z`をダウンロード

### 2. ファイルの解凍と配置
1. ダウンロードした7zファイルを解凍（7-Zipが必要）
2. 解凍したフォルダを`C:\ffmpeg`に配置
   - フォルダ構成: `C:\ffmpeg\bin\ffmpeg.exe`が存在する状態

### 3. 環境変数PATHの設定
1. Windowsキー + R → `sysdm.cpl`を入力してEnter
2. 「詳細設定」タブ → 「環境変数」をクリック
3. 「システム環境変数」の「Path」を選択して「編集」
4. 「新規」をクリックして`C:\ffmpeg\bin`を追加
5. 「OK」で全て閉じる

### 4. インストール確認
1. 新しいコマンドプロンプトを開く（重要：既存のものは閉じる）
2. 以下のコマンドを実行：
```cmd
ffmpeg -version
```

## 方法2: Chocolateyを使用（代替方法）

### 前提条件
Chocolateyがインストールされている必要があります。

### インストール手順
管理者権限でPowerShellを開いて実行：
```powershell
choco install ffmpeg
```

## 方法3: 簡易的な解決方法

プロジェクトディレクトリに直接配置する方法：

1. [こちら](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)から軽量版をダウンロード
2. ZIPファイルを解凍
3. `ffmpeg.exe`を以下の場所にコピー：
   - `C:\Users\ya211\OneDrive\ドキュメント\movie_auto_screenshot\youtube_timeline_generator\`

この方法の場合、プロジェクトディレクトリから実行する必要があります。

## トラブルシューティング

### 「ffmpegは内部コマンドまたは外部コマンド...」エラー
- PATHの設定後、必ず新しいコマンドプロンプトを開いてください
- パスに日本語が含まれていないか確認

### アンチウイルスソフトの警告
- FFmpegは正規のソフトウェアですが、一部のアンチウイルスが警告する場合があります
- 公式サイトからダウンロードしたものであれば安全です

### 動作確認
インストール後、以下のコマンドで動作確認：
```cmd
ffmpeg -version
ffmpeg -codecs
```

正常にインストールされていれば、バージョン情報とコーデック一覧が表示されます。