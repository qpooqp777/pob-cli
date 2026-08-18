from __future__ import annotations

from typing import Any

DAMAGE_SECTIONS = ("Physical", "Fire", "Cold", "Lightning", "Chaos", "AverageHit", "AverageBurstDamage")
DEFENCE_SECTIONS = (
    "Life", "EnergyShield", "Mana", "Armour", "Evasion", "Ward", "BlockChance", "SpellBlockChance", "AttackDodgeChance", "SpellDodgeChance", "SpellSuppressionChance", "FireResist", "ColdResist", "LightningResist", "ChaosResist", "PhysicalDamageReduction", "FireDamageReduction", "ColdDamageReduction", "LightningDamageReduction", "ChaosDamageReduction", "TotalEHP", "PhysicalMaximumHitTaken", "FireMaximumHitTaken", "ColdMaximumHitTaken", "LightningMaximumHitTaken", "ChaosMaximumHitTaken", "totalTakenHit", "PhysicalTakenHit", "FireTakenHit", "ColdTakenHit", "LightningTakenHit", "ChaosTakenHit", "PhysicalTakenHitMult", "FireTakenHitMult", "ColdTakenHitMult", "LightningTakenHitMult", "ChaosTakenHitMult", "PhysicalTakenDotMult", "FireTakenDotMult", "ColdTakenDotMult", "LightningTakenDotMult", "ChaosTakenDotMult", "PhysicalDotEHP", "FireDotEHP", "ColdDotEHP", "LightningDotEHP", "ChaosDotEHP", "PhysicalTotalPool", "FireTotalPool", "ColdTotalPool", "LightningTotalPool", "ChaosTotalPool",
)


def _sort_keys(value: dict[str, Any]) -> list[str]:
    return sorted(value, key=lambda key: (0, int(key)) if str(key).isdigit() else (1, str(key)))


def _sections_for_metric(breakdown: dict[str, Any], metric: str) -> list[str]:
    metric = metric.lower().replace("_", "-")
    if metric in {"all", "full"}:
        return sorted(breakdown)
    if metric in {"dps", "damage", "offence", "offense"}:
        return [key for key in DAMAGE_SECTIONS if key in breakdown]
    if metric in {"defence", "defense", "ehp", "survival"}:
        return [key for key in DEFENCE_SECTIONS if key in breakdown]
    aliases = {"average-hit": "AverageHit", "burst": "AverageBurstDamage", "physical": "Physical", "fire": "Fire", "cold": "Cold", "lightning": "Lightning", "chaos": "Chaos"}
    key = aliases.get(metric, metric)
    if key not in breakdown:
        raise ValueError(f"找不到 breakdown metric：{metric}；可用：all、dps、defence、AverageHit、Cold、Fire、Lightning、Chaos")
    return [key]


def build_breakdown_payload(raw: dict[str, Any], metric: str = "all") -> dict[str, Any]:
    breakdown = raw.get("breakdown") or {}
    if not isinstance(breakdown, dict):
        raise ValueError("PoB 沒有回傳可用的 breakdown object")
    sections = _sections_for_metric(breakdown, metric)
    output = raw.get("output") or {}
    summary_keys = ["TotalDPS", "TotalDotDPS", "AverageHit", "AverageBurstDamage", "TotalEHP", "PhysicalMaximumHitTaken", "FireMaximumHitTaken", "ColdMaximumHitTaken", "LightningMaximumHitTaken", "ChaosMaximumHitTaken"]
    return {
        "schema_version": 1,
        "engine": raw.get("engine"),
        "tree": raw.get("tree"),
        "level": raw.get("level"),
        "class": raw.get("class"),
        "selected_skill": raw.get("selected_skill"),
        "metric": metric,
        "available_sections": sorted(breakdown),
        "summary": {key: output[key] for key in summary_keys if key in output},
        "sections": {key: breakdown[key] for key in sections},
    }


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, (dict, list)):
        return "[structured]"
    return str(value)


def format_breakdown_markdown(payload: dict[str, Any]) -> str:
    lines = ["# PoB Damage Breakdown", "", f"- Engine: `{payload.get('engine', '')}`", f"- PassiveTree: `{payload.get('tree', '')}`", f"- Skill: `{payload.get('selected_skill') or '(PoB default)'}`", f"- Metric: `{payload.get('metric', 'all')}`", "", "## Summary", "", "| Field | Value |", "|---|---:|"]
    for key, value in payload.get("summary", {}).items():
        lines.append(f"| `{key}` | {_format_value(value)} |")
    for name, section in payload.get("sections", {}).items():
        lines.extend(["", f"## `{name}`", ""])
        if isinstance(section, dict):
            text_items = [(key, value) for key, value in section.items() if str(key).isdigit()]
            for key, value in sorted(text_items, key=lambda pair: int(pair[0])):
                lines.append(f"{value}  ")
            for table_name in ("damageTypes", "rowList", "slots", "reservations"):
                rows = section.get(table_name)
                if isinstance(rows, dict) and rows:
                    lines.extend(["", f"### {table_name}", "", "| Key | Values |", "|---|---|"])
                    for row_key in _sort_keys(rows):
                        row = rows[row_key]
                        if isinstance(row, dict):
                            rendered = "; ".join(f"`{k}`={_format_value(v)}" for k, v in row.items())
                        else:
                            rendered = _format_value(row)
                        lines.append(f"| `{row_key}` | {rendered} |")
        elif isinstance(section, list):
            lines.extend(str(value) + "  " for value in section)
        else:
            lines.append(_format_value(section))
    return "\n".join(lines) + "\n"
