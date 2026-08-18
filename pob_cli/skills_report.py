from __future__ import annotations

from typing import Any


def build_skills_payload(raw: dict[str, Any]) -> dict[str, Any]:
    selected = raw.get("selected_skill")
    sets = []
    for skill_set in raw.get("skill_sets") or []:
        groups = []
        for group in skill_set.get("groups") or []:
            gems = group.get("gems") or []
            for gem in gems:
                gem["isMainSkill"] = bool(selected and (gem.get("name") == selected or gem.get("skillId") == selected or gem.get("variantId") == selected))
            main = next((gem for gem in gems if gem.get("isMainSkill")), next((gem for gem in gems if not gem.get("isSupport")), None))
            group["mainGem"] = main.get("name") if main else None
            group["supportGems"] = [gem.get("name") for gem in gems if gem.get("isSupport")]
            groups.append(group)
        sets.append({"id": skill_set.get("id"), "title": skill_set.get("title"), "groups": groups})
    return {
        "schema_version": 1,
        "engine": raw.get("engine"),
        "tree": raw.get("tree"),
        "level": raw.get("level"),
        "class": raw.get("class"),
        "selected_skill": selected,
        "available_skills": raw.get("available_skills", []),
        "skill_sets": sets,
    }


def format_skills_markdown(payload: dict[str, Any]) -> str:
    lines = ["# PoB Skills and Support Gems", "", f"- Engine: `{payload.get('engine', '')}`", f"- PassiveTree: `{payload.get('tree', '')}`", f"- Selected skill: **{payload.get('selected_skill') or '(PoB default)'}**", ""]
    for skill_set in payload.get("skill_sets", []):
        lines.extend([f"## Skill Set {skill_set.get('id')}: {skill_set.get('title') or '(untitled)'}", "", "| Group | Slot | Enabled | Main skill | Support gems | Gem count |", "|---:|---|---|---|---|---:|"])
        for group in skill_set.get("groups", []):
            support = ", ".join(group.get("supportGems") or []) or "-"
            lines.append(f"| {group.get('index', '')} | `{group.get('slot', '')}` | {group.get('enabled')} | **{group.get('mainGem') or '-'}** | {support} | {len(group.get('gems') or [])} |")
        lines.append("")
        for group in skill_set.get("groups", []):
            lines.extend([f"### Group {group.get('index')}: {group.get('slot', '')}", "", "| # | Gem | Kind | Level | Quality | Enabled | Variant | Part | Stage | Mine | Tags | Minion context |", "|---:|---|---|---:|---:|---|---|---|---|---|---|"
])
            for gem in group.get("gems", []):
                kind = "Support" if gem.get("isSupport") else ("Main skill" if gem.get("isMainSkill") else gem.get("gemType", "active"))
                ctx = gem.get("minionContext") or {}
                context_text = ", ".join(f"{key}={value}" for key, value in ctx.items() if value is not None) or "-"
                part = gem.get("skillPart") if gem.get("skillPart") is not None else gem.get("skillPartCalcs")
                stage = gem.get("skillStageCount") if gem.get("skillStageCount") is not None else gem.get("skillStageCountCalcs")
                mine = gem.get("skillMineCount") if gem.get("skillMineCount") is not None else gem.get("skillMineCountCalcs")
                lines.append(f"| {gem.get('index', '')} | {gem.get('name', '')} | {kind} | {gem.get('level', '')} | {gem.get('quality', '')} | {gem.get('enabled')} | `{gem.get('variantId', '')}` | {part if part is not None else '-'} | {stage if stage is not None else '-'} | {mine if mine is not None else '-'} | {gem.get('tags') or '-'} | `{context_text}` |")
            lines.append("")
    return "\n".join(lines) + "\n"
