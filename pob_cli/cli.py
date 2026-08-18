from __future__ import annotations

import argparse
import json
import base64
import re
import sys
import urllib.request
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .headless import format_calcs, run_pob_calcs
from .i18n import make_translator, translate_compound_name, translate_item_text
from .build_db import load_db, find_build, stage_report, export_pob
from .config import parse_config_pairs
from .diff import compare_trees, format_tree_diff
from .breakdown import build_breakdown_payload, format_breakdown_markdown
from .config_options import format_config_options_markdown
from .analyze_report import build_analysis_payload, format_analysis_markdown
from .skills_report import build_skills_payload, format_skills_markdown
from .power_report import build_power_report, format_power_report_markdown
from .tree_candidates import calculate_tree_candidate
from .tree_matrix import calculate_tree_matrix, format_tree_matrix_markdown
from .core import (
    Build, defensive_report, load_build, load_ninja_character, poe_ninja_price,
    print_report, upgrade_recommendations,
)

ROOT = Path(__file__).resolve().parents[1]
TREE_FILE = Path(__file__).resolve().with_name("tree.lua")


def xml_root(path: str) -> ET.Element:
    return ET.parse(path).getroot()


def tree_spec(path: str) -> dict[str, Any]:
    root = xml_root(path)
    tree = root.find("Tree")
    spec = tree.find("Spec") if tree is not None else None
    if spec is None:
        raise ValueError("找不到 PoB Tree/Spec")
    return {"tree": spec.attrib, "nodes": [int(x) for x in spec.attrib.get("nodes", "").split(",") if x]}


def node_blocks() -> dict[int, str]:
    text = TREE_FILE.read_text(encoding="utf-8", errors="ignore")
    blocks = {}
    for match in re.finditer(r"\n        \[(\d+)\]= \{(.*?)(?=\n        \[\d+\]= \{|\n    \},\n    \[\d+\]=)", text, re.S):
        blocks[int(match.group(1))] = match.group(2)
    return blocks


def node_info(node_id: int, blocks: dict[int, str]) -> dict[str, Any]:
    block = blocks.get(node_id, "")
    name = re.search(r'\["name"\]= "([^"]*)"', block)
    stats_block = re.search(r'\["stats"\]= \{(.*?)\n            \}', block, re.S)
    stats = re.findall(r'"((?:[^"\\]|\\.)*)"', stats_block.group(1)) if stats_block else []
    flags = [key for key in ("isKeystone", "isNotable", "isMastery") if f'["{key}"]= true' in block]
    return {"id": node_id, "name": name.group(1) if name else "", "flags": flags, "stats": stats}


def cmd_tree(args: argparse.Namespace) -> int:
    spec = tree_spec(args.build)
    translator = getattr(args, "translator", make_translator("en"))
    blocks = node_blocks()
    print(f"PassiveTree {spec['tree'].get('treeVersion', '?')}｜已配置 {len(spec['nodes'])} 點")
    for node_id in spec["nodes"]:
        info = node_info(node_id, blocks)
        if info["name"] and (info["flags"] or args.all):
            flag = "/".join(info["flags"]) or "passive"
            name = translator(info["name"])
            stats = " | ".join(translator(stat) for stat in info["stats"])
            print(f"{node_id:>6}  {name:<38} [{flag}]  {stats}")
    return 0


def cmd_skills(args: argparse.Namespace) -> int:
    if getattr(args, "details", False):
        payload = run_pob_calcs(args.build, args.pob_root, args.timeout, args.skill, include_skills=True)
        detailed = build_skills_payload(payload)
        if args.format == "json":
            print(json.dumps(detailed, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(format_skills_markdown(detailed), end="")
        return 0
    root = xml_root(args.build)
    translator = getattr(args, "translator", make_translator("en"))
    print("技能配置")
    for skill in root.findall(".//Skill"):
        gems = [gem.attrib.get("skillId") or gem.attrib.get("name") or "未知技能" for gem in skill.findall("Gem")]
        if gems:
            print(f"[{skill.attrib.get('slot', '未知部位')}] {' + '.join(translator(gem) for gem in gems)}")
    return 0


def cmd_items(args: argparse.Namespace) -> int:
    root = xml_root(args.build)
    translator = getattr(args, "translator", make_translator("en"))
    print("裝備與物品")
    for item in root.findall(".//Item"):
        text = item.text or ""
        translated = translate_item_text(text, translator)
        print(f"[{item.attrib.get('id', '?')}]\n{translated[:2000]}")
    return 0


def cmd_calc(args: argparse.Namespace) -> int:
    config = parse_config_pairs(args.config)
    payload = run_pob_calcs(args.build, args.pob_root, args.timeout, args.skill, config=config)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_calcs(payload))
    return 0


def cmd_config_options(args: argparse.Namespace) -> int:
    config = parse_config_pairs(args.config)
    payload = run_pob_calcs(args.build, args.pob_root, args.timeout, args.skill, config=config, include_config_options=True)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_config_options_markdown(payload), end="")
    return 0


