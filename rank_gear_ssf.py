#!/usr/bin/env python3
"""Join PoB gear-candidate results with SSF expected crafting costs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def combine_routes(route_names: list[str], route_rows: dict[str, dict[str, Any]]) -> tuple[float, dict[str, float]]:
    total = 0.0
    materials: dict[str, float] = {}
    for name in route_names:
        row = route_rows[name]
        total += float(row["expected_total_units"])
        for material, amount in row["expected_materials"].items():
            materials[material] = materials.get(material, 0.0) + float(amount)
    return total, materials


def main() -> int:
    parser = argparse.ArgumentParser(description="合併 PoB 裝備候選與 SSF 製作期望成本")
    parser.add_argument("--pob-results", type=Path, default=Path("/tmp/gear_upgrade_search_results.json"))
    parser.add_argument("--craft-config", type=Path, default=Path("ssf_crafting_examples.json"))
    parser.add_argument("--mapping", type=Path, default=Path("gear_ssf_routes.json"))
    parser.add_argument("--confidence", type=float, default=0.90)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    pob = load(args.pob_results)
    craft = load(args.craft_config)
    mapping = load(args.mapping)
    routes = {}
    for route in craft["routes"]:
        p = float(route["success_probability"])
        attempts = 1.0 / p
        materials = dict(route.get("fixed_materials", {}))
        for material, amount in route.get("materials_per_attempt", {}).items():
            materials[material] = materials.get(material, 0) + float(amount) * attempts
        total = sum(float(v) * float(craft.get("unit_values", {}).get(k, 0)) for k, v in materials.items())
        confidence_attempts = __import__("math").ceil(__import__("math").log1p(-args.confidence) / __import__("math").log1p(-p))
        routes[route["name"]] = {"expected_total_units": total, "expected_materials": materials, "confidence_attempts": confidence_attempts}
    hard = mapping["hard_constraints"]
    baseline = mapping["baseline"]
    output=[]
    for candidate in pob["results"]:
        name=candidate["name"]
        route_names=mapping.get("candidate_routes", {}).get(name)
        if not route_names or candidate.get("name") == "baseline": continue
        if any(r not in routes for r in route_names): continue
        cost, materials=combine_routes(route_names, routes)
        meets=(candidate["ab"]>=hard["min_attack_block"] and candidate["sb"]>=hard["min_spell_block"] and candidate["ehp"]>=baseline["ehp"]*hard["min_ehp_ratio"] and candidate["dps_pct"]>=hard["min_dps_gain_pct"])
        row=dict(candidate)
        row.update({"route_names":route_names,"expected_cost_units":cost,"expected_materials":materials,"meets_hc_target":meets,
                    "dps_gain_per_cost": (candidate["dps"]-baseline["dps"])/cost if cost else 0,
                    "dps_pct_per_cost": candidate["dps_pct"]/cost if cost else 0})
        output.append(row)
    output.sort(key=lambda x:(x["meets_hc_target"],x["dps_gain_per_cost"]), reverse=True)
    result={"confidence":args.confidence,"baseline":baseline,"hard_constraints":hard,"results":output}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("PoB × SSF 製作成本整合排名")
        print("="*80)
        print(f"HC 硬性條件：Attack Block ≥ {hard['min_attack_block']}%、Spell Block ≥ {hard['min_spell_block']}%、EHP ≥ {hard['min_ehp_ratio']:.0%} 基準、DPS ≥ +{hard['min_dps_gain_pct']}%")
        for i,row in enumerate(output,1):
            status="PASS" if row["meets_hc_target"] else "FAIL"
            print(f"[{i}] {status} {row['name']} | DPS {row['dps_pct']:+.2f}% | EHP {row['ehp_pct']:+.2f}% | 成本 {row['expected_cost_units']:,.2f} | DPS增益/成本 {row['dps_gain_per_cost']:.4f}")
            print(f"    路線：{' + '.join(row['route_names'])}")
            print(f"    材料：{', '.join(f'{k}={v:.2f}' for k,v in row['expected_materials'].items())}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
