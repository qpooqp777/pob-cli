# pob CLI 使用手冊

`pob CLI` 是 Path of Building Community Fork 的 PoE1 命令列分析工具。它可以讀取 PoB XML、列出天賦／技能／裝備、使用 PoB Lua Headless 計算核心取得精確防禦與傷害數據、查詢 poe.ninja 物價，並依照 PoB 內建流程產生 `pobb.in` 分享網址。

本手冊以 Linux／Ubuntu、PoE1、Path of Building Community Fork 和 Python 3 為例。命令輸出通常使用繁體中文；需要給其他程式處理時，可使用 `--format json`。

## 1. 安裝前提

使用純 XML 解析、天賦列出、技能列出、裝備列出和簡化分析時，只需要 Python 3。使用 `pob calc` 的精確 PoB 計算時，還需要 LuaJIT 與 Path of Building Community Fork 原始碼。使用 `pob price`、`pob analyze --price` 或 `pob share` 時，需要網路連線。

| 能力 | 必要條件 |
|---|---|
| `tree`、`skills`、`items` | Python 3 |
| `analyze` | Python 3；若輸入 Ninja 公開頁，還需要網路 |
| `calc` | Python 3、LuaJIT、PoB Community Fork 原始碼 |
| `price` | Python 3、網路、可用 poe.ninja economy API |
| `share` | Python 3、網路；實際上傳會公開 Build |
| `compare` | Python 3、兩個 PoB XML |

安裝 Python 套件：

```bash
cd pob-cli
python3 -m pip install --user -e .
```

安裝 LuaJIT：

```bash
sudo apt update
sudo apt install -y luajit
```

確認命令已安裝：

```bash
pob --help
```

如果不想安裝套件，可以從專案根目錄執行：

```bash
PYTHONPATH=. python3 -m pob_cli --help
```

## 2. Path of Building 計算核心設定

`pob calc` 會啟動 PoB Community Fork 的 Headless Lua runner。CLI 會依序嘗試 `--pob-root`、環境變數 `POB_ROOT`、`/home/ubuntu/PathOfBuilding` 和使用者家目錄下的 `PathOfBuilding`。

```bash
export POB_ROOT="$HOME/PathOfBuilding"
pob calc build.xml --skill Earthshatter
```

也可以明確指定來源目錄：

```bash
pob calc build.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill Earthshatter
```

`POB_ROOT` 必須包含：

```text
PathOfBuilding/
├── src/HeadlessWrapper.lua
├── src/Launch.lua
├── src/Modules/
├── src/TreeData/
└── runtime/
```

若出現 `找不到 luajit`，請安裝 LuaJIT 或將 `luajit` 放入 `PATH`。若出現 `找不到 PathOfBuilding`，請使用 `--pob-root`。若 Build XML 來自不同 PoE 版本，請使用與該 XML 相容的 Community Fork 版本。

## 3. 全域 help 與命令總覽

```bash
pob --help
```

目前命令如下：

| 命令 | 用途 |
|---|---|
| `pob calc` | 使用 PoB Lua 核心精確計算單一 Build |
| `pob analyze` | 產生 Build／角色的繁中分析報告 |
| `pob tree` | 列出已配置的 PassiveTree 節點 |
| `pob skills` | 列出技能組與技能寶石 |
| `pob items` | 列出裝備與原始詞綴 |
| `pob compare` | 比較兩個 Build 的基本防禦欄位 |
| `pob price` | 查詢 poe.ninja 物價 |
| `pob share` | 依 PoB 流程上傳至 `pobb.in` 或只產生分享 code |

每個命令都支援自己的 help：

```bash
pob calc --help
pob analyze --help
pob tree --help
pob skills --help
pob items --help
pob compare --help
pob price --help
pob share --help
```

## 4. `pob calc`：使用 PoB Lua 精確計算

### 語法

```bash
pob calc BUILD [--pob-root POB_ROOT] [--format text|json] [--skill SKILL] [--timeout SECONDS]
```

| 參數 | 說明 |
|---|---|
| `BUILD` | PoB XML 檔案 |
| `--pob-root` | Path of Building Community Fork 根目錄 |
| `--format text` | 預設值，輸出繁中摘要 |
| `--format json` | 輸出完整 JSON，適合腳本或其他程式讀取 |
| `--skill SKILL` | 指定要計算的主技能，例如 `Earthshatter` |
| `--timeout` | Lua 計算逾時秒數，預設 180 秒 |

