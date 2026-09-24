import json
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from scripts.codex_history_manager import (
    CodexHistoryError,
    backup_database,
    replace_in_place,
    rollout_index,
)


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "codex_history_manager.py"
SOURCE_A = "01a0d301-0000-7000-8000-000000000001"
SOURCE_B = "01a0d301-0000-7000-8000-000000000002"
OFFICIAL = "01a0d301-0000-7000-8000-000000000003"
TURN_ID = "01a0d301-0000-7000-8000-000000000004"


def write_rollout(path: Path, thread_id: str, provider: str | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"id": thread_id, "cwd": "/tmp/workspace"}
    if provider is not None:
        meta["model_provider"] = provider
    records = [
        {"type": "session_meta", "payload": meta},
        {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Keep this message"}]}},
    ]
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def create_fixture(root: Path) -> tuple[Path, Path, dict[str, Path]]:
    home = root / "codex"
    home.mkdir()
    older = home / "archived_sessions" / f"rollout-2026-09-22T09-00-00-{SOURCE_A}.jsonl"
    newer = home / "archived_sessions" / f"rollout-2026-09-23T09-00-00-{SOURCE_A}_{TURN_ID}.jsonl"
    second = home / "sessions" / "2026" / "09" / "24" / f"rollout-2026-09-24T09-00-00-{SOURCE_B}.jsonl"
    official = home / "sessions" / "2026" / "09" / "24" / f"rollout-2026-09-24T10-00-00-{OFFICIAL}.jsonl"
    for path, thread_id, provider in (
        (older, SOURCE_A, "openai1"),
        (newer, SOURCE_A, "openai1"),
        (second, SOURCE_B, None),
        (official, OFFICIAL, "openai"),
    ):
        write_rollout(path, thread_id, provider)

    conn = sqlite3.connect(home / "state_5.sqlite")
    conn.execute("""
        CREATE TABLE threads (
            id TEXT PRIMARY KEY,
            rollout_path TEXT NOT NULL,
            created_at INTEGER NOT NULL DEFAULT 100,
            updated_at INTEGER NOT NULL DEFAULT 200,
            source TEXT NOT NULL DEFAULT 'vscode',
            model_provider TEXT NOT NULL,
            cwd TEXT NOT NULL DEFAULT '/tmp/workspace',
            title TEXT NOT NULL DEFAULT 'fixture',
            sandbox_policy TEXT NOT NULL DEFAULT 'danger-full-access',
            approval_mode TEXT NOT NULL DEFAULT 'never',
            tokens_used INTEGER NOT NULL DEFAULT 0,
            has_user_event INTEGER NOT NULL DEFAULT 1,
            archived INTEGER NOT NULL DEFAULT 0,
            archived_at INTEGER,
            git_sha TEXT,
            git_branch TEXT,
            git_origin_url TEXT,
            cli_version TEXT NOT NULL DEFAULT '0.155.1',
            first_user_message TEXT NOT NULL DEFAULT '',
            agent_nickname TEXT,
            agent_role TEXT,
            memory_mode TEXT NOT NULL DEFAULT 'enabled',
            model TEXT,
            reasoning_effort TEXT,
            agent_path TEXT,
            history_mode TEXT NOT NULL DEFAULT 'paginated'
        )
    """)
    conn.executemany(
        "INSERT INTO threads (id,rollout_path,model_provider,updated_at,archived) VALUES (?,?,?,?,?)",
        [
            (SOURCE_A, str(newer), "openai1", 201, 1),
            (SOURCE_B, str(second), "openai1", 202, 0),
            (OFFICIAL, str(official), "openai", 203, 0),
        ],
    )
    conn.commit()
    conn.close()
    rollout_index.cache_clear()
    return home, root / "backups", {"older": older, "newer": newer, "second": second, "official": official}


def run_migration(home: Path, backups: Path, flag: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), "--codex-home", str(home), "--backup-root", str(backups),
         "migrate-provider", "--from-provider", "openai1", "--to-provider", "openai", flag],
        text=True, capture_output=True, check=False,
    )


