# Codex History Manager

[English README](./README.md)

`codex-history-manager` 是一个面向本地 Codex 历史记录的技能和 CLI 工具，用来搜索、读取、导出、迁移、克隆、改 provider，以及在严格确认流程下修改历史内容。

它操作的是本机 `~/.codex` 下的两类数据：

- `state_5.sqlite`：thread 元数据
- `sessions/.../rollout-*.jsonl` 和 `archived_sessions/...`：会话事件流

## 兼容性

- CLI 默认会兼容 `threads` SQLite 表里新增但未使用的 metadata 列，避免 Codex 升级后像 `search` 这样的常用命令因为加列而失效。
- 当本地 Codex 元数据结构发生变化时，优先更新仓库里的 CLI 或重新安装包，而不是手工改 SQLite。

## 安装

直接在仓库目录使用：

```bash
python3 scripts/codex_history_manager.py --help
```

安装成系统命令：

```bash
python3 -m pip install .
codex-history-manager --help
```

或者用 `pipx`：

```bash
pipx install .
codex-history-manager --help
```

## 能做什么

- 搜索历史 thread
- 读取单条 thread 的可见对话
- 导出 thread 为 `markdown`、`json`、`jsonl`
- 生成 handoff 文档，方便智能体接班
- 按 thread / workspace / 全部切换 `provider`
- 按 thread / workspace 迁移或克隆到别的 workspace
- 在最高危险度流程下改写历史内容

## 适合的场景

- “我之前在另一个 workspace 聊过这个，帮我找出来”
- “把这个 thread 复制到新的 workspace 里继续用”
- “把这个 workspace 下的历史都改到另一个 provider”
- “导出这条对话做归档或交接”
- “对历史内容做受控的、安全可审计的修订”

## 不适合的场景

- 网页版 ChatGPT / Claude / Gemini 的远端历史管理
- 修改 OpenAI/Anthropic 服务端保存的记录
- 无确认地大批量改写聊天正文
- 当作数据库修复器，随意手改所有底层字段

## 常用命令

### 搜索和读取

```bash
./codex-history-manager search --query "payments"
./codex-history-manager show-thread --id <thread-id>
```

### 导出和交接

```bash
./codex-history-manager export-thread --id <thread-id> --format markdown --output /tmp/thread.md
./codex-history-manager handoff --id <thread-id> --output /tmp/handoff.md
```

### workspace 迁移和克隆

```bash
./codex-history-manager move-workspace --cwd /abs/src --to-cwd /abs/dst --dry-run
./codex-history-manager clone-workspace --cwd /abs/src --to-cwd /abs/dst --dry-run
```

### provider 切换

用 `--from-provider` 和 `--to-provider` 迁移当前属于某个 provider 的全部本地 Codex 历史。先核对范围，再执行：

```bash
./codex-history-manager --backup-root /有足够空间的路径 migrate-provider --from-provider openai1 --to-provider openai --dry-run
./codex-history-manager --backup-root /有足够空间的路径 migrate-provider --from-provider openai1 --to-provider openai --apply
./codex-history-manager --backup-root /有足够空间的路径 migrate-provider --from-provider openai --to-provider openai1 --dry-run
```

这会更新匹配 thread 的 SQLite 元数据及其全部 rollout 文件，并保留历史时间与消息内容。反向命令会选中当前所有 `openai` 会话，包括原本就在官方下创建的会话。目标 provider 需要已在 Codex 中配置，迁移后才能打开。

```bash
./codex-history-manager change-provider --id <thread-id> --provider openai1 --dry-run
./codex-history-manager change-provider-workspace --cwd /abs/path --provider anthropic --dry-run
./codex-history-manager change-provider-all --provider openai1 --dry-run
```

## 危险操作

这个工具支持最高危险度的操作：改写已保存的历史正文。这个流程必须分两步执行。

1. 先生成计划：

```bash
./codex-history-manager plan-dangerous-edit --id <thread-id> --find "old text" --replace "new text" --output /tmp/edit-plan.json
```

2. 在对话里展示警告和精确修改清单，得到用户明确批准后再执行：

```bash
./codex-history-manager apply-dangerous-edit --plan /tmp/edit-plan.json --confirm-plan-id <plan-id> --acknowledge-history-rewrite --apply
```

这一步会直接改写已保存的历史内容，不是简单的 metadata 修改。

## 安全原则

- 写操作先跑 `--dry-run`
- 当你只是想在新 workspace 复用历史时，优先 `clone`
- 对 `change-provider-all` 这类全局命令，先检查作用域统计
- 真实写入前总是先备份
- 危险历史改写必须遵守：先出计划，再对话确认，最后执行

## 参考文档

- [SKILL.md](./SKILL.md)
- [references/commands.md](./references/commands.md)
- [references/safety.md](./references/safety.md)
- [references/storage.md](./references/storage.md)
