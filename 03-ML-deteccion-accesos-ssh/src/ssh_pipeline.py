from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


FAILED_PASSWORD_RE = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s+\d\d:\d\d:\d\d)\s+"
    r"(?P<hostname>\S+)\s+sshd\[\d+\]:\s+Failed password for "
    r"(?:(invalid user )?)(?P<username>\S+)\s+from\s+"
    r"(?P<source_ip>\d+\.\d+\.\d+\.\d+)\s+port\s+(?P<source_port>\d+)"
)

ACCEPTED_PASSWORD_RE = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s+\d\d:\d\d:\d\d)\s+"
    r"(?P<hostname>\S+)\s+sshd\[\d+\]:\s+Accepted password for "
    r"(?P<username>\S+)\s+from\s+(?P<source_ip>\d+\.\d+\.\d+\.\d+)\s+"
    r"port\s+(?P<source_port>\d+)"
)

INVALID_USER_RE = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s+\d\d:\d\d:\d\d)\s+"
    r"(?P<hostname>\S+)\s+sshd\[\d+\]:\s+Invalid user\s+"
    r"(?P<username>\S+)\s+from\s+(?P<source_ip>\d+\.\d+\.\d+\.\d+)"
)


@dataclass
class ParsedEvent:
    timestamp: str
    hostname: str
    source_ip: str
    source_port: int | None
    username: str
    ssh_event_type: str
    auth_result: str
    raw_message: str


def load_settings(config_path: Path | None) -> dict:
    if config_path is None or not config_path.exists():
        return {
            "features": {"windows_minutes": [1, 5, 15]},
            "model": {"contamination": 0.08, "random_state": 42},
        }

    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        return {
            "features": {"windows_minutes": [1, 5, 15]},
            "model": {"contamination": 0.08, "random_state": 42},
        }

    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def parse_timestamp(value: str, year: int) -> pd.Timestamp:
    return pd.to_datetime(f"{year} {value}", format="%Y %b %d %H:%M:%S", errors="coerce")


def parse_log_line(line: str) -> ParsedEvent | None:
    for regex, event_type, auth_result in (
        (FAILED_PASSWORD_RE, "failed_password", "failure"),
        (ACCEPTED_PASSWORD_RE, "accepted_password", "success"),
        (INVALID_USER_RE, "invalid_user", "failure"),
    ):
        match = regex.search(line)
        if match:
            groups = match.groupdict()
            port_value = groups.get("source_port")
            return ParsedEvent(
                timestamp=groups["timestamp"],
                hostname=groups["hostname"],
                source_ip=groups["source_ip"],
                source_port=int(port_value) if port_value else None,
                username=groups["username"],
                ssh_event_type=event_type,
                auth_result=auth_result,
                raw_message=line.strip(),
            )
    return None


def parse_ssh_log(input_path: Path, output_path: Path, year: int) -> pd.DataFrame:
    events: list[dict] = []

    with input_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parsed = parse_log_line(line)
            if parsed is None:
                continue
            row = parsed.__dict__.copy()
            row["timestamp"] = parse_timestamp(parsed.timestamp, year)
            events.append(row)

    frame = pd.DataFrame(events)
    if frame.empty:
        frame = pd.DataFrame(
            columns=[
                "timestamp",
                "hostname",
                "source_ip",
                "source_port",
                "username",
                "ssh_event_type",
                "auth_result",
                "raw_message",
            ]
        )
    else:
        frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return frame


def _rolling_count(series: pd.Series, window: str) -> pd.Series:
    return series.rolling(window, min_periods=1).sum()


def rolling_nunique_by_group(
    frame: pd.DataFrame,
    group_col: str,
    value_col: str,
    timestamp_col: str,
    minutes: int,
) -> pd.Series:
    results = pd.Series(index=frame.index, dtype="float64")
    window = pd.Timedelta(minutes=minutes)

    for _, group in frame.groupby(group_col):
        group = group.sort_values(timestamp_col)
        timestamps = group[timestamp_col]
        values = group[value_col]
        group_results: list[int] = []

        for idx, current_time in enumerate(timestamps):
            start_time = current_time - window
            mask = (timestamps >= start_time) & (timestamps <= current_time)
            group_results.append(values[mask].nunique())

        results.loc[group.index] = group_results

    return results.sort_index()


