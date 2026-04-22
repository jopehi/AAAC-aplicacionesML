from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.response_actions import (
    classify_response_level,
    execute_ufw_action,
    has_successful_block,
    record_response_action,
    ufw_available,
)
from src.ssh_pipeline import ParsedEvent, load_settings, parse_log_line, parse_timestamp


@dataclass
class MonitorArtifacts:
    model: object
    feature_columns: list[str]
    config: dict


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ssh_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_hash TEXT UNIQUE,
            timestamp TEXT NOT NULL,
            hostname TEXT,
            source_ip TEXT,
            source_port INTEGER,
            username TEXT,
            ssh_event_type TEXT,
            auth_result TEXT,
            raw_message TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ssh_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_hash TEXT UNIQUE,
            created_at TEXT NOT NULL,
            source_ip TEXT,
            username TEXT,
            ssh_event_type TEXT,
            auth_result TEXT,
            risk_score REAL,
            prediction_label TEXT,
            reason_summary TEXT,
            rule_hits TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            raw_message TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS response_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_ip TEXT NOT NULL,
            action_type TEXT NOT NULL,
            trigger_source TEXT NOT NULL,
            action_status TEXT NOT NULL,
            note TEXT,
            command_text TEXT,
            command_stdout TEXT,
            command_stderr TEXT
        )
        """
    )
    conn.commit()
    return conn


def load_artifacts(model_path: Path, metadata_path: Path, settings_path: Path | None) -> MonitorArtifacts:
    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    model_version = metadata.get("sklearn_version")
    current_version = sklearn.__version__
    if model_version and model_version != current_version:
        print(
            f"Advertencia: el modelo fue entrenado con scikit-learn {model_version} "
            f"y el entorno actual usa {current_version}. Conviene reentrenar con "
            f"'python scripts/retrain_model.py --input-log /var/log/auth.log'."
        )
    model = joblib.load(model_path)
    settings = load_settings(settings_path)
    return MonitorArtifacts(
        model=model,
        feature_columns=metadata["feature_columns"],
        config=settings.get("realtime", {}),
    )


def event_hash(event: ParsedEvent) -> str:
    raw = f"{event.timestamp}|{event.hostname}|{event.source_ip}|{event.username}|{event.ssh_event_type}|{event.raw_message}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _filter_window(events: Deque[dict], current_ts: pd.Timestamp, minutes: int) -> list[dict]:
    start = current_ts - pd.Timedelta(minutes=minutes)
    return [item for item in events if start <= item["timestamp"] <= current_ts]


def build_realtime_features(history: Deque[dict], event: dict) -> dict:
    current_ts = event["timestamp"]
    history.append(event)

    # Trim to 15 minutes to keep memory bounded for the current feature set.
    min_ts = current_ts - pd.Timedelta(minutes=15)
    while history and history[0]["timestamp"] < min_ts:
        history.popleft()

    features = {
        "hour_of_day": current_ts.hour,
        "day_of_week": current_ts.dayofweek,
        "is_weekend": 1 if current_ts.dayofweek in (5, 6) else 0,
    }

    for minutes in (1, 5, 15):
        window_events = _filter_window(history, current_ts, minutes)
        same_ip = [item for item in window_events if item["source_ip"] == event["source_ip"]]
        same_user = [item for item in window_events if item["username"] == event["username"]]
        features[f"failed_count_{minutes}m"] = sum(1 for item in same_ip if item["auth_result"] == "failure")
        features[f"success_count_{minutes}m"] = sum(1 for item in same_ip if item["auth_result"] == "success")
        features[f"user_events_{minutes}m"] = len(same_user)

    window_5_events = _filter_window(history, current_ts, 5)
    same_ip_5 = [item for item in window_5_events if item["source_ip"] == event["source_ip"]]
    same_user_5 = [item for item in window_5_events if item["username"] == event["username"]]
    features["user_count_per_ip_5m"] = len({item["username"] for item in same_ip_5})
    features["ip_count_per_user_5m"] = len({item["source_ip"] for item in same_user_5})
    features["failure_success_ratio"] = features["failed_count_5m"] / (features["success_count_5m"] + 1.0)

    return features


def score_event(artifacts: MonitorArtifacts, feature_row: dict) -> tuple[float, str]:
    model_frame = pd.DataFrame([[feature_row[column] for column in artifacts.feature_columns]], columns=artifacts.feature_columns)
    anomaly_score = artifacts.model.decision_function(model_frame)[0]
    prediction = artifacts.model.predict(model_frame)[0]
    risk_score = float(-anomaly_score)
    label = "high_risk" if prediction == -1 else "normal"
    return risk_score, label


def derive_rule_hits(event: dict, feature_row: dict, risk_score: float, label: str, config: dict) -> list[str]:
    hits: list[str] = []
    if feature_row["failed_count_5m"] >= int(config.get("high_failure_threshold_5m", 8)):
        hits.append("high_failures_5m")
    if feature_row["user_count_per_ip_5m"] >= int(config.get("distinct_users_threshold_5m", 4)):
        hits.append("many_users_per_ip_5m")
    if event["auth_result"] == "success" and feature_row["failed_count_5m"] >= int(config.get("successful_after_failures_threshold_5m", 5)):
        hits.append("success_after_failures")
    if risk_score >= float(config.get("risk_score_threshold", 0.1)):
        hits.append("risk_score_threshold")
    if label == "high_risk":
        hits.append("ml_high_risk")
    return hits


def build_reason_summary(rule_hits: list[str], event: dict, feature_row: dict) -> str:
    if not rule_hits:
        return "Sin alertas activadas."
    return (
        f"Evento {event['ssh_event_type']} para usuario {event['username']} desde {event['source_ip']}; "
        f"fallos 5m={feature_row['failed_count_5m']}, usuarios distintos 5m={feature_row['user_count_per_ip_5m']}, "
        f"reglas={', '.join(rule_hits)}"
    )


def persist_event(conn: sqlite3.Connection, event: dict) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO ssh_events (
            event_hash, timestamp, hostname, source_ip, source_port, username, ssh_event_type, auth_result, raw_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["event_hash"],
            event["timestamp"].isoformat(),
            event["hostname"],
            event["source_ip"],
            event["source_port"],
            event["username"],
            event["ssh_event_type"],
            event["auth_result"],
            event["raw_message"],
        ),
    )
    conn.commit()


def persist_alert(
    conn: sqlite3.Connection,
    event: dict,
    risk_score: float,
    label: str,
    reason_summary: str,
    rule_hits: list[str],
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO ssh_alerts (
            event_hash, created_at, source_ip, username, ssh_event_type, auth_result,
            risk_score, prediction_label, reason_summary, rule_hits, status, raw_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["event_hash"],
            event["timestamp"].isoformat(),
            event["source_ip"],
            event["username"],
            event["ssh_event_type"],
            event["auth_result"],
            risk_score,
            label,
            reason_summary,
            json.dumps(rule_hits),
            "new",
            event["raw_message"],
        ),
    )
    conn.commit()


def maybe_auto_block(
    conn: sqlite3.Connection,
    event: dict,
    rule_hits: list[str],
    label: str,
    settings: dict,
) -> None:
    response_cfg = settings.get("response", {})
    if not response_cfg.get("enable_ufw_actions", False):
        return
    if not response_cfg.get("auto_block_enabled", False):
        return
    if classify_response_level(rule_hits, label) != "candidate_block":
        return
    source_ip = event.get("source_ip", "")
    if not source_ip or source_ip == "unknown":
        return
    if has_successful_block(conn, source_ip):
        return
    if not ufw_available():
        record_response_action(
            conn,
            created_at=event["timestamp"].isoformat(),
            source_ip=source_ip,
            action_type="block",
            trigger_source="automatic",
            action_status="skipped",
            note="No se encontro ufw en el sistema.",
        )
        return

    result = execute_ufw_action(
        "block",
        source_ip=source_ip,
        port=int(response_cfg.get("ufw_port", 22)),
        sudo_command=str(response_cfg.get("sudo_command", "sudo")),
    )
    record_response_action(
        conn,
        created_at=event["timestamp"].isoformat(),
        source_ip=source_ip,
        action_type="block",
        trigger_source="automatic",
        action_status="success" if result.success else "failed",
        note=result.note,
        command_text=result.command_text,
        command_stdout=result.stdout,
        command_stderr=result.stderr,
    )


def process_line(
    line: str,
    year: int,
    history: Deque[dict],
    conn: sqlite3.Connection,
    artifacts: MonitorArtifacts,
) -> bool:
    parsed = parse_log_line(line)
    if parsed is None:
        return False

    event = {
        "event_hash": event_hash(parsed),
        "timestamp": parse_timestamp(parsed.timestamp, year),
        "hostname": parsed.hostname,
        "source_ip": parsed.source_ip,
        "source_port": parsed.source_port,
        "username": parsed.username,
        "ssh_event_type": parsed.ssh_event_type,
        "auth_result": parsed.auth_result,
        "raw_message": parsed.raw_message,
    }

    if pd.isna(event["timestamp"]):
        return False

    persist_event(conn, event)
    feature_row = build_realtime_features(history, event)
    risk_score, label = score_event(artifacts, feature_row)
    rule_hits = derive_rule_hits(event, feature_row, risk_score, label, artifacts.config)

    if rule_hits:
        persist_alert(
            conn,
            event,
            risk_score,
            label,
            build_reason_summary(rule_hits, event, feature_row),
            rule_hits,
        )
        maybe_auto_block(conn, event, rule_hits, label, artifacts.config)
    return True


def replay_file(
    input_path: Path,
    year: int,
    history: Deque[dict],
    conn: sqlite3.Connection,
    artifacts: MonitorArtifacts,
) -> int:
    processed = 0
    with input_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if process_line(line, year, history, conn, artifacts):
                processed += 1
    return processed


def follow_file(
    input_path: Path,
    year: int,
    history: Deque[dict],
    conn: sqlite3.Connection,
    artifacts: MonitorArtifacts,
    poll_seconds: float,
) -> None:
    with input_path.open("r", encoding="utf-8", errors="ignore") as handle:
        handle.seek(0, 2)
        while True:
            line = handle.readline()
            if not line:
                time.sleep(poll_seconds)
                continue
            process_line(line, year, history, conn, artifacts)


def follow_journal(
    year: int,
    history: Deque[dict],
    conn: sqlite3.Connection,
    artifacts: MonitorArtifacts,
) -> None:
    process = subprocess.Popen(
        ["journalctl", "-u", "ssh", "-f", "-o", "short-iso"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert process.stdout is not None
    for line in process.stdout:
        process_line(line, year, history, conn, artifacts)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor continuo SSH con scoring y SQLite.")
    parser.add_argument("--model-path", type=Path, default=Path("models/ssh_anomaly_model.joblib"))
    parser.add_argument("--metadata-path", type=Path, default=Path("models/model_metadata.json"))
    parser.add_argument("--config", type=Path, default=Path("config/settings.yaml"))
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--input-file", type=Path, default=None)
    parser.add_argument("--replay-existing", action="store_true")
    parser.add_argument("--follow-file", action="store_true")
    parser.add_argument("--follow-journal", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--year", type=int, default=pd.Timestamp.utcnow().year)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    settings = load_settings(args.config)
    realtime_cfg = settings.get("realtime", {})
    db_path = args.db_path or Path(realtime_cfg.get("sqlite_path", "data/processed/ssh_monitor.db"))
    conn = init_db(db_path)
    artifacts = load_artifacts(args.model_path, args.metadata_path, args.config)
    history: Deque[dict] = deque()

    if args.replay_existing and args.input_file:
        replay_file(args.input_file, args.year, history, conn, artifacts)

    if args.follow_journal:
        follow_journal(args.year, history, conn, artifacts)
        return

    if args.follow_file and args.input_file:
        follow_file(args.input_file, args.year, history, conn, artifacts, args.poll_seconds)
        return


if __name__ == "__main__":
    main()
