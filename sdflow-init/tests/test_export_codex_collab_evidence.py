"""Codex collaboration rollout evidence exporter contract."""

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "sdflow-init" / "assets" / "hack" / "export-codex-collab-evidence.py"
THREAD_ID = "11111111-2222-3333-4444-555555555555"
CLI_VERSION = "0.154.0"
SECRET = "CANARY-SECRET-must-never-leave"


def _top(ordinal, record_type, payload):
    return {
        "timestamp": f"2026-09-17T00:00:{ordinal:02d}.000Z",
        "ordinal": ordinal,
        "type": record_type,
        "payload": payload,
    }


def _session_meta():
    return _top(
        0,
        "session_meta",
        {
            "id": THREAD_ID,
            "session_id": THREAD_ID,
            "timestamp": "2026-09-17T00:00:00.000Z",
            "cwd": "/private/worktree",
            "originator": "codex_cli_rs",
            "cli_version": CLI_VERSION,
            "source": "cli",
            "model_provider": "openai",
            "base_instructions": {"text": SECRET},
            "thread_source": "cli",
            "history_mode": "full",
            "git": None,
            "context_window": 1000,
        },
    )


def _call(ordinal, name, call_id, arguments):
    return _top(
        ordinal,
        "response_item",
        {
            "type": "function_call",
            "name": name,
            "arguments": json.dumps(arguments, ensure_ascii=False, separators=(",", ":")),
            "call_id": call_id,
            "id": f"fc-{ordinal}",
            "namespace": "collaboration",
            "internal_chat_message_metadata_passthrough": None,
        },
    )


def _call_output(ordinal, call_id, output):
    if not isinstance(output, str):
        output = json.dumps(output, ensure_ascii=False, separators=(",", ":"))
    return _top(
        ordinal,
        "response_item",
        {
            "type": "function_call_output",
            "call_id": call_id,
            "output": output,
            "id": f"fco-{ordinal}",
            "internal_chat_message_metadata_passthrough": None,
        },
    )


def _activity(ordinal, call_id, kind, path, agent_thread_id):
    activity_id = call_id if kind in {"started", "interrupted"} else f"subagent-{kind}-{ordinal}"
    return _top(
        ordinal,
        "event_msg",
        {
            "type": "item_completed",
            "thread_id": THREAD_ID,
            "turn_id": "turn-1",
            "started_at_ms": ordinal,
            "completed_at_ms": ordinal + 1,
            "item": {
                "type": "SubAgentActivity",
                "id": activity_id,
                "kind": kind,
                "agent_thread_id": agent_thread_id,
                "agent_path": path,
            },
        },
    )