class ProviderMigrationTest(unittest.TestCase):
    def test_dry_run_reports_only_source_provider_and_all_rollouts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home, backups, _ = create_fixture(Path(tmp))

            result = run_migration(home, backups, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("2 threads", result.stdout)
            self.assertIn("3 rollout files", result.stdout)
            self.assertFalse(backups.exists())

    def test_apply_updates_every_source_rollout_and_preserves_other_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home, backups, paths = create_fixture(Path(tmp))
            original_message = json.loads(paths["older"].read_text().splitlines()[1])

            result = run_migration(home, backups, "--apply")

            self.assertEqual(result.returncode, 0, result.stderr)
            with closing(sqlite3.connect(home / "state_5.sqlite")) as conn:
                rows = conn.execute("SELECT id,model_provider,updated_at,history_mode FROM threads ORDER BY id").fetchall()
            self.assertEqual(rows, [
                (SOURCE_A, "openai", 201, "paginated"),
                (SOURCE_B, "openai", 202, "paginated"),
                (OFFICIAL, "openai", 203, "paginated"),
            ])
            for name in ("older", "newer", "second"):
                records = [json.loads(line) for line in paths[name].read_text().splitlines()]
                self.assertEqual(records[0]["payload"]["model_provider"], "openai")
                self.assertEqual(records[1], original_message)
            self.assertEqual(json.loads(paths["official"].read_text().splitlines()[0])["payload"]["model_provider"], "openai")

            backup_dirs = list(backups.iterdir())
            self.assertEqual(len(backup_dirs), 1)
            with closing(sqlite3.connect(backup_dirs[0] / "state_5.before.sqlite")) as conn:
                self.assertEqual(conn.execute("PRAGMA quick_check").fetchone()[0], "ok")
                self.assertEqual(conn.execute("SELECT count(*) FROM threads WHERE model_provider='openai1'").fetchone()[0], 2)
            with tarfile.open(backup_dirs[0] / "rollouts-before.tar.gz") as archive:
                self.assertEqual(len(archive.getmembers()), 3)

    def test_apply_rejects_mismatched_session_id_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home, backups, paths = create_fixture(Path(tmp))
            records = [json.loads(line) for line in paths["older"].read_text().splitlines()]
            records[0]["payload"]["id"] = OFFICIAL
            paths["older"].write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")

            result = run_migration(home, backups, "--apply")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("session id", result.stderr.lower())
            self.assertFalse(backups.exists())
            with closing(sqlite3.connect(home / "state_5.sqlite")) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM threads WHERE model_provider='openai1'").fetchone()[0], 2)

    def test_apply_rejects_active_thread_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home, backups, _ = create_fixture(Path(tmp))
            locks = home / "thread-writer-locks"
            locks.mkdir()
            (locks / f"{SOURCE_A}.lock").touch()

            result = run_migration(home, backups, "--apply")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("writer lock", result.stderr.lower())
            self.assertFalse(backups.exists())

    def test_apply_rejects_non_object_session_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home, backups, paths = create_fixture(Path(tmp))
            paths["older"].write_text('[]\n', encoding="utf-8")

            result = run_migration(home, backups, "--apply")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing session metadata", result.stderr.lower())
            self.assertFalse(backups.exists())

    def test_failed_rewrite_removes_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rollout = root / "rollout.jsonl"
            rollout.write_text('{"type":"session_meta"}\nnot-json\n', encoding="utf-8")

            with self.assertRaises(CodexHistoryError):
                replace_in_place(rollout, lambda record: record)

            self.assertEqual(list(root.iterdir()), [rollout])

    def test_sqlite_backup_includes_uncheckpointed_wal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "state_5.sqlite"
            conn = sqlite3.connect(db)
            self.assertEqual(conn.execute("PRAGMA journal_mode=WAL").fetchone()[0], "wal")
            conn.execute("PRAGMA wal_autocheckpoint=0")
            conn.execute("CREATE TABLE marker (value TEXT)")
            conn.commit()
            conn.execute("INSERT INTO marker VALUES ('recent')")
            conn.commit()
            target = root / "backup"
            target.mkdir()

            snapshot = backup_database(db, target)

            with closing(sqlite3.connect(snapshot)) as copy:
                self.assertEqual(copy.execute("SELECT value FROM marker").fetchone()[0], "recent")
            conn.close()


if __name__ == "__main__":
    unittest.main()
