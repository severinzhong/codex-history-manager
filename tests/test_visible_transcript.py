import json
import tempfile
import unittest
from pathlib import Path

from scripts.codex_history_manager import (
    thread_id_from_rollout_name,
    thread_rollout_paths,
    thread_transcript,
    visible_transcript,
    ThreadRecord,
    rollout_index,
)


THREAD_ID = "01a05a8b-debd-7a11-9308-cffaeaba6b58"


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _response_item(message_id: str, role: str, text: str, *, kinds=None, phase=None) -> dict:
    content_type = "input_text" if role == "user" else "output_text"
    payload = {
        "type": "message",
        "id": message_id,
        "role": role,
        "content": [{"type": content_type, "text": text}],
    }
    if phase is not None:
        payload["phase"] = phase
    if kinds is not None:
        payload["internal_chat_message_metadata_passthrough"] = {"content_item_kinds": kinds}
    return {"timestamp": "2026-09-03T01:00:00.000Z", "type": "response_item", "payload": payload}


def _legacy_event(message_type: str, text: str) -> dict:
    return {
        "timestamp": "2026-09-03T01:00:00.000Z",
        "type": "event_msg",
        "payload": {"type": message_type, "message": text},
    }


def _thread_record(rollout_path: Path) -> ThreadRecord:
    return ThreadRecord(
        id=THREAD_ID,
        rollout_path=rollout_path,
        created_at=0,
        updated_at=0,
        source="vscode",
        model_provider="openai1",
        cwd="/tmp/workspace",
        title="t",
        sandbox_policy="danger-full-access",
        approval_mode="never",
        tokens_used=0,
        has_user_event=1,
        archived=0,
        archived_at=None,
        git_sha=None,
        git_branch=None,
        git_origin_url=None,
        cli_version="0.152.0",
        first_user_message="",
        agent_nickname=None,
        agent_role=None,
        memory_mode="enabled",
        model=None,
        reasoning_effort=None,
        agent_path=None,
    )


class VisibleTranscriptTest(unittest.TestCase):
    def test_response_item_messages_are_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout.jsonl"
            _write_jsonl(
                path,
                [
                    {"type": "session_meta", "payload": {"id": THREAD_ID}},
                    _response_item("m1", "user", "我们是有minio的吧", kinds=["user.text"]),
                    _response_item("m2", "assistant", "先看一下", phase="commentary"),
                    _response_item("m3", "assistant", "正式回复", phase="final_answer"),
                ],
            )

            messages = visible_transcript(path)

            self.assertEqual([m.role for m in messages], ["user", "assistant", "assistant"])
            self.assertEqual(messages[0].text, "我们是有minio的吧")
            self.assertEqual(messages[1].phase, "commentary")
            self.assertEqual(messages[2].phase, "final_answer")
            self.assertEqual(messages[2].message_id, "m3")

    def test_injected_user_role_records_are_filtered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout.jsonl"
            _write_jsonl(
                path,
                [
                    _response_item("m1", "user", "<environment_context>...</environment_context>", kinds=["environments.environment_context"]),
                    _response_item("m2", "user", "# AGENTS.md instructions ...", kinds=["agents_md.instructions", "environments.environment_context"]),
                    _response_item("m3", "user", "<turn_aborted>...</turn_aborted>", kinds=["generic.turn_aborted"]),
                    _response_item("m4", "developer", "system instructions", kinds=["generic.developer_instructions"]),
                    _response_item("m5", "user", "真实问题", kinds=["user.text"]),
                    # 无 metadata 的旧记录按已知包装前缀过滤
                    _response_item("m6", "user", "<environment_context>legacy</environment_context>"),
                    _response_item("m7", "user", "没有 metadata 的真实提问"),
                ],
            )

            messages = visible_transcript(path)

            self.assertEqual([m.text for m in messages], ["真实问题", "没有 metadata 的真实提问"])

    def test_legacy_event_msg_format_still_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout.jsonl"
            _write_jsonl(
                path,
                [
                    _legacy_event("user_message", "旧格式提问"),
                    _legacy_event("agent_message", "旧格式回答"),
                    _legacy_event("token_count", "not a message"),
                ],
            )

            messages = visible_transcript(path)

            self.assertEqual([(m.role, m.text) for m in messages], [("user", "旧格式提问"), ("assistant", "旧格式回答")])


class ThreadRolloutDiscoveryTest(unittest.TestCase):
    def test_thread_id_from_rollout_name(self) -> None:
        with_suffix = f"rollout-2026-09-03T08-58-58-{THREAD_ID}_01a064c6-b197-7dc1-9904-6fa5b0eb3c38.jsonl"
        without_suffix = f"rollout-2026-09-03T08-58-58-{THREAD_ID}.jsonl"
        self.assertEqual(thread_id_from_rollout_name(with_suffix), THREAD_ID)
        self.assertEqual(thread_id_from_rollout_name(without_suffix), THREAD_ID)
        self.assertIsNone(thread_id_from_rollout_name("rollout-notes.txt"))
        self.assertIsNone(thread_id_from_rollout_name("other.jsonl"))

    def test_transcript_concatenates_rollouts_and_dedupes_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            day = home / "sessions" / "2026" / "09" / "03"
            older = day / f"rollout-2026-09-03T08-58-58-{THREAD_ID}_01a064c6-b197-7dc1-9904-6fa5b0eb3c38.jsonl"
            newer = day / f"rollout-2026-09-03T11-09-52-{THREAD_ID}_01a0653e-887b-7542-891c-5c1a0a15a711.jsonl"
            _write_jsonl(
                older,
                [
                    _response_item("m1", "user", "第一句", kinds=["user.text"]),
                    _response_item("m2", "assistant", "第一句回复", phase="final_answer"),
                ],
            )
            _write_jsonl(
                newer,
                [
                    {"type": "compacted", "payload": {"message": "第一句 第一句回复 摘要"}},
                    _response_item("m3", "user", "第二句", kinds=["user.text"]),
                ],
            )
            rollout_index.cache_clear()

            thread = _thread_record(newer)
            paths = thread_rollout_paths(home, thread)
            self.assertEqual(paths, [older, newer])

            messages = thread_transcript(home, thread)
            self.assertEqual([(m.role, m.text) for m in messages], [("user", "第一句"), ("assistant", "第一句回复"), ("user", "第二句")])

    def test_transcript_falls_back_to_recorded_rollout_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            rollout = home / "elsewhere" / "rollout-custom-name.jsonl"
            _write_jsonl(rollout, [_response_item("m1", "user", "唯一消息", kinds=["user.text"])])
            rollout_index.cache_clear()

            messages = thread_transcript(home, _thread_record(rollout))

            self.assertEqual([m.text for m in messages], ["唯一消息"])


if __name__ == "__main__":
    unittest.main()
