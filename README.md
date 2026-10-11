<h1 align="center">grape-template</h1>

<p align="center">English | <a href="README.zh.md">中文</a></p>

<p align="center">
  <strong>Official project templates for the Grape platform</strong>
  <br>
  The stock templates ship here, versioned independently from the main grape repository.
</p>

<p align="center">
  <a href="#what-is-grape-template">What is grape-template</a> ·
  <a href="#repo-layout">Repo Layout</a> ·
  <a href="#registry-structure">Registry Structure</a> ·
  <a href="#local-templates">Local Templates</a> ·
  <a href="#adding-a-template">Adding a Template</a> ·
  <a href="#usage">Usage</a>
</p>

---

## What is grape-template

`grape-template` is the standalone repo for Grape's official project templates. At the **build / deploy
stage of the main grape repo**, `scripts/sync_templates.sh` pulls these contents into the deployment root:

- template directories → `examples/`
- the template registry → `configs/project-templates.json`

Keeping the templates in their own repo lets them ship and version independently from the platform.

**In one sentence: add a template here + register its id in `project-templates.json` → it appears in the Grape "New Project" flow.**

## Repo Layout

| Path | Description |
|---|---|
| `hello-*` | Official local templates. The directory name is the template `id` and maps one-to-one with `source: "local"` entries in `project-templates.json` |
| `project-templates.json` | The template registry — every entry (local and git) organized by category; versioned with this repo |

## Registry Structure

`project-templates.json` organizes all templates into categories (`categories`). The two `*-featured`
categories are synced daily and their counts drift with the sync result:

| category `id` | Category | scene | Entries | Notes |
|---|---|---|---|---|
| `hello-world` | Hello World starters | default | 15 | 6 local + 9 popular GitCode git templates (random mode) |
| `agent-best-practices` | Agent best practices | default | 7 | AI Agent templates from the `agent-best-practices` org |
| `skills` | Skills project templates | skill-dev | 1 | Local `hello-skill` |
| `ai-office` | AI office templates | default | 1 | AI office application starter |
| `cloud-native` | Cloud-native templates | cloud-native | 6 | Containerized / microservice starters |
| `iac` | IaaC templates | iac | 1 | Infrastructure-as-Code starter |
| `gitcode-featured` | GitCode featured | default | 101 | Popular cloud-native repos, auto-synced daily |
| `github-featured` | GitHub featured | default | 42 | Popular cloud-native repos, auto-synced daily |

## Local Templates

- `hello-flask` — minimal Flask web app (default scene)
- `hello-fastapi` — minimal FastAPI service (default scene)
- `hello-todo` — command-line todo list (default scene)
- `hello-calculator` — calculator with unit tests (default scene)
- `hello-html` — static web page (HTML + CSS + JS, default scene)
- `hello-blog` — Flask multi-page blog skeleton (default scene)
- `hello-skill` — minimal Skill project template (skill-dev scene)

## Adding a Template

To add a **local** template, both steps are required at the same time:

1. Create a new template directory whose name is the template `id`
2. Register that same `id` in `project-templates.json` with `"source": "local"`

A mismatch between the directory and the registry fails the grape-side gate
`test_local_template_dir_exists`. Git-backed templates only need a `source: "git"` registry entry.

## Usage

```bash
# Synced by the grape main repo at deploy time
bash scripts/sync_templates.sh
```