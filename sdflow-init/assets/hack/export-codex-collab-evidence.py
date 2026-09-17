#!/usr/bin/env python3
"""从 Codex rollout 导出白名单 collaboration 生命周期证据。"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path


EVIDENCE_SCHEMA_VERSION = 1
MANIFEST_SCHEMA_VERSION = 1
SUPPORTED_CODEX_CLI_VERSIONS = {"0.154.0"}
THREAD_ID_RE = re.compile(r"^[0-9a-fA-F-]+$")
CALL_PAYLOAD_KEYS = {
    "type", "name", "arguments", "call_id", "id", "namespace",
    "internal_chat_message_metadata_passthrough",
}
OUTPUT_PAYLOAD_KEYS = {
    "type", "call_id", "output", "id", "internal_chat_message_metadata_passthrough",
}
AGENT_MESSAGE_KEYS = {
    "type", "id", "author", "recipient", "content",
    "internal_chat_message_metadata_passthrough",
}
ITEM_COMPLETED_KEYS = {
    "type", "thread_id", "turn_id", "started_at_ms", "completed_at_ms", "item",
}
ACTIVITY_KEYS = {"type", "id", "kind", "agent_thread_id", "agent_path"}
SESSION_META_KEYS = {
    "id", "session_id", "timestamp", "cwd", "originator", "cli_version", "source",
    "model_provider", "base_instructions", "thread_source", "history_mode", "git",
    "context_window",
}
MANIFEST_KEYS = {"schema_version", "run_id", "thread_id", "codex_cli_version", "records"}
RECORD_KEYS = {"evidence_id", "task_id", "nonce", "request", "terminal", "result"}
REQUEST_BASE_KEYS = {
    "call_id", "prompt_sha256", "prompt_length", "requested_model", "requested_effort",
    "context_mode", "expected_result",
}
TERMINAL_BASE_KEYS = {"state", "source_ordinal"}
RESULT_BASE_KEYS = {"source_type", "expectation"}
EVIDENCE_KEYS = {
    "schema_version", "record_type", "evidence_id", "run_id", "task_id", "nonce",
    "request_call_id", "request_source_ordinal", "requested_model", "requested_effort",
    "context_mode", "request_result", "rejection_kind", "agent_path", "agent_thread_id",
    "terminal_state", "terminal_source_ordinal", "terminal_call_id", "result_status",
    "result_ref", "observed_run_id", "observed_task_id", "observed_nonce",
    "result_source_ordinal", "result_source_call_id", "prompt_sha256", "prompt_length",
}


class EvidenceError(Exception):
    pass


def _fail(message):
    raise EvidenceError(message)


def _exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        _fail(f"{label}: schema drift")


def _read_json(path, label):
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except Exception as exc:
        _fail(f"{label}: invalid JSON: {exc}")
    if not isinstance(value, dict):
        _fail(f"{label}: object required")
    return value


def _read_manifest(path):
    manifest = _read_json(path, "manifest")
    _exact_keys(manifest, MANIFEST_KEYS, "manifest")
    if manifest["schema_version"] != MANIFEST_SCHEMA_VERSION:
        _fail("manifest: unsupported schema_version")
    for key in ("run_id", "thread_id", "codex_cli_version"):
        if not isinstance(manifest[key], str) or not manifest[key]:
            _fail(f"manifest: invalid {key}")
    if manifest["codex_cli_version"] not in SUPPORTED_CODEX_CLI_VERSIONS:
        _fail("manifest: unsupported Codex CLI version")
    if not isinstance(manifest["records"], list) or not manifest["records"]:
        _fail("manifest: non-empty records required")
    seen = set()
    for index, record in enumerate(manifest["records"]):
        _exact_keys(record, RECORD_KEYS, f"manifest.records[{index}]")
        for key in ("evidence_id", "task_id", "nonce"):
            if not isinstance(record[key], str) or not record[key]:
                _fail(f"manifest.records[{index}]: invalid {key}")
        if record["evidence_id"] in seen:
            _fail("manifest: duplicate evidence_id")
        seen.add(record["evidence_id"])
        _validate_manifest_record(record, index)
    return manifest


def _validate_manifest_record(record, index):
    label = f"manifest.records[{index}]"
    request = record["request"]
    request_keys = set(REQUEST_BASE_KEYS)
    if request.get("expected_result") == "accepted":
        request_keys |= {"agent_path", "agent_thread_id"}
        if "dispatch_call_id" in request:
            request_keys.add("dispatch_call_id")
    elif request.get("expected_result") == "rejected":
        request_keys.add("rejection_kind")
    else:
        _fail(f"{label}.request: invalid expected_result")
    _exact_keys(request, request_keys, f"{label}.request")
    if request["context_mode"] != "none":
        _fail(f"{label}.request: unsupported context_mode")
    if not re.fullmatch(r"[0-9a-f]{64}", request["prompt_sha256"] or ""):
        _fail(f"{label}.request: invalid prompt_sha256")
    if not isinstance(request["prompt_length"], int) or isinstance(request["prompt_length"], bool):
        _fail(f"{label}.request: invalid prompt_length")
    if request.get("rejection_kind") not in (None, "capacity", "unsupported-effort"):
        _fail(f"{label}.request: invalid rejection_kind")

    terminal = record["terminal"]
    terminal_keys = set(TERMINAL_BASE_KEYS)
    if terminal.get("state") in {"rejected", "interrupted"}:
        terminal_keys.add("call_id")
    _exact_keys(terminal, terminal_keys, f"{label}.terminal")
    if terminal["state"] not in {"rejected", "completed", "interrupted"}:
        _fail(f"{label}.terminal: invalid state")

    result = record["result"]
    result_keys = set(RESULT_BASE_KEYS)
    if result.get("source_type") == "agent_message":
        result_keys |= {"source_ordinal", "format"}
    elif result.get("source_type") == "list_agents":
        result_keys |= {"call_id", "agent_path", "format"}
    elif result.get("source_type") != "none":
        _fail(f"{label}.result: invalid source_type")
    if result.get("expectation") == "owner_mismatch":
        result_keys.add("observed_identity")
    _exact_keys(result, result_keys, f"{label}.result")
    if result["expectation"] not in {"attributed", "missing_result_ref", "owner_mismatch", "none"}:
        _fail(f"{label}.result: invalid expectation")
    if result.get("format") not in (None, "json", "nonce_marker"):
        _fail(f"{label}.result: invalid format")
    if "observed_identity" in result:
        _exact_keys(result["observed_identity"], {"run_id", "task_id", "nonce"}, f"{label}.result.observed_identity")


def _locate_rollout(args, manifest):
    if args.input:
        path = Path(args.input).expanduser()
        if not path.is_file():
            _fail("input rollout not found")
        return path
    thread_id = args.thread_id or os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
    if not thread_id:
        thread_id = manifest["thread_id"]
    if not THREAD_ID_RE.fullmatch(thread_id) or Path(thread_id).name != thread_id:
        _fail("invalid thread id")
    if thread_id != manifest["thread_id"]:
        _fail("thread id does not match manifest")
    root = Path(args.sessions_root).expanduser()
    matches = sorted(root.glob(f"**/rollout-*-{thread_id}.jsonl"))
    if len(matches) != 1:
        _fail(f"thread lookup expected one rollout, found {len(matches)}")
    return matches[0]


def _read_rollout(path, manifest):
    rows = []
    try:
        with path.open("r", encoding="utf-8", errors="strict") as stream:
            for line_number, raw in enumerate(stream, 1):
                if not raw.endswith("\n"):
                    _fail("rollout: truncated final line")
                try:
                    row = json.loads(raw)
                except Exception as exc:
                    _fail(f"rollout line {line_number}: invalid JSON: {exc}")
                if not isinstance(row, dict):
                    _fail(f"rollout line {line_number}: object required")
                if row.get("ordinal") != len(rows):
                    _fail(f"rollout line {line_number}: ordinal drift")
                rows.append(row)
    except EvidenceError:
        raise
    except Exception as exc:
        _fail(f"rollout: read failed: {exc}")
    if not rows:
        _fail("rollout: empty")
    if rows[-1].get("type") != "event_msg" or rows[-1].get("payload", {}).get("type") != "task_complete":
        _fail("rollout: no final task_complete; transcript may be truncated")
    metas = [row for row in rows if row.get("type") == "session_meta"]
    if len(metas) != 1:
        _fail("rollout: exactly one session_meta required")
    meta = metas[0]
    _exact_keys(meta, {"timestamp", "ordinal", "type", "payload"}, "session_meta record")
    _exact_keys(meta["payload"], SESSION_META_KEYS, "session_meta payload")
    if meta["payload"]["id"] != manifest["thread_id"] or meta["payload"]["session_id"] != manifest["thread_id"]:
        _fail("rollout: session identity mismatch")
    if meta["payload"]["cli_version"] != manifest["codex_cli_version"]:
        _fail("rollout: Codex CLI version mismatch")
    if meta["payload"]["cli_version"] not in SUPPORTED_CODEX_CLI_VERSIONS:
        _fail("rollout: unsupported Codex CLI version")
    return rows


def _index_rollout(rows):
    calls = {}
    outputs = {}
    activities = []
    for row in rows:
        if row.get("type") == "response_item" and isinstance(row.get("payload"), dict):
            payload = row["payload"]
            if payload.get("type") == "function_call":
                _exact_keys(payload, CALL_PAYLOAD_KEYS, f"function_call ordinal {row['ordinal']}")
                call_id = payload["call_id"]
                if call_id in calls:
                    _fail(f"duplicate function_call {call_id}")
                calls[call_id] = row
            elif payload.get("type") == "function_call_output":
                _exact_keys(payload, OUTPUT_PAYLOAD_KEYS, f"function_call_output ordinal {row['ordinal']}")
                call_id = payload["call_id"]
                if call_id in outputs:
                    _fail(f"duplicate function_call_output {call_id}")
                outputs[call_id] = row
        if row.get("type") == "event_msg" and isinstance(row.get("payload"), dict):
            payload = row["payload"]
            item = payload.get("item")
            if payload.get("type") == "item_completed" and isinstance(item, dict) and item.get("type") == "SubAgentActivity":
                _exact_keys(payload, ITEM_COMPLETED_KEYS, f"activity payload ordinal {row['ordinal']}")
                _exact_keys(item, ACTIVITY_KEYS, f"activity item ordinal {row['ordinal']}")
                activities.append(row)
    for call_id in set(calls) | set(outputs):
        if (call_id in calls) != (call_id in outputs):
            # Codex can omit an output only while a live transcript is incomplete; final transcripts may not.
            _fail(f"unpaired collaboration call {call_id}")
    return calls, outputs, activities


def _parse_arguments(row):
    try:
        value = json.loads(row["payload"]["arguments"])
    except Exception:
        _fail(f"function_call ordinal {row['ordinal']}: invalid arguments JSON")
    if not isinstance(value, dict):
        _fail(f"function_call ordinal {row['ordinal']}: arguments object required")
    return value


def _parse_json_output(row, label):
    try:
        value = json.loads(row["payload"]["output"])
    except Exception:
        _fail(f"{label}: invalid JSON output")
    return value


def _one_activity(activities, *, source_ordinal=None, call_id=None, kind=None):
    matches = []
    for row in activities:
        item = row["payload"]["item"]
        if source_ordinal is not None and row["ordinal"] != source_ordinal:
            continue
        if call_id is not None and item["id"] != call_id:
            continue
        if kind is not None and item["kind"] != kind:
            continue
        matches.append(row)
    if len(matches) != 1:
        _fail("activity correlation is missing or ambiguous")
    return matches[0]


def _validate_request(record, calls, outputs, activities):
    expected = record["request"]
    call_id = expected["call_id"]
    call = calls.get(call_id)
    output = outputs.get(call_id)
    if call is None or output is None:
        _fail(f"{record['evidence_id']}: request call is missing")
    is_followup = call["payload"]["name"] == "followup_task"
    if call["payload"]["name"] not in {"spawn_agent", "followup_task"}:
        _fail(f"{record['evidence_id']}: request is not a supported collaboration call")
    args = _parse_arguments(call)
    expected_arg_keys = {"target", "message"} if is_followup else {
        "task_name", "fork_turns", "message", "model", "reasoning_effort"
    }
    _exact_keys(args, expected_arg_keys, f"{record['evidence_id']}: spawn arguments")
    prompt = args["message"]
    if not isinstance(prompt, str):
        _fail(f"{record['evidence_id']}: prompt is not text")
    if len(prompt) != expected["prompt_length"] or hashlib.sha256(prompt.encode()).hexdigest() != expected["prompt_sha256"]:
        _fail(f"{record['evidence_id']}: prompt identity mismatch")
    dispatch_args = args
    if is_followup:
        if expected.get("expected_result") != "accepted" or args["target"] != expected["agent_path"]:
            _fail(f"{record['evidence_id']}: followup target mismatch")
        dispatch_call_id = expected.get("dispatch_call_id")
        dispatch = calls.get(dispatch_call_id)
        dispatch_output = outputs.get(dispatch_call_id)
        if dispatch is None or dispatch_output is None or dispatch["payload"]["name"] != "spawn_agent":
            _fail(f"{record['evidence_id']}: origin dispatch missing")
        dispatch_args = _parse_arguments(dispatch)
        _exact_keys(
            dispatch_args,
            {"task_name", "fork_turns", "message", "model", "reasoning_effort"},
            f"{record['evidence_id']}: origin dispatch arguments",
        )
        if _parse_json_output(dispatch_output, f"{record['evidence_id']}: origin dispatch output") != {"task_name": expected["agent_path"]}:
            _fail(f"{record['evidence_id']}: origin dispatch output mismatch")
        started = _one_activity(activities, call_id=dispatch_call_id, kind="started")
        started_item = started["payload"]["item"]
        if started_item["agent_path"] != expected["agent_path"] or started_item["agent_thread_id"] != expected["agent_thread_id"]:
            _fail(f"{record['evidence_id']}: origin dispatch attribution mismatch")
        if output["payload"]["output"] != "":
            _fail(f"{record['evidence_id']}: followup output mismatch")
        interacted = _one_activity(activities, call_id=call_id, kind="interacted")
        interacted_item = interacted["payload"]["item"]
        if interacted_item["agent_path"] != expected["agent_path"] or interacted_item["agent_thread_id"] != expected["agent_thread_id"]:
            _fail(f"{record['evidence_id']}: followup attribution mismatch")
    elif "dispatch_call_id" in expected:
        _fail(f"{record['evidence_id']}: unexpected dispatch_call_id")
    if dispatch_args["model"] != expected["requested_model"] or dispatch_args["reasoning_effort"] != expected["requested_effort"]:
        _fail(f"{record['evidence_id']}: model or effort mismatch")
    if dispatch_args["fork_turns"] != expected["context_mode"]:
        _fail(f"{record['evidence_id']}: context mismatch")

    if expected["expected_result"] == "accepted":
        if not is_followup:
            parsed = _parse_json_output(output, f"{record['evidence_id']}: accepted output")
            if parsed != {"task_name": expected["agent_path"]}:
                _fail(f"{record['evidence_id']}: accepted output mismatch")
            started = _one_activity(activities, call_id=call_id, kind="started")
            item = started["payload"]["item"]
            if started["payload"]["thread_id"] != manifest_thread_id or item["agent_path"] != expected["agent_path"] or item["agent_thread_id"] != expected["agent_thread_id"]:
                _fail(f"{record['evidence_id']}: accepted agent attribution mismatch")
        return call, output, expected["agent_path"], expected["agent_thread_id"], None

    raw = output["payload"]["output"]
    rejection_kind = expected["rejection_kind"]
    if rejection_kind == "capacity":
        matched = raw == "collab spawn failed: agent thread limit reached"
    else:
        matched = bool(re.fullmatch(r"Reasoning effort [`'][^`']+[`'] is not supported for model [`'][^`']+[`']\. Supported reasoning efforts: [a-z, ]+", raw))
    if not matched:
        _fail(f"{record['evidence_id']}: rejection output mismatch")
    if any(row["payload"]["item"]["id"] == call_id for row in activities):
        _fail(f"{record['evidence_id']}: rejected call unexpectedly started")
    return call, output, None, None, rejection_kind


def _validate_terminal(record, calls, outputs, activities, agent_path, agent_thread_id):
    terminal = record["terminal"]
    state = terminal["state"]
    source = terminal["source_ordinal"]
    if state == "rejected":
        call_id = terminal["call_id"]
        row = outputs.get(call_id)
        if row is None or row["ordinal"] != source or call_id != record["request"]["call_id"]:
            _fail(f"{record['evidence_id']}: rejected terminal mismatch")
        return call_id
    activity = _one_activity(activities, source_ordinal=source, kind=state)
    item = activity["payload"]["item"]
    if activity["payload"]["thread_id"] != manifest_thread_id or item["agent_path"] != agent_path or item["agent_thread_id"] != agent_thread_id:
        _fail(f"{record['evidence_id']}: terminal attribution mismatch")
    if state == "interrupted":
        call_id = terminal["call_id"]
        if item["id"] != call_id:
            _fail(f"{record['evidence_id']}: interrupt call_id mismatch")
        call = calls.get(call_id)
        output = outputs.get(call_id)
        if call is None or output is None or call["payload"]["name"] != "interrupt_agent":
            _fail(f"{record['evidence_id']}: interrupt call missing")
        if _parse_arguments(call) != {"target": agent_path}:
            _fail(f"{record['evidence_id']}: interrupt target mismatch")
        if _parse_json_output(output, f"{record['evidence_id']}: interrupt output") != {"previous_status": "running"}:
            _fail(f"{record['evidence_id']}: interrupt output mismatch")
        return call_id
    return None


def _parse_agent_message(row, agent_path):
    if row.get("type") != "response_item":
        _fail("result agent_message: wrong record type")
    payload = row.get("payload")
    _exact_keys(payload, AGENT_MESSAGE_KEYS, f"agent_message ordinal {row.get('ordinal')}")
    if payload["type"] != "agent_message" or payload["author"] != agent_path or payload["recipient"] != "/root":
        _fail("result agent_message: attribution mismatch")
    content = payload["content"]
    if not isinstance(content, list) or len(content) != 1 or set(content[0]) != {"type", "text"} or content[0]["type"] != "input_text":
        _fail("result agent_message: content schema drift")
    prefix = f"Message Type: FINAL_ANSWER\nTask name: /root\nSender: {agent_path}\nPayload:\n"
    text = content[0]["text"]
    if not isinstance(text, str) or not text.startswith(prefix):
        _fail("result agent_message: envelope mismatch")
    return text[len(prefix):]


def _result_text(result, rows, calls, outputs, agent_path):
    source_type = result["source_type"]
    if source_type == "none":
        return None, None, None
    if source_type == "agent_message":
        ordinal = result["source_ordinal"]
        if not isinstance(ordinal, int) or ordinal < 0 or ordinal >= len(rows):
            _fail("result agent_message: invalid source ordinal")
        return _parse_agent_message(rows[ordinal], agent_path), ordinal, None
    call_id = result["call_id"]
    call = calls.get(call_id)
    output = outputs.get(call_id)
    if call is None or output is None or call["payload"]["name"] != "list_agents" or _parse_arguments(call) != {}:
        _fail("result list_agents call mismatch")
    parsed = _parse_json_output(output, "result list_agents output")
    if not isinstance(parsed, dict) or set(parsed) != {"agents"} or not isinstance(parsed["agents"], list):
        _fail("result list_agents schema drift")
    matches = [agent for agent in parsed["agents"] if isinstance(agent, dict) and agent.get("agent_name") == result["agent_path"]]
    if len(matches) != 1 or set(matches[0]) != {"agent_name", "agent_status"}:
        _fail("result list_agents attribution is missing or ambiguous")
    status = matches[0]["agent_status"]
    if not isinstance(status, dict) or set(status) != {"completed"} or not isinstance(status["completed"], str):
        _fail("result list_agents terminal schema drift")
    if result["agent_path"] != agent_path:
        _fail("result list_agents agent_path mismatch")
    return status["completed"], output["ordinal"], call_id


def _validate_result(record, rows, calls, outputs, agent_path):
    result = record["result"]
    raw, source_ordinal, source_call_id = _result_text(result, rows, calls, outputs, agent_path)
    expectation = result["expectation"]
    if expectation == "none":
        if raw is not None:
            _fail(f"{record['evidence_id']}: unexpected result")
        return "none", None, None, None, None, source_ordinal, source_call_id
    if result["format"] == "nonce_marker":
        match = re.fullmatch(r"[A-Z][A-Z0-9_]* nonce=([A-Za-z0-9._-]+)", raw or "")
        if not match or match.group(1) != record["nonce"] or expectation != "attributed":
            _fail(f"{record['evidence_id']}: nonce marker mismatch")
        return "attributed", record["nonce"], record_run_id, record["task_id"], record["nonce"], source_ordinal, source_call_id
    try:
        payload = json.loads(raw)
    except Exception:
        _fail(f"{record['evidence_id']}: result payload is not JSON")
    if not isinstance(payload, dict) or set(payload) not in (
        {"run_id", "task_id", "nonce", "status"},
        {"run_id", "task_id", "nonce", "status", "result_ref"},
    ) or payload.get("status") != "completed":
        _fail(f"{record['evidence_id']}: result schema drift")
    observed = (payload["run_id"], payload["task_id"], payload["nonce"])
    current = (record_run_id, record["task_id"], record["nonce"])
    result_ref = payload.get("result_ref")
    if expectation == "attributed":
        if observed != current or not isinstance(result_ref, str) or not result_ref:
            _fail(f"{record['evidence_id']}: result attribution mismatch")
        status = "attributed"
    elif expectation == "missing_result_ref":
        if observed != current or "result_ref" in payload:
            _fail(f"{record['evidence_id']}: missing-result negative evidence mismatch")
        status = "missing-result"
    else:
        expected_observed = result["observed_identity"]
        if observed != (
            expected_observed["run_id"], expected_observed["task_id"], expected_observed["nonce"]
        ) or observed == current or not isinstance(result_ref, str) or not result_ref:
            _fail(f"{record['evidence_id']}: old-result negative evidence mismatch")
        status = "old-result"
    return status, result_ref, observed[0], observed[1], observed[2], source_ordinal, source_call_id


def _export(manifest, rows):
    global manifest_thread_id, record_run_id
    manifest_thread_id = manifest["thread_id"]
    record_run_id = manifest["run_id"]
    calls, outputs, activities = _index_rollout(rows)
    evidence_rows = []
    for record in manifest["records"]:
        call, _output, agent_path, agent_thread_id, rejection_kind = _validate_request(
            record, calls, outputs, activities
        )
        terminal_call_id = _validate_terminal(
            record, calls, outputs, activities, agent_path, agent_thread_id
        )
        (
            result_status, result_ref, observed_run_id, observed_task_id, observed_nonce,
            result_source_ordinal, result_source_call_id,
        ) = _validate_result(record, rows, calls, outputs, agent_path)
        evidence_rows.append(
            {
                "schema_version": EVIDENCE_SCHEMA_VERSION,
                "record_type": "evidence",
                "evidence_id": record["evidence_id"],
                "run_id": manifest["run_id"],
                "task_id": record["task_id"],
                "nonce": record["nonce"],
                "request_call_id": record["request"]["call_id"],
                "request_source_ordinal": call["ordinal"],
                "requested_model": record["request"]["requested_model"],
                "requested_effort": record["request"]["requested_effort"],
                "context_mode": record["request"]["context_mode"],
                "request_result": record["request"]["expected_result"],
                "rejection_kind": rejection_kind,
                "agent_path": agent_path,
                "agent_thread_id": agent_thread_id,
                "terminal_state": record["terminal"]["state"],
                "terminal_source_ordinal": record["terminal"]["source_ordinal"],
                "terminal_call_id": terminal_call_id,
                "result_status": result_status,
                "result_ref": result_ref,
                "observed_run_id": observed_run_id,
                "observed_task_id": observed_task_id,
                "observed_nonce": observed_nonce,
                "result_source_ordinal": result_source_ordinal,
                "result_source_call_id": result_source_call_id,
                "prompt_sha256": record["request"]["prompt_sha256"],
                "prompt_length": record["request"]["prompt_length"],
            }
        )
    return [
        {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "record_type": "run",
            "run_id": manifest["run_id"],
            "source_thread_id": manifest["thread_id"],
            "source_cli_version": manifest["codex_cli_version"],
        },
        *evidence_rows,
    ]


def _atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_jsonl(path, rows):
    text = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    _atomic_write(path, text)


def _read_evidence(path):
    rows = []
    try:
        with Path(path).open("r", encoding="utf-8", errors="strict") as stream:
            for raw in stream:
                rows.append(json.loads(raw))
    except Exception as exc:
        _fail(f"sanitized evidence: invalid JSONL: {exc}")
    if not rows:
        _fail("sanitized evidence: empty")
    header = rows[0]
    _exact_keys(
        header,
        {"schema_version", "record_type", "run_id", "source_thread_id", "source_cli_version"},
        "sanitized evidence header",
    )
    if header["schema_version"] != EVIDENCE_SCHEMA_VERSION or header["record_type"] != "run":
        _fail("sanitized evidence: unsupported schema")
    for index, row in enumerate(rows[1:], 1):
        _exact_keys(row, EVIDENCE_KEYS, f"sanitized evidence row {index}")
        if row["schema_version"] != EVIDENCE_SCHEMA_VERSION or row["record_type"] != "evidence":
            _fail(f"sanitized evidence row {index}: unsupported schema")
    return rows


def _source_text(row):
    parts = [f"request:{row['request_source_ordinal']}/{row['request_call_id']}"]
    terminal = f"terminal:{row['terminal_source_ordinal']}"
    if row["terminal_call_id"]:
        terminal += f"/{row['terminal_call_id']}"
    parts.append(terminal)
    if row["result_source_ordinal"] is not None:
        result = f"result:{row['result_source_ordinal']}"
        if row["result_source_call_id"]:
            result += f"/{row['result_source_call_id']}"
        parts.append(result)
    return "; ".join(parts)


def _render(rows):
    header = rows[0]
    lines = [
        "# Codex collaboration evidence",
        "",
        f"- run_id: `{header['run_id']}`",
        f"- source_thread_id: `{header['source_thread_id']}`",
        f"- source_cli_version: `{header['source_cli_version']}`",
        "",
        "| evidence_id | task_id / nonce | request | model / effort / context | terminal | result | source |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows[1:]:
        request = row["request_result"]
        if row["rejection_kind"]:
            request += f" ({row['rejection_kind']})"
        result = row["result_status"]
        if row["result_ref"]:
            result += f" (`{row['result_ref']}`"
            if row["result_status"] == "old-result":
                result += (
                    f"; observed {row['observed_run_id']}/{row['observed_task_id']}/"
                    f"{row['observed_nonce']}"
                )
            result += ")"
        lines.append(
            f"| {row['evidence_id']} | {row['task_id']} / {row['nonce']} | {request} | "
            f"{row['requested_model']} / {row['requested_effort']} / {row['context_mode']} | "
            f"{row['terminal_state']} | {result} | {_source_text(row)} |"
        )
    return "\n".join(lines) + "\n"


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    export = subparsers.add_parser("export")
    export.add_argument("--manifest", required=True)
    export.add_argument("--input")
    export.add_argument("--thread-id")
    export.add_argument("--sessions-root", default="~/.codex/sessions")
    export.add_argument("--output", required=True)
    render = subparsers.add_parser("render")
    render.add_argument("--input", required=True)
    render.add_argument("--output", required=True)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        if args.command == "export":
            manifest = _read_manifest(Path(args.manifest))
            rollout = _locate_rollout(args, manifest)
            rows = _read_rollout(rollout, manifest)
            evidence = _export(manifest, rows)
            _write_jsonl(args.output, evidence)
        else:
            evidence = _read_evidence(args.input)
            _atomic_write(args.output, _render(evidence))
    except EvidenceError as exc:
        print(f"export-codex-collab-evidence: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
