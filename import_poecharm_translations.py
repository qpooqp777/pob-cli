#!/usr/bin/env python3
"""Convert PoeCharm Data/Translate/zh-rTW CSV files to pob-cli JSON.

Usage:
  python3 import_poecharm_translations.py \
      --input /home/ubuntu/PoeCharm/Data/Translate/zh-rTW \
      --output /home/ubuntu/pob-cli/locales/zh_TW.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ENCODINGS = ("utf-8-sig", "utf-8", "cp950", "big5", "gb18030")


def read_rows(path: Path) -> tuple[list[tuple[str, str]], str]:
    last_error: Exception | None = None
    for encoding in ENCODINGS:
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                rows: list[tuple[str, str]] = []
                for row in csv.reader(f):
                    if not row or not any(cell.strip() for cell in row):
                        continue
                    key = row[0].strip().lstrip("\ufeff")
                    value = row[1].strip() if len(row) > 1 else ""
                    if not key or key.startswith("#") or not value:
                        continue
                    rows.append((key, value))
                return rows, encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"無法讀取 {path}: {last_error}")


def category(filename: str) -> str:
    name = filename.lower()
    if name.startswith("items_") or name.startswith("uniques"):
        return "items"
    if "gem" in name or "flask" in name or "monster" in name:
        return "game_data"
    if "stat" in name or "mod" in name or "prefix" in name or "suffix" in name or name.startswith("tree_sd") or name.startswith("tree_dn"):
        return "mods"
    if "passive" in name or name.startswith("tree"):
        return "tree"
    if name.endswith(".csv"):
        return "ui"
    return "other"


def clean_source_key(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description="將 PoeCharm zh-rTW CSV 轉成 pob-cli JSON")
    parser.add_argument("--input", type=Path, required=True, help="PoeCharm/Data/Translate/zh-rTW 目錄")
    parser.add_argument("--output", type=Path, required=True, help="輸出的 JSON 路徑")
    parser.add_argument("--locale", default="zh-TW")
    parser.add_argument("--include", nargs="*", help="只轉換指定檔名，例如 GUI.csv Items_Weapons.txt.csv")
    args = parser.parse_args()

    if not args.input.is_dir():
        parser.error(f"找不到翻譯目錄：{args.input}")
    files = sorted(args.input.rglob("*.csv"))
    if args.include:
        wanted = set(args.include)
        files = [p for p in files if p.name in wanted or p.relative_to(args.input).as_posix() in wanted]
    if not files:
        parser.error("輸入目錄沒有 CSV 翻譯檔")

    translations: dict[str, dict[str, str]] = defaultdict(dict)
    source_files: dict[str, list[str]] = defaultdict(list)
    conflicts: list[dict[str, Any]] = []
    stats: dict[str, Any] = {"files": 0, "rows": 0, "by_category": defaultdict(int), "encodings": {}}

    for path in files:
        rows, encoding = read_rows(path)
        cat = category(path.name)
        rel = clean_source_key(path, args.input)
        stats["files"] += 1
        stats["rows"] += len(rows)
        stats["by_category"][cat] += len(rows)
        stats["encodings"][encoding] = stats["encodings"].get(encoding, 0) + 1
        for key, value in rows:
            old = translations[cat].get(key)
            if old is not None and old != value:
                conflicts.append({"category": cat, "key": key, "existing": old, "incoming": value, "source": rel})
                continue
            translations[cat][key] = value
            source_files[cat].append(rel)

    sorted_translations = {k: dict(sorted(v.items())) for k, v in sorted(translations.items())}
    # pob-cli 常見情境只需要給一個英文鍵查詢中文；保留分類資料之外，
    # 再建立扁平索引。相同翻譯不算衝突；不同翻譯則採用 items → mods →
    # game_data → tree → ui 的優先順序，完整差異仍保留在 conflicts。
    lookup: dict[str, str] = {}
    for cat in ("ui", "tree", "game_data", "mods", "items"):
        lookup.update(sorted_translations.get(cat, {}))
    output = {
        "schema_version": 1,
        "locale": args.locale,
        "source": {"name": "PoeCharm", "directory": str(args.input), "file_count": stats["files"]},
        "translations": sorted_translations,
        "lookup": dict(sorted(lookup.items())),
        "conflicts": conflicts,
        "metadata": {
            "generated_by": "import_poecharm_translations.py",
            "stats": {**stats, "by_category": dict(stats["by_category"])},
            "source_files": {k: sorted(set(v)) for k, v in source_files.items()},
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已輸出：{args.output}")
    print(f"檔案：{stats['files']}；翻譯列：{stats['rows']}；衝突：{len(conflicts)}")
    print("分類：" + ", ".join(f"{k}={v}" for k, v in sorted(stats["by_category"].items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