### 互動範例：計算 Earthshatter

```console
$ pob calc slammerlappen_pob.xml --pob-root /home/ubuntu/PathOfBuilding --skill Earthshatter
PoB Lua 計算器｜PassiveTree 3_29
================================================================
生命                3620
能量護盾              0
護甲                17253
閃避                 437
火焰抗性              84
冰冷抗性              81
閃電抗性              81
混沌抗性              -1
總有效生命          23344.14
總 DPS           203075.42
混沌最大承受傷害       6615
```

### 互動範例：輸出 JSON

```bash
pob calc slammerlappen_pob.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill Earthshatter \
  --format json > slammerlappen-earthshatter.json
```

JSON 包含 `engine`、`tree`、`level`、`class`、`selected_skill`、`available_skills` 和 `output`。`output` 是 PoB `calcsOutput` 的 scalar 欄位，包含生命、護甲、抗性、DPS、攻速、命中、有效生命和各類最大承受傷害。

### 互動範例：不知道技能名稱時

先列出技能：

```bash
pob skills slammerlappen_pob.xml
```

再使用輸出的完整技能名稱：

```bash
pob calc slammerlappen_pob.xml \
  --pob-root /home/ubuntu/PathOfBuilding \
  --skill Earthshatter
```

指定技能會改變 `CalcsTab` 的技能選擇；如果不指定 `--skill`，CLI 使用 PoB 當前預設技能，可能不是角色的主攻擊技能。因此分析 DPS 時應明確指定主技能。

## 5. `pob analyze`：產生 Build 分析

### 語法

```bash
pob analyze SOURCE [--league LEAGUE] [--price ITEM]
```

`SOURCE` 可以是 PoB XML、本地 JSON，或可解析的公開 Ninja 角色頁資料。`--league` 指定物價查詢聯盟；`--price` 可重複使用，用來在分析報告中附加物價。

```bash
pob analyze slammerlappen_pob.xml
```

加入物價查詢：

```bash
pob analyze slammerlappen_pob.xml \
  --league allflame \
  --price "Divine Orb" \
  --price "Mageblood"
```

Ninja 角色資料可能是快取快照、角色未被收錄或因隱私設定而無法取得。若需要精確天賦、技能、裝備和 PoB 計算，應先從 PoB 或 Ninja 頁面取得 PoB XML，再使用 `pob calc`。

## 6. `pob tree`：查看天賦樹

### 語法

```bash
pob tree BUILD [--all]
```

預設只列出重要節點：Keystone、Notable、Mastery 和其他具名稱的節點。

```bash
pob tree slammerlappen_pob.xml
```

列出所有普通小天賦：

```bash
pob tree slammerlappen_pob.xml --all > slammerlappen-tree.txt
```

互動範例：尋找所有 Mastery：

```console
$ pob tree slammerlappen_pob.xml --all | grep -i mastery
35977  Warcry Mastery       Warcries cannot Exert Travel Skills
8460   Warcry Mastery       Warcries cannot Exert Travel Skills
4707   Charge Mastery        100% increased Charge Duration
```

節點 ID 和 Mastery effect ID 很重要。若要建立候選天賦方案，應保留原始 XML，複製成新的候選檔後再修改 `masteryEffects` 或 `nodes`。

## 7. `pob skills`：查看技能組

### 語法

```bash
pob skills BUILD
```

```console
$ pob skills slammerlappen_pob.xml
技能組 1：Frostblink
技能組 2：Blood Rage
技能組 3：Molten Shell
技能組 4：Rallying Cry
技能組 5：Autoexertion
技能組 6：Earthshatter
```

技能列表用於確認 `pob calc --skill` 的名稱，也能快速確認主技能、位移、Guard、Warcry 和光環配置。技能列表本身不等於完整技能 DPS；DPS 必須使用 `pob calc` 和 PoB Lua 核心。

## 8. `pob items`：查看裝備與詞綴

### 語法

```bash
pob items BUILD
```

