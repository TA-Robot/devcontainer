from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(args: list[str], store_path: Path) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "-m",
        "notecli",
        "--store",
        str(store_path),
        *args,
    ]
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )


def test_add_and_list(tmp_path: Path) -> None:
    store_path = tmp_path / "notes.json"

    res_add = run_cli(["add", "最初のメモ"], store_path)
    assert res_add.returncode == 0
    assert res_add.stdout.strip() == "1"

    res_list = run_cli(["list"], store_path)
    assert res_list.returncode == 0
    lines = [l for l in res_list.stdout.splitlines() if l.strip()]
    assert len(lines) == 1
    cols = lines[0].split("\t")
    assert cols[0] == "1"
    assert cols[2] == "最初のメモ"
    assert cols[1]  # created_at が入っていること


def test_search(tmp_path: Path) -> None:
    store_path = tmp_path / "notes.json"

    res_add1 = run_cli(["add", "hello world"], store_path)
    assert res_add1.returncode == 0
    res_add2 = run_cli(["add", "bye"], store_path)
    assert res_add2.returncode == 0

    res_search = run_cli(["search", "hello"], store_path)
    assert res_search.returncode == 0
    lines = [l for l in res_search.stdout.splitlines() if l.strip()]
    assert len(lines) == 1
    assert "hello world" in lines[0]


def test_delete(tmp_path: Path) -> None:
    store_path = tmp_path / "notes.json"

    res_add = run_cli(["add", "削除対象"], store_path)
    assert res_add.returncode == 0

    res_del = run_cli(["delete", "1"], store_path)
    assert res_del.returncode == 0

    res_list = run_cli(["list"], store_path)
    assert res_list.returncode == 0
    assert res_list.stdout.strip() == ""


def test_delete_missing_id(tmp_path: Path) -> None:
    store_path = tmp_path / "notes.json"

    res_del = run_cli(["delete", "99"], store_path)
    assert res_del.returncode != 0
    assert "見つかりません" in res_del.stderr


def test_delete_non_integer_id(tmp_path: Path) -> None:
    store_path = tmp_path / "notes.json"

    res_del = run_cli(["delete", "foo"], store_path)
    assert res_del.returncode != 0
    assert "整数" in res_del.stderr

