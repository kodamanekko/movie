#!/usr/bin/env python3
import os
import json
import argparse
from datetime import datetime
import shutil
import sys

# Windows環境での文字化け対策
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

TICKETS_DIR = "tickets"
STATES = ["todo", "in_progress", "done"]
PRIORITIES = ["high", "medium", "low"]

def ensure_directories():
    """チケット管理用のディレクトリが存在することを確認"""
    for state in STATES:
        os.makedirs(os.path.join(TICKETS_DIR, state), exist_ok=True)

def create_ticket(title, description, assignee=None, priority="medium"):
    """新しいチケットを作成"""
    ensure_directories()
    
    # チケットIDを生成（タイムスタンプベース）
    ticket_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    ticket_data = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "assignee": assignee,
        "priority": priority,
        "state": "todo",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # チケットファイルを作成
    ticket_path = os.path.join(TICKETS_DIR, "todo", f"{ticket_id}.json")
    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(ticket_data, f, ensure_ascii=False, indent=2)
    
    print(f"チケットを作成しました: {ticket_id} - {title}")
    return ticket_id

def move_ticket(ticket_id, new_state):
    """チケットの状態を変更"""
    if new_state not in STATES:
        print(f"エラー: 無効な状態です。有効な状態: {', '.join(STATES)}")
        return False
    
    # 現在のチケットを探す
    current_path = None
    current_state = None
    
    for state in STATES:
        ticket_path = os.path.join(TICKETS_DIR, state, f"{ticket_id}.json")
        if os.path.exists(ticket_path):
            current_path = ticket_path
            current_state = state
            break
    
    if not current_path:
        print(f"エラー: チケット {ticket_id} が見つかりません")
        return False
    
    if current_state == new_state:
        print(f"チケット {ticket_id} は既に {new_state} 状態です")
        return True
    
    # チケットデータを読み込む
    with open(current_path, "r", encoding="utf-8") as f:
        ticket_data = json.load(f)
    
    # 状態を更新
    ticket_data["state"] = new_state
    ticket_data["updated_at"] = datetime.now().isoformat()
    
    # 新しい場所に移動
    new_path = os.path.join(TICKETS_DIR, new_state, f"{ticket_id}.json")
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(ticket_data, f, ensure_ascii=False, indent=2)
    
    # 古いファイルを削除
    os.remove(current_path)
    
    print(f"チケット {ticket_id} を {current_state} から {new_state} に移動しました")
    return True

def list_tickets(state=None):
    """チケットの一覧を表示"""
    ensure_directories()
    
    states_to_check = [state] if state and state in STATES else STATES
    
    for current_state in states_to_check:
        print(f"\n=== {current_state.upper()} ===")
        state_dir = os.path.join(TICKETS_DIR, current_state)
        
        tickets = []
        for filename in os.listdir(state_dir):
            if filename.endswith(".json"):
                with open(os.path.join(state_dir, filename), "r", encoding="utf-8") as f:
                    ticket_data = json.load(f)
                    tickets.append(ticket_data)
        
        # 優先度順でソート（high > medium > low）、同じ優先度なら更新日時でソート
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tickets.sort(key=lambda x: (priority_order.get(x.get("priority", "medium"), 1), x["updated_at"]))
        
        if tickets:
            for ticket in tickets:
                assignee = f" (@{ticket['assignee']})" if ticket.get('assignee') else ""
                priority = ticket.get('priority', 'medium')
                priority_mark = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "")
                print(f"  {priority_mark} [{ticket['id']}] {ticket['title']}{assignee}")
                if ticket.get('description'):
                    print(f"      {ticket['description'][:50]}...")
        else:
            print("  チケットがありません")

def show_ticket(ticket_id):
    """チケットの詳細を表示"""
    # チケットを探す
    for state in STATES:
        ticket_path = os.path.join(TICKETS_DIR, state, f"{ticket_id}.json")
        if os.path.exists(ticket_path):
            with open(ticket_path, "r", encoding="utf-8") as f:
                ticket_data = json.load(f)
            
            print(f"\nチケット詳細: {ticket_id}")
            print("=" * 50)
            print(f"タイトル: {ticket_data['title']}")
            print(f"状態: {ticket_data['state']}")
            print(f"優先度: {ticket_data.get('priority', 'medium')}")
            print(f"担当者: {ticket_data.get('assignee', '未割当')}")
            print(f"作成日時: {ticket_data['created_at']}")
            print(f"更新日時: {ticket_data['updated_at']}")
            print(f"\n説明:\n{ticket_data['description']}")
            return
    
    print(f"エラー: チケット {ticket_id} が見つかりません")

def main():
    parser = argparse.ArgumentParser(description="チケット管理システム")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")
    
    # create コマンド
    create_parser = subparsers.add_parser("create", help="新しいチケットを作成")
    create_parser.add_argument("title", help="チケットのタイトル")
    create_parser.add_argument("-d", "--description", default="", help="チケットの説明")
    create_parser.add_argument("-a", "--assignee", help="担当者")
    create_parser.add_argument("-p", "--priority", choices=PRIORITIES, default="medium", help="優先度")
    
    # move コマンド
    move_parser = subparsers.add_parser("move", help="チケットの状態を変更")
    move_parser.add_argument("ticket_id", help="チケットID")
    move_parser.add_argument("state", choices=STATES, help="新しい状態")
    
    # list コマンド
    list_parser = subparsers.add_parser("list", help="チケット一覧を表示")
    list_parser.add_argument("-s", "--state", choices=STATES, help="特定の状態のみ表示")
    
    # show コマンド
    show_parser = subparsers.add_parser("show", help="チケットの詳細を表示")
    show_parser.add_argument("ticket_id", help="チケットID")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_ticket(args.title, args.description, args.assignee, args.priority)
    elif args.command == "move":
        move_ticket(args.ticket_id, args.state)
    elif args.command == "list":
        list_tickets(args.state)
    elif args.command == "show":
        show_ticket(args.ticket_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()