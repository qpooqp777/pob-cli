from __future__ import annotations

import re
from pathlib import Path
from typing import Any

POB_CONFIG_OPTIONS = Path('/home/ubuntu/PathOfBuilding/src/Modules/ConfigOptions.lua')

# Values frequently used in reproducible PoB calculations. The complete variable
# name/type inventory is augmented from the installed PoB ConfigOptions.lua.
KNOWN_TYPES: dict[str, str] = {
    'enemyIsBoss': 'list',
    'enemyLevel': 'integer',
    'enemyResist': 'integer',
    'usePowerCharges': 'check',
    'useEnduranceCharges': 'check',
    'useFrenzyCharges': 'check',
    'useMinimumCharges': 'check',
    'useConvergence': 'check',
    'conditionEnemyChilled': 'check',
    'conditionEnemyShocked': 'check',
    'conditionEnemyIgnited': 'check',
    'conditionEnemyBleeding': 'check',
    'conditionEnemyPoisoned': 'check',
    'conditionEnemyMaimed': 'check',
    'conditionEnemyTaunted': 'check',
    'conditionEnemyIntimidated': 'check',
    'conditionEnemyUnnerved': 'check',
    'conditionBeenHitRecently': 'check',
    'conditionCritRecently': 'check',
    'conditionHaveOnslaught': 'check',
    'conditionHaveRampage': 'check',
    'conditionHaveArcaneSurge': 'check',
    'conditionHaveAlchemistsGenius': 'check',
    'conditionHaveFortify': 'check',
    'conditionHaveFrenzyCharge': 'check',
    'conditionHavePowerCharge': 'check',
    'conditionHaveEnduranceCharge': 'check',
    'conditionEnemyHasLessThanHalfLife': 'check',
    'multiplierNearbyEnemies': 'count',
    'multiplierNearbyRareOrUniqueEnemies': 'count',
    'numberOfEnemies': 'count',
    'conditionShockEffect': 'float',
}


def _inventory() -> dict[str, str]:
    result = dict(KNOWN_TYPES)
    if POB_CONFIG_OPTIONS.exists():
        text = POB_CONFIG_OPTIONS.read_text(encoding='utf-8', errors='ignore')
        for match in re.finditer(r'\{\s*var\s*=\s*["\']([^"\']+)["\']\s*,\s*type\s*=\s*["\']([^"\']+)', text):
            result.setdefault(match.group(1), match.group(2))
    return result


def schema() -> dict[str, str]:
    return _inventory()


def _parse_bool(value: str) -> bool:
    value = value.strip().lower()
    if value in {'true', '1', 'yes', 'on'}:
        return True
    if value in {'false', '0', 'no', 'off'}:
        return False
    raise ValueError(f'布林值必須是 true／false：{value}')


def parse_value(key: str, raw: str, expected: str) -> Any:
    if expected == 'check':
        return _parse_bool(raw)
    if expected in {'count', 'integer', 'countAllowZero'}:
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f'{key} 必須是整數：{raw}') from exc
        if expected != 'countAllowZero' and value < 0:
            raise ValueError(f'{key} 不可小於 0：{value}')
        return value
    if expected == 'float':
        try:
            return float(raw)
        except ValueError as exc:
            raise ValueError(f'{key} 必須是數字：{raw}') from exc
    if expected in {'list', 'text'}:
        if not raw.strip():
            raise ValueError(f'{key} 不可為空字串')
        return raw
    return raw


def parse_config_pairs(pairs: list[str]) -> dict[str, Any]:
    available = schema()
    result: dict[str, Any] = {}
    for pair in pairs:
        if '=' not in pair:
            raise ValueError(f'Config 必須使用 key=value 格式：{pair}')
        key, raw = pair.split('=', 1)
        key = key.strip()
        if key not in available:
            suggestions = ', '.join(sorted(k for k in available if key.lower() in k.lower())[:5])
            suffix = f'；可能的欄位：{suggestions}' if suggestions else ''
            raise ValueError(f'未知 PoB Config 欄位：{key}{suffix}')
        result[key] = parse_value(key, raw, available[key])
    return result
