# pob-cli 與 PoB Community Fork 驗證報告

## 驗證基準

本次驗證使用本機 Path of Building Community Fork，PoB `manifest.xml` 版本為 `2.67.2`，Git commit 為 `bcbca9b60b04abc17935c84ff3589342193bd758`，PassiveTree 版本為 `3.29`。CLI 使用 Python 3.12.3 與 LuaJIT 2.1.1703358377。

## 測試結果摘要

本次擴充後的自動化測試矩陣共 **32／32 通過**。本輪加入 TreeData 節點連通性驗證、批次候選矩陣與 HC-first 排序；測試報告保存於 `validation_report.json`，執行命令如下：

```bash
cd /home/ubuntu/pob-cli
python3 validate_pob_cli.py
```

| 測試類別 | 結果 | 說明 |
|---|---:|---|
| Python syntax | PASS | 主要腳本與 CLI 模組可編譯 |
| 安裝後 `pob --help` | PASS | console entry point 可正常啟動 |
| 繁中裝備／天賦／技能命令 | PASS | 可讀取 attached_build.xml 並輸出內容 |
| 英文 fallback | PASS | `--locale en` 可停用繁中顯示 |
| XML Build analyze | PASS | 可分析現有 PoB XML |
| Build compare | PASS | 兩個 XML 可完成比較流程 |
| share dry-run | PASS | 可產生分享 code，不會上傳 |
| build DB list／show／export | PASS | JSON 與 XML 產生流程可執行 |
| PoeCharm 更新檢查 | PASS | 可讀取本機 PoeCharm commit 狀態 |
| PoB release 檢查 | PASS | 可向 GitHub release API 比對版本 |
| SSF gear ranking | PASS | PoB 候選與 SSF 成本排序可執行 |
| PoB Headless 計算 | PASS | 官方 PoB Lua 核心可回傳完整 scalar output |
| Config override | PASS | 驗證 key／型別後注入 PoB active ConfigSet |
| PassiveTree diff | PASS | 比較 node、Mastery effect、版本與點數差異 |
| CalcBreakdown JSON | PASS | 官方 breakdown sections 與 damageTypes 可序列化 |
| CalcBreakdown Markdown | PASS | 可輸出人類可讀的 breakdown 報告 |
| ConfigVisibility | PASS | 回傳目前 Build／技能可見 ConfigOptions |
| Defence breakdown | PASS | 回傳 EHP、最大承受傷害、hit／DoT 與防禦 sections |
| Full analysis JSON | PASS | Build、裝備、防禦、物價、官方 scalar 與 warnings |
| Full analysis Markdown | PASS | 可讀的 Build／防禦／裝備／計算報告 |
| Skills details JSON | PASS | 官方 SkillsTab metadata 與 support relationship |
| Skills details Markdown | PASS | 技能組與寶石人類可讀報告 |
| Gem variant classification | PASS | active／support／vaal／transfigured／awakened 分類 |
| Minion context | PASS | minion ID、item set、active skill index |
| Power Report | PASS | 官方 scalar before／after 與技能 context 差異 |
| Gear candidate context | PASS | 49 個候選均保存官方 Power Report 與 skill context |
| PassiveTree candidate recalculation | PASS | node／Mastery 候選 XML、官方重算、Tree diff、TreeData validation 與 HC checks |
| PassiveTree candidate matrix | PASS | 2 個候選、2 個成功、0 個失敗，官方重算與排序完成 |
| 既有 unittest | PASS | CLI、Headless 與 SSF 測試通過 |

## PoB 正式計算證據

使用已知可運作的 `attached_build.xml` 與主技能 `Creeping Frost`：

```bash
pob calc attached_build.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill "Creeping Frost" \
  --format json
```

PoB Headless 回傳成功，PassiveTree 為 `3_29`，主技能選取成功，並得到 760 個 scalar 欄位：

