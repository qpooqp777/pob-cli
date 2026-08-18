from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .tree_candidates import calculate_tree_candidate


def load_candidate_matrix(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    text = source.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if source.suffix.lower() in {".jsonl", ".ndjson"}:
        raw = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        payload = json.loads(text)
        raw = payload.get("candidates", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw, list):
        raise ValueError("候選矩陣必須是 JSON 陣列，或包含 candidates 陣列的 JSON 物件")
    normalized = []
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            raise ValueError(f"候選 #{index} 必須是 JSON 物件")
        mastery = item.get("mastery", item.get("mastery_changes", [])) or []
        pairs = []
        for value in mastery:
            if isinstance(value, str):
                if "=" not in value:
                    raise ValueError(f"候選 #{index} Mastery 必須使用 nodeId=effectId")
                node, effect = value.split("=", 1)
                pairs.append((int(node), int(effect)))
            elif isinstance(value, dict):
                pairs.append((int(value["node_id"]), int(value["effect_id"])))
            else:
                pairs.append((int(value[0]), int(value[1])))
        normalized.append({
            "name": str(item.get("name", f"candidate-{index}")),
            "add_nodes": [int(value) for value in item.get("add_nodes", item.get("add", [])) or []],
            "remove_nodes": [int(value) for value in item.get("remove_nodes", item.get("remove", [])) or []],
            "mastery": pairs,
            "metadata": item.get("metadata", {}),
        })
    return normalized


def _score(report: dict[str, Any]) -> tuple[Any, ...]:
    power = report.get("power_report", {})
    scalar = power.get("scalar_delta", {})
    hc = power.get("hc_constraints", {})
    dps = scalar.get("TotalDPS", {}).get("percent", float("-inf")) or float("-inf")
    ehp = scalar.get("TotalEHP", {}).get("percent", float("-inf")) or float("-inf")
    max_hit = scalar.get("MaximumHitTaken", {}).get("percent", float("-inf")) or float("-inf")
    return (1 if hc.get("passed") else 0, dps, ehp, max_hit)


def calculate_tree_matrix(
    source: str | Path,
    matrix_file: str | Path,
    pob_root: str | Path,
    skill: str | None = None,
    config: dict[str, Any] | None = None,
    timeout: int = 180,
    limit: int | None = None,
) -> dict[str, Any]:
    candidates = load_candidate_matrix(matrix_file)
    if limit is not None:
        candidates = candidates[:limit]
    results = []
    failures = []
    for candidate in candidates:
        try:
            report = calculate_tree_candidate(
                source,
                pob_root,
                add_nodes=candidate["add_nodes"],
                remove_nodes=candidate["remove_nodes"],
                mastery=candidate["mastery"],
                skill=skill,
                config=config,
                timeout=timeout,
            )
            results.append({
                "name": candidate["name"],
                "metadata": candidate["metadata"],
                "operations": {k: candidate[k] for k in ("add_nodes", "remove_nodes", "mastery")},
                "tree_validation": report.get("tree_validation"),
                "tree_diff": report["tree_diff"],
                "power_report": report["power_report"],
            })
        except Exception as exc:
            failures.append({"name": candidate["name"], "error": str(exc), "operations": {k: candidate[k] for k in ("add_nodes", "remove_nodes", "mastery")}})
    results.sort(key=_score, reverse=True)
    for rank, result in enumerate(results, 1):
        result["rank"] = rank
        result["score"] = list(_score(result))
    return {
        "schema_version": 1,
        "source": str(source),
        "matrix": str(matrix_file),
        "candidate_count": len(candidates),
        "success_count": len(results),
        "failure_count": len(failures),
        "results": results,
        "failures": failures,
    }


def format_tree_matrix_markdown(payload: dict[str, Any]) -> str:
    lines = ["# PassiveTree Candidate Matrix", "", f"- Source: `{payload['source']}`", f"- Candidates: `{payload['candidate_count']}`", f"- Successful: `{payload['success_count']}`", f"- Failed validation/calculation: `{payload['failure_count']}`", "", "| Rank | Candidate | HC pass | DPS delta | EHP delta | Tree delta |", "|---:|---|---|---:|---:|---:|"]
    for result in payload["results"]:
        scalar = result["power_report"].get("scalar_delta", {})
        hc = result["power_report"].get("hc_constraints", {}).get("passed", False)
        dps = scalar.get("TotalDPS", {}).get("percent")
        ehp = scalar.get("TotalEHP", {}).get("percent")
        dps_text = "-" if dps is None else f"{dps:+.2f}%"
        ehp_text = "-" if ehp is None else f"{ehp:+.2f}%"
        tree_delta = result.get("tree_diff", {}).get("point_delta", 0)
        lines.append(f"| {result['rank']} | `{result['name']}` | `{hc}` | {dps_text} | {ehp_text} | {tree_delta:+d} |")
    if payload["failures"]:
        lines.extend(["", "## Failed candidates", ""])
        for failure in payload["failures"]:
            lines.append(f"- `{failure['name']}`: {failure['error']}")
    return "\n".join(lines) + "\n"