```console
$ pob items slammerlappen_pob.xml
[10] Rarity: RARE Chimeric Salvation Astral Plate
Armour: 1792
+12% to all Elemental Resistances
+139 to Armour
72% increased Armour
+21% to Fire Resistance
+28% to Cold Resistance
crafted +24% to Lightning Resistance
```

輸出的是 PoB XML 中的原始裝備文字。使用者可根據它辨識低基礎護甲、沒有生命、缺少混沌抗性、武器 DPS 不足、抗性超額或 Mastery 條件不成立等問題。

常見互動流程：

```bash
pob items build.xml > items.txt
grep -iE "body|astral|chaos|life|armour" items.txt
```

## 9. `pob compare`：比較兩個 Build

### 語法

```bash
pob compare CURRENT CANDIDATE
```

```bash
pob compare current.xml candidate.xml
```

目前比較器主要比較基本防禦欄位，例如生命、護甲、元素抗性、混沌抗性和法術壓制。若需要比較完整 DPS、有效生命、最大承受傷害與技能條件，請對兩個檔案分別執行 `pob calc --format json`，再比較 JSON。

```bash
pob calc current.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > current.json
pob calc candidate.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > candidate.json
pob compare current.xml candidate.xml
```

候選檔案不應覆寫原始 Build。建議命名為 `build-candidate-chaos-res.xml`、`build-candidate-charge-mastery.xml` 等。

## 10. `pob price`：查詢 poe.ninja 物價

### 語法

```bash
pob price NAME [--league LEAGUE]
```

```bash
pob price "Divine Orb"
pob price "Mageblood" --league allflame
```

互動範例：

```console
$ pob price "Divine Orb"
聯盟：Allflame
物品：Divine Orb
混沌石價格：145.2
```

聯盟名稱應與 poe.ninja 當前 API 使用的名稱一致。省略 `--league` 時，CLI 會嘗試自動判斷目前聯盟。價格是市場快照，可能延遲或因 API 快取而變動；HC SSF 不應把交易價格當成實際可取得性。

## 11. `pob share`：建立 pobb.in 分享網址

### 語法

```bash
pob share BUILD
pob share BUILD --dry-run
```

`pob share BUILD` 會依 Path of Building Community Fork 的內建流程，將 PoB code 以 Deflate 壓縮、URL-safe Base64 編碼，再上傳到 `https://pobb.in/pob/`。成功後會輸出公開分享網址。

```console
$ pob share slammerlappen_pob.xml
pobb.in 分享網址：https://pobb.in/AbCdEf12
```

這是會公開 Build 的網路操作。執行前應確認 XML 不含不想公開的資訊。

若只想檢查分享 code，不上傳：

```bash
pob share slammerlappen_pob.xml --dry-run > slammerlappen-share-code.txt
```

`--dry-run` 適合測試壓縮／編碼流程或把 code 交給其他工具。分析命令不會自動上傳 Build。

## 12. 建議工作流程

### 流程 A：第一次分析一個 PoB Build

```bash
pob skills build.xml
pob tree build.xml
pob items build.xml
pob calc build.xml --pob-root "$POB_ROOT" --skill Earthshatter
pob calc build.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > baseline.json
```

先確認主技能，再讀取天賦和裝備，最後執行精確計算。這能避免把 Frostblink、Guard 技能或輔助技能誤當成主 DPS。

### 流程 B：HC SSF 生存優化

```bash
pob calc build.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > baseline.json
pob tree build.xml --all > tree.txt
pob items build.xml > items.txt
cp build.xml candidate-chaos-res.xml
# 修改 candidate-chaos-res.xml 後：
pob calc candidate-chaos-res.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > candidate.json
pob compare build.xml candidate-chaos-res.xml
```

優先比較混沌抗性、最大承受傷害、有效生命、護甲、生命回復和異常狀態防護，再考慮小幅 DPS。對 SSF，將候選寫成可用工藝、掉落或現有庫存能達成的詞綴目標。

### 流程 C：比較天賦 Mastery

```bash
cp build.xml candidate-warcry.xml
cp build.xml candidate-charge.xml
# 在候選 XML 中修改 masteryEffects
pob calc build.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > base.json
pob calc candidate-warcry.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > warcry.json
pob calc candidate-charge.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > charge.json
```

