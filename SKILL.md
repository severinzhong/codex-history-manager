---
name: codex-history-manager
description: Search, read, export, hand off, clone, move, or rebind local Codex history stored under ~/.codex. Use when the user wants to inspect past Codex sessions, bring a thread into another workspace, export transcripts, generate handoff notes, or change a thread's workspace/provider metadata.
---

# Codex History Manager

Use `codex-history-manager` when the task is about local Codex history, not general ChatGPT or web chat history.

Codex stores local history in two places (`~/.codex` on macOS/Linux, `%USERPROFILE%\.codex` on Windows, unless `--codex-home` is set):

- `~/.codex/state_5.sqlite` for thread metadata
- `~/.codex/sessions/.../rollout-*.jsonl` and `~/.codex/archived_sessions/...` for event logs

The bundled CLI is the source of truth for reading and mutating that state:

- `./codex-history-manager ...`
- On Windows, run `py -3 <skill-folder>\scripts\codex_history_manager.py ...` or use the repository's `codex-history-manager.cmd` launcher.

The CLI supports additive metadata columns and current `response_item` messages. Reading, exporting, handing off, and `migrate-provider` cover threads spanning multiple rollout files. Other write commands still target the latest rollout file; check for older segments before using them on a compacted thread.

## Default workflow

1. For discovery, start with `search`.
2. For context, use `show-thread` or `handoff`.
3. For exports, use `export-thread`.
4. For cross-workspace reuse, prefer `clone-thread` over `move-thread`.
5. For writes, run a dry run first, then rerun with `--apply`.
6. For history body rewrites, always do `plan-dangerous-edit`, show the warning and change list to the user, get explicit approval in chat, then run `apply-dangerous-edit`.

## Migrating between providers

Use `migrate-provider` to move every local thread whose current provider matches `--from-provider` to `--to-provider`. The command changes provider metadata in SQLite and every rollout file for matching threads, including files created after compaction. It preserves timestamps, model names, and conversation content.

1. Run `./codex-history-manager migrate-provider --from-provider <source-id> --to-provider <target-id> --dry-run`.
2. Review the thread count, rollout count, active-writer check, and available backup space. Set `--backup-root /path/with/enough/space` when the default volume is too small.
3. Run the same command with `--apply`. The CLI holds thread writer locks, checks the rollout records, and creates a SQLite snapshot and rollout archive before changing metadata.
4. Have the user verify representative threads in Codex and check that no source-provider rows remain. The target provider must be configured in Codex for migrated threads to open.

On Windows, replace `./codex-history-manager` in these commands with `py -3 <skill-folder>\scripts\codex_history_manager.py` (or the `.cmd` launcher when using a cloned repository). Close Codex before `--apply` so its session database and rollout files are not being written during migration.

For a full reverse migration, `--from-provider openai --to-provider openai1` selects **all** current `openai` threads, including threads that were originally official. It does not restore their previous individual provider assignments.

Read [references/safety.md](references/safety.md) before a bulk migration.

## Core commands

- Search threads:
  `./codex-history-manager search --query "payments"`
- Read one thread:
  `./codex-history-manager show-thread --id <thread-id>`
- Export transcript:
  `./codex-history-manager export-thread --id <thread-id> --format markdown --output /tmp/thread.md`
- Create a handoff note:
  `./codex-history-manager handoff --id <thread-id> --output /tmp/handoff.md`
- Plan a dangerous history content rewrite:
  `./codex-history-manager plan-dangerous-edit --id <thread-id> --find "old" --replace "new" --output /tmp/edit-plan.json`
- Clone a thread into another workspace:
  `./codex-history-manager clone-thread --id <thread-id> --to-cwd /abs/path --dry-run`
- Move all threads in one workspace:
  `./codex-history-manager move-workspace --cwd /abs/src --to-cwd /abs/dst --dry-run`
- Clone all threads in one workspace:
  `./codex-history-manager clone-workspace --cwd /abs/src --to-cwd /abs/dst --dry-run`
- Move a thread to another workspace:
  `./codex-history-manager move-thread --id <thread-id> --to-cwd /abs/path --dry-run`
- Rebind provider metadata:
  `./codex-history-manager change-provider --id <thread-id> --provider openai1 --dry-run`
- Rebind provider metadata for one workspace:
  `./codex-history-manager change-provider-workspace --cwd /abs/path --provider openai1 --dry-run`
- Rebind provider metadata for all local threads:
  `./codex-history-manager change-provider-all --provider openai1 --dry-run`
- Migrate all threads currently assigned to one provider:
  `./codex-history-manager migrate-provider --from-provider openai1 --to-provider openai --dry-run`
- Migrate all current official-provider threads to a custom provider:
  `./codex-history-manager migrate-provider --from-provider openai --to-provider openai1 --dry-run`

## Safety rules

- Never perform a write first. Use the default dry run or pass `--dry-run`.
- Only use `--apply` after reviewing the plan.
- For bulk provider changes, use `migrate-provider` with `--from-provider`; `change-provider-all` includes every local thread.
- Prefer cloning over moving unless the user explicitly wants to change ownership.
- Do not hand edit `state_5.sqlite` or rollout files if the CLI can do the job.
- If the user asks to modify message content, stop and confirm. You must first produce a dangerous edit plan, present the warning and change list in the conversation, and wait for explicit user approval before running `apply-dangerous-edit`.

Read these references only when needed:

- Command details: [references/commands.md](references/commands.md)
- Write safety and backups: [references/safety.md](references/safety.md)
- Storage model: [references/storage.md](references/storage.md)
