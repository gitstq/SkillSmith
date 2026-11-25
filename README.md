<div align="center">

# 🛠️ SkillSmith

**Zero-dependency CLI toolkit to scaffold, validate, pack and install agent skill packages.**

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

</div>

---

## 🎉 介绍

Agent 技能包（Skill）正成为 AI 工作流的标准组件，但技能包的**创建、校验、分发与安装**目前缺乏统一工具链。SkillSmith 参考主流 agent skills 框架的产品逻辑，自研了一套端到端的技能包生命周期管理方案：

- **纯 Python 标准库实现**，运行时零第三方依赖，任何 Python ≥ 3.9 环境开箱即用
- 一条命令完成「脚手架 → 校验 → 打包 → 安装 → 管理」全流程
- 内置 SHA-256 完整性清单，安装时可检测包篡改

## ✨ 特性

| 功能 | 说明 |
| --- | --- |
| 🏗️ `new` | 生成规范技能骨架：`SKILL.md`（YAML frontmatter）+ `scripts/` + `references/` |
| ✅ `validate` | 结构与策略校验：命名规范、必填字段、语义化版本、超限告警，支持 `--strict` 与自定义规则注入 |
| 📦 `pack` | 打包为 `.skill` 归档（gzip tar），内置逐文件 SHA-256 清单，字节级可复现 |
| 🚀 `install` | 校验清单后解包安装，幂等重装，冲突需 `--force` |
| 📋 `list` / `uninstall` | 基于 `installed.json` 注册表的安装态管理 |
| 🔌 库形态 | 除 CLI 外可作为库使用：`Scaffold` / `SkillValidator` / `SkillPackager` / `SkillInstaller` |

## 🚀 快速开始

```bash
# 从源码安装
pip install git+https://github.com/gitstq/SkillSmith.git

# 30 秒体验完整流程
skillsmith new my-skill --description "我的第一个技能包"
skillsmith validate my-skill
skillsmith pack my-skill -o dist
skillsmith install dist/my-skill-0.1.0.skill -t ~/.agents/skills
skillsmith list -t ~/.agents/skills
```

源码安装：

```bash
git clone https://github.com/gitstq/SkillSmith.git
cd SkillSmith && pip install .
```

## 📖 使用指南

### 校验规则

- `name`：小写 kebab-case（字母/数字/连字符，2-64 位）
- `description`：必填，超过 1024 字符告警
- `version`：语义化版本 `MAJOR.MINOR.PATCH`
- 缺少 `README.md`、包含 `__pycache__` 等构建产物会给出告警
- `--strict` 模式下告警升级为错误；`extra_rules` 可注入团队自定义规则

### 库调用示例

```python
from pathlib import Path
from skillsmith import Scaffold, SkillValidator, SkillPackager, SkillInstaller

skill = Scaffold().new_skill(Path("skills"), "lint-docs", description="Doc linting")
report = SkillValidator(skill).validate()
if report.ok:
    pkg = SkillPackager(skill).pack(Path("dist"))
    SkillInstaller(Path.home() / ".agents/skills").install(pkg)
```

### `.skill` 包结构

```
manifest.json          # 元数据 + 每个文件的 size/SHA-256
payload/...            # 技能文件本体
```

## 💡 设计迭代

- `v1.0.0`：首发版本。完整生命周期管理、SHA-256 防篡改清单、确定性归档（固定 mtime/uid）保证相同内容打包出相同字节
- 未来计划：签名校验（ed25519）、技能依赖解析、远程 registry

## 📦 打包部署

```bash
# 构建 wheel 与 sdist
bash build.sh          # 产物位于 dist/

# 运行测试套件
python -m pytest tests/ -v
```

## 🤝 贡献

欢迎 Issue 与 PR！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，提交信息遵循 Angular 规范（`feat:` / `fix:` / `docs:` / `refactor:` / `test:`）。

## 📄 协议

本项目基于 [MIT License](LICENSE) 开源。
