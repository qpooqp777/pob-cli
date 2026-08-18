from __future__ import annotations

import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any


class TreeDataError(ValueError):
    pass


def _tree_path(pob_root: str | Path, tree_version: str) -> Path:
    root = Path(pob_root)
    candidates = [
        root / "src" / "TreeData" / tree_version / "tree.lua",
        root / "src" / "TreeData" / tree_version.replace("_", ".") / "tree.lua",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise TreeDataError(f"PoB TreeData 不存在：{tree_version}")


@lru_cache(maxsize=16)
def load_tree_data(pob_root: str, tree_version: str) -> dict[str, Any]:
    root = Path(pob_root)
    tree_path = _tree_path(root, tree_version)
    bridge = Path(__file__).with_name("_dump_treedata.lua")
    try:
        proc = subprocess.run(
            [os.environ.get("LUAJIT", "luajit"), str(bridge), str(tree_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise TreeDataError("找不到 LuaJIT，無法載入 PoB TreeData") from exc
    except subprocess.CalledProcessError as exc:
        raise TreeDataError(f"PoB TreeData 載入失敗：{exc.stderr.strip()}") from exc
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise TreeDataError("PoB TreeData 匯出結果不是有效 JSON") from exc
    data["_path"] = str(tree_path)
    return data


def _node_map(data: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for node_id, node in data.get("nodes", {}).items():
        try:
            result[int(node_id)] = node
        except (TypeError, ValueError):
            # PoB also stores a synthetic `root` node; it is not selectable in XML.
            continue
    return result


def _adjacency(nodes: dict[int, dict[str, Any]]) -> dict[int, set[int]]:
    graph = {node_id: set() for node_id in nodes}
    for node_id, node in nodes.items():
        for neighbor in list(node.get("out", [])) + list(node.get("in", [])):
            try:
                other = int(neighbor)
            except (TypeError, ValueError):
                continue
            if other in nodes:
                graph[node_id].add(other)
                graph[other].add(node_id)
    return graph


def validate_tree_selection(
    pob_root: str | Path,
    tree_version: str,
    selected_nodes: list[int],
    class_id: int | None = None,
    added_nodes: list[int] | None = None,
    removed_nodes: list[int] | None = None,
    mastery: list[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    data = load_tree_data(str(Path(pob_root).resolve()), tree_version)
    nodes = _node_map(data)
    selected = set(selected_nodes)
    added = list(dict.fromkeys(added_nodes or []))
    removed = list(dict.fromkeys(removed_nodes or []))
    unknown_selected = sorted(selected - set(nodes))
    unknown_added = sorted(set(added) - set(nodes))
    if unknown_added:
        raise TreeDataError(f"新增 passive node 不存在於 PoB TreeData：{unknown_added}")
    unknown_removed = sorted(set(removed) - set(nodes))
    # Existing unknown IDs can be Cluster Jewel or other PoB extension nodes.
    # They remain reported as external nodes and may be removed from the XML.
    known_selected = selected & set(nodes)
    special_existing = {
        node_id for node_id in known_selected
        if node_id not in set(added)
        and (nodes[node_id].get("isJewelSocket", False)
             or (not nodes[node_id].get("in") and nodes[node_id].get("classStartIndex") is None))
    }
    connectivity_nodes = known_selected - special_existing

    graph = _adjacency(nodes)
    if class_id is None:
        roots = [node_id for node_id, node in nodes.items() if node.get("classStartIndex") is not None]
    else:
        roots = [node_id for node_id, node in nodes.items() if node.get("classStartIndex") == class_id]
    selected_roots = sorted(set(roots) & connectivity_nodes)
    reachable: set[int] = set(selected_roots)
    stack = list(selected_roots)
    while stack:
        current = stack.pop()
        for neighbor in graph.get(current, ()) & connectivity_nodes:
            if neighbor not in reachable:
                reachable.add(neighbor)
                stack.append(neighbor)
    disconnected = sorted(connectivity_nodes - reachable)
    added_disconnected = sorted(set(added) & set(disconnected))
    invalid_mastery = []
    for node_id, effect_id in mastery or []:
        node = nodes.get(node_id)
        if node is None or node_id not in selected:
            invalid_mastery.append({"node_id": node_id, "effect_id": effect_id, "reason": "node_not_selected"})
        elif not node.get("isMastery", False):
            invalid_mastery.append({"node_id": node_id, "effect_id": effect_id, "reason": "node_is_not_mastery"})

    valid = not disconnected and not invalid_mastery and bool(selected_roots or not known_selected)
    return {
        "valid": valid,
        "tree_version": tree_version,
        "tree_data_path": data["_path"],
        "class_id": class_id,
        "root_nodes": sorted(roots),
        "selected_roots": selected_roots,
        "selected_node_count": len(selected),
        "known_selected_node_count": len(known_selected),
        "external_selected_nodes": sorted(set(unknown_selected) | special_existing),
        "external_removed_nodes": unknown_removed,
        "special_tree_nodes": sorted(special_existing),
        "known_node_count": len(nodes),
        "disconnected_nodes": disconnected,
        "added_disconnected_nodes": added_disconnected,
        "invalid_mastery": invalid_mastery,
        "added_nodes": added,
        "removed_nodes": removed,
        "errors": ([f"節點未由職業起點連通：{disconnected}"] if disconnected else [])
        + ([f"Mastery 設定不合法：{invalid_mastery}"] if invalid_mastery else []),
    }


def validate_mastery_effects(
    pob_root: str | Path,
    tree_version: str,
    selected_nodes: list[int],
    mastery: list[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    return validate_tree_selection(pob_root, tree_version, selected_nodes, mastery=mastery)
