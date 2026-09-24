# Storage Model

## SQLite

`state_5.sqlite` under the Codex home (`~/.codex` on macOS/Linux, `%USERPROFILE%\.codex` on Windows)

Important table:

- `threads`

Important columns:

- `id`
- `rollout_path`
- `cwd`
- `title`
- `first_user_message`
- `model_provider`
- `model`
- `archived`
- `created_at`
- `updated_at`
- `history_mode` (recent Codex releases may mark threads as `paginated`)

## Rollout JSONL

Each rollout starts with a `session_meta` record. Relevant fields:

- `payload.id`
- `payload.cwd`
- `payload.model_provider`

One thread can span multiple rollout files. After compaction, Codex continues the
thread in a new `rollout-<timestamp>-<thread-id>_<turn-uuid>.jsonl` file and the
SQLite `threads.rollout_path` only points at the latest one. To rebuild the full
transcript, glob every `rollout-*<thread-id>*.jsonl` under `sessions/` and
`archived_sessions/`, sort them by the timestamp in the file name, and dedupe
messages by `payload.id`.

Visible conversation text comes from two record shapes:

- Legacy: `event_msg` records with `payload.type == "user_message"` or
  `"agent_message"` and text in `payload.message`.
- Current (observed since Codex Desktop/CLI 0.152.0): `response_item` records with
  `payload.type == "message"`, `payload.role` of `user` or `assistant`, and text in
  `payload.content[]` items of type `input_text` / `output_text`. `payload.phase`
  distinguishes `commentary` from `final_answer`.

For `response_item` user-role records, filter out host-injected content. Real user
input reports `internal_chat_message_metadata_passthrough.content_item_kinds` of
`["user.text"]`; injected records use kinds such as
`environments.environment_context`, `agents_md.instructions`, or
`generic.turn_aborted`. When metadata is missing, fall back to skipping known
wrapper prefixes like `<environment_context>`, `<user_instructions>`, and
`<turn_aborted>`.

`compacted` records carry a summary in `payload.message`; they are not visible
conversation and must not be treated as transcript messages.

`turn_context` records may also carry model metadata:

- `payload.model`

For workspace migration or provider rebinding, keep SQLite and rollout metadata in sync.
The built-in OpenAI provider id is `openai`; older local rows can retain a provider id that is no longer defined in Codex configuration. Such rows may appear in history but fail to resume. A provider migration must update both `threads.model_provider` and `session_meta.payload.model_provider` in every rollout belonging to each selected thread.
