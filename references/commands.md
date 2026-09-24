# Commands

## Search

```bash
./codex-history-manager search --query "bug" --limit 20
./codex-history-manager search --cwd /abs/path --provider openai1 --json
```

Search checks:

- thread title
- first user message stored in SQLite
- visible transcript messages from rollout logs

## Read

```bash
./codex-history-manager show-thread --id <thread-id>
./codex-history-manager show-thread --id <thread-id> --json
```

## Export

```bash
./codex-history-manager export-thread --id <thread-id> --format markdown --output /abs/path/thread.md
./codex-history-manager export-thread --id <thread-id> --format json --output /abs/path/thread.json
./codex-history-manager export-thread --id <thread-id> --format jsonl --output /abs/path/thread.jsonl
```

`jsonl` writes a normalized event stream, not a byte-for-byte copy of the original rollout file.

## Handoff

```bash
./codex-history-manager handoff --id <thread-id> --output /abs/path/handoff.md
```

The generated handoff is deterministic. If you need a richer human summary, read the handoff or thread data and then write a higher quality summary in the main agent response.

## Dangerous history rewrite

```bash
./codex-history-manager plan-dangerous-edit --id <thread-id> --find "old text" --replace "new text" --output /abs/path/edit-plan.json
./codex-history-manager apply-dangerous-edit --plan /abs/path/edit-plan.json --confirm-plan-id <plan-id> --acknowledge-history-rewrite --apply
```

Workflow:

- Run `plan-dangerous-edit`
- Show the warning and change list to the user in-chat
- Wait for explicit approval
- Run `apply-dangerous-edit` with the matching `plan_id`

## Workspace reassignment

```bash
./codex-history-manager move-thread --id <thread-id> --to-cwd /abs/path --dry-run
./codex-history-manager move-thread --id <thread-id> --to-cwd /abs/path --apply
./codex-history-manager clone-thread --id <thread-id> --to-cwd /abs/path --dry-run
./codex-history-manager clone-thread --id <thread-id> --to-cwd /abs/path --apply
./codex-history-manager move-workspace --cwd /abs/src --to-cwd /abs/dst --dry-run
./codex-history-manager move-workspace --cwd /abs/src --to-cwd /abs/dst --apply
./codex-history-manager clone-workspace --cwd /abs/src --to-cwd /abs/dst --dry-run
./codex-history-manager clone-workspace --cwd /abs/src --to-cwd /abs/dst --apply
```

## Provider reassignment

Migrate every local Codex thread currently assigned to a specified provider. The command covers every rollout file for each thread and preserves recency timestamps:

```bash
./codex-history-manager --backup-root /volume/with/space migrate-provider --from-provider openai1 --to-provider openai --dry-run
./codex-history-manager --backup-root /volume/with/space migrate-provider --from-provider openai1 --to-provider openai --apply
```

The target can be any provider id configured in Codex. To move all current official-provider threads to `openai1`, reverse the parameters:

```bash
./codex-history-manager --backup-root /volume/with/space migrate-provider --from-provider openai --to-provider openai1 --dry-run
./codex-history-manager --backup-root /volume/with/space migrate-provider --from-provider openai --to-provider openai1 --apply
```

The reverse command includes threads that were originally official. This changes local metadata; it does not import histories from another app or alter message bodies.

On Windows PowerShell, call the bundled script through the Python launcher:

```powershell
py -3 .\scripts\codex_history_manager.py --backup-root "D:\CodexBackups" migrate-provider --from-provider openai1 --to-provider openai --dry-run
```

```bash
./codex-history-manager change-provider --id <thread-id> --provider openai1 --dry-run
./codex-history-manager change-provider --id <thread-id> --provider openai1 --apply
./codex-history-manager change-provider --id <thread-id> --provider openai1 --model gpt-5.4 --apply
./codex-history-manager change-provider-workspace --cwd /abs/path --provider openai1 --dry-run
./codex-history-manager change-provider-workspace --cwd /abs/path --provider openai1 --apply
./codex-history-manager change-provider-all --provider openai1 --dry-run
./codex-history-manager change-provider-all --provider openai1 --apply
```