| 欄位 | 數值 |
|---|---:|
| Life | 5,149 |
| Total EHP | 101,832.71 |
| Total DPS | 442,240.55 |
| Total DoT DPS | 100,686.38 |
| Attack Block | 75% |
| Spell Block | 73% |

這表示 **pob-cli 對現有、結構完整的 PoB XML，確實可以使用官方 PoB Lua 核心計算**，不是簡化公式。

## 已確認正常的功能

目前可正常使用的核心命令包括：

```bash
pob calc attached_build.xml --pob-root /home/ubuntu/PathOfBuilding --skill "Creeping Frost" --format json
pob analyze attached_build.xml
pob 天賦 attached_build.xml
pob 技能 attached_build.xml
pob 裝備 attached_build.xml
pob compare attached_build.xml attached_build.xml
pob 分享 attached_build.xml --dry-run
pob 物價 "Divine Orb" --league Allflame
pob 流派 list
pob 流派 show toxic-rain-pathfinder --stage early
pob 流派 export toxic-rain-pathfinder --stage mid --output /tmp/toxic-rain-mid.xml
```

本次實際物價查詢也成功回傳 `Divine Orb` 的 Allflame 資料，結果包含 `found=true` 與 `chaos_value=199.2`。外部價格屬於即時資料，不能視為永久固定值。

## 已完成的新功能

### PoB Config override

`pob calc` 支援可重複指定的 `--config key=value`。CLI 從目前 PoB 核心的 `ConfigOptions.lua` 建立欄位與型別 inventory，拒絕未知 key 與型別錯誤，再將合法值注入 active ConfigSet，呼叫 PoB `ConfigTab:BuildModList()` 後執行正式計算。

```bash
pob calc build.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill "Creeping Frost" \
  --config usePowerCharges=true \
  --config conditionShockEffect=25 \
  --format json
```

### PassiveTree diff

`pob tree-diff current.xml candidate.xml` 已能比較 Tree/Spec 的 node ID、Mastery effect、tree version、class／ascendancy ID 與點數差異，並支援 JSON。完整 node 名稱、Keystone／Notable 語意與路徑圖仍未加入。

## CalcBreakdown 輸出

新增 `pob breakdown` 命令，直接使用 PoB `CalcBreakdown.lua` 產生的 actor breakdown tables，不以 Python 簡化公式重算：

```bash
pob breakdown attached_build.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill "Creeping Frost" \
  --metric dps \
  --format json

pob breakdown attached_build.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill "Creeping Frost" \
  --metric Cold \
  --format markdown
```

目前 JSON 包含 PoB engine/tree metadata、主技能、scalar summary、可用 section 名稱、官方 breakdown lines，以及 PoB 提供時的 `damageTypes` rows。已用 Creeping Frost 驗證取得 165 個 damage breakdown sections；`Cold` section 包含 base damage、damage effectiveness、hit damage、effective DPS modifier 與 damageTypes。

`pob breakdown --metric defence` 已用同一 Build 驗證取得 11 個核心 defence sections，包括 `TotalEHP`、五種 `MaximumHitTaken`、各傷害類型 `TakenHit` 與完整 maximum-hit rowList。代表數值為 Total EHP `101832.71`、Physical maximum hit `10428`、Fire／Cold／Lightning maximum hit `29279`、Chaos maximum hit `20596`。

`pob config-options` 已使用官方 `ConfigVisibility.lua` 對 Creeping Frost Build 篩出 105 個目前可見選項，並回傳變數、型別、label、default 與 list values。

## 完整 Build analysis 輸出

`pob analyze` 已支援 text、JSON、Markdown。對本地 XML 的 JSON／Markdown 模式可呼叫官方 PoB Headless 計算，並保留 Build metadata、裝備原文、基本防禦檢查、物價結果、完整 scalar output 與 warnings。

```bash
pob analyze attached_build.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill "Creeping Frost" \
  --format json
```

