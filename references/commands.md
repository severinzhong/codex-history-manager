# Commands

## Search

```bash
python3 scripts/codex_history.py search --query "bug" --limit 20
python3 scripts/codex_history.py search --cwd /abs/path --provider openai1 --json
```

Search checks:

- thread title
- first user message stored in SQLite
- visible transcript messages from rollout logs

## Read

```bash
python3 scripts/codex_history.py show-thread --id <thread-id>
python3 scripts/codex_history.py show-thread --id <thread-id> --json
```

## Export

```bash
python3 scripts/codex_history.py export-thread --id <thread-id> --format markdown --output /abs/path/thread.md
python3 scripts/codex_history.py export-thread --id <thread-id> --format json --output /abs/path/thread.json
python3 scripts/codex_history.py export-thread --id <thread-id> --format jsonl --output /abs/path/thread.jsonl
```

`jsonl` writes a normalized event stream, not a byte-for-byte copy of the original rollout file.

## Handoff

```bash
python3 scripts/codex_history.py handoff --id <thread-id> --output /abs/path/handoff.md
```

The generated handoff is deterministic. If you need a richer human summary, read the handoff or thread data and then write a higher quality summary in the main agent response.

## Dangerous history rewrite

```bash
python3 scripts/codex_history.py plan-dangerous-edit --id <thread-id> --find "old text" --replace "new text" --output /abs/path/edit-plan.json
python3 scripts/codex_history.py apply-dangerous-edit --plan /abs/path/edit-plan.json --confirm-plan-id <plan-id> --acknowledge-history-rewrite --apply
```

Workflow:

- Run `plan-dangerous-edit`
- Show the warning and change list to the user in-chat
- Wait for explicit approval
- Run `apply-dangerous-edit` with the matching `plan_id`

## Workspace reassignment

```bash
python3 scripts/codex_history.py move-thread --id <thread-id> --to-cwd /abs/path --dry-run
python3 scripts/codex_history.py move-thread --id <thread-id> --to-cwd /abs/path --apply
python3 scripts/codex_history.py clone-thread --id <thread-id> --to-cwd /abs/path --dry-run
python3 scripts/codex_history.py clone-thread --id <thread-id> --to-cwd /abs/path --apply
python3 scripts/codex_history.py move-workspace --cwd /abs/src --to-cwd /abs/dst --dry-run
python3 scripts/codex_history.py move-workspace --cwd /abs/src --to-cwd /abs/dst --apply
python3 scripts/codex_history.py clone-workspace --cwd /abs/src --to-cwd /abs/dst --dry-run
python3 scripts/codex_history.py clone-workspace --cwd /abs/src --to-cwd /abs/dst --apply
```

## Provider reassignment

```bash
python3 scripts/codex_history.py change-provider --id <thread-id> --provider openai1 --dry-run
python3 scripts/codex_history.py change-provider --id <thread-id> --provider openai1 --apply
python3 scripts/codex_history.py change-provider --id <thread-id> --provider openai1 --model gpt-5.4 --apply
python3 scripts/codex_history.py change-provider-workspace --cwd /abs/path --provider openai1 --dry-run
python3 scripts/codex_history.py change-provider-workspace --cwd /abs/path --provider openai1 --apply
python3 scripts/codex_history.py change-provider-all --provider openai1 --dry-run
python3 scripts/codex_history.py change-provider-all --provider openai1 --apply
```
