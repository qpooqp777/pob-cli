#!/usr/bin/env python3
"""PoE SSF craft expected-cost calculator.

The model is intentionally explicit: success probabilities and material costs are
inputs, not hidden claims about the current league.  A route is modeled as a
geometric process: expected attempts = 1 / success_probability.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Route:
    name: str
    success_probability: float
    materials_per_attempt: dict[str, float]
    fixed_materials: dict[str, float]
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Route":
        p = float(data["success_probability"])
        if not 0 < p <= 1:
            raise ValueError(f"{data.get('name', 'route')}: success_probability must be in (0, 1]")
        return cls(
            name=str(data["name"]),
            success_probability=p,
            materials_per_attempt={str(k): float(v) for k, v in data.get("materials_per_attempt", {}).items()},
            fixed_materials={str(k): float(v) for k, v in data.get("fixed_materials", {}).items()},
            notes=str(data.get("notes", "")),
        )

    def expected_attempts(self) -> float:
        return 1.0 / self.success_probability

    def probability_within(self, attempts: int) -> float:
        return 1.0 - (1.0 - self.success_probability) ** attempts

    def attempts_for_confidence(self, confidence: float) -> int:
        if confidence <= 0:
            return 0
        if confidence >= 1:
            return math.inf  # type: ignore[return-value]
        return math.ceil(math.log1p(-confidence) / math.log1p(-self.success_probability))

    def expected_materials(self) -> dict[str, float]:
        multiplier = self.expected_attempts()
        result = dict(self.fixed_materials)
        for material, amount in self.materials_per_attempt.items():
            result[material] = result.get(material, 0.0) + amount * multiplier
        return result

    def expected_total_units(self, unit_values: dict[str, float]) -> float:
        return sum(amount * unit_values.get(material, 0.0) for material, amount in self.expected_materials().items())


def load_config(path: Path) -> tuple[dict[str, Any], list[Route]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    routes = [Route.from_dict(x) for x in data.get("routes", [])]
    if not routes:
        raise ValueError("config must contain at least one route")
    return data, routes


def fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    return f"{value:,.2f}"


def render_route(route: Route, values: dict[str, float], confidence: float) -> str:
    lines = [
        f"路線：{route.name}",
        f"成功率：{route.success_probability:.6%}",
        f"期望嘗試次數：{fmt(route.expected_attempts())}",
        f"達成 {confidence:.0%} 把握所需嘗試上限：{route.attempts_for_confidence(confidence):,}",
        f"期望成本單位：{fmt(route.expected_total_units(values))}",
        "期望材料需求：",
    ]
    for material, amount in sorted(route.expected_materials().items()):
        lines.append(f"  {material}: {fmt(amount)}")
    if route.notes:
        lines.append(f"備註：{route.notes}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="計算 PoE SSF 裝備製作路線的期望成本與材料需求")
    parser.add_argument("config", type=Path, help="JSON 設定檔")
    parser.add_argument("--confidence", type=float, default=0.90, help="成功把握率，預設 0.90")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    parser.add_argument("--sort", choices=["cost", "probability"], default="cost", help="排序方式")
    args = parser.parse_args(argv)
    if not 0 < args.confidence < 1:
        parser.error("--confidence 必須介於 0 與 1 之間")
    try:
        config, routes = load_config(args.config)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"讀取設定失敗：{exc}", file=sys.stderr)
        return 2
    values = {str(k): float(v) for k, v in config.get("unit_values", {}).items()}
    routes.sort(key=(lambda r: r.expected_total_units(values)) if args.sort == "cost" else (lambda r: -r.success_probability))
    rows = []
    for route in routes:
        rows.append({
            "name": route.name,
            "success_probability": route.success_probability,
            "expected_attempts": route.expected_attempts(),
            "attempts_for_confidence": route.attempts_for_confidence(args.confidence),
            "expected_materials": route.expected_materials(),
            "expected_total_units": route.expected_total_units(values),
            "notes": route.notes,
        })
    if args.json:
        print(json.dumps({"confidence": args.confidence, "routes": rows}, ensure_ascii=False, indent=2))
        return 0
    print("PoE SSF 製作期望成本分析")
    print("=" * 72)
    print(f"成功把握率：{args.confidence:.0%}；排序：{'期望成本' if args.sort == 'cost' else '成功率'}")
    print("注意：所有成功率與材料數值來自設定檔，請依聯盟／版本校正。\n")
    for i, route in enumerate(routes, 1):
        print(f"[{i}] {render_route(route, values, args.confidence)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
