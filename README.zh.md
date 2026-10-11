<h1 align="center">grape-template</h1>

<p align="center"><a href="README.md">English</a> | 中文</p>

<p align="center">
  <strong>Grape 官方项目模板独立仓库</strong>
  <br>
  官方内置模板在此维护，与 grape 主仓独立发版。
</p>

<p align="center">
  <a href="#grape-template-是什么">grape-template 是什么</a> ·
  <a href="#目录约定">目录约定</a> ·
  <a href="#模板注册表结构">模板注册表结构</a> ·
  <a href="#本地模板列表">本地模板列表</a> ·
  <a href="#新增模板">新增模板</a> ·
  <a href="#使用">使用</a>
</p>

---

## grape-template 是什么

`grape-template` 是 Grape 官方项目模板的独立仓库。在 **grape 主仓的构建/部署阶段**，
`scripts/sync_templates.sh` 会将本仓库内容拉取到部署根目录：

- 模板目录 → `examples/`
- 模板注册表 → `configs/project-templates.json`

模板独立成仓，便于与平台本体分开维护、单独发版。

**一句话：在这里新增模板 + 在 `project-templates.json` 登记 `id` → 该模板就会出现在 Grape 的「创建项目」流程里。**

## 目录约定

| 目录/文件 | 说明 |
|---|---|
| `hello-*` | 官方本地模板。目录名即模板 `id`，与 `project-templates.json` 中 `source: "local"` 的条目一一对应 |
| `project-templates.json` | 模板注册表——含 local 与 git 模板全量条目，按分类组织，随本仓库独立发版 |

## 模板注册表结构

`project-templates.json` 按分类（`categories`）组织全部模板。其中 `cloud-native` 与 `iac` 分类每日自动同步，
条目数随同步结果浮动：

| category `id` | 分类名 | scene | 条目数 | 说明 |
|---|---|---|---|---|
| `hello-world` | 👋 Hello World 新手模板 | hello-world | 15 | 本地 7 + GitCode 热门 git 模板 8（随机模式） |
| `general` | ⚙ 通用项目模板 | default | 3 | 通用型 git 模板 |
| `mobile` | 🍃 移动开发项目模板 | harmony | 2 | HarmonyOS / 移动端 git 模板 |
| `cloud-native` | ☁ 云原生开发 | cloud-native | 110 | 云原生精选仓库，每日自动同步 |
| `iac` | 🏗️ IaC 开发 | iac | 22 | IaC 精选仓库，每日自动同步 |
| `skill-dev` | 🔧 技能开发项目模板 | skill-dev | 1 | 本地 `hello-skill` |
| `ai` | 🤖 AI应用项目模板 | agent-dev | 20 | AI 应用 git 模板 |
| `content` | 📝 内容创作项目模板 | blog-publish | 3 | 博客 / 内容创作 git 模板 |

## 本地模板列表

- `hello-flask` — 心情追踪器：Flask Web 应用，含 5 个 API 端点与单元测试（hello-world 场景）
- `hello-fastapi` — 极简 FastAPI 服务（hello-world 场景）
- `hello-todo` — 命令行待办清单（hello-world 场景）
- `hello-calculator` — 计算器 + 单元测试（hello-world 场景）
- `hello-html` — 静态网页前端三件套（hello-world 场景）
- `hello-blog` — Flask 多页博客骨架（hello-world 场景）
- `snake-game` — 经典贪吃蛇小游戏（已转为本地模板，hello-world 场景）
- `hello-skill` — 最小 Skill 项目模板（skill-dev 场景）

## 新增模板

新增**本地**模板时，必须同时满足两步：

1. 新建模板目录，目录名即模板 `id`
2. 在 `project-templates.json` 中登记该 `id` 且 `"source": "local"`

> 注意：每一条 `source: "local"` 都必须有同名目录，否则 grape 侧 `test_local_template_dir_exists` 门禁失败；
> `source: "git"` 的目录则保持 `git` 来源即可，二者不混用。

## 使用

```bash
# 由 grape 主仓在部署阶段同步
bash scripts/sync_templates.sh
```