Creeping Frost 驗證結果為 760 個官方 scalar 欄位，包含 `TotalDPS=442240.5503` 與 `TotalEHP=101832.7091`；Build 中解析到 23 個 Item。`--skip-calc` 可只產生 XML／Ninja 分析，不執行 Lua 計算。

## PassiveTree 候選官方重算

新增 `pob optimize-tree`，支援 `--add-node`、`--remove-node`、`--mastery nodeId=effectId` 與 `--output candidate.xml`。候選 XML 以原始 XML 的 Tree/Spec 為基礎修改，原始 Build 不會被覆寫；完成後使用官方 PoB Headless 計算 before／after，輸出 Tree diff、Power Report、技能 context 與 HC checks。

```bash
pob optimize-tree attached_build.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill "Creeping Frost" \
  --remove-node 7388 \
  --add-node 7388 \
  --mastery 45558=30612 \
  --format json
```

HC checks 使用官方 scalar：Attack Block >= 70%、Spell Block >= 70%、候選 EHP >= 基準 95%、DPS gain >= 3%。本輪使用 remove／add 相同 node 的零差異 fixture，驗證 node count 133 -> 133、Tree point delta 0、DPS delta 0、EHP delta 0，且候選 Power Report 正常產生。

## TreeData 連通性與批次候選矩陣

新增 `pob optimize-tree-matrix`，輸入 JSON／JSONL 候選矩陣，逐一執行 node／Mastery XML 修改、官方 PoB Headless before／after 計算、Tree diff、TreeData 驗證與 Power Report 排序。排序優先順序為 HC checks 全部通過，其次是 DPS、EHP 與最大承受傷害的 scalar delta。

```bash
pob optimize-tree-matrix attached_build.xml test_tree_matrix.json \\
  --pob-root /home/ubuntu/PathOfBuilding \\
  --skill "Creeping Frost" \\
  --format json
```

本輪測試包含 `same-node-mastery` 與 `remove-intelligence` 兩個候選，結果為 **2 successful／0 failures**。TreeData 驗證會拒絕新增不存在於官方 TreeData 的 node、非法 Mastery node，或相對基準新增的斷線 node；既有 Build 的斷線與 Cluster Jewel／特殊外部 node 會保留為可追蹤 warning，不阻擋正常的官方 PoB 重算。

## 候選 Build Power Report

新增 `pob power-report before.xml after.xml`，對基準與候選 XML 各執行一次官方 PoB Headless 計算，輸出 `scalar_delta`、selected skill 與 before／after skill context。`search_gear_upgrades.py` 現在對每一個候選使用相同的主技能與完整技能 context 重算，並將 `power_report`、`skill_context` 與 `selected_skill` 寫入 `/tmp/gear_upgrade_search_results.json`；本次實際產生 49 個候選，49 個均包含 Power Report。

```bash
pob power-report current.xml candidate.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill "Creeping Frost" \
  --format json
```

## 技能／支援寶石模型輸出

新增 `pob skills --details`，使用官方 PoB SkillsTab runtime，而不是只解析 XML 的自由文字。Creeping Frost Build 驗證取得 1 個 SkillSet、12 個 socket groups，第一組包含 1 個主技能與 5 個支援寶石。每個 gem 提供 level、quality、game ID、variant ID、tags、granted effect、requirements、enabled 與 minion 欄位；支援寶石由官方 `/SupportGem` game ID 路徑判斷。寶石分類另外回傳 `gemType` 與 `classificationSource`：`AltX`／`AltY`／`AltZ` 為 transfigured，Vaal game／variant 為 vaal，名稱／game ID／variant ID 含 Awakened 時為 awakened。召喚物 gem 的 `minionContext` 會回傳 minion ID、計算用 minion ID、item set ID 與 active skill index。

```bash
pob skills attached_build.xml \
  --details \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill "Creeping Frost" \
  --format json
```

## 已知限制與部分正常功能

