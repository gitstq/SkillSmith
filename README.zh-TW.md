<div align="center">

# 🛠️ SkillSmith

**用純標準庫打造：Agent 技能包的腳手架、校驗、打包與安裝一站式 CLI 工具**

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

</div>

---

## 🎉 介紹

Agent 技能包（Skill）正成為 AI 工作流的標準組件，但技能包的**建立、校驗、分發與安裝**目前缺乏統一工具鏈。SkillSmith 參考主流 agent skills 框架的產品邏輯，自研了一套端到端的技能包生命週期管理方案：

- **純 Python 標準庫實作**，執行時零第三方相依，任何 Python ≥ 3.9 環境開箱即用
- 一條命令完成「腳手架 → 校驗 → 打包 → 安裝 → 管理」全流程
- 內建 SHA-256 完整性清單，安裝時可偵測套件遭竄改

## ✨ 特性

| 功能 | 說明 |
| --- | --- |
| 🏗️ `new` | 產生規範技能骨架：`SKILL.md`（YAML frontmatter）+ `scripts/` + `references/` |
| ✅ `validate` | 結構與策略校驗：命名規範、必填欄位、語意化版本、超限警示，支援 `--strict` 與自訂規則注入 |
| 📦 `pack` | 打包為 `.skill` 封存檔（gzip tar），內建逐檔案 SHA-256 清單，位元組級可重現 |
| 🚀 `install` | 校驗清單後解包安裝，冪等重裝，衝突需 `--force` |
| 📋 `list` / `uninstall` | 基於 `installed.json` 註冊表的安裝態管理 |
| 🔌 函式庫形態 | 除 CLI 外可作為函式庫使用：`Scaffold` / `SkillValidator` / `SkillPackager` / `SkillInstaller` |

## 🚀 快速開始

```bash
# 從 PyPI 安裝（或使用下方原始碼安裝）
pip install skillsmith

# 30 秒體驗完整流程
skillsmith new my-skill --description "我的第一個技能包"
skillsmith validate my-skill
skillsmith pack my-skill -o dist
skillsmith install dist/my-skill-0.1.0.skill -t ~/.agents/skills
skillsmith list -t ~/.agents/skills
```

原始碼安裝：

```bash
git clone https://github.com/gitstq/SkillSmith.git
cd SkillSmith && pip install .
```

## 📖 使用指南

### 校驗規則

- `name`：小寫 kebab-case（字母/數字/連字號，2-64 位）
- `description`：必填，超過 1024 字元警示
- `version`：語意化版本 `MAJOR.MINOR.PATCH`
- 缺少 `README.md`、包含 `__pycache__` 等建置產物會給出警示
- `--strict` 模式下警示升級為錯誤；`extra_rules` 可注入團隊自訂規則

### 函式庫呼叫範例

```python
from pathlib import Path
from skillsmith import Scaffold, SkillValidator, SkillPackager, SkillInstaller

skill = Scaffold().new_skill(Path("skills"), "lint-docs", description="Doc linting")
report = SkillValidator(skill).validate()
if report.ok:
    pkg = SkillPackager(skill).pack(Path("dist"))
    SkillInstaller(Path.home() / ".agents/skills").install(pkg)
```

### `.skill` 包結構

```
manifest.json          # 中繼資料 + 每個檔案的 size/SHA-256
payload/...            # 技能檔案本體
```

## 💡 設計迭代

- `v1.0.0`：首發版本。完整生命週期管理、SHA-256 防竄改清單、確定性封存（固定 mtime/uid）保證相同內容打包出相同位元組
- 未來規劃：簽章校驗（ed25519）、技能相依解析、遠端 registry

## 📦 打包部署

```bash
# 建置 wheel 與 sdist
bash build.sh          # 產物位於 dist/

# 執行測試套件
python -m pytest tests/ -v
```

## 🤝 貢獻

歡迎 Issue 與 PR！請先閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)，提交資訊遵循 Angular 規範（`feat:` / `fix:` / `docs:` / `refactor:` / `test:`）。

## 📄 授權條款

本專案基於 [MIT License](LICENSE) 開源。
