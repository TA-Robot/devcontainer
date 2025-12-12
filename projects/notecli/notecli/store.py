"""notecli の保存層。

メモは JSON ファイルに配列として保存する。
各要素は {id, created_at, text} を持つ辞書。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class StoreError(RuntimeError):
    """保存に関するユーザー向けエラー。"""


def default_store_path() -> Path:
    """デフォルトの保存先を返す。"""
    return Path.home() / ".local" / "share" / "notecli" / "notes.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class NoteStore:
    """メモの読み書きを担うストア。"""

    def __init__(self, path: Path):
        self.path = path

    def list_notes(self) -> List[Dict[str, Any]]:
        return self._load_notes()

    def add_note(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if not text:
            raise StoreError("メモの内容が空です。")
        notes = self._load_notes()
        max_id = 0
        for n in notes:
            note_id = _safe_int(n.get("id", 0))
            if note_id is None:
                # 手編集等で壊れたデータが混じっていても、新規追加は継続できるようにする
                continue
            if note_id > max_id:
                max_id = note_id
        next_id = max_id + 1
        note: Dict[str, Any] = {
            "id": next_id,
            "created_at": _now_iso(),
            "text": text,
        }
        notes.append(note)
        self._save_notes(notes)
        return note

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        query = query.strip()
        notes = self._load_notes()
        if not query:
            return notes
        q_lower = query.lower()
        return [
            n
            for n in notes
            if q_lower in str(n.get("text", "")).lower()
        ]

    def delete_note(self, note_id: int) -> None:
        notes = self._load_notes()
        remaining: List[Dict[str, Any]] = []
        removed = False
        for n in notes:
            try:
                current_id = int(n.get("id", -1))
            except (TypeError, ValueError):
                current_id = -1
            if current_id == note_id:
                removed = True
                continue
            remaining.append(n)
        if not removed:
            raise KeyError(note_id)
        self._save_notes(remaining)

    def _load_notes(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError as e:
            raise StoreError(f"保存ファイルを読み込めませんでした: {self.path}") from e
        if not raw.strip():
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise StoreError(f"保存ファイルが壊れています: {self.path}") from e
        if not isinstance(data, list):
            raise StoreError(f"保存ファイルの形式が不正です: {self.path}")
        notes: List[Dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict):
                notes.append(item)
        return notes

    def _save_notes(self, notes: List[Dict[str, Any]]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp_path.write_text(
                json.dumps(notes, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp_path.replace(self.path)
        except OSError as e:
            raise StoreError(f"保存ファイルに書き込めませんでした: {self.path}") from e
