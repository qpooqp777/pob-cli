# pob CLI TODO

本檔案只記錄目前尚未完成、尚未以 Path of Building Community Fork 計算核心驗證，或需要額外整合工作的項目。完成後應將該項目移至 README.md 的「目前已完成的 CLI 功能」或更新其狀態，不應只刪除紀錄。

## P0：完整重用 PoB 計算器

### Headless Lua runner — 已完成

`pob CLI` 已使用 Community Fork 的 `src/HeadlessWrapper.lua`，由 LuaJIT 啟動 PoB 的資料載入器、Build object、ModDB、技能／物品資料與 `CalcsTab:BuildOutput()`。Python bridge 目前可取得 Slammerlappen 的 717 個 scalar 計算欄位，包含生命、護甲、抗性、主要技能 DPS、有效生命與各類最大承受傷害。實作與驗證細節已移至 README.md。

已驗證命令：

```bash
pob calc slammerlappen_pob.xml --pob-root /home/ubuntu/PathOfBuilding --format json
```

### 完整 `Calcs` 單一 Build 輸出 — 已完成第一階段

已包裝 `CalcsTab:BuildOutput()`，由 PoB 內部呼叫 `calcs.buildOutput`、`calcs.perform` 與攻擊／防禦計算模組，並以 JSON IPC 回傳 scalar output。Config 覆寫第一階段已完成；剩餘差異工作是 breakdown 結構化、替換方案重算與跨 GUI／CLI 的欄位差異報告。

### 計算 Config — 已完成第一階段

`pob calc` 現在支援可重複指定的 `--config key=value`。CLI 會從安裝中的 `Modules/ConfigOptions.lua` 建立欄位／型別 inventory，驗證 key 與 boolean、integer、float、list、text 值，再將結果注入 PoB active ConfigSet，呼叫 `ConfigTab:BuildModList()` 後執行官方計算。

```bash
pob calc build.xml \
  --skill Earthshatter \
  --config enemyIsBoss=Uber \
  --config usePowerCharges=true \
  --config useEnduranceCharges=true \
  --config useFrenzyCharges=true
```

`pob config-options` 已使用官方 `ConfigVisibility.lua`，依 Build、主技能、天賦、旗標、條件、倍率、敵人狀態與 active Config 輸入列出目前可見選項。剩餘工作是讓 Python schema 也能完整重用每個 list 的官方值域，以及支援 ConfigVisibility 的所有特殊 GUI tooltip。

## P1：完整 Build 分析

### DPS 與防禦 JSON／Markdown 報告 — 已完成第一階段

`pob analyze` 現在支援 `text`、`json`、`markdown`，對本地 PoB XML 可選擇呼叫官方 Headless 計算，並將 Build metadata、技能／主技能、Config、裝備、基本防禦檢查、物價結果、官方 scalar output 與 warnings 放入穩定 schema。

```bash
pob analyze build.xml --pob-root /home/ubuntu/PathOfBuilding --skill Earthshatter --format json
pob analyze build.xml --skill Earthshatter --format markdown
pob analyze build.xml --skip-calc --format json
```

剩餘工作是把完整 Tree／Skills／Config／Items 結構化資料加入同一 schema，並整合完整 Power Report、breakdown 與候選方案比較。

### 傷害 breakdown — 已完成第一階段

已整合 `Modules/CalcBreakdown.lua` 產生的 actor breakdown tables，透過 Headless bridge 輸出官方 breakdown lines、damageTypes、DPS scalar 摘要與 JSON／Markdown 格式。

```bash
pob breakdown build.xml --skill Earthshatter --metric dps --format markdown
pob breakdown build.xml --skill Earthshatter --metric Cold --format json
```

目前支援 `all`、`dps`、`defence`、`AverageHit`、`Physical`、`Fire`、`Cold`、`Lightning`、`Chaos`。剩餘工作是完整串接所有 CalcsTab 可見條件、完整防禦 breakdown、ConfigVisibility 與跨技能／召喚物 breakdown。

### 有效生命與最大承受傷害 — 已完成第一階段

`pob breakdown --metric defence` 現在輸出官方 `CalcDefence.lua`／actor breakdown 可用資料，包括生命、能量護盾、魔力、護甲、閃避、Ward、格擋、閃避率、法術壓制、抗性、物理減傷、Total EHP、總承受 hit、物理／元素／混沌最大承受傷害、hit breakdown、DoT multiplier、DoT EHP 與 resource pool。

