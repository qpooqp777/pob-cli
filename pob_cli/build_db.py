from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "build_db.json"
TREE_FILE = Path(__file__).resolve().with_name("tree.lua")

GEM_META = {
    "Toxic Rain": ("ToxicRain", "ToxicRain", "Metadata/Items/Gems/SkillGemToxicRain"),
    "Vicious Projectiles": ("SupportViciousProjectiles", "SupportViciousProjectiles", "Metadata/Items/Gems/SupportGemPhysicalProjectileAttackDamage"),
    "Void Manipulation": ("SupportVoidManipulation", "SupportVoidManipulation", "Metadata/Items/Gems/SupportGemVoidManipulation"),
    "Swift Affliction": ("SupportSwiftAffliction", "SupportSwiftAffliction", "Metadata/Items/Gems/SupportGemRapidDecay"),
    "Mirage Archer": ("SupportMirageArcher", "SupportMirageArcher", "Metadata/Items/Gems/SupportGemMirageArcher"),
    "Efficacy": ("SupportEfficacy", "SupportEfficacy", "Metadata/Items/Gems/SupportGemEfficacy"),
    "Empower": ("SupportEmpower", "SupportEmpower", "Metadata/Items/Gems/SkillGemSupportEmpower"),
    "Despair": ("Despair", "Despair", "Metadata/Items/Gems/SkillGemVulnerability"),
    "Withering Step": ("WitheringStep", "WitheringStep", "Metadata/Items/Gems/SkillGemWitheringStep"),
    "Grace": ("Grace", "Grace", "Metadata/Items/Gems/SkillGemGrace"),
    "Malevolence": ("Malevolence", "Malevolence", "Metadata/Items/Gems/SkillGemDamageOverTimeAura"),
    "Defiance Banner": ("DefianceBanner", "DefianceBanner", "Metadata/Items/Gems/SkillGemDefianceBanner"),
    "Steelskin": ("Steelskin", "Steelskin", "Metadata/Items/Gems/SkillGemSteelskin"),
    "Dash": ("Dash", "Dash", "Metadata/Items/Gems/SkillGemDash"),
    "Lifetap": ("SupportLifetap", "SupportLifetap", "Metadata/Items/Gems/SupportGemLifetap"),
    "Caustic Arrow": ("CausticArrow", "CausticArrow", "Metadata/Items/Gems/SkillGemCausticArrow")
}


def load_db(path: str | Path = DEFAULT_DB) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find_build(db: dict[str, Any], build_id: str) -> dict[str, Any]:
    for build in db.get("builds", []):
        if build.get("id") == build_id:
            return build
    raise KeyError(f"找不到流派：{build_id}")


def tree_nodes_by_name() -> dict[str, int]:
    text = TREE_FILE.read_text(encoding="utf-8", errors="ignore")
    result: dict[str, int] = {}
    for match in re.finditer(r"\n\s+\[(\d+)\]= \{(.*?)(?=\n\s+\[\d+\]= \{|\n\s+\},\n\s+\[\d+\]=)", text, re.S):
        name = re.search(r'\["name"\]= "([^"]+)"', match.group(2))
        if name:
            result.setdefault(name.group(1), int(match.group(1)))
    return result


def resolve_nodes(names: list[str]) -> tuple[list[int], list[str]]:
    mapping = tree_nodes_by_name()
    ids, missing = [], []
    for name in names:
        if name in mapping:
            ids.append(mapping[name])
        else:
            missing.append(name)
    return ids, missing


def stage_report(build: dict[str, Any], stage: str) -> str:
    data = build["stages"][stage]
    lines = [f"{build['name_zhTW']}｜{data['label_zhTW']}", "=" * 72]
    lines.append(f"等級：{data['level_range'][0]}–{data['level_range'][1]}")
    lines.append("\n天賦方向：")
    lines.extend(f"- {x}" for x in data["tree_strategy"])
    ids, missing = resolve_nodes(data["key_nodes"])
    lines.append("\n核心天賦：" + "、".join(data["key_nodes"]))
    lines.append("PoB 節點 ID：" + ",".join(map(str, ids)) if ids else "PoB 節點 ID：無")
    if missing:
        lines.append("未在目前 tree.lua 找到：" + "、".join(missing))
    lines.append("\n裝備清單：")
    for item in sorted(data["gear"], key=lambda x: x.get("priority", 99)):
        lines.append(f"{item['priority']}. {item['slot']}｜{item['base']}｜" + "、".join(item["target_mods"]))
    lines.append("\n技能寶石：")
    for group in data["skills"]:
        lines.append(f"{group['group']}：" + " + ".join(group["gems"]))
    lines.append("\n階段目標：" + "；".join(data["milestones"]))
    return "\n".join(lines)


