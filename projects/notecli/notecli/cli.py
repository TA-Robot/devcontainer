"""notecli のCLI定義。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .store import NoteStore, StoreError, default_store_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notecli",
        description="ローカルにメモを保存して管理するCLIツール",
    )
    parser.add_argument(
        "--store",
        help="保存ファイルのパス（デフォルト: ~/.local/share/notecli/notes.json）",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_p = subparsers.add_parser("add", help="メモを追加する")
    add_p.add_argument("text", nargs="+", help="追加するメモ本文")

    subparsers.add_parser("list", help="メモ一覧を表示する")

    search_p = subparsers.add_parser("search", help="メモを検索する（部分一致）")
    search_p.add_argument("query", nargs="+", help="検索語")

    delete_p = subparsers.add_parser("delete", help="メモを削除する")
    delete_p.add_argument("id", help="削除するメモID")

    return parser


def _print_notes(notes: List[Dict[str, Any]]) -> None:
    for note in notes:
        note_id = note.get("id", "")
        created_at = note.get("created_at", "")
        text = note.get("text", "")
        print(f"{note_id}\t{created_at}\t{text}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    store_path = (
        Path(args.store).expanduser()
        if getattr(args, "store", None)
        else default_store_path()
    )
    store = NoteStore(store_path)

    try:
        if args.command == "add":
            text = " ".join(args.text)
            note = store.add_note(text)
            print(note["id"])
            return 0

        if args.command == "list":
            _print_notes(store.list_notes())
            return 0

        if args.command == "search":
            query = " ".join(args.query)
            _print_notes(store.search_notes(query))
            return 0

        if args.command == "delete":
            try:
                note_id = int(args.id)
            except ValueError:
                print("IDは整数で指定してください。", file=sys.stderr)
                return 1
            try:
                store.delete_note(note_id)
            except KeyError:
                print(f"ID {note_id} のメモは見つかりません。", file=sys.stderr)
                return 1
            print(f"削除しました: {note_id}")
            return 0

        parser.print_help()
        return 2
    except StoreError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}", file=sys.stderr)
        return 1
