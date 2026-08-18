from __future__ import annotations

from typing import Any

POWER_KEYS = [
    "TotalDPS", "TotalDotDPS", "TotalEHP", "Life", "EnergyShield", "Armour", "Evasion",
    "EffectiveAverageBlockChance", "EffectiveSpellBlockChance", "SpellSuppressionChance",
    "FireResist", "ColdResist", "LightningResist", "ChaosResist",
    "PhysicalMaximumHitTaken", "FireMaximumHitTaken", "ColdMaximumHitTaken",
    "LightningMaximumHitTaken", "ChaosMaximumHitTaken",
]


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def scalar_delta(before: dict[str, Any], after: dict[str, Any], keys: list[str] | None = None) -> dict[str, dict[str, float | None]]:
    result: dict[str, dict[str, float | None]] = {}
    for key in keys or POWER_KEYS:
        old = _number(before.get(key))
        new = _number(after.get(key))
        absolute = new - old if old is not None and new is not None else None
        percent = absolute / old * 100 if absolute is not None and old not in (None, 0) else None
        result[key] = {"before": old, "after": new, "absolute": absolute, "percent": percent}
    return result


def skill_context_digest(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {"selected_skill": None, "groups": []}
    groups = []
    for skill_set in payload.get("skill_sets") or []:
        for group in skill_set.get("groups") or []:
            gems = []
            for gem in group.get("gems") or []:
                gems.append({
                    "name": gem.get("name"), "skillId": gem.get("skillId"), "variantId": gem.get("variantId"),
                    "gemType": gem.get("gemType"), "level": gem.get("level"), "quality": gem.get("quality"),
                    "enabled": gem.get("enabled"), "skillPart": gem.get("skillPart"),
                    "skillStageCount": gem.get("skillStageCount"), "skillMineCount": gem.get("skillMineCount"),
                    "minionContext": gem.get("minionContext"),
                })
            groups.append({"set_id": skill_set.get("id"), "group_index": group.get("index"), "slot": group.get("slot"), "gems": gems})
    return {"selected_skill": payload.get("selected_skill"), "groups": groups}


def evaluate_hc_constraints(before: dict[str, Any], after: dict[str, Any], min_dps_gain_pct: float = 3.0, min_ehp_ratio: float = 0.95, min_attack_block: float = 70.0, min_spell_block: float = 70.0) -> dict[str, Any]:
    old = before.get("output", {})
    new = after.get("output", {})
    dps_old = _number(old.get("TotalDPS")) or 0.0
    dps_new = _number(new.get("TotalDPS")) or 0.0
    ehp_old = _number(old.get("TotalEHP")) or 0.0
    ehp_new = _number(new.get("TotalEHP")) or 0.0
    ab = _number(new.get("EffectiveAverageBlockChance")) or 0.0
    sb = _number(new.get("EffectiveSpellBlockChance")) or 0.0
    dps_pct = (dps_new / dps_old - 1.0) * 100 if dps_old else 0.0
    checks = {
        "dps_gain": {"actual_pct": dps_pct, "minimum_pct": min_dps_gain_pct, "pass": dps_pct >= min_dps_gain_pct},
        "ehp_ratio": {"actual": ehp_new / ehp_old if ehp_old else 0.0, "minimum": min_ehp_ratio, "pass": ehp_new >= ehp_old * min_ehp_ratio},
        "attack_block": {"actual": ab, "minimum": min_attack_block, "pass": ab >= min_attack_block},
        "spell_block": {"actual": sb, "minimum": min_spell_block, "pass": sb >= min_spell_block},
    }
    return {"passed": all(row["pass"] for row in checks.values()), "checks": checks}


def build_power_report(before: dict[str, Any], after: dict[str, Any], before_skills: dict[str, Any] | None = None, after_skills: dict[str, Any] | None = None) -> dict[str, Any]:
    before_context = skill_context_digest(before_skills)
    after_context = skill_context_digest(after_skills)
    return {
        "schema_version": 1,
        "engine": after.get("engine") or before.get("engine"),
        "tree": after.get("tree") or before.get("tree"),
        "selected_skill": after.get("selected_skill") or before.get("selected_skill"),
        "scalar_delta": scalar_delta(before.get("output", {}), after.get("output", {})),
        "skill_context": {"before": before_context, "after": after_context, "changed": before_context != after_context},
        "hc_constraints": evaluate_hc_constraints(before, after),
        "warnings": list(before.get("warnings") or []) + list(after.get("warnings") or []),
    }


def format_power_report_markdown(report: dict[str, Any]) -> str:
    lines = ["# PoB Power Report", "", f"- Engine: `{report.get('engine', '')}`", f"- PassiveTree: `{report.get('tree', '')}`", f"- Selected skill: **{report.get('selected_skill') or '-'}**", "", "| Metric | Before | After | Delta | Change |", "|---|---:|---:|---:|---:|"]
    for key, row in report.get("scalar_delta", {}).items():
        def f(value: Any) -> str:
            return "-" if value is None else f"{value:.2f}"
        pct = row.get("percent")
        pct_text = "-" if pct is None else f"{pct:+.2f}%"
        lines.append(f"| `{key}` | {f(row.get('before'))} | {f(row.get('after'))} | {f(row.get('absolute'))} | {pct_text} |")
    context = report.get("skill_context", {})
    hc = report.get("hc_constraints", {})
    lines.extend(["", f"- Skill context changed: `{context.get('changed', False)}`", f"- HC constraints passed: `{hc.get('passed', False)}`", "", "| HC check | Actual | Minimum | Pass |", "|---|---:|---:|---|"])
    for name, row in hc.get("checks", {}).items():
        actual = row.get("actual_pct", row.get("actual", "-"))
        minimum = row.get("minimum_pct", row.get("minimum", "-"))
        if isinstance(actual, float): actual = f"{actual:.2f}"
        if isinstance(minimum, float): minimum = f"{minimum:.2f}"
        lines.append(f"| `{name}` | {actual} | {minimum} | {row.get('pass')} |")
    return "\n".join(lines) + "\n"