```bash
pob breakdown build.xml --skill Earthshatter --metric defence --format markdown
pob breakdown build.xml --skill Earthshatter --metric defence --format json
```

剩餘工作是完整重現 GUI 的敵人條件／穿透／暴擊情境選擇、所有專用 defence panel、PvP 與特殊召喚物承傷資料。

## P1：天賦樹與 Build 比較

### PassiveTree diff — 已完成第一階段

`pob tree-diff current.xml candidate.xml` 現在比較兩個 PoB XML 的 Tree/Spec，輸出新增／移除 node ID、Mastery effect、tree version、class／ascendancy ID 與點數差異，並支援 JSON。

```bash
pob tree-diff current.xml candidate.xml
pob tree-diff current.xml candidate.xml --format json
```

剩餘工作是解析 node 名稱、Keystone、Notable、Mastery 顯示文字與路徑差異，並整合完整 TreeData localization。

### 天賦方案自動比較 — 已完成第一階段

`pob optimize-tree` 會從原始 XML 建立隔離候選，支援 `--add-node`、`--remove-node` 與 `--mastery nodeId=effectId`，再以官方 PoB Headless 重算基準／候選，輸出 Tree diff、scalar delta、技能 context、Power Report 與 HC 硬性條件。

```bash
pob optimize-tree build.xml \
  --remove-node 7388 \
  --add-node 7388 \
  --mastery 45558=30612 \
  --skill Earthshatter \
  --format json
```

目前已完成單一候選的安全 XML 修改與官方重算。`pob optimize-tree-matrix` 已支援 JSON／JSONL 批次候選、官方 PoB 重算、HC-first 排序、失敗候選隔離，以及依官方 TreeData 的 node 存在性、職業起點連通性與 Mastery 合法性驗證。既有 Build 的斷線會以 baseline warning 保留；候選新增斷線會被拒絕。

```bash
pob optimize-tree-matrix build.xml candidates.json \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill Earthshatter --format json
```

剩餘工作是從 TreeData 自動產生候選路徑矩陣、驗證職業／昇華限制的完整語意、加入更多特殊 TreeData 節點類型，以及完整 CompareTab GUI 等價欄位。

預期命令：

```bash
pob optimize build.xml --remove 14206 --set-mastery 35977=23021
```

### CompareTab 功能 — Power Report 與 PassiveTree 候選第一階段完成

新增 `pob power-report before.xml after.xml`，使用官方 PoB Headless 對兩個 XML 重算，輸出 scalar delta、DPS／EHP／最大承受傷害、selected skill 與 before／after 技能 context。裝備候選搜尋也會為每個候選保存 `power_report`、`skill_context` 與 `selected_skill` 後再交給 SSF 成本排名。

```bash
pob power-report current.xml candidate.xml --skill Earthshatter --format json
```

剩餘工作是完整輸出 Config／Items／Tree diff、Power Report、完整 CompareTab 欄位、由 TreeData 自動產生批次候選路徑，以及技能候選方案的 GUI 等價比較。

## P1：技能、裝備與資料模型

### ModParser／ModDB adapter

目前裝備詞綴仍以原始文字比對為主。需要將 `Modules/ModParser.lua` 和 `Classes/ModDB.lua` 的詞綴解析結果轉成可查詢的結構，例如 `maximum_life`、`chaos_resistance`、`increased_armour`、`more_physical_attack_damage` 和觸發條件。

### 技能與支援寶石完整解析 — 已完成第一階段

`pob skills --details` 現在使用官方 PoB SkillsTab runtime，解析 skill set、socket group、主技能、支援寶石、啟用狀態、DPS inclusion、gem level、quality、PoB game ID、variant ID、tags、granted effect、需求與 minion 設定。

```bash
pob skills build.xml --details --skill Earthshatter --format json
pob skills build.xml --details --skill Earthshatter --format markdown
```

支援寶石分類使用官方 PoB game ID 的 `/SupportGem` 路徑，不依賴自由文字名稱猜測。已補上 `active`、`support`、`vaal`、`transfigured`、`awakened` 分類，以及召喚物的 minion ID、計算用 minion ID、item set 與 active skill index context。已完整輸出每個 gem 的 `skillPart`、`skillPartCalcs`、`skillStageCount`、`skillStageCountCalcs`、`skillMineCount`、`skillMineCountCalcs`，並補上 minion ID、計算用 minion ID、item set、active skill index 與 grantedEffect minion list。剩餘工作是把技能模型整合進候選 Build 重算與 Power Report，並在 PoB runtime 有資料時解析更高階的 active skill 名稱與專用 context。

