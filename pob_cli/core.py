from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

NINJA_CHARACTER_HINT = "poe.ninja 角色詳情 API 屬未文件化介面；若角色頁無法直接提供資料，請改用 PoB XML。"

API_BASE = "https://api.pathofexile.com"
POE_NINJA_BASE = "https://poe.ninja/poe1/api/economy"


def http_json(url: str, timeout: int = 15) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "pob-cli/0.1 (+personal CLI)"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def num(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
    return float(match.group(0)) if match else default


def fmt(value: float) -> str:
    return str(int(value)) if value == int(value) else f"{value:.1f}"


@dataclass
class Item:
    slot: str
    name: str
    text: str
    mods: list[str] = field(default_factory=list)

    def searchable_name(self) -> str:
        return self.name.strip() or self.slot


@dataclass
class Build:
    name: str = "未命名 Build"
    level: int = 0
    class_name: str = "未知職業"
    stats: dict[str, float] = field(default_factory=dict)
    items: list[Item] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def parse_item_text(slot: str, text: str) -> Item:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = ""
    for line in lines:
        if not line.startswith(("Rarity:", "Implicits:", "--------")) and not re.match(r"^[+-]?\d", line):
            name = line
            break
    return Item(slot=slot, name=name, text=text, mods=lines)


def parse_pob_xml(path: str | Path) -> Build:
    root = ET.parse(path).getroot()
    build_node = root.find("Build")
    if build_node is None:
        raise ValueError("找不到 PoB XML 的 Build 節點")
    build = Build(
        name=build_node.attrib.get("label") or build_node.attrib.get("name") or "未命名 Build",
        level=int(num(build_node.attrib.get("level"), 0)),
        class_name=build_node.attrib.get("className") or build_node.attrib.get("class") or "未知職業",
    )
    for key, value in build_node.attrib.items():
        build.raw[key] = value
    stat_map = {
        "Life": "life", "EnergyShield": "energy_shield", "Armour": "armour",
        "Evasion": "evasion", "FireResist": "fire_res", "ColdResist": "cold_res",
        "LightningResist": "lightning_res", "ChaosResist": "chaos_res",
        "SpellSuppressionChance": "spell_suppression", "BlockChance": "block",
    }
    for node in root.iter():
        tag = node.tag.lower()
        stat_name = node.attrib.get("stat") or node.attrib.get("name")
        value = node.attrib.get("value")
        if stat_name and value is not None:
            canonical = stat_map.get(stat_name) or stat_map.get(node.attrib.get("stat", ""))
            if canonical:
                build.stats[canonical] = num(value)
        if tag == "item":
            slot = node.attrib.get("slot") or node.attrib.get("id") or "未指定部位"
            build.items.append(parse_item_text(slot, node.text or ""))
    # Some PoB exports store values as Build attributes rather than PlayerStat nodes.
    attr_map = {"life": "life", "energyShield": "energy_shield", "armour": "armour", "evasion": "evasion",
                "fireResist": "fire_res", "coldResist": "cold_res", "lightningResist": "lightning_res",
                "chaosResist": "chaos_res", "spellSuppression": "spell_suppression", "block": "block"}
    for source, target in attr_map.items():
        if source in build_node.attrib:
            build.stats[target] = num(build_node.attrib[source])
    return build


def parse_json_build(path: str | Path) -> Build:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Build(name=data.get("name", "未命名 Build"), level=int(data.get("level", 0)),
                 class_name=data.get("class_name", "未知職業"), stats={k: float(v) for k, v in data.get("stats", {}).items()},
                 items=[Item(**item) for item in data.get("items", [])], raw=data)


def load_build(path: str | Path) -> Build:
    suffix = Path(path).suffix.lower()
    return parse_json_build(path) if suffix == ".json" else parse_pob_xml(path)


def _walk_json(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _normalise_ninja_payload(data: dict[str, Any], source: str) -> Build:
    """Convert common public Ninja/PoB-like payloads into our Build model."""
    root = data.get("build", data)
    stats_source = root.get("stats", root.get("defences", root.get("defenses", {})))
    key_aliases = {
        "life": "life", "maximumLife": "life", "maxLife": "life",
        "energyShield": "energy_shield", "armour": "armour", "armor": "armour",
        "evasion": "evasion", "fireRes": "fire_res", "fireResistance": "fire_res",
        "coldRes": "cold_res", "coldResistance": "cold_res", "lightningRes": "lightning_res",
        "lightningResistance": "lightning_res", "chaosRes": "chaos_res", "chaosResistance": "chaos_res",
        "spellSuppression": "spell_suppression", "spellSuppressionChance": "spell_suppression", "block": "block",
    }
    stats = {}
    for key, value in stats_source.items() if isinstance(stats_source, dict) else []:
        target = key_aliases.get(key)
        if target:
            stats[target] = num(str(value))
    raw_items = root.get("items", root.get("equipment", []))
    items = []
    if isinstance(raw_items, dict):
        raw_items = [{"slot": slot, **(item if isinstance(item, dict) else {"text": str(item)})} for slot, item in raw_items.items()]
    for item in raw_items if isinstance(raw_items, list) else []:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("rawText") or item.get("description") or ""
        if isinstance(text, list):
            text = "\n".join(map(str, text))
        mods = item.get("explicitModifiers") or item.get("mods") or []
        if isinstance(mods, list):
            text = "\n".join([str(text)] + [str(x) for x in mods])
        items.append(Item(slot=str(item.get("slot", item.get("type", "未指定部位"))),
                          name=str(item.get("name", item.get("baseType", ""))), text=str(text), mods=[str(x) for x in mods] if isinstance(mods, list) else []))
    if not stats and not items:
        raise ValueError(f"Ninja 回應沒有可辨識的角色狀態或裝備。{NINJA_CHARACTER_HINT}")
    return Build(name=str(root.get("name", root.get("character", "Ninja 角色"))),
                 level=int(num(str(root.get("level", 0)))), class_name=str(root.get("className", root.get("class", "未知職業"))),
                 stats=stats, items=items, raw={"source": source, "ninja": data})


def load_ninja_character(source: str) -> Build:
    """Load a user-provided Ninja JSON endpoint or public character-page payload.

    This intentionally does not guess undocumented profile endpoints. The caller
    supplies the public URL, making failures explicit when Ninja changes its UI/API.
    """
    if source.startswith("http://") or source.startswith("https://"):
        req = urllib.request.Request(source, headers={"User-Agent": "pob-cli/0.1 (+personal CLI; contact user)"})
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
        try:
            return _normalise_ninja_payload(json.loads(body), source)
        except json.JSONDecodeError:
            # Best-effort extraction from JSON-LD/embedded props on a public page.
            candidates = []
            for match in re.finditer(r"(?:props|__NEXT_DATA__|application/ld\\+json)[^>{]{0,80}(\\{.*?\\})", body, re.S):
                try:
                    candidates.append(json.loads(match.group(1)))
                except json.JSONDecodeError:
                    continue
            for candidate in candidates:
                for obj in _walk_json(candidate):
                    if isinstance(obj, dict) and ("items" in obj or "equipment" in obj or "stats" in obj):
                        try:
                            return _normalise_ninja_payload(obj, source)
                        except ValueError:
                            pass
            raise ValueError(f"無法從 Ninja 公開頁解析角色資料。{NINJA_CHARACTER_HINT}")
    return _normalise_ninja_payload(json.loads(Path(source).read_text(encoding="utf-8")), source)


def defensive_report(build: Build) -> list[dict[str, str]]:
    s = build.stats
    checks = [
        ("火焰抗性", s.get("fire_res", 0), 75, "%", "resistance"),
        ("冰冷抗性", s.get("cold_res", 0), 75, "%", "resistance"),
        ("閃電抗性", s.get("lightning_res", 0), 75, "%", "resistance"),
        ("混沌抗性", s.get("chaos_res", 0), 0, "%", "chaos"),
        ("法術壓制", s.get("spell_suppression", 0), 100, "%", "suppression"),
        ("生命", s.get("life", 0), 3000 if build.level >= 85 else 2000, "", "life"),
    ]
    result = []
    for label, value, target, unit, kind in checks:
        gap = target - value
        if kind == "chaos":
            status = "良好" if value >= target else ("注意" if value >= -30 else "嚴重缺口")
        else:
            status = "良好" if value >= target else ("注意" if gap <= 15 else "嚴重缺口")
        result.append({"name": label, "value": f"{fmt(value)}{unit}", "target": f"{fmt(target)}{unit}", "gap": f"{fmt(max(gap, 0))}{unit}", "status": status})
    return result


def current_league() -> str:
    # Official API may require account authorization in some environments;
    # poe.ninja's public economy league list is sufficient for market queries.
    data = http_json(f"{POE_NINJA_BASE}/leagues")
    leagues = data if isinstance(data, list) else data.get("leagues", [])
    return leagues[0].get("id", "Standard") if leagues else "Standard"


def poe_ninja_price(name: str, league: str | None = None) -> dict[str, Any]:
    league = league or current_league()
    needle = name.lower().strip()
    currency_url = f"{POE_NINJA_BASE}/exchange/current/overview?{urllib.parse.urlencode({'league': league, 'type': 'Currency'})}"
    currency_data = http_json(currency_url)
    core_items = currency_data.get("core", {}).get("items", [])
    item_by_id = {str(x.get("id")): x for x in core_items}
    currency_matches = [x for x in core_items if needle in str(x.get("name", "")).lower()]
    if currency_matches:
        target = currency_matches[0]
        line = next((x for x in currency_data.get("lines", []) if str(x.get("id")) == str(target.get("id"))), {})
        return {"league": league, "name": target.get("name", name), "found": bool(line),
                "chaos_value": line.get("primaryValue"), "divine_value": None,
                "icon": target.get("image")}

    # Search the supported unique equipment categories. This is deliberately
    # bounded to avoid flooding the public API and is cached by the server.
    categories = ["UniqueWeapon", "UniqueArmour", "UniqueAccessory", "UniqueFlask", "UniqueJewel", "UniqueTincture"]
    for category in categories:
        params = urllib.parse.urlencode({"league": league, "type": category})
        data = http_json(f"{POE_NINJA_BASE}/stash/current/item/overview?{params}")
        matches = [row for row in data.get("lines", []) if needle in str(row.get("name", "")).lower()]
        if matches:
            row = sorted(matches, key=lambda x: 0 if str(x.get("name", "")).lower() == needle else 1)[0]
            return {"league": league, "name": row.get("name", name), "found": True,
                    "chaos_value": row.get("chaosValue"), "divine_value": row.get("divineValue"),
                    "icon": row.get("icon"), "listing_count": row.get("listingCount"),
                    "explicit_modifiers": row.get("explicitModifiers", [])}
    return {"league": league, "name": name, "found": False}


def upgrade_recommendations(build: Build, league: str | None = None) -> list[dict[str, Any]]:
    report = defensive_report(build)
    gaps = {row["name"]: float(row["gap"].rstrip("%")) for row in report if row["status"] != "良好"}
    candidates = []
    for item in build.items:
        text = item.text.lower()
        contribution = 0.0
        reasons = []
        missing = []
        if "火焰抗性" in item.text or "fire resistance" in text:
            contribution += gaps.get("火焰抗性", 0) * 1.2; reasons.append("補火焰抗性"); missing.append("火焰抗性")
        if "冰冷抗性" in item.text or "cold resistance" in text:
            contribution += gaps.get("冰冷抗性", 0) * 1.2; reasons.append("補冰冷抗性"); missing.append("冰冷抗性")
        if "閃電抗性" in item.text or "lightning resistance" in text:
            contribution += gaps.get("閃電抗性", 0) * 1.2; reasons.append("補閃電抗性"); missing.append("閃電抗性")
        if "混沌抗性" in item.text or "chaos resistance" in text:
            contribution += max(0, -build.stats.get("chaos_res", 0)) * 0.8; reasons.append("補混沌抗性"); missing.append("混沌抗性")
        if "生命" in item.text or "maximum life" in text:
            contribution += max(0, gaps.get("生命", 0)) * 0.04; reasons.append("增加生命"); missing.append("最大生命")
        if "法術壓制" in item.text or "spell suppression" in text:
            contribution += gaps.get("法術壓制", 0) * 0.6; reasons.append("提高法術壓制"); missing.append("法術壓制")
        if contribution > 0:
            candidates.append({"slot": item.slot, "item": item.searchable_name(), "score": contribution,
                               "reason": "、".join(dict.fromkeys(reasons)),
                               "target_mods": "、".join(dict.fromkeys(missing))})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:3]


def print_report(build: Build, prices: list[str], league: str | None) -> None:
    print(f"\npob CLI｜{build.name}｜{build.class_name} Lv.{build.level or '未知'}")
    print("=" * 62)
    print("防禦檢查")
    print(f"{'項目':<16}{'目前':>10}{'目標':>10}{'缺口':>10}{'狀態':>12}")
    for row in defensive_report(build):
        print(f"{row['name']:<16}{row['value']:>10}{row['target']:>10}{row['gap']:>10}{row['status']:>12}")
    print("\n前三個升級方向（依缺口關聯性排序；仍需實測 PoB）")
    recs = upgrade_recommendations(build, league)
    if not recs:
        print("目前沒有從裝備文本辨識出明確的防禦升級候選；請確認 PoB XML 是否包含裝備內容。")
    for i, rec in enumerate(recs, 1):
        print(f"{i}. [{rec['slot']}] 優先尋找更好的替代品｜目前：{rec['item']}｜目標：{rec['target_mods']}｜{rec['reason']}｜關聯分數 {rec['score']:.1f}")
    if prices:
        print("\n物價查詢")
        for query in prices:
            try:
                price = poe_ninja_price(query, league)
                if price.get("found"):
                    print(f"{price['name']}: {price.get('chaos_value', '?')} Chaos，約 {price.get('divine_value', '?')} Divine｜聯盟 {price['league']}")
                else:
                    print(f"{query}: 找不到近似物品｜聯盟 {price['league']}")
            except Exception as exc:
                print(f"{query}: 物價查詢失敗（{exc}）")


def main() -> int:
    parser = argparse.ArgumentParser(prog="poe-helper", description="PoE1 Build 防禦與物價助手")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="分析 PoB XML/JSON Build")
    check.add_argument("build", help="PoB XML 或 JSON 檔案")
    check.add_argument("--league", help="指定聯盟；省略時自動取得目前 PC 聯盟")
    check.add_argument("--price", action="append", default=[], help="額外查詢物品價格，可重複指定")
    ninja = sub.add_parser("ninja", help="從使用者提供的公開 Ninja JSON／角色頁取得狀態與裝備")
    ninja.add_argument("source", help="公開 Ninja JSON URL、角色頁 URL，或本地 JSON 檔案")
    ninja.add_argument("--league", help="指定物價聯盟")
    ninja.add_argument("--price", action="append", default=[], help="額外查詢物品價格，可重複指定")
    price = sub.add_parser("price", help="查詢物品價格")
    price.add_argument("name")
    price.add_argument("--league")
    args = parser.parse_args()
    try:
        if args.command == "check":
            print_report(load_build(args.build), args.price, args.league)
        elif args.command == "ninja":
            print_report(load_ninja_character(args.source), args.price, args.league)
        else:
            row = poe_ninja_price(args.name, args.league)
            if row.get("found"):
                print(f"{row['name']}｜{row.get('chaos_value', '?')} Chaos｜約 {row.get('divine_value', '?')} Divine｜{row['league']}")
            else:
                print(f"找不到：{args.name}｜{row['league']}")
        return 0
    except (OSError, ET.ParseError, ValueError, urllib.error.URLError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
