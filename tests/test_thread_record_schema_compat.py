import sqlite3
import unittest

from scripts.codex_history_manager import fetch_threads


def _create_threads_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE threads (
            id TEXT PRIMARY KEY,
            rollout_path TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            source TEXT NOT NULL,
            model_provider TEXT NOT NULL,
            cwd TEXT NOT NULL,
            title TEXT NOT NULL,
            sandbox_policy TEXT NOT NULL,
            approval_mode TEXT NOT NULL,
            tokens_used INTEGER NOT NULL DEFAULT 0,
            has_user_event INTEGER NOT NULL DEFAULT 0,
            archived INTEGER NOT NULL DEFAULT 0,
            archived_at INTEGER,
            git_sha TEXT,
            git_branch TEXT,
            git_origin_url TEXT,
            cli_version TEXT NOT NULL DEFAULT '',
            first_user_message TEXT NOT NULL DEFAULT '',
            agent_nickname TEXT,
            agent_role TEXT,
            memory_mode TEXT NOT NULL DEFAULT 'enabled',
            model TEXT,
            reasoning_effort TEXT,
            agent_path TEXT,
            created_at_ms INTEGER,
            updated_at_ms INTEGER
        )
        """
    )


class ThreadRecordSchemaCompatTest(unittest.TestCase):
    def test_fetch_threads_ignores_unknown_columns(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        _create_threads_table(conn)
        conn.execute(
            """
            INSERT INTO threads (
                id, rollout_path, created_at, updated_at, source, model_provider, cwd,
                title, sandbox_policy, approval_mode, tokens_used, has_user_event,
                archived, archived_at, git_sha, git_branch, git_origin_url, cli_version,
                first_user_message, agent_nickname, agent_role, memory_mode, model,
                reasoning_effort, agent_path, created_at_ms, updated_at_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "thread-1",
                "/tmp/rollout.jsonl",
                1710000000,
                1710000100,
                "vscode",
                "openai1",
                "/tmp/workspace",
                "Schema drift test",
                "danger-full-access",
                "never",
                0,
                1,
                0,
                None,
                None,
                "main",
                None,
                "1.0.0",
                "hello",
                None,
                None,
                "enabled",
                "gpt-5",
                "medium",
                None,
                1710000000000,
                1710000100000,
            ),
        )

        threads = fetch_threads(conn)

        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0].id, "thread-1")


if __name__ == "__main__":
    unittest.main()
