# PoE SSF 製作期望成本計算器

`ssf_crafting_cost.py` 用來比較不同裝備製作路線的**期望嘗試次數、期望材料需求、指定成功把握率所需的嘗試上限，以及可選的期望成本單位**。

## 重要限制

這支腳本不會自行猜測當前聯盟的詞綴權重或掉落率。PoE 的詞綴資料、Essence／化石結果、Harvest 選項、工藝限制和材料取得率可能因版本而改變，因此所有 `success_probability` 與材料消耗都放在 JSON 設定檔中，由使用者自行校正。

> 這是一個「輸入假設後做透明期望值計算」工具，不是官方掉落模擬器，也不會宣稱產生真實保證成本。

## 基本用法

```bash
cd /home/ubuntu/pob-cli
python3 ssf_crafting_cost.py ssf_crafting_examples.json
```

指定 95% 成功把握率並輸出 JSON：

```bash
python3 ssf_crafting_cost.py ssf_crafting_examples.json \
  --confidence 0.95 \
  --json > crafting_report.json
```

依成功率排序：

```bash
python3 ssf_crafting_cost.py ssf_crafting_examples.json --sort probability
```

## 計算模型

每一條製作路線以幾何分布估算：

```text
期望嘗試次數 = 1 / 單次成功率
期望材料 = 一次嘗試材料 × 期望嘗試次數 + 固定材料
N 次內成功機率 = 1 - (1 - 單次成功率)^N
```

例如單次成功率為 0.5%，則期望嘗試次數為 200 次；但這不代表每 200 次一定成功。若要達到 90% 成功把握，腳本會另外計算所需嘗試上限。

## 設定檔格式

```json
{
  "unit_values": {
    "Essence of Hatred": 8,
    "Orb of Scouring": 1
  },
  "routes": [
    {
      "name": "護符：Essence 路線",
      "success_probability": 0.004,
      "materials_per_attempt": {
        "Essence of Hatred": 1,
        "Orb of Scouring": 0.25
      },
      "fixed_materials": {
        "Turquoise Amulet base": 1
      },
      "notes": "請依實際詞綴權重校正"
    }
  ]
}
```

`success_probability` 必須是 0 到 1 之間的小數。例如 0.4% 要輸入 `0.004`，不是 `0.4`。`materials_per_attempt` 是每次失敗或成功嘗試都會消耗的材料；`fixed_materials` 是開始路線時只消耗一次的材料。`unit_values` 不是交易價格，而是使用者自訂的 SSF 內部成本權重，可以用來將稀有材料和一般材料放在同一個比較尺度。

## 建議的 SSF 輸入方式

對護符 `+1 Cold Skill Gems` 或法術武器 `+1 Spell Skill Gems`，不要直接把「某個高階詞綴」寫成固定真實機率，除非你已經有相同版本、相同基底、相同 ilvl、相同詞綴池和相同製作方法的資料。比較可靠的做法是分開建立不同路線：

| 路線 | 應輸入的資料 |
|---|---|
| Essence | Essence 種類、每次消耗、保留詞綴後目標成功率、重骰材料 |
| Fossil | Fossil、Resonator 數量、目標成功率、基底成本 |
| Alteration／Regal | 每次改造數、富豪石、重鑄、目標詞綴同時出現機率 |
| Harvest | Lifeforce 類型、每次重擲數、目標成功率、保留詞綴代價 |
| 掉落／基地 | 基底掉落或取得的平均成本、後續工藝成功率 |

如果某一路線包含「先固定一條詞綴，再用另一種方法完成第二條詞綴」，應把整個流程的成功率輸入為**完成整件目標裝備的單次成功率**，或把流程拆成多個階段並在外部先計算各階段期望值；目前腳本的每一條 route 是單一幾何成功流程，不會自動理解複雜的保留、失敗回退或中間品價值。

## 讀懂輸出

```text
成功率：0.400000%
期望嘗試次數：250
達成 90% 把握所需嘗試上限：575
期望材料需求：
  Essence of Hatred: 250
  Orb of Scouring: 62.50
```

「期望」是長期平均，不是保證值。SSF 規劃時建議同時看 50%、90% 和 95% 成功把握所需的材料量，並另外保留失敗後仍可用的中間品，不要只準備期望值。

## 與 PoB 裝備候選搜尋串接

`rank_gear_ssf.py` 會把前一輪 `search_gear_upgrades.py` 產生的 `/tmp/gear_upgrade_search_results.json`，與 SSF 製作路線設定合併。串接資料由 `gear_ssf_routes.json` 定義：

```text
PoB candidate name
  -> one or more SSF route names
  -> expected materials and expected cost units
  -> PoB DPS／EHP／Block hard filter
  -> DPS gain per expected cost ranking
```

執行方式：

```bash
python3 search_gear_upgrades.py
python3 rank_gear_ssf.py
```

JSON 輸出：

```bash
python3 rank_gear_ssf.py --json > gear_ssf_ranked.json
```

整合器會套用目前的 HC 門檻：

```text
Attack Block >= 70%
Spell Block >= 70%
Total EHP >= 95% of baseline
DPS gain >= 3%
```

排序指標為：

```text
DPS 增益／期望成本 = (candidate DPS - baseline DPS) / expected cost units
```

這個排序不是交易市價，也不是「越便宜一定越好」的結論；`unit_values` 是 SSF 內部成本權重。實際使用時應將 `success_probability`、每次材料消耗和材料權重換成目前版本、目標基底與你的 SSF 存量資料。

本次範例整合結果顯示，`weapon_spell1` 的 PoB 候選約為 +13.06% Creeping Frost DPS、Total EHP +1.96%、Attack／Spell Block 74.5%／74%，在範例化石路線假設下成本單位為 700。這個結果只表示「在設定檔假設下的排序」，不代表該詞綴組合在目前聯盟一定有相同成功率。

## 驗證

```bash
python3 -m py_compile ssf_crafting_cost.py rank_gear_ssf.py
python3 -m unittest discover -s tests -v
python3 rank_gear_ssf.py
```

目前範例資料是示範資料，必須依實際 PoE 版本與聯盟更新。若要與 pob CLI 的天賦／裝備模擬串接，下一步可把每一個可製作的詞綴組合交給 PoB 重算，將「DPS 增益」與本腳本的「SSF 期望材料」合併成 `DPS 增益／期望成本` 排名。