需要區分靜態數值與事件型效果。例如 `Recover 15% of Life when you use a Warcry` 可能不改變靜態 `Life` 或 `TotalEHP`，但以 3,620 Life 的角色來說，理論上每次 Warcry 可恢復 543 Life；報告中應把這種效果標示為條件式戰鬥收益，而不能說它沒有作用。

### 流程 D：建立分享網址

```bash
pob share build.xml --dry-run
pob share build.xml
```

先用 `--dry-run` 驗證，再由使用者明確執行實際上傳。`pobb.in` 分享網址公開後，任何取得網址的人都可能讀取 Build 內容。

## 13. 錯誤處理與診斷

| 錯誤情況 | 常見原因 | 處理方式 |
|---|---|---|
| `找不到 luajit` | LuaJIT 未安裝或不在 PATH | `sudo apt install -y luajit` |
| `找不到 PathOfBuilding` | 未找到 `HeadlessWrapper.lua` | 使用 `--pob-root` 或設定 `POB_ROOT` |
| `找不到技能` | 名稱拼寫不同或技能未載入 | 先執行 `pob skills build.xml` |
| XML 解析失敗 | 檔案不是 PoB XML 或版本不相容 | 從 PoB 重新匯出 XML |
| 物價查不到 | 名稱、聯盟或 API 資料不匹配 | 使用完整物品名稱與 `--league` |
| Ninja 角色沒有資料 | 私人角色、未被收錄或頁面資料是動態載入 | 使用 PoB XML |
| `pobb.in` 上傳失敗 | 網路、服務或端點暫時不可用 | 先用 `--dry-run`，稍後重試 |
| 計算逾時 | Build 複雜、Lua 啟動慢或 runtime 問題 | 增加 `--timeout`，例如 `--timeout 300` |

遇到計算錯誤時，先執行：

```bash
pob calc build.xml --pob-root "$POB_ROOT" --skill Earthshatter --timeout 300
```

如果仍失敗，保留完整錯誤輸出、PoB Community Fork commit、Build XML 和使用的技能名稱，這些資料是重現問題所需的最小資訊。

## 14. 腳本化與 JSON 使用

`--format json` 適合接到 `jq`、Python、Shell 或 CI pipeline：

```bash
pob calc build.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json \
  | jq '.output | {life: .Life, armour: .Armour, chaos_res: .ChaosResist, dps: .TotalDPS}'
```

輸出 CSV 風格摘要：

```bash
pob calc build.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json \
  | jq -r '[.level, .class, .selected_skill, .output.Life, .output.Armour, .output.ChaosResist, .output.TotalDPS] | @csv'
```

候選方案應保存原始 JSON：

```bash
mkdir -p reports
pob calc build.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > reports/base.json
pob calc candidate.xml --pob-root "$POB_ROOT" --skill Earthshatter --format json > reports/candidate.json
```

## 15. 目前功能邊界

目前 `pob calc` 已能載入 PoB XML、選擇主技能並呼叫 PoB Community Fork 的 Headless Lua 計算核心。尚未完成的功能包括完整 `--config key=value` 覆寫、修改天賦／裝備後自動搜尋所有候選、完整傷害 breakdown JSON、完整多 Build DPS 比較和官方帳號／stash API 整合。詳細待辦事項請查看專案的 `TODO.md`。

Ninja 角色頁通常是公開快照，不應視為穩定的單角色 API。需要精確且可重現的分析時，請優先使用 PoB XML。物價屬於市場快照；HC SSF 分析時，應把它作為資訊參考而不是升級可行性的判定。

## 16. 相關文件

| 文件 | 用途 |
|---|---|
| `README.md` | 專案概覽、原始碼盤點與功能矩陣 |
| `CLI_USAGE.md` | 本完整命令列使用手冊 |
| `TODO.md` | 尚未完成的 CLI 功能與後續實作順序 |
| `tests/test_cli.py` | 基本 CLI 與資料解析測試 |
| `tests/test_headless.py` | PoB Lua Headless integration test |

## 17. PoeCharm 繁中翻譯自動更新與中文命令

`pob-cli` 內建 `pob_cli/locales/zh_TW.json`，來源是 PoeCharm 的 `Data/Translate/zh-rTW`。使用下列命令可檢查 GitHub 來源的最新 commit；只有來源 commit 變更，或輸出檔不存在時，才重新產生 JSON：

