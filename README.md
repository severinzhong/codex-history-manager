# Codex History Manager

`codex-history-manager` 是一个面向本地 Codex 历史记录的技能和 CLI 工具，用来搜索、读取、导出、迁移、克隆、改 provider，以及在严格确认流程下修改历史内容。

它操作的是本机 `~/.codex` 下的两类数据：

- `state_5.sqlite`：thread 元数据
- `sessions/.../rollout-*.jsonl` 和 `archived_sessions/...`：会话事件流

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

```bash
./codex-history-manager change-provider --id <thread-id> --provider openai1 --dry-run
./codex-history-manager change-provider-workspace --cwd /abs/path --provider anthropic --dry-run
./codex-history-manager change-provider-all --provider openai1 --dry-run
```

## 危险操作

这个技能支持“最高危险度”的历史正文改写，但必须走两步：

1. 先生成计划

```bash
./codex-history-manager plan-dangerous-edit --id <thread-id> --find "old text" --replace "new text" --output /tmp/edit-plan.json
```

2. 在对话里展示修改清单和警告，获得用户明确批准后再执行

```bash
./codex-history-manager apply-dangerous-edit --plan /tmp/edit-plan.json --confirm-plan-id <plan-id> --acknowledge-history-rewrite --apply
```

这一步会直接改写历史记录内容。它不是 metadata 级修改，而是真正重写已保存的文本。

## 安全原则

- 写命令默认应该先 `--dry-run`
- `clone` 通常比 `move` 更安全
- `change-provider-all` 这种全局操作必须先看作用域统计
- 每次真实写入前都会自动备份
- 危险历史改写必须先出计划，再确认，再执行

## 参考文档

- [SKILL.md](./SKILL.md)
- [references/commands.md](./references/commands.md)
- [references/safety.md](./references/safety.md)
- [references/storage.md](./references/storage.md)
