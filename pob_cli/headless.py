from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


class HeadlessPobError(RuntimeError):
    pass


def _default_pob_root() -> Path | None:
    candidates = [
        os.environ.get("POB_ROOT"),
        "/home/ubuntu/PathOfBuilding",
        str(Path.home() / "PathOfBuilding"),
    ]
    for candidate in candidates:
        if candidate and (Path(candidate) / "src" / "HeadlessWrapper.lua").exists():
            return Path(candidate)
    return None


def run_pob_calcs(build_path: str | Path, pob_root: str | Path | None = None, timeout: int = 180, skill: str | None = None, config: dict[str, Any] | None = None, include_breakdown: bool = False, include_config_options: bool = False, include_skills: bool = False) -> dict[str, Any]:
    root = Path(pob_root) if pob_root else _default_pob_root()
    if root is None:
        raise HeadlessPobError("找不到 PathOfBuilding；請使用 --pob-root 或設定 POB_ROOT")
    root = root.resolve()
    src = root / "src"
    runner = Path(__file__).resolve().parents[1] / "pob_headless.lua"
    build = Path(build_path).resolve()
    if not runner.exists():
        raise HeadlessPobError(f"找不到 headless runner：{runner}")
    if not (src / "HeadlessWrapper.lua").exists():
        raise HeadlessPobError(f"不是有效的 PathOfBuilding 原始碼目錄：{root}")
    if not build.exists():
        raise HeadlessPobError(f"找不到 Build：{build}")

    env = os.environ.copy()
    env["LUA_PATH"] = f"{root / 'runtime' / 'lua' / '?.lua'};{root / 'runtime' / 'lua' / '?/init.lua'};;"
    bundled_runtime = Path(__file__).resolve().parents[1] / "runtime" / "linux"
    env["LUA_CPATH"] = f"{bundled_runtime / '?.so'};{root / 'runtime' / '?.so'};{root / 'runtime' / 'lua' / '?.so'};;"
    command = ["luajit", str(runner), str(build), str(src)]
    if skill or config or include_breakdown or include_config_options:
        command.append(skill or "")
    if config:
        command.append(json.dumps(config, ensure_ascii=False, separators=(",", ":")))
    elif include_breakdown or include_config_options:
        command.append("")
    if include_breakdown:
        command.append("breakdown")
    if include_config_options or include_skills:
        if len(command) < 6:
            command.append("")
        command.append("config-options" if include_config_options else "skills")
        if include_skills and include_config_options:
            command.append("skills")
    try:
        completed = subprocess.run(command, cwd=src, env=env, text=True, capture_output=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise HeadlessPobError("找不到 luajit；請安裝 LuaJIT 2.1 或設定 PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise HeadlessPobError(f"PoB headless 計算超時（>{timeout} 秒）") from exc

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    payload = None
    for line in reversed(lines):
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and ("ok" in candidate or "output" in candidate):
            payload = candidate
            break
    if payload is None:
        detail = (completed.stderr or completed.stdout)[-4000:]
        raise HeadlessPobError(f"PoB headless 沒有回傳 JSON（exit={completed.returncode}）\n{detail}")
    if not payload.get("ok", False):
        raise HeadlessPobError(str(payload.get("error", "PoB Lua 計算失敗")))
    if completed.returncode != 0:
        raise HeadlessPobError(f"PoB headless exit={completed.returncode}\n{completed.stderr[-2000:]}")
    return payload


def format_calcs(payload: dict[str, Any]) -> str:
    output = payload.get("output", {})
    keys = [
        ("Life", "生命"), ("EnergyShield", "能量護盾"), ("Armour", "護甲"),
        ("Evasion", "閃避"), ("FireResist", "火焰抗性"), ("ColdResist", "冰冷抗性"),
        ("LightningResist", "閃電抗性"), ("ChaosResist", "混沌抗性"),
        ("SpellSuppressionChance", "法術壓制"), ("TotalEHP", "總有效生命"),
        ("TotalDPS", "總 DPS"), ("TotalDotDPS", "總 DoT DPS"),
        ("MaximumHitTaken", "最大承受傷害"), ("PhysicalMaximumHitTaken", "物理最大承受傷害"),
        ("FireMaximumHitTaken", "火焰最大承受傷害"), ("ColdMaximumHitTaken", "冰冷最大承受傷害"),
        ("LightningMaximumHitTaken", "閃電最大承受傷害"), ("ChaosMaximumHitTaken", "混沌最大承受傷害"),
    ]
    lines = [f"PoB Lua 計算器｜PassiveTree {payload.get('tree', '?')}", "=" * 64]
    for key, label in keys:
        if key in output:
            value = output[key]
            if isinstance(value, float):
                value = f"{value:.2f}"
            lines.append(f"{label:<18}{value}")
    lines.append(f"\n完整 scalar output：{len(output)} 個欄位")
    return "\n".join(lines)
