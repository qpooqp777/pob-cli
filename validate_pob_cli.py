#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "validation_report.json"


def run(name: str, cmd: list[str], timeout: int = 60) -> dict:
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return {"name": name, "status": "PASS" if p.returncode == 0 else "FAIL", "returncode": p.returncode, "output": p.stdout[-4000:]}
    except subprocess.TimeoutExpired as exc:
        return {"name": name, "status": "TIMEOUT", "returncode": None, "output": str(exc)}
    except Exception as exc:
        return {"name": name, "status": "ERROR", "returncode": None, "output": repr(exc)}


def main() -> int:
    py = sys.executable
    results = []
    results.append(run("python_syntax", [py, "-m", "py_compile", "import_poecharm_translations.py", "update_poecharm_translations.py", "update_pob_core.py", "rank_gear_ssf.py", "pob_cli/cli.py", "pob_cli/i18n.py", "pob_cli/build_db.py", "pob_cli/config.py", "pob_cli/diff.py", "pob_cli/skills_report.py", "pob_cli/power_report.py", "pob_cli/tree_candidates.py", "pob_cli/treedata.py", "pob_cli/tree_matrix.py", "search_gear_upgrades.py", "rank_gear_ssf.py", "validate_pob_cli.py"]))
    results.append(run("cli_help", [py, "-m", "pob_cli.cli", "--help"]))
    results.append(run("cli_chinese_items", [py, "-m", "pob_cli.cli", "裝備", "attached_build.xml"]))
    results.append(run("cli_chinese_tree", [py, "-m", "pob_cli.cli", "天賦", "attached_build.xml"]))
    results.append(run("cli_chinese_skills", [py, "-m", "pob_cli.cli", "技能", "attached_build.xml"]))
    results.append(run("cli_english_fallback", [py, "-m", "pob_cli.cli", "--locale", "en", "items", "attached_build.xml"]))
    results.append(run("cli_analyze_xml", [py, "-m", "pob_cli.cli", "analyze", "attached_build.xml"]))
    results.append(run("cli_compare", [py, "-m", "pob_cli.cli", "compare", "attached_build.xml", "attached_build.xml"]))
    results.append(run("tree_diff", [py, "-m", "pob_cli.cli", "tree-diff", "attached_build.xml", "attached_build.xml", "--format", "json"]))
    results.append(run("config_override", [py, "-m", "pob_cli.cli", "calc", "attached_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--config", "usePowerCharges=true", "--config", "conditionShockEffect=25", "--format", "json", "--timeout", "180"], 210))
    results.append(run("breakdown_json", [py, "-m", "pob_cli.cli", "breakdown", "attached_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--metric", "dps", "--format", "json", "--timeout", "180"], 210))
    results.append(run("breakdown_markdown", [py, "-m", "pob_cli.cli", "breakdown", "attached_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--metric", "Cold", "--format", "markdown", "--timeout", "180"], 210))
    results.append(run("config_visibility", [py, "-m", "pob_cli.cli", "config-options", "attached_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--format", "json", "--timeout", "180"], 210))
    results.append(run("defence_breakdown", [py, "-m", "pob_cli.cli", "breakdown", "attached_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--metric", "defence", "--format", "json", "--timeout", "180"], 210))
    results.append(run("analyze_json", [py, "-m", "pob_cli.cli", "analyze", "attached_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--format", "json", "--timeout", "180"], 210))
    results.append(run("analyze_markdown", [py, "-m", "pob_cli.cli", "analyze", "attached_build.xml", "--skip-calc", "--format", "markdown"]))
    results.append(run("skills_details_json", [py, "-m", "pob_cli.cli", "skills", "attached_build.xml", "--details", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--format", "json", "--timeout", "180"], 210))
    results.append(run("skills_details_markdown", [py, "-m", "pob_cli.cli", "技能", "attached_build.xml", "--details", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--format", "markdown", "--timeout", "180"], 210))
    results.append(run("power_report", [py, "-m", "pob_cli.cli", "power-report", "attached_build.xml", "attached_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--format", "json", "--timeout", "180"], 300))
    results.append(run("gear_candidate_context", [py, "search_gear_upgrades.py"], 900))
    results.append(run("tree_candidate_recalculation", [py, "-m", "pob_cli.cli", "optimize-tree", "attached_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--remove-node", "7388", "--add-node", "7388", "--mastery", "45558=30612", "--format", "json", "--timeout", "180"], 300))
    results.append(run("tree_matrix_batch", [py, "-m", "pob_cli.cli", "optimize-tree-matrix", "attached_build.xml", "test_tree_matrix.json", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--format", "json", "--timeout", "180"], 600))
    results.append(run("cli_share_dry_run", [py, "-m", "pob_cli.cli", "分享", "attached_build.xml", "--dry-run"]))
    results.append(run("build_db_list", [py, "-m", "pob_cli.cli", "流派", "list"]))
    results.append(run("build_db_show", [py, "-m", "pob_cli.cli", "流派", "show", "toxic-rain-pathfinder", "--stage", "early"]))
    results.append(run("build_db_export_xml", [py, "-m", "pob_cli.cli", "流派", "export", "toxic-rain-pathfinder", "--stage", "mid", "--output", "/tmp/pob_cli_validate_build.xml"]))
    results.append(run("translation_update_check", [py, "update_poecharm_translations.py", "--check-only", "--repo-dir", "/home/ubuntu/PoeCharm", "--output", "/tmp/zh_TW_validate.json", "--package-output", "/tmp/zh_TW_package_validate.json", "--state", "/tmp/poecharm_validate_state.json"]))
    results.append(run("pob_release_check", [py, "update_pob_core.py", "--source-dir", "/home/ubuntu/PathOfBuilding", "--state", "/tmp/pob_core_validate_state.json"], 60))
    results.append(run("ssf_rank", [py, "rank_gear_ssf.py"], 60))
    results.append(run("pob_calc_headless", [py, "-m", "pob_cli.cli", "calc", "attached_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--skill", "Creeping Frost", "--format", "json", "--timeout", "180"], 210))
    results.append(run("pob_calc_generated_build", [py, "-m", "pob_cli.cli", "calc", "/tmp/pob_cli_validate_build.xml", "--pob-root", "/home/ubuntu/PathOfBuilding", "--format", "json", "--timeout", "180"], 210))
    results.append(run("unit_tests", [py, "-m", "unittest", "discover", "-s", "tests", "-v"], 180))
    summary = {"results": results, "pass": sum(r["status"] == "PASS" for r in results), "total": len(results)}
    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": summary["pass"], "total": summary["total"], "report": str(REPORT)}, ensure_ascii=False))
    for row in results:
        print(f"{row['status']:7} {row['name']}")
    return 0 if summary["pass"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