def cmd_breakdown(args: argparse.Namespace) -> int:
    config = parse_config_pairs(args.config)
    raw = run_pob_calcs(args.build, args.pob_root, args.timeout, args.skill, config=config, include_breakdown=True)
    payload = build_breakdown_payload(raw, args.metric)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_breakdown_markdown(payload), end="")
    return 0


def cmd_optimize_tree(args: argparse.Namespace) -> int:
    config = parse_config_pairs(args.config)
    add_nodes = [int(value) for value in args.add_node]
    remove_nodes = [int(value) for value in args.remove_node]
    mastery = []
    for value in args.mastery:
        if "=" not in value:
            raise ValueError("--mastery 必須使用 nodeId=effectId")
        node, effect = value.split("=", 1)
        mastery.append((int(node), int(effect)))
    report = calculate_tree_candidate(args.source, args.pob_root, add_nodes, remove_nodes, mastery, args.skill, config, args.output, args.timeout)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        diff = report["tree_diff"]
        power = report["power_report"]
        print("# PassiveTree Candidate Power Report")
        print("")
        print(f"- Candidate XML: `{report['candidate_xml']}`")
        print(f"- Added nodes: `{report['tree_change']['added_nodes']}`")
        print(f"- Removed nodes: `{report['tree_change']['removed_nodes']}`")
        print(f"- Mastery changes: `{report['tree_change']['mastery_changes']}`")
        print("")
        print(format_power_report_markdown(power), end="")
        print(f"- Tree point delta: `{diff['point_delta']:+d}`")
    return 0


def cmd_optimize_tree_matrix(args: argparse.Namespace) -> int:
    config = parse_config_pairs(args.config)
    report = calculate_tree_matrix(args.source, args.matrix, args.pob_root, args.skill, config, args.timeout, args.limit)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_tree_matrix_markdown(report), end="")
    return 0 if report["failure_count"] == 0 else 2


def cmd_power_report(args: argparse.Namespace) -> int:
    config = parse_config_pairs(args.config)
    before = run_pob_calcs(args.before, args.pob_root, args.timeout, args.skill, config=config, include_skills=True)
    after = run_pob_calcs(args.after, args.pob_root, args.timeout, args.skill, config=config, include_skills=True)
    report = build_power_report(before, after, before, after)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_power_report_markdown(report), end="")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    build = load_ninja_character(args.source) if args.source.startswith(("http://", "https://")) else load_build(args.source)
    warnings: list[str] = []
    price_rows: list[dict[str, Any]] = []
    for query in args.price:
        try:
            row = poe_ninja_price(query, args.league)
            row["query"] = query
            price_rows.append(row)
        except Exception as exc:
            warnings.append(f"物價查詢失敗：{query}：{exc}")
    calculation = None
    if not args.skip_calc and not args.source.startswith(("http://", "https://")) and Path(args.source).suffix.lower() == ".xml":
        try:
            calculation = run_pob_calcs(args.source, args.pob_root, args.timeout, args.skill, config=parse_config_pairs(args.config))
        except Exception as exc:
            warnings.append(f"官方 PoB 計算未完成：{exc}")
    payload = build_analysis_payload(build, args.source, price_rows, calculation, warnings)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(format_analysis_markdown(payload), end="")
    else:
        print_report(build, args.price, args.league)
    return 0