def build_feature_frame(events_path: Path, output_path: Path, windows_minutes: Iterable[int]) -> pd.DataFrame:
    frame = pd.read_csv(events_path, parse_dates=["timestamp"])
    if frame.empty:
        feature_frame = pd.DataFrame()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        feature_frame.to_csv(output_path, index=False)
        return feature_frame

    frame = frame.sort_values("timestamp").reset_index(drop=True)
    frame["is_failure"] = (frame["auth_result"] == "failure").astype(int)
    frame["is_success"] = (frame["auth_result"] == "success").astype(int)
    frame["hour_of_day"] = frame["timestamp"].dt.hour
    frame["day_of_week"] = frame["timestamp"].dt.dayofweek
    frame["is_weekend"] = frame["day_of_week"].isin([5, 6]).astype(int)

    indexed = frame.set_index("timestamp")

    for minutes in windows_minutes:
        window = f"{minutes}min"
        frame[f"failed_count_{minutes}m"] = (
            indexed.groupby("source_ip")["is_failure"]
            .rolling(window, min_periods=1)
            .sum()
            .reset_index(level=0, drop=True)
            .values
        )
        frame[f"success_count_{minutes}m"] = (
            indexed.groupby("source_ip")["is_success"]
            .rolling(window, min_periods=1)
            .sum()
            .reset_index(level=0, drop=True)
            .values
        )
        frame[f"user_events_{minutes}m"] = (
            indexed.groupby("username")["is_failure"]
            .rolling(window, min_periods=1)
            .count()
            .reset_index(level=0, drop=True)
            .values
        )

    frame["user_count_per_ip_5m"] = rolling_nunique_by_group(
        frame,
        group_col="source_ip",
        value_col="username",
        timestamp_col="timestamp",
        minutes=5,
    )
    frame["ip_count_per_user_5m"] = rolling_nunique_by_group(
        frame,
        group_col="username",
        value_col="source_ip",
        timestamp_col="timestamp",
        minutes=5,
    )

    frame["failure_success_ratio"] = frame["failed_count_5m"] / (frame["success_count_5m"] + 1.0)
    frame["label"] = np.where(
        (frame["failed_count_5m"] >= 5) | (frame["user_count_per_ip_5m"] >= 3),
        1,
        0,
    )

    feature_columns = [
        "timestamp",
        "hostname",
        "source_ip",
        "username",
        "ssh_event_type",
        "auth_result",
        "hour_of_day",
        "day_of_week",
        "is_weekend",
        "failed_count_1m",
        "failed_count_5m",
        "failed_count_15m",
        "success_count_1m",
        "success_count_5m",
        "success_count_15m",
        "user_events_1m",
        "user_events_5m",
        "user_events_15m",
        "user_count_per_ip_5m",
        "ip_count_per_user_5m",
        "failure_success_ratio",
        "label",
        "raw_message",
    ]

    feature_frame = frame[feature_columns].copy()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    feature_frame.to_csv(output_path, index=False)
    return feature_frame


def train_baseline_model(
    features_path: Path,
    model_output: Path,
    metadata_output: Path,
    contamination: float,
    random_state: int,
) -> dict:
    frame = pd.read_csv(features_path, parse_dates=["timestamp"])
    if frame.empty:
        raise ValueError("El dataset de features esta vacio.")

    numeric_features = [
        "hour_of_day",
        "day_of_week",
        "is_weekend",
        "failed_count_1m",
        "failed_count_5m",
        "failed_count_15m",
        "success_count_1m",
        "success_count_5m",
        "success_count_15m",
        "user_events_1m",
        "user_events_5m",
        "user_events_15m",
        "user_count_per_ip_5m",
        "ip_count_per_user_5m",
        "failure_success_ratio",
    ]

    model_frame = frame[numeric_features].fillna(0)

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=200,
    )
    model.fit(model_frame)

    anomaly_score = model.decision_function(model_frame)
    prediction_raw = model.predict(model_frame)
    prediction_label = np.where(prediction_raw == -1, "high_risk", "normal")

    scored = frame.copy()
    scored["risk_score"] = -anomaly_score
    scored["prediction_label"] = prediction_label

    model_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output)
    scored.to_csv(metadata_output.parent / "scored_events.csv", index=False)

    metadata = {
        "model_type": "IsolationForest",
        "feature_columns": numeric_features,
        "contamination": contamination,
        "random_state": random_state,
        "training_rows": int(len(frame)),
        "high_risk_count": int((prediction_label == "high_risk").sum()),
    }

    with metadata_output.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    return metadata


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Utilidades del pipeline SSH ML.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_cmd = subparsers.add_parser("parse")
    parse_cmd.add_argument("--input", required=True, type=Path)
    parse_cmd.add_argument("--output", required=True, type=Path)
    parse_cmd.add_argument("--year", type=int, default=pd.Timestamp.utcnow().year)

    feat_cmd = subparsers.add_parser("features")
    feat_cmd.add_argument("--input", required=True, type=Path)
    feat_cmd.add_argument("--output", required=True, type=Path)
    feat_cmd.add_argument("--config", type=Path, default=None)

    train_cmd = subparsers.add_parser("train")
    train_cmd.add_argument("--input", required=True, type=Path)
    train_cmd.add_argument("--model-output", required=True, type=Path)
    train_cmd.add_argument("--metadata-output", required=True, type=Path)
    train_cmd.add_argument("--config", type=Path, default=None)

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.command == "parse":
        parse_ssh_log(args.input, args.output, args.year)
        return

    settings = load_settings(args.config)

    if args.command == "features":
        windows = settings.get("features", {}).get("windows_minutes", [1, 5, 15])
        build_feature_frame(args.input, args.output, windows)
        return

    if args.command == "train":
        model_cfg = settings.get("model", {})
        train_baseline_model(
            args.input,
            args.model_output,
            args.metadata_output,
            contamination=float(model_cfg.get("contamination", 0.08)),
            random_state=int(model_cfg.get("random_state", 42)),
        )


if __name__ == "__main__":
    main()
