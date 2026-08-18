from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .diff import compare_trees
from .headless import run_pob_calcs
from .power_report import build_power_report
from .treedata import TreeDataError, validate_tree_selection

_SPEC_RE = re.compile(r"<Spec\b([^>]*)>", re.S)
_ATTR_RE = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9_]*)=(?P<quote>[\"'])(?P<value>.*?)(?P=quote)")


def _parse_spec(text: str) -> tuple[dict[str, str], str, re.Match[str]]:
    match = _SPEC_RE.search(text)
    if not match:
        raise ValueError("PoB XML 找不到 Tree/Spec")
    attrs: dict[str, str] = {}
    for item in _ATTR_RE.finditer(match.group(1)):
        attrs[item.group("key")] = item.group("value")
    if "nodes" not in attrs:
        raise ValueError("PoB Tree/Spec 缺少 nodes")
    return attrs, match.group(1), match


def _node_ids(value: str) -> list[int]:
    out: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if token:
            if not token.isdigit():
                raise ValueError(f"無效 passive node ID：{token}")
            out.append(int(token))
    return out


def _mastery_pairs(value: str) -> list[tuple[int, int]]:
    pairs = []
    for token in value.split(",") if value else []:
        if "=" not in token:
            raise ValueError(f"Mastery 格式必須是 nodeId=effectId：{token}")
        node, effect = token.split("=", 1)
        if not node.strip().isdigit() or not effect.strip().isdigit():
            raise ValueError(f"無效 Mastery node/effect：{token}")
        pairs.append((int(node), int(effect)))
    return pairs


def modify_tree_xml(source: str | Path, add_nodes: list[int] | None = None, remove_nodes: list[int] | None = None, mastery: list[tuple[int, int]] | None = None) -> tuple[str, dict[str, Any]]:
    path = Path(source)
    text = path.read_text(encoding="utf-8")
    attrs, raw_attrs, match = _parse_spec(text)
    original_nodes = _node_ids(attrs["nodes"])
    node_set = set(original_nodes)
    add = list(dict.fromkeys(add_nodes or []))
    remove = list(dict.fromkeys(remove_nodes or []))
    missing_remove = [node for node in remove if node not in node_set]
    if missing_remove:
        raise ValueError(f"不能移除未配置的 passive node：{missing_remove}")
    final_nodes = [node for node in original_nodes if node not in set(remove)]
    final_set = set(final_nodes)
    for node in add:
        if node not in final_set:
            final_nodes.append(node)
            final_set.add(node)
    final_mastery = dict()
    mastery_text = attrs.get("masteryEffects", "")
    for node, effect in re.findall(r"\{(\d+),(\d+)\}", mastery_text):
        final_mastery[int(node)] = int(effect)
    for node, effect in mastery or []:
        if node not in set(final_nodes):
            raise ValueError(f"Mastery node {node} 不在候選已配置 nodes 中")
        final_mastery[node] = effect
    new_nodes = ",".join(str(node) for node in final_nodes)
    new_mastery = ",".join(f"{{{node},{effect}}}" for node, effect in final_mastery.items() if node in set(final_nodes))
    replacements = {"nodes": new_nodes, "masteryEffects": new_mastery}
    new_raw = raw_attrs
    for key, value in replacements.items():
        pattern = re.compile(rf"\b{key}=(\"|').*?\1", re.S)
        if pattern.search(new_raw):
            new_raw = pattern.sub(lambda m, k=key, v=value: f'{k}="{v}"', new_raw, count=1)
        else:
            new_raw += f' {key}="{value}"'
    output = text[:match.start(1)] + new_raw + text[match.end(1):]
    metadata = {
        "tree_version": attrs.get("treeVersion"),
        "added_nodes": add,
        "removed_nodes": remove,
        "mastery_changes": [{"node_id": node, "effect_id": effect} for node, effect in mastery or []],
        "before_node_count": len(original_nodes),
        "after_node_count": len(final_nodes),
    }
    return output, metadata


def calculate_tree_candidate(source: str | Path, pob_root: str | Path, add_nodes: list[int] | None = None, remove_nodes: list[int] | None = None, mastery: list[tuple[int, int]] | None = None, skill: str | None = None, config: dict[str, Any] | None = None, output: str | Path | None = None, timeout: int = 180, validate_connectivity: bool = True) -> dict[str, Any]:
    source_text = Path(source).read_text(encoding="utf-8")
    source_attrs, _, _ = _parse_spec(source_text)
    original_nodes = _node_ids(source_attrs["nodes"])
    candidate_xml, tree_change = modify_tree_xml(source, add_nodes, remove_nodes, mastery)
    candidate_attrs, _, _ = _parse_spec(candidate_xml)
    candidate_nodes = _node_ids(candidate_attrs["nodes"])
    connectivity = None
    baseline_connectivity = None
    if validate_connectivity:
        class_id = int(source_attrs["classId"]) if source_attrs.get("classId", "").isdigit() else None
        baseline_connectivity = validate_tree_selection(
            pob_root, source_attrs.get("treeVersion", ""), original_nodes, class_id=class_id
        )
        effective_added = sorted(set(candidate_nodes) - set(original_nodes))
        effective_removed = sorted(set(original_nodes) - set(candidate_nodes))
        candidate_connectivity = validate_tree_selection(
            pob_root,
            source_attrs.get("treeVersion", ""),
            candidate_nodes,
            class_id=class_id,
            added_nodes=effective_added,
            removed_nodes=effective_removed,
            mastery=mastery,
        )
        baseline_disconnected = set(baseline_connectivity["disconnected_nodes"])
        new_disconnected = sorted(set(candidate_connectivity["disconnected_nodes"]) - baseline_disconnected)
        candidate_connectivity["baseline_disconnected_nodes"] = sorted(baseline_disconnected)
        candidate_connectivity["new_disconnected_nodes"] = new_disconnected
        candidate_connectivity["valid"] = not new_disconnected and not candidate_connectivity["added_disconnected_nodes"] and not candidate_connectivity["invalid_mastery"]
        candidate_connectivity["errors"] = ([f"候選新增未連通節點：{new_disconnected}"] if new_disconnected else [])
        candidate_connectivity["warnings"] = ([f"基準 Build 已存在未連通節點：{sorted(baseline_disconnected)}"] if baseline_disconnected else [])
        connectivity = candidate_connectivity
        if not connectivity["valid"]:
            raise TreeDataError("；".join(connectivity["errors"]) or "候選天賦樹未通過 TreeData 驗證")
    before = run_pob_calcs(source, pob_root, skill=skill, config=config, include_skills=True, timeout=timeout)
    candidate_path = Path(output) if output else Path(source).with_suffix(".candidate.xml")
    candidate_path.write_text(candidate_xml, encoding="utf-8")
    try:
        after = run_pob_calcs(candidate_path, pob_root, skill=skill, config=config, include_skills=True, timeout=timeout)
        power = build_power_report(before, after, before, after)
        tree_diff = compare_trees(str(source), str(candidate_path))
        return {"schema_version": 1, "candidate_xml": str(candidate_path), "tree_change": tree_change, "tree_diff": tree_diff, "tree_validation": connectivity, "baseline_tree_validation": baseline_connectivity, "power_report": power, "before": before, "after": after}
    finally:
        if output is None:
            candidate_path.unlink(missing_ok=True)
