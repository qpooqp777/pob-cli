from __future__ import annotations

from typing import Any

from .core import Build, defensive_report


def build_analysis_payload(build: Build, source: str, prices: list[dict[str, Any]] | None = None, calculation: dict[str, Any] | None = None, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source": source,
        "build": {
            "name": build.name,
            "level": build.level,
            "class": build.class_name,
            "stats": build.stats,
            "items": [
                {"slot": item.slot, "name": item.name, "mods": item.mods, "text": item.text}
                for item in build.items
            ],
        },
        "defence_checks": defensive_report(build),
        "prices": prices or [],
        "official_calculation": calculation,
        "warnings": warnings or [],
    }


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    if value is None:
        return "-"
    return str(value)


def format_analysis_markdown(payload: dict[str, Any]) -> str:
    build = payload.get("build", {})
    lines = [
        "# PoB Build Analysis",
        "",
        f"- Source: `{payload.get('source', '')}`",
        f"- Build: **{build.get('name', 'Unknown')}**",
        f"- Class: `{build.get('class', 'Unknown')}`",
        f"- Level: `{build.get('level', 'Unknown')}`",
        "",
        "## Build Stats",
        "",
        "| Stat | Value |",
        "|---|---:|",
    ]
    for key, value in (build.get("stats") or {}).items():
        lines.append(f"| `{key}` | {_fmt(value)} |")

    lines.extend(["", "## Defence Checks", "", "| Check | Current | Target | Gap | Status |", "|---|---:|---:|---:|---|"])
    for row in payload.get("defence_checks", []):
        lines.append(f"| {row.get('name', '')} | {row.get('value', '')} | {row.get('target', '')} | {row.get('gap', '')} | {row.get('status', '')} |")

    lines.extend(["", "## Equipment", ""])
    for item in build.get("items", []):
        lines.extend([f"### `{item.get('slot', 'Unknown')}` — {item.get('name') or 'Unnamed'}", ""])
        text = item.get("text") or ""
        if text:
            lines.append("```text")
            lines.extend(text.splitlines()[:80])
            lines.extend(["```", ""])

    calc = payload.get("official_calculation")
    if calc:
        output = calc.get("output", {})
        lines.extend(["## Official PoB Calculation", "", f"- Engine: `{calc.get('engine', '')}`", f"- PassiveTree: `{calc.get('tree', '')}`", f"- Selected skill: `{calc.get('selected_skill') or '(PoB default)'}`", "", "| Scalar | Value |", "|---|---:|"])
        preferred = ["Life", "EnergyShield", "Armour", "Evasion", "FireResist", "ColdResist", "LightningResist", "ChaosResist", "BlockChance", "SpellBlockChance", "SpellSuppressionChance", "TotalEHP", "TotalDPS", "TotalDotDPS", "MaximumHitTaken", "PhysicalMaximumHitTaken", "FireMaximumHitTaken", "ColdMaximumHitTaken", "LightningMaximumHitTaken", "ChaosMaximumHitTaken"]
        keys = [key for key in preferred if key in output] + [key for key in sorted(output) if key not in preferred][:20]
        for key in keys:
            lines.append(f"| `{key}` | {_fmt(output[key])} |")
        lines.append("")

    if payload.get("prices"):
        lines.extend(["## Prices", "", "| Query | Name | League | Chaos | Divine | Found |", "|---|---|---|---:|---:|---|"])
        for row in payload["prices"]:
            lines.append(f"| {row.get('query', '')} | {row.get('name', '')} | {row.get('league', '')} | {_fmt(row.get('chaos_value'))} | {_fmt(row.get('divine_value'))} | {row.get('found', False)} |")

    if payload.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"> {warning}" for warning in payload["warnings"])
    return "\n".join(lines) + "\n"