```bash
python3 update_poecharm_translations.py
```

首次執行會建立 `.cache/PoeCharm`；之後會以 shallow Git fetch 更新來源，並把最近匯入的 commit 記錄在 `locales/.poecharm_update.json`。只檢查、不改檔案：

```bash
python3 update_poecharm_translations.py --check-only
```

每週一上午 06:30 檢查一次的 Linux cron 範例：

```cron
30 6 * * 1 cd /home/ubuntu/pob-cli && /usr/bin/python3 update_poecharm_translations.py >> /home/ubuntu/.cache/pob-cli-poecharm.log 2>&1
```

預設語系為繁體中文，英文命令仍然保留：

```bash
pob --locale zh-TW 裝備 attached_build.xml
pob --locale zh-TW 天賦 attached_build.xml
pob --locale zh-TW 技能 attached_build.xml
pob --locale zh-TW 分析 https://poe.ninja/poe1/profile/...
pob --locale en items attached_build.xml
```

可用 `--translations` 指定另一個轉換後的 JSON。中文命令別名包含 `計算`、`分析`、`天賦`、`天賦樹`、`技能`、`裝備`、`物品`、`分享`、`比較`、`物價` 和 `價格`。翻譯只改變顯示層，不改變 PoB XML、Lua 計算核心或傳給 poe.ninja 的英文查詢鍵；找不到翻譯時會保留英文原文。

相關檔案如下：

| 檔案 | 用途 |
|---|---|
| `import_poecharm_translations.py` | 將 PoeCharm CSV 轉換成 `zh_TW.json` |
| `update_poecharm_translations.py` | 檢查 Git commit 並在有更新時重新轉換 |
| `pob_cli/i18n.py` | 載入 catalog、英文 fallback 與複合物品文字翻譯 |
| `pob_cli/locales/zh_TW.json` | 安裝後可直接讀取的內建繁中資料 |

## 18. PoB Community Fork 版本檢查與更新

PoE1 PoB 核心版本可透過 `update_pob_core.py` 對照 [PathOfBuildingCommunity releases](https://github.com/PathOfBuildingCommunity/PathOfBuilding/releases) 的最新穩定 release。預設為唯讀檢查，不會修改本機核心：

```bash
python3 update_pob_core.py \
  --source-dir /home/ubuntu/PathOfBuilding
```

目前腳本會讀取本機 `manifest.xml` 的 `<Version>`，並向 GitHub release API 取得 `tag_name`。若需要真正切換版本，必須明確加入 `--apply`；腳本只允許乾淨的 Git worktree，避免覆蓋未提交修改：

```bash
python3 update_pob_core.py \
  --source-dir /home/ubuntu/PathOfBuilding \
  --apply \
  --state /home/ubuntu/pob-cli/.pob_core_update.json
```

`--apply` 會先 fetch tags，再 detached checkout 最新穩定 tag，並在 state JSON 保存更新前後 commit。若工作區有修改，腳本會停止；不建議使用 `--force`，除非已經自行備份。

每週檢查 PoB 核心和 PoeCharm 翻譯的 cron 範例：

```cron
30 6 * * 1 cd /home/ubuntu/pob-cli && /usr/bin/python3 update_pob_core.py --source-dir /home/ubuntu/PathOfBuilding >> /home/ubuntu/.cache/pob-cli-pob.log 2>&1
35 6 * * 1 cd /home/ubuntu/pob-cli && /usr/bin/python3 update_poecharm_translations.py >> /home/ubuntu/.cache/pob-cli-poecharm.log 2>&1
```

PoB 核心更新後，應重新執行驗證：

```bash
python3 validate_pob_cli.py
```

驗證報告會寫入 `validation_report.json`，目前測試涵蓋 Python syntax、CLI help、中文／英文命令、PoeCharm 更新檢查、PoB release 檢查、SSF 裝備成本排名、PoB Lua Headless 計算與既有 unittest。

## References

[1]: https://github.com/PathOfBuildingCommunity/PathOfBuilding "Path of Building Community Fork"

[2]: https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/HeadlessWrapper.lua "PoB HeadlessWrapper.lua"

[3]: https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Modules/BuildSiteTools.lua "PoB BuildSiteTools.lua"