def _agent_message(ordinal, path, payload):
    text = (
        "Message Type: FINAL_ANSWER\n"
        "Task name: /root\n"
        f"Sender: {path}\n"
        "Payload:\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
    return _top(
        ordinal,
        "response_item",
        {
            "type": "agent_message",
            "id": f"msg-{ordinal}",
            "author": path,
            "recipient": "/root",
            "content": [{"type": "input_text", "text": text}],
            "internal_chat_message_metadata_passthrough": None,
        },
    )


def _task_complete(ordinal):
    return _top(
        ordinal,
        "event_msg",
        {
            "type": "task_complete",
            "turn_id": "turn-1",
            "last_agent_message": SECRET,
            "started_at": 1,
            "completed_at": 2,
            "duration_ms": 1,
            "time_to_first_token_ms": 1,
        },
    )


def _prompt(run_id, task_id, nonce):
    return f"run_id={run_id} task_id={task_id} nonce={nonce} secret={SECRET}"


def _request_manifest(call, prompt, result, path=None, agent_thread_id=None, rejection_kind=None):
    request = {
        "call_id": call,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_length": len(prompt),
        "requested_model": "gpt-5.6-luna",
        "requested_effort": "low",
        "context_mode": "none",
        "expected_result": result,
    }
    if path is not None:
        request["agent_path"] = path
        request["agent_thread_id"] = agent_thread_id
    if rejection_kind is not None:
        request["rejection_kind"] = rejection_kind
    return request


def _fixture():
    run_id = "run-1"
    records = [_session_meta()]
    manifest_records = []
    ordinal = 1

    def accepted(evidence_id, task_id, nonce, terminal, result_payload=None, expectation="attributed"):
        nonlocal ordinal
        path = f"/root/{evidence_id}"
        agent_thread_id = f"aaaaaaaa-bbbb-cccc-dddd-{ordinal:012d}"
        call_id = f"call_{evidence_id}"
        prompt = _prompt(run_id, task_id, nonce)
        records.extend(
            [
                _call(
                    ordinal,
                    "spawn_agent",
                    call_id,
                    {
                        "task_name": evidence_id,
                        "fork_turns": "none",
                        "message": prompt,
                        "model": "gpt-5.6-luna",
                        "reasoning_effort": "low",
                    },
                ),
                _activity(ordinal + 1, call_id, "started", path, agent_thread_id),
                _call_output(ordinal + 2, call_id, {"task_name": path}),
            ]
        )
        request = _request_manifest(call_id, prompt, "accepted", path, agent_thread_id)
        item = {
            "evidence_id": evidence_id,
            "task_id": task_id,
            "nonce": nonce,
            "request": request,
        }
        if terminal == "interrupted":
            interrupt_call = f"call_interrupt_{evidence_id}"
            records.extend(
                [
                    _call(ordinal + 3, "interrupt_agent", interrupt_call, {"target": path}),
                    _activity(ordinal + 4, interrupt_call, "interrupted", path, agent_thread_id),
                    _call_output(ordinal + 5, interrupt_call, {"previous_status": "running"}),
                ]
            )
            item["terminal"] = {
                "state": "interrupted",
                "source_ordinal": ordinal + 4,
                "call_id": interrupt_call,
            }
            item["result"] = {"source_type": "none", "expectation": "none"}
            ordinal += 6
        else:
            records.append(_activity(ordinal + 3, call_id, "completed", path, agent_thread_id))
            records.append(_agent_message(ordinal + 4, path, result_payload))
            item["terminal"] = {"state": "completed", "source_ordinal": ordinal + 3}
            item["result"] = {
                "source_type": "agent_message",
                "source_ordinal": ordinal + 4,
                "format": "json",
                "expectation": expectation,
            }
            if expectation == "owner_mismatch":
                item["result"]["observed_identity"] = {
                    "run_id": result_payload["run_id"],
                    "task_id": result_payload["task_id"],
                    "nonce": result_payload["nonce"],
                }
            ordinal += 5
        manifest_records.append(item)

    accepted(
        "completed",
        "task-completed",
        "nonce-completed",
        "completed",
        {
            "run_id": run_id,
            "task_id": "task-completed",
            "nonce": "nonce-completed",
            "status": "completed",
            "result_ref": "result-completed",
        },
    )

    rejected_prompt = _prompt(run_id, "task-rejected", "nonce-rejected")
    rejected_call = "call_rejected"
    records.extend(
        [
            _call(
                ordinal,
                "spawn_agent",
                rejected_call,
                {
                    "task_name": "rejected",
                    "fork_turns": "none",
                    "message": rejected_prompt,
                    "model": "gpt-5.6-luna",
                    "reasoning_effort": "low",
                },
            ),
            _call_output(ordinal + 1, rejected_call, "collab spawn failed: agent thread limit reached"),
        ]
    )
    manifest_records.append(
        {
            "evidence_id": "rejected",
            "task_id": "task-rejected",
            "nonce": "nonce-rejected",
            "request": _request_manifest(
                rejected_call, rejected_prompt, "rejected", rejection_kind="capacity"
            ),
            "terminal": {"state": "rejected", "source_ordinal": ordinal + 1, "call_id": rejected_call},
            "result": {"source_type": "none", "expectation": "none"},
        }
    )
    ordinal += 2

    accepted("interrupted", "task-interrupted", "nonce-interrupted", "interrupted")
    accepted(
        "missing",
        "task-missing",
        "nonce-missing",
        "completed",
        {
            "run_id": run_id,
            "task_id": "task-missing",
            "nonce": "nonce-missing",
            "status": "completed",
        },
        "missing_result_ref",
    )
    accepted(
        "old",
        "task-current",
        "nonce-current",
        "completed",
        {
            "run_id": "old-run",
            "task_id": "old-task",
            "nonce": "old-nonce",
            "status": "completed",
            "result_ref": "old-result",
        },
        "owner_mismatch",
    )
    records.append(_task_complete(ordinal))
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "thread_id": THREAD_ID,
        "codex_cli_version": CLI_VERSION,
        "records": manifest_records,
    }
    return records, manifest


