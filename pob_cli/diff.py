from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _spec(path: str | Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    node = root.find("Tree/Spec")
    if node is None:
        raise ValueError(f"找不到 Tree/Spec：{path}")
    ids = {int(x) for x in node.attrib.get("nodes", "").replace("\n", ",").split(",") if x.strip()}
    effects = {x.strip() for x in node.attrib.get("masteryEffects", "").split(",") if x.strip()}
    return {"tree_version": node.attrib.get("treeVersion"), "class_id": node.attrib.get("classId"), "ascend_class_id": node.attrib.get("ascendClassId"), "nodes": ids, "mastery_effects": effects}


def compare_trees(current: str | Path, candidate: str | Path) -> dict[str, Any]:
    left = _spec(current)
    right = _spec(candidate)
    return {
        "current": str(current),
        "candidate": str(candidate),
        "tree_version": {"current": left["tree_version"], "candidate": right["tree_version"]},
        "class": {"current": left["class_id"], "candidate": right["class_id"]},
        "ascend_class": {"current": left["ascend_class_id"], "candidate": right["ascend_class_id"]},
        "added_nodes": sorted(right["nodes"] - left["nodes"]),
        "removed_nodes": sorted(left["nodes"] - right["nodes"]),
        "changed_mastery": {
            "added": sorted(right["mastery_effects"] - left["mastery_effects"]),
            "removed": sorted(left["mastery_effects"] - right["mastery_effects"]),
        },
        "point_delta": len(right["nodes"]) - len(left["nodes"]),
        "current_node_count": len(left["nodes"]),
        "candidate_node_count": len(right["nodes"]),
    }


def format_tree_diff(report: dict[str, Any]) -> str:
    lines = ["PassiveTree diff", "=" * 64]
    lines.append(f"Current：{report['current']}")
    lines.append(f"Candidate：{report['candidate']}")
    lines.append(f"Tree version：{report['tree_version']['current']} -> {report['tree_version']['candidate']}")
    lines.append(f"節點數：{report['current_node_count']} -> {report['candidate_node_count']} ({report['point_delta']:+d})")
    lines.append("新增節點：" + (", ".join(map(str, report["added_nodes"])) or "無"))
    lines.append("移除節點：" + (", ".join(map(str, report["removed_nodes"])) or "無"))
    lines.append("新增 Mastery：" + (", ".join(report["changed_mastery"]["added"]) or "無"))
    lines.append("移除 Mastery：" + (", ".join(report["changed_mastery"]["removed"]) or "無"))
    return "\n".join(lines)