def _item_template(stage: str, slot: str) -> str:
    templates = {
        "武器": "Rarity: RARE\nToxic Rain Bow\nSpine Bow\n+2 to Level of Socketed Bow Gems\n+1 to Level of Socketed Gems\n20% increased Attack Speed\n+80 to maximum Life",
        "箭袋": "Rarity: RARE\nToxic Rain Quiver\nBroadhead Arrow Quiver\n+80 to maximum Life\n20% increased Attack Speed\n+20% to Chaos Damage over Time Multiplier",
        "胸甲": "Rarity: RARE\nToxic Rain Body Armour\nZodiac Leather\n+120 to maximum Life\n+20% to Suppression Chance\n+30% to Fire Resistance",
        "鞋子": "Rarity: RARE\nToxic Rain Boots\nTwo-Toned Boots\n30% increased Movement Speed\n+90 to maximum Life\n+20% to Suppression Chance",
        "護符": "Rarity: RARE\nToxic Rain Amulet\nJade Amulet\n+1 to Level of all Skill Gems\n+70 to maximum Life\n+20% to Chaos Damage over Time Multiplier",
    }
    return templates.get(slot, f"Rarity: RARE\n{stage} {slot}\n+80 to maximum Life\n+30% to Fire Resistance")


def export_pob(build: dict[str, Any], stage: str, output: str | Path) -> tuple[Path, list[str]]:
    data = build["stages"][stage]
    export = build["pob_export"]
    ids, missing = resolve_nodes(data["key_nodes"])
    template = ROOT / "attached_build.xml"
    if template.exists():
        root = ET.parse(template).getroot()
        for child in list(root):
            if child.tag not in {"Build", "Tree", "Skills"}:
                root.remove(child)
        build_node = root.find("Build")
        build_node.attrib.update({
            "level": str(data["level_range"][1]), "className": build["class"],
            "ascendClassName": build["ascendancy"], "label": f"{build['name_zhTW']} - {data['label_zhTW']}",
            "targetVersion": "3_0", "mainSocketGroup": "1", "viewMode": "TREE"
        })
        root.remove(root.find("Tree"))
    else:
        root = ET.Element("PathOfBuilding")
        ET.SubElement(root, "Build", {
            "level": str(data["level_range"][1]), "className": build["class"],
            "ascendClassName": build["ascendancy"], "label": f"{build['name_zhTW']} - {data['label_zhTW']}",
            "targetVersion": "3_0", "mainSocketGroup": "1", "viewMode": "TREE"
        })
    tree = ET.SubElement(root, "Tree", {"activeSpec": "1"})
    ET.SubElement(tree, "Spec", {
        "treeVersion": export["tree_version"], "classId": str(export["class_id"]),
        "ascendClassId": str(export["ascend_class_id"]), "nodes": ",".join(map(str, ids))
    })
    skills = root.find("Skills")
    if skills is None:
        skills = ET.SubElement(root, "Skills", {"sortGemsByDPSField": "CombinedDPS", "activeSkillSet": "1", "sortGemsByDPS": "true", "defaultGemQuality": "nil", "defaultGemLevel": "normalMaximum", "showSupportGemTypes": "ALL", "showLegacyGems": "false"})
    skill_set = skills.find("SkillSet")
    if skill_set is None:
        skill_set = ET.SubElement(skills, "SkillSet", {"id": "1"})
    for child in list(skill_set):
        skill_set.remove(child)
    group = data["skills"][0]
    skill = ET.SubElement(skill_set, "Skill", {"slot": "Body Armour", "mainActiveSkill": "1", "mainActiveSkillCalcs": "1", "enabled": "true", "includeInFullDPS": "nil", "label": ""})
    for gem in group["gems"]:
        if gem not in GEM_META:
            continue
        skill_id, variant_id, gem_id = GEM_META[gem]
        ET.SubElement(skill, "Gem", {"skillId": skill_id, "variantId": variant_id, "gemId": gem_id, "nameSpec": gem, "level": "20", "quality": "20", "enabled": "true", "enableGlobal1": "true", "enableGlobal2": "true", "count": "nil"})
    # PoB 會依 section 順序初始化；Tree 應位於 Skills 之前。
    root.remove(tree)
    root.insert(1, tree)
    items = ET.SubElement(root, "Items")
    item_id = 1
    for item in data["gear"]:
        if item["slot"] not in {"武器", "箭袋", "胸甲", "鞋子", "護符"}:
            continue
        ET.SubElement(items, "Item", {"id": str(item_id), "label": item["slot"]}).text = _item_template(stage, item["slot"])
        item_id += 1
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="\t")
    out.write_text(ET.tostring(root, encoding="unicode") + "\n", encoding="utf-8")
    return out, missing
