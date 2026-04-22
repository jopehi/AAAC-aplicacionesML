from __future__ import annotations

import ipaddress
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass


@dataclass
class ResponseResult:
    success: bool
    action_type: str
    command_text: str
    stdout: str
    stderr: str
    note: str


def classify_response_level(rule_hits: list[str], prediction_label: str) -> str:
    high_abuse_hits = {"high_failures_5m", "many_users_per_ip_5m", "success_after_failures"}
    hits = set(rule_hits)
    if len(hits & high_abuse_hits) >= 2:
        return "candidate_block"
    if "ml_high_risk" in hits and len(hits & high_abuse_hits) >= 1:
        return "candidate_block"
    if "risk_score_threshold" in hits or "ml_high_risk" in hits or prediction_label == "high_risk":
        return "review"
    return "observe"


def normalize_ip(value: str) -> str:
    if not value or value == "unknown":
        raise ValueError("No hay una IP valida para ejecutar acciones.")
    return str(ipaddress.ip_address(value))


def ufw_available() -> bool:
    return shutil.which("ufw") is not None


def build_ufw_command(action: str, source_ip: str, port: int, sudo_command: str) -> list[str]:
    if action == "block":
        return [
            sudo_command,
            "ufw",
            "insert",
            "1",
            "deny",
            "from",
            source_ip,
            "to",
            "any",
            "port",
            str(port),
            "comment",
            f"ssh-ml-{source_ip}",
        ]
    if action == "unblock":
        return [
            sudo_command,
            "ufw",
            "delete",
            "deny",
            "from",
            source_ip,
            "to",
            "any",
            "port",
            str(port),
        ]
    raise ValueError(f"Accion UFW no soportada: {action}")


def execute_ufw_action(action: str, source_ip: str, port: int = 22, sudo_command: str = "sudo") -> ResponseResult:
    ip_value = normalize_ip(source_ip)
    command = build_ufw_command(action, ip_value, port, sudo_command)
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    success = process.returncode == 0
    note = "Accion ejecutada correctamente." if success else "La accion UFW fallo."
    return ResponseResult(
        success=success,
        action_type=action,
        command_text=" ".join(command),
        stdout=process.stdout.strip(),
        stderr=process.stderr.strip(),
        note=note,
    )


def record_response_action(
    conn: sqlite3.Connection,
    created_at: str,
    source_ip: str,
    action_type: str,
    trigger_source: str,
    action_status: str,
    note: str,
    command_text: str = "",
    command_stdout: str = "",
    command_stderr: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO response_actions (
            created_at, source_ip, action_type, trigger_source, action_status,
            note, command_text, command_stdout, command_stderr
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            source_ip,
            action_type,
            trigger_source,
            action_status,
            note,
            command_text,
            command_stdout,
            command_stderr,
        ),
    )
    conn.commit()


def has_successful_block(conn: sqlite3.Connection, source_ip: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM response_actions
        WHERE source_ip = ?
          AND action_type = 'block'
          AND action_status = 'success'
        ORDER BY id DESC
        LIMIT 1
        """,
        (source_ip,),
    ).fetchone()
    return row is not None