### 裝備替換與候選產生

建立 slot-aware item model，支援物品稀有度、基底、implicit、explicit、crafted、fractured、enchant、corrupted、socket、link 與 influence。之後才能可靠地計算「替換這件裝備後」的結果，而不是只以詞綴文字推測。

### Jewels、Timeless Jewels 與特殊物品

需要接入 `DataJewelFileLoader.lua`、Timeless Jewel lookup table、Abyss／Legion lookup table 與特殊物品技能。沒有這些資料時，不應對相關 Build 宣稱完整計算。

## P2：匯入、匯出與外部服務

### pobb.in 下載／匯入

PoB 原始碼已提供 `BuildSiteTools.DownloadBuild` 的 URL 轉換與下載流程，但 pob CLI 尚未提供：

```bash
pob import https://pobb.in/<id> --output build.xml
```

需要下載 raw XML、錯誤處理、壓縮／Base64 解碼，以及驗證 XML root 為 `PathOfBuilding`。

### 其他分享站

PoB 原始碼還包含 Maxroll、pob.codes、PoeNinja、Pastebin、Rentry 與 poedb.tw 的網站設定。應先逐一確認現行端點，再加入 `pob share --site <site>`；不能假設每個站點的 API 永久有效。

### 官方 PoE API

需要建立授權與隱私策略，支援公開角色、天梯、stash、聯盟與帳號資料。不得把未文件化的 poe.ninja 角色端點當作穩定 API，也不得在沒有使用者授權時讀取私人資料。

### Trade Query CLI

重用 `TradeQueryGenerator.lua`、`TradeQueryRequests.lua` 與 `TradeQueryRateLimiter.lua` 的概念，讓 CLI 能從物品需求產生官方交易搜尋 JSON／URL。需要處理詞綴 ID、數值範圍、聯盟、Online 狀態、排序與 rate limit。

預期命令：

```bash
pob trade search --slot ring --life 80 --chaos-res 30 --league <league>
```

## P2：角色與經濟分析

### Ninja Build 頁面與角色資料

目前 Ninja adapter 是 best-effort，能處理提供的 JSON／頁面內嵌資料，但未文件化的單角色端點可能變更、快取或受角色隱私限制。需要建立版本化 adapter、固定 fixture 與失敗降級到 PoB XML 的流程。

### 價格快取與成本效益

目前能查詢 poe.ninja 物價，但尚未儲存快照、計算價格歷史、估算裝備總成本，或比較「防禦／DPS 增益 ÷ Divine 成本」。需要 SQLite cache、時間戳、聯盟欄位與 stale data 警告。

## P3：PoB GUI 周邊功能

以下功能屬 GUI 工作流，只有在 CLI 需求明確後才實作：

| 功能 | 原始碼方向 | CLI 替代 |
|---|---|---|
| TreeTab 視覺化 | `Classes/TreeTab.lua`、`PassiveTreeView.lua` | node list、diff、JSON 或 Mermaid |
| ItemsTab 拖曳操作 | `Classes/ItemsTab.lua` | `pob item add/remove/replace` |
| SkillsTab 連線操作 | `Classes/SkillsTab.lua` | `pob skill set/enable/disable` |
| UndoHandler | `Classes/UndoHandler.lua` | immutable input、輸出新 XML、transaction log |
| Tooltip／Popup | 多個 Control class | 純文字說明與 Markdown 報告 |
| Build folder UI | `BuildList.lua`、`BuildListControl.lua` | `pob list`、`pob validate` |

## 品質與安全要求

所有計算功能必須保留來源版本，例如 PoB commit、PassiveTree 版本、技能資料版本和聯盟。所有外部 HTTP 請求必須使用合理 User-Agent、timeout、重試上限與 cache；公開上傳 `pobb.in` 前應由使用者明確執行 `pob share`，分析命令不能暗中上傳 Build。

每個新增計算模組都應加入 fixture-based test，至少包含一個可在 PoB GUI 交叉驗證的 Build。若 CLI 尚未使用真正的 PoB calculator，輸出必須標示為「簡化分析」而不能宣稱與 PoB DPS 完全相同。

## 參考原始碼

[1]: https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Modules/BuildSiteTools.lua "BuildSiteTools.lua"

[2]: https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Classes/ImportTab.lua "ImportTab.lua"

[3]: https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Modules/Calcs.lua "Calcs.lua"

[4]: https://github.com/PathOfBuildingCommunity/PathOfBuilding/tree/dev/src/Modules "PoB calculation modules"