### 流派 DB 的 PoB XML 主技能載入尚未完成

`pob 流派 export` 可以產生 XML，而且 XML 本身可以被 Headless Build loader 讀取；但是指定新生成 Build 的 `ToxicRain` 主技能時，Headless runner 回傳：

```text
找不到技能：ToxicRain
```

未指定技能時，Build 可以完成載入，但 `SkillsTab` 的 socket group 沒有正常建立。因此目前只能把流派 DB 的 XML 輸出標記為 **可產生、尚未完成 PoB 技能計算驗證**，不能宣稱可直接得到可靠 Toxic Rain DPS。

這不是現有 `attached_build.xml` 的問題；現有 Build 的技能載入與 Creeping Frost 計算已通過。後續需要比對 PoB 實際保存的 SkillSet、Gem metadata、Build section 順序與輸入欄位，再修正匯出器。

### 中文化不是所有句子完整翻譯

PoeCharm 翻譯資料可正常載入固定物品名稱、基底與大量詞綴，但複合句中仍可能出現中英混合，例如某些 `Spells`、`Damage`、`when` 或特殊條件文字。找不到完全相同的 PoeCharm key 時，CLI 會保留英文 fallback。這是翻譯資料 key 對照完整度問題，不是 PoB 計算問題。

### `analyze` 與 `compare` 尚非完整 PoB Report

目前命令可正常執行，但仍未完整重用 `CalcBreakdown.lua`、`CompareTab.lua` 與完整 Config。輸出不能視為涵蓋所有傷害 breakdown、敵人條件、技能支援關係或所有防禦條件的完整 GUI 等價報告。

## TODO 中仍未完成的主要功能

| 優先級 | 功能 | 狀態 |
|---|---|---|
| P0 | `--config key=value` 的 key／型別／值域驗證 | 已完成第一階段 |
| P1 | DPS 與防禦完整 JSON／Markdown schema | 部分完成 |
| P1 | 傷害 breakdown | 已完成第一階段 |
| P1 | 完整元素／物理／混沌／法術／DoT 承傷報告 | 未完成 |
| P1 | PassiveTree diff | 已完成第一階段 |
| P1 | 天賦候選完整 PoB 重算 | 已完成單候選／批次第一階段 |
| P1 | ModParser／ModDB 結構化詞綴 | 未完成 |
| P1 | 完整技能／支援寶石解析 | 部分完成 |
| P1 | slot-aware 裝備替換與候選產生 | 部分完成 |
| P1 | Jewels／Timeless Jewels／特殊物品 | 未完成 |
| P2 | `pob import https://pobb.in/<id>` | 未完成 |
| P2 | 官方 Trade Query CLI | 未完成 |
| P2 | 官方 PoE API 授權與隱私策略 | 未完成 |
| P2 | Ninja adapter fixture 與版本化 | 未完成 |
| P2 | 物價 SQLite 快取／歷史／stale warning | 未完成 |
| P3 | GUI 視覺化、拖曳、Undo 等功能 | 未規劃為核心 CLI 功能 |

## 結論

**核心計算功能正常：** 對現有完整 PoB XML，pob-cli 能呼叫官方 PoB Community Fork Lua 核心並取得正式計算結果。

**CLI 基礎功能正常：** 中文／英文命令、XML 分析、技能／裝備／天賦列出、比較、分享 dry-run、物價查詢、SSF 排名與版本檢查均已通過目前測試。

**整體功能尚未達到「完整重現 PoB GUI」：** Config、breakdown、完整 defence、PassiveTree diff、結構化裝備模型、pobb.in import、官方 Trade API 與部分資料來源仍在 TODO。

**目前最需要修正的程式問題是流派 DB 的 PoB XML 技能載入。** 在這項問題修正並以 Headless 與 GUI 交叉驗證前，不應使用自動生成的 Toxic Rain XML 作為正式 DPS 或 HC 生存結論。
