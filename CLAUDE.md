# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 重要: チケット駆動開発の厳守

**このプロジェクトではチケット駆動開発を採用しています。以下のルールを必ず守ってください:**

1. **作業開始前に必ずチケットを確認または作成**
   ```bash
   # まず既存チケットを確認
   python ticket.py list -s todo
   
   # なければ新規作成
   python ticket.py create "作業内容" -d "詳細説明" -a "担当者"
   ```

2. **チケットなしでの作業は絶対禁止**
   - コード変更、ドキュメント更新、設定変更、すべてチケットが必要
   - ユーザーから作業依頼があったら、まずチケットを作成

3. **作業フロー**
   ```bash
   # 1. チケットを作業中に変更（これを忘れずに！）
   python ticket.py move [チケットID] in_progress
   
   # 2. 作業実施
   
   # 3. 完了したらdoneへ
   python ticket.py move [チケットID] done
   ```

4. **同時作業は1チケットのみ**
   - in_progress状態は常に1つまで
   - 現在の作業を完了してから次へ

### チケット駆動開発のルール

1. **作業開始前に必ずチケットを確認**
   - 既存のチケットがあるか確認: `python ticket.py list -s todo`
   - なければ新規作成: `python ticket.py create "タイトル" -d "詳細"`

2. **チケットなしでの作業は禁止**
   - すべての変更（機能追加、バグ修正、リファクタリング）はチケットに紐づける
   - 緊急の修正でも必ずチケットを作成してから作業

3. **チケットのライフサイクル**
   ```
   todo → in_progress → done
   ```
   - 作業開始時: `python ticket.py move [ID] in_progress`
   - 作業完了時: `python ticket.py move [ID] done`

4. **同時進行は1チケットまで**
   - in_progress状態のチケットは1つまで
   - 完了してから次のチケットに着手

5. **チケットの粒度**
   - 1チケット = 1〜4時間で完了できる作業
   - 大きな機能は複数のチケットに分割

6. **コミットメッセージにチケットID記載**
   ```bash
   git commit -m "[チケットID] 実装内容の説明"
   # 例: git commit -m "[20241212_143025] ユーザー認証機能を実装"
   ```

### Ticket Management Commands

```bash
# Create a new ticket
python ticket.py create "タイトル" -d "説明" -a "担当者名"

# List tickets
python ticket.py list               # All tickets
python ticket.py list -s todo       # Only todo tickets
python ticket.py list -s in_progress # Only in-progress tickets

# Show ticket details
python ticket.py show チケットID

# Update ticket status
python ticket.py move チケットID in_progress  # Start work
python ticket.py move チケットID done         # Mark complete
```

### Claude Code Slash Commands

Use these commands directly in Claude Code:
- `/ticket_create "タイトル" -d "説明" -a "担当者"`
- `/ticket_list [-s 状態]`
- `/ticket_show チケットID`
- `/ticket_move チケットID 新状態`

## Common Tasks

### 作業開始時の手順（必須）
```bash
# 1. 既存チケットの確認
python ticket.py list -s todo

# 2a. 既存チケットがある場合
python ticket.py move [ID] in_progress

# 2b. 新規作業の場合（必ずチケット作成）
python ticket.py create "作業タイトル" -d "詳細説明" -a "あなたの名前"
python ticket.py move [新規ID] in_progress

# 3. 作業実施

# 4. 完了時
python ticket.py move [ID] done
```

### チケット作成が必要な例
- 新機能の実装
- バグ修正
- リファクタリング
- ドキュメント更新
- 設定ファイルの変更
- **ユーザーからの作業依頼すべて**

### 注意事項
- チケットなしで作業を開始しない
- 「ちょっとした修正」でも必ずチケットを作成
- コミット時は `git commit -m "[チケットID] 変更内容"`