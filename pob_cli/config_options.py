from __future__ import annotations

from typing import Any


def format_config_options_markdown(payload: dict[str, Any]) -> str:
    lines = ["# PoB Config Options", "", f"- Skill: `{payload.get('selected_skill') or '(PoB default)'}`", f"- PassiveTree: `{payload.get('tree', '')}`", "", "| Variable | Type | Label | Default | Values |", "|---|---|---|---|---|"]
    for option in payload.get("config_options", []) or []:
        values = ", ".join(str(item.get("value")) for item in option.get("values", []))
        lines.append(f"| `{option.get('var', '')}` | `{option.get('type', '')}` | {option.get('label') or ''} | `{option.get('defaultState')}` | `{values}` |")
    lines.append("")
    lines.append(f"可見選項數量：**{len(payload.get('config_options', []) or [])}**")
    return "\n".join(lines) + "\n"