def _write_fixture(tmp_path, records=None, manifest=None):
    default_records, default_manifest = _fixture()
    records = default_records if records is None else records
    manifest = default_manifest if manifest is None else manifest
    transcript = tmp_path / f"rollout-test-{THREAD_ID}.jsonl"
    transcript.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8"
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return transcript, manifest_path


def _export(tmp_path, records=None, manifest=None, extra_args=()):
    transcript, manifest_path = _write_fixture(tmp_path, records, manifest)
    output = tmp_path / "evidence.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "export",
            "--input",
            str(transcript),
            "--manifest",
            str(manifest_path),
            "--output",
            str(output),
            *extra_args,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result, output


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_export_covers_lifecycle_negative_results_and_privacy_canary(tmp_path):
    result, output = _export(tmp_path)

    assert result.returncode == 0, result.stderr
    rows = _jsonl(output)
    assert rows[0] == {
        "schema_version": 1,
        "record_type": "run",
        "run_id": "run-1",
        "source_thread_id": THREAD_ID,
        "source_cli_version": CLI_VERSION,
    }
    evidence = {row["evidence_id"]: row for row in rows[1:]}
    assert evidence["completed"]["request_result"] == "accepted"
    assert evidence["completed"]["terminal_state"] == "completed"
    assert evidence["completed"]["result_status"] == "attributed"
    assert evidence["completed"]["result_ref"] == "result-completed"
    assert evidence["rejected"]["request_result"] == "rejected"
    assert evidence["rejected"]["rejection_kind"] == "capacity"
    assert evidence["interrupted"]["terminal_state"] == "interrupted"
    assert evidence["missing"]["result_status"] == "missing-result"
    assert evidence["old"]["result_status"] == "old-result"
    assert evidence["old"]["observed_task_id"] == "old-task"
    serialized = output.read_text(encoding="utf-8")
    assert SECRET not in serialized
    assert "secret=" not in serialized
    assert all(row["prompt_length"] > 0 for row in rows[1:])
    assert all(len(row["prompt_sha256"]) == 64 for row in rows[1:])


