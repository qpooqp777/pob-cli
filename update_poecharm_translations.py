#!/usr/bin/env python3
"""Check PoeCharm for updates and regenerate pob-cli/locales/zh_TW.json.

This script only executes the local converter; it never executes code from
PoeCharm. It stores the last imported commit in a small state JSON file.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REPO = "https://github.com/Chuanhsing/PoeCharm.git"
HERE = Path(__file__).resolve().parent
CONVERTER = HERE / "import_poecharm_translations.py"


def run(*cmd: str, cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.strip()


def ensure_repo(repo_dir: Path, repo_url: str, branch: str) -> str:
    if not (repo_dir / ".git").is_dir():
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "--depth", "1", "--branch", branch, repo_url, str(repo_dir))
    else:
        run("git", "fetch", "--depth", "1", "origin", branch, cwd=repo_dir)
        run("git", "reset", "--hard", f"origin/{branch}", cwd=repo_dir)
    return run("git", "rev-parse", "HEAD", cwd=repo_dir)


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def atomic_replace(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    shutil.copyfile(src, tmp)
    tmp.replace(dst)


def main() -> int:
    parser = argparse.ArgumentParser(description="檢查 PoeCharm 更新並重新產生 pob-cli 繁中 JSON")
    parser.add_argument("--repo-url", default=DEFAULT_REPO)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--repo-dir", type=Path, default=HERE / ".cache" / "PoeCharm")
    parser.add_argument("--output", type=Path, default=HERE / "locales" / "zh_TW.json")
    parser.add_argument("--package-output", type=Path, default=HERE / "pob_cli" / "locales" / "zh_TW.json", help="同步更新套件內建翻譯檔；使用 --no-package-output 停用")
    parser.add_argument("--no-package-output", action="store_true")
    parser.add_argument("--state", type=Path, default=HERE / "locales" / ".poecharm_update.json")
    parser.add_argument("--force", action="store_true", help="即使 commit 未變更也重新產生")
    parser.add_argument("--check-only", action="store_true", help="只檢查來源，不改寫 JSON")
    args = parser.parse_args()

    commit = ensure_repo(args.repo_dir, args.repo_url, args.branch)
    state = load_state(args.state)
    old_commit = state.get("source_commit")
    changed = old_commit != commit or not args.output.exists()
    print(f"PoeCharm commit: {commit}")
    print(f"上次匯入 commit: {old_commit or '無'}")
    print(f"狀態: {'需要更新' if changed else '已是最新'}")

    if args.check_only or (not changed and not args.force):
        return 0

    with tempfile.TemporaryDirectory(prefix="pob-cli-poecharm-") as tmp:
        generated = Path(tmp) / "zh_TW.json"
        run("python3", str(CONVERTER), "--input", str(args.repo_dir / "Data" / "Translate" / "zh-rTW"), "--output", str(generated))
        atomic_replace(generated, args.output)
        if not args.no_package_output and args.package_output.resolve() != args.output.resolve():
            atomic_replace(generated, args.package_output)

    new_state = {
        "source_repo": args.repo_url,
        "source_branch": args.branch,
        "source_commit": commit,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "output": str(args.output),
        "package_output": None if args.no_package_output else str(args.package_output),
    }
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(new_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已更新：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
