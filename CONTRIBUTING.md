# Contributing to grape-template

Thanks for taking the time to contribute! `grape-template` hosts the official project templates of the
[Grape](https://gitcode.com/grape-dev/grape) platform. Any template added here shows up in the
platform's "New Project" flow, so keep the change self-contained and easy for any template consumer to run.

## Getting started

1. **Open an Issue** — describe the problem or the template you want to add before writing code.
2. **Fork & develop** — work on a feature branch.
3. **Add / update docs** — every template ships with its own `README.md`; keep the main `README.md`
   (and `README.zh.md`) in sync with the directory layout.
4. **Submit a PR** — describe the change, any test results, and link the Issue.

## Adding a new template

A **local** template requires both changes at the same time:

1. Create a new directory whose name is the template `id` (e.g. `hello-<name>`).
2. Register the same `id` in `project-templates.json` with `"source": "local"`.

> A mismatch between the directory and the registry fails the grape-side gate
> `test_local_template_dir_exists`. Git-backed templates only need a `source: "git"` registry entry.

Membership in a category is set via the `category.id` block in the registry; `scene_id` must match an
existing platform scene (`default`, `skill-dev`, `cloud-native`, `iac`).

## Commit conventions

Keep commit messages in **English** and follow **Conventional Commits**:

```
docs(templates): add hello-<name> template
fix(registry): correct scene_id of hello-blog
chore: bump project-templates.json
```

Keep the change small and scoped; do not mix unrelated edits in one commit.

## Before submitting

- Verify the template runs as documented (its own `README.md` instructions).
- Verify `project-templates.json` is still valid JSON.
- Do not commit secrets, `.env` files, private keys, or any internal host/path values.