def make_pob_code(build_path: str) -> str:
    xml = Path(build_path).read_bytes()
    compressed = zlib.compress(xml)
    return base64.urlsafe_b64encode(compressed).decode("ascii")


def cmd_share(args: argparse.Namespace) -> int:
    code = make_pob_code(args.build)
    if args.dry_run:
        print(code)
        return 0
    req = urllib.request.Request(
        "https://pobb.in/pob/",
        data=code.encode("ascii"),
        method="POST",
        headers={"User-Agent": "pob-cli/0.1", "Content-Type": "text/plain"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        result = response.read().decode("utf-8", errors="replace").strip()
    if not result:
        raise RuntimeError("pobb.in 沒有回傳分享 ID")
    if result.startswith("http://") or result.startswith("https://"):
        print(result)
    else:
        print("https://pobb.in/" + result.lstrip("/"))
    return 0


def cmd_build_db(args: argparse.Namespace) -> int:
    db = load_db(args.db)
    if args.action == "list":
        print(f"流派資料庫：PoE {db.get('poe_version', '?')}｜聯盟：{db.get('league', '?')}")
        for build in db.get("builds", []):
            print(f"{build['id']}｜{build['name_zhTW']}｜{build['class']} {build['ascendancy']}｜{'、'.join(build.get('tags', []))}")
        return 0
    build = find_build(db, args.build_id)
    if args.action == "show":
        if args.stage:
            print(stage_report(build, args.stage))
        else:
            print(f"{build['name_zhTW']} / {build['name_en']}")
            print(f"PoE {db.get('poe_version')}｜{build['class']}｜{build['ascendancy']}")
            print("階段：" + "、".join(build["stages"]))
            print(build.get("notes", ""))
        return 0
    if args.action == "export":
        output, missing = export_pob(build, args.stage, args.output)
        print(f"已產生 PoB XML：{output}")
        if missing:
            print("警告：以下天賦名稱未在目前 tree.lua 找到：" + "、".join(missing))
        print("請在 PoB 中匯入後重新檢查技能寶石 ID、裝備詞綴與天賦路徑，再使用 pob calc 取得正式數值。")
        return 0
    raise ValueError(f"未知 action：{args.action}")


def cmd_tree_diff(args: argparse.Namespace) -> int:
    report = compare_trees(args.current, args.candidate)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_tree_diff(report))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    current = load_build(args.current)
    candidate = load_build(args.candidate)
    print("pob CLI Build 比較")
    print(f"目前：{current.name}｜候選：{candidate.name}")
    print("\n防禦差異（候選 - 目前）")
    for row in defensive_report(current):
        name = row["name"]
        # map display names back through the stable report order
        mapping = {"火焰抗性":"fire_res", "冰冷抗性":"cold_res", "閃電抗性":"lightning_res", "混沌抗性":"chaos_res", "法術壓制":"spell_suppression", "生命":"life"}
        before = current.stats.get(mapping[name], 0)
        after = candidate.stats.get(mapping[name], 0)
        print(f"{name:<12} {before:>8.1f} -> {after:>8.1f}  ({after-before:+.1f})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pob", description="Path of Building Community Fork command-line analyzer")
    parser.add_argument("--locale", default="en", choices=["en", "zh-TW", "zh-CN"], help="output locale (default: en)")
    parser.add_argument("--translations", help="自訂 PoeCharm 轉換後的 JSON 路徑")
    sub = parser.add_subparsers(dest="command", required=True)
    calc = sub.add_parser("calc", aliases=["計算"], help="使用 PoB Community Fork Lua 核心精確計算")
    calc.add_argument("build", help="PoB XML 檔案")
    calc.add_argument("--pob-root", help="PathOfBuilding 原始碼根目錄；也可用 POB_ROOT")
    calc.add_argument("--format", choices=["text", "json"], default="text")
    calc.add_argument("--skill", help="指定主技能名稱，例如 Earthshatter")
    calc.add_argument("--config", action="append", default=[], metavar="KEY=VALUE", help="覆寫 PoB Config，可重複指定")
    calc.add_argument("--timeout", type=int, default=180)
    calc.set_defaults(func=cmd_calc)
    config_options = sub.add_parser("config-options", aliases=["設定選項", "設定可見性"], help="列出目前 Build 的 PoB 可見 ConfigOptions")
    config_options.add_argument("build", help="PoB XML 檔案")
    config_options.add_argument("--pob-root", help="PathOfBuilding 原始碼根目錄；也可用 POB_ROOT")
    config_options.add_argument("--skill", help="指定主技能名稱")
    config_options.add_argument("--config", action="append", default=[], metavar="KEY=VALUE", help="先套用 Config 再判斷可見性")
    config_options.add_argument("--format", choices=["markdown", "json"], default="markdown")
    config_options.add_argument("--timeout", type=int, default=180)
    config_options.set_defaults(func=cmd_config_options)
    breakdown = sub.add_parser("breakdown", aliases=["傷害拆解", "傷害分析"], help="使用 PoB CalcBreakdown.lua 輸出傷害 breakdown")
    breakdown.add_argument("build", help="PoB XML 檔案")
    breakdown.add_argument("--pob-root", help="PathOfBuilding 原始碼根目錄；也可用 POB_ROOT")
    breakdown.add_argument("--skill", help="指定主技能名稱")
    breakdown.add_argument("--metric", default="all", help="all、dps、defence、AverageHit、Cold、Fire、Lightning 或 Chaos")
    breakdown.add_argument("--config", action="append", default=[], metavar="KEY=VALUE", help="覆寫 PoB Config，可重複指定")
    breakdown.add_argument("--format", choices=["markdown", "json"], default="markdown")
    breakdown.add_argument("--timeout", type=int, default=180)
    breakdown.set_defaults(func=cmd_breakdown)
    optimize_tree = sub.add_parser("optimize-tree", aliases=["天賦最佳化", "天賦候選"], help="修改 PassiveTree node／Mastery 後使用官方 PoB 重算")
    optimize_tree.add_argument("source", help="基準 PoB XML")
    optimize_tree.add_argument("--add-node", action="append", default=[], metavar="NODE_ID")
    optimize_tree.add_argument("--remove-node", action="append", default=[], metavar="NODE_ID")
    optimize_tree.add_argument("--mastery", action="append", default=[], metavar="NODE_ID=EFFECT_ID")
    optimize_tree.add_argument("--output", help="保存候選 XML；未指定時使用暫存檔並於完成後刪除")
    optimize_tree.add_argument("--pob-root", help="PathOfBuilding 原始碼根目錄；也可用 POB_ROOT")
    optimize_tree.add_argument("--skill", help="指定主技能")
    optimize_tree.add_argument("--config", action="append", default=[], metavar="KEY=VALUE")
    optimize_tree.add_argument("--format", choices=["json", "markdown"], default="markdown")
    optimize_tree.add_argument("--timeout", type=int, default=180)
    optimize_tree.set_defaults(func=cmd_optimize_tree)
    tree_matrix = sub.add_parser("optimize-tree-matrix", aliases=["天賦矩陣", "批次天賦"], help="批次重算 PassiveTree 候選矩陣並依 HC／Power Report 排序")
    tree_matrix.add_argument("source", help="基準 PoB XML")
    tree_matrix.add_argument("matrix", help="候選矩陣 JSON／JSONL")
    tree_matrix.add_argument("--pob-root", help="PathOfBuilding 原始碼根目錄；也可用 POB_ROOT")
    tree_matrix.add_argument("--skill", help="指定主技能")
    tree_matrix.add_argument("--config", action="append", default=[], metavar="KEY=VALUE")
    tree_matrix.add_argument("--limit", type=int, help="最多處理幾個候選")
    tree_matrix.add_argument("--format", choices=["json", "markdown"], default="markdown")
    tree_matrix.add_argument("--timeout", type=int, default=180)
    tree_matrix.set_defaults(func=cmd_optimize_tree_matrix)
    power_report = sub.add_parser("power-report", aliases=["戰力報告", "比較戰力"], help="比較兩個 PoB Build 的官方 scalar 與技能 context")
    power_report.add_argument("before", help="基準 PoB XML")
    power_report.add_argument("after", help="候選 PoB XML")
    power_report.add_argument("--pob-root", help="PathOfBuilding 原始碼根目錄；也可用 POB_ROOT")
    power_report.add_argument("--skill", help="指定主技能")
    power_report.add_argument("--config", action="append", default=[], metavar="KEY=VALUE", help="覆寫官方 PoB Config")
    power_report.add_argument("--format", choices=["json", "markdown"], default="markdown")
    power_report.add_argument("--timeout", type=int, default=180)
    power_report.set_defaults(func=cmd_power_report)
    analyze = sub.add_parser("analyze", aliases=["分析"], help="分析 PoB XML／Ninja JSON 或公開頁")
    analyze.add_argument("source")
    analyze.add_argument("--league")
    analyze.add_argument("--price", action="append", default=[])
    analyze.add_argument("--pob-root", help="PathOfBuilding 原始碼根目錄；也可用 POB_ROOT")
    analyze.add_argument("--skill", help="指定官方 PoB 計算主技能")
    analyze.add_argument("--config", action="append", default=[], metavar="KEY=VALUE", help="覆寫官方 PoB Config，可重複指定")
    analyze.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    analyze.add_argument("--skip-calc", action="store_true", help="跳過本地 PoB 官方計算")
    analyze.add_argument("--timeout", type=int, default=180)
    analyze.set_defaults(func=cmd_analyze)
    tree = sub.add_parser("tree", aliases=["天賦", "天賦樹"], help="列出已配置 PassiveTree 節點")
    tree.add_argument("build")
    tree.add_argument("--all", action="store_true", help="也列出普通小天賦")
    tree.set_defaults(func=cmd_tree)
    skills = sub.add_parser("skills", aliases=["技能"], help="列出技能組")
    skills.add_argument("build")
    skills.add_argument("--details", action="store_true", help="使用官方 PoB SkillsTab 輸出寶石 metadata 與支援關係")
    skills.add_argument("--format", choices=["text", "json", "markdown"], default="markdown")
    skills.add_argument("--pob-root", help="PathOfBuilding 原始碼根目錄；也可用 POB_ROOT")
    skills.add_argument("--skill", help="指定官方 PoB 主技能")
    skills.add_argument("--timeout", type=int, default=180)
    skills.set_defaults(func=cmd_skills)
    items = sub.add_parser("items", aliases=["裝備", "物品"], help="列出裝備與物品")
    items.add_argument("build")
    items.set_defaults(func=cmd_items)
    share = sub.add_parser("share", aliases=["分享"], help="使用 PoB 內建流程上傳至 pobb.in")
    share.add_argument("build", help="PoB XML 檔案")
    share.add_argument("--dry-run", action="store_true", help="只輸出與 PoB 相同的分享 code，不上傳")
    share.set_defaults(func=cmd_share)
    tree_diff = sub.add_parser("tree-diff", aliases=["天賦差異", "天賦比較"], help="比較兩個 PoB PassiveTree")
    tree_diff.add_argument("current")
    tree_diff.add_argument("candidate")
    tree_diff.add_argument("--format", choices=["text", "json"], default="text")
    tree_diff.set_defaults(func=cmd_tree_diff)
    compare = sub.add_parser("compare", aliases=["比較"], help="比較兩個 PoB Build 的防禦數值")
    compare.add_argument("current")
    compare.add_argument("candidate")
    compare.set_defaults(func=cmd_compare)
    db = sub.add_parser("build-db", aliases=["流派", "流派庫"], help="管理分階段 PoE 流派資料庫並匯出 PoB XML")
    db.add_argument("action", choices=["list", "show", "export"], help="list 列出流派；show 查看；export 匯出 PoB")
    db.add_argument("build_id", nargs="?", default="toxic-rain-pathfinder")
    db.add_argument("--stage", choices=["early", "mid", "late"], default="early")
    db.add_argument("--db", default=str(ROOT / "build_db.json"))
    db.add_argument("--output", default="toxic-rain-pathfinder.xml")
    db.set_defaults(func=cmd_build_db)
    price = sub.add_parser("price", aliases=["物價", "價格"], help="查詢 poe.ninja 物價")
    price.add_argument("name")
    price.add_argument("--league")
    price.set_defaults(func=lambda a: print(json.dumps(poe_ninja_price(a.name, a.league), ensure_ascii=False, indent=2)))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.translator = make_translator(args.locale, args.translations)
    try:
        return int(args.func(args) or 0)
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
