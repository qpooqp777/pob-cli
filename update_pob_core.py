#!/usr/bin/env python3
"""Check and optionally update the local PathOfBuildingCommunity core.

Default mode is read-only. --apply requires a clean Git worktree and checks
out the latest GitHub release tag, keeping a recovery record in JSON.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_API = "https://api.github.com/repos/PathOfBuildingCommunity/PathOfBuilding/releases/latest"


def run(*cmd: str, cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(f"命令失敗：{' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def latest_release(api_url: str) -> dict[str, Any]:
    request = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json", "User-Agent": "pob-cli"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("draft") or data.get("prerelease"):
        raise RuntimeError("GitHub latest release 回傳 draft/prerelease，請檢查 API")
    return data


def manifest_version(source_dir: Path) -> str | None:
    path = source_dir / "manifest.xml"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    import re
    m = re.search(r'<Version\s+number="([^"]+)"', text)
    return m.group(1) if m else None


def git_version(source_dir: Path) -> str:
    return run("git", "describe", "--tags", "--always", "--dirty", cwd=source_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="檢查或更新 Path of Building Community Fork PoE1 核心")
    parser.add_argument("--source-dir", type=Path, default=Path("/home/ubuntu/PathOfBuilding"))
    parser.add_argument("--api-url", default=DEFAULT_API)
    parser.add_argument("--state", type=Path, default=Path(".pob_core_update.json"))
    parser.add_argument("--apply", action="store_true", help="切換本機 Git 核心到最新穩定 release；預設不修改")
    parser.add_argument("--force", action="store_true", help="忽略 dirty worktree，危險，僅適合已自行備份者")
    args = parser.parse_args()
    source = args.source_dir.resolve()
    if not (source / ".git").is_dir():
        raise SystemExit(f"找不到 Git 版 PoB 核心：{source}")

    release = latest_release(args.api_url)
    tag = release.get("tag_name", "")
    remote_version = tag.removeprefix("v")
    local_manifest = manifest_version(source)
    local_git = git_version(source)
    print(f"PoB 本機 manifest：{local_manifest or '未知'}")
    print(f"PoB 本機 Git：{local_git}")
    print(f"GitHub 最新穩定 release：{tag}（{release.get('published_at', '未知日期')}）")
    up_to_date = local_manifest == remote_version and not local_git.endswith("-dirty")
    print(f"狀態：{'已是最新' if up_to_date else '有更新或版本狀態不一致'}")

    if not args.apply:
        return 0
    status = run("git", "status", "--porcelain", cwd=source)
    if status and not args.force:
        raise SystemExit("PoB 原始碼工作區有未提交變更；為避免覆蓋，未執行更新。請先提交／備份，或明確使用 --force。")

    old_commit = run("git", "rev-parse", "HEAD", cwd=source)
    run("git", "fetch", "--tags", "origin", cwd=source)
    run("git", "checkout", "--detach", tag, cwd=source)
    new_commit = run("git", "rev-parse", "HEAD", cwd=source)
    state = {
        "source_dir": str(source),
        "previous_commit": old_commit,
        "updated_commit": new_commit,
        "release_tag": tag,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已切換 PoB 核心：{old_commit[:12]} → {new_commit[:12]}（{tag}）")
    print("注意：若要復原，使用 state JSON 的 previous_commit 執行 git checkout。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