def test_render_markdown_from_sanitized_jsonl_has_stable_golden(tmp_path):
    export_result, evidence = _export(tmp_path)
    assert export_result.returncode == 0, export_result.stderr
    markdown = tmp_path / "evidence.md"

    render = subprocess.run(
        [sys.executable, str(SCRIPT), "render", "--input", str(evidence), "--output", str(markdown)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert render.returncode == 0, render.stderr
    assert markdown.read_text(encoding="utf-8") == (
        "# Codex collaboration evidence\n\n"
        f"- run_id: `run-1`\n- source_thread_id: `{THREAD_ID}`\n"
        f"- source_cli_version: `{CLI_VERSION}`\n\n"
        "| evidence_id | task_id / nonce | request | model / effort / context | terminal | result | source |\n"
        "|---|---|---|---|---|---|---|\n"
        "| completed | task-completed / nonce-completed | accepted | gpt-5.6-luna / low / none | completed | attributed (`result-completed`) | request:1/call_completed; terminal:4; result:5 |\n"
        "| rejected | task-rejected / nonce-rejected | rejected (capacity) | gpt-5.6-luna / low / none | rejected | none | request:6/call_rejected; terminal:7/call_rejected |\n"
        "| interrupted | task-interrupted / nonce-interrupted | accepted | gpt-5.6-luna / low / none | interrupted | none | request:8/call_interrupted; terminal:12/call_interrupt_interrupted |\n"
        "| missing | task-missing / nonce-missing | accepted | gpt-5.6-luna / low / none | completed | missing-result | request:14/call_missing; terminal:17; result:18 |\n"
        "| old | task-current / nonce-current | accepted | gpt-5.6-luna / low / none | completed | old-result (`old-result`; observed old-run/old-task/old-nonce) | request:19/call_old; terminal:22; result:23 |\n"
    )
    assert SECRET not in markdown.read_text(encoding="utf-8")


def test_thread_id_locates_exact_rollout_from_environment(tmp_path):
    records, manifest = _fixture()
    sessions = tmp_path / "sessions" / "2026" / "09" / "17"
    sessions.mkdir(parents=True)
    transcript = sessions / f"rollout-date-{THREAD_ID}.jsonl"
    transcript.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8"
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "evidence.jsonl"
    env = dict(os.environ, CODEX_THREAD_ID=THREAD_ID)
    env.pop("CODEX_SESSION_ID", None)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "export",
            "--sessions-root",
            str(tmp_path / "sessions"),
            "--manifest",
            str(manifest_path),
            "--output",
            str(output),
        ],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0, result.stderr
    assert _jsonl(output)[0]["source_thread_id"] == THREAD_ID


@pytest.mark.parametrize("mutation", ["call_id", "agent_thread_id", "identity"])
def test_unexpected_attribution_mismatch_fails_closed(tmp_path, mutation):
    records, manifest = _fixture()
    if mutation == "call_id":
        manifest["records"][0]["request"]["call_id"] = "call_absent"
    elif mutation == "agent_thread_id":
        manifest["records"][0]["request"]["agent_thread_id"] = "wrong-thread"
    else:
        payload = records[5]["payload"]["content"][0]["text"]
        records[5]["payload"]["content"][0]["text"] = payload.replace(
            "nonce-completed", "unexpected-nonce"
        )

    result, output = _export(tmp_path, records, manifest)

    assert result.returncode != 0
    assert not output.exists()


def test_duplicate_call_id_fails_closed(tmp_path):
    records, manifest = _fixture()
    duplicate = copy.deepcopy(records[1])
    duplicate["ordinal"] = records[-1]["ordinal"]
    records.insert(-1, duplicate)
    records[-1]["ordinal"] += 1

    result, output = _export(tmp_path, records, manifest)

    assert result.returncode != 0
    assert not output.exists()


def test_truncated_rollout_fails_closed(tmp_path):
    records, manifest = _fixture()

    result, output = _export(tmp_path, records[:-1], manifest)

    assert result.returncode != 0
    assert not output.exists()


@pytest.mark.parametrize(
    "drift", ["manifest_schema", "cli_version", "relevant_payload_shape", "missing_required_field"]
)
def test_unknown_schema_or_version_fails_closed(tmp_path, drift):
    records, manifest = _fixture()
    if drift == "manifest_schema":
        manifest["schema_version"] = 2
    elif drift == "cli_version":
        records[0]["payload"]["cli_version"] = "0.155.0"
    elif drift == "relevant_payload_shape":
        records[1]["payload"]["new_unknown_field"] = True
    else:
        del records[1]["payload"]["namespace"]

    result, output = _export(tmp_path, records, manifest)

    assert result.returncode != 0
    assert not output.exists()


def test_ambiguous_thread_lookup_fails_closed(tmp_path):
    records, manifest = _fixture()
    sessions = tmp_path / "sessions"
    for name in ("a", "b"):
        path = sessions / name / f"rollout-date-{THREAD_ID}.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8"
        )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "evidence.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "export",
            "--thread-id",
            THREAD_ID,
            "--sessions-root",
            str(sessions),
            "--manifest",
            str(manifest_path),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode != 0
    assert not output.exists()


def test_setup_installs_exporter_as_executable_copy(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))

    result = subprocess.run(
        ["bash", str(REPO / "setup.sh")],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    installed = home / ".sdflow" / "hack" / SCRIPT.name
    assert result.returncode == 0, result.stderr
    assert installed.is_file() and not installed.is_symlink()
    assert os.access(installed, os.X_OK)
