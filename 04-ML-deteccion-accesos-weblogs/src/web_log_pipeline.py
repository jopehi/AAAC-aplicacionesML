from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


APACHE_COMBINED_RE = re.compile(
    r'^(?P<source_ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<url>\S+)\s+(?P<protocol>[^"]+)"\s+'
    r"(?P<status_code>\d{3})\s+(?P<bytes_sent>\S+)"
    r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<user_agent>[^"]*)")?'
)

APACHE_ERROR_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<module>[^\]:]+):(?P<level>[^\]]+)\]\s+"
    r"\[pid\s+(?P<pid>\d+)(?::tid\s+(?P<tid>\d+))?\]\s*(?:\[client\s+(?P<client>[^\]]+)\]\s*)?"
    r"(?P<message>.*)$"
)

SUSPICIOUS_PATTERNS = {
    "sql_injection": re.compile(r"(?:'|%27|--|%2d%2d|\bunion\b|\bselect\b|\bor\b\s+1=1|\bsleep\s*\()", re.I),
    "xss": re.compile(r"(?:<script|%3cscript|javascript:|onerror=|onload=)", re.I),
    "path_traversal": re.compile(r"(?:\.\./|%2e%2e%2f|/etc/passwd|boot\.ini)", re.I),
    "sensitive_file": re.compile(r"(?:\.env|wp-config\.php|\.git|/phpmyadmin|/wp-admin|/admin)", re.I),
    "command_injection": re.compile(r"(?:;|\||%7c|`|\$\(|\bcat\s+|\bwget\s+|\bcurl\s+)", re.I),
}


def load_settings(config_path: Path | None) -> dict:
    defaults = {
        "model": {"random_state": 42, "test_size": 0.25, "max_iter": 1000, "class_weight": "balanced"},
        "scoring": {"high_risk_threshold": 0.70, "review_threshold": 0.35},
    }
    if config_path is None or not config_path.exists():
        return defaults
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        return defaults
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    return {**defaults, **loaded}


def _clean_column_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    normalized = {_clean_column_name(col): col for col in columns}
    for candidate in candidates:
        match = normalized.get(_clean_column_name(candidate))
        if match is not None:
            return match
    return None


def normalize_csic_dataset(input_path: Path, output_path: Path) -> pd.DataFrame:
    paths: list[Path]
    if input_path.is_dir():
        paths = sorted(input_path.rglob("*.csv"))
    else:
        paths = [input_path]

    frames = []
    for path in paths:
        frame = pd.read_csv(path, encoding="utf-8", encoding_errors="ignore")
        frame.columns = [_clean_column_name(col) for col in frame.columns]
        frame["source_file"] = path.name
        frames.append(frame)

    if not frames:
        raise ValueError(f"No se encontraron archivos CSV en {input_path}")

    raw = pd.concat(frames, ignore_index=True)
    method_col = _find_column(raw.columns, ["method", "request_method"])
    url_col = _find_column(raw.columns, ["url", "request_url", "path"])
    content_col = _find_column(raw.columns, ["content", "payload", "body", "params"])
    user_agent_col = _find_column(raw.columns, ["user_agent", "user-agent"])
    label_col = _find_column(raw.columns, ["classification", "class", "label", "target"])

    if label_col is None:
        raise ValueError("No se encontro columna de etiqueta. Esperaba classification, class, label o target.")

    normalized = pd.DataFrame()
    normalized["method"] = raw[method_col].fillna("GET").astype(str) if method_col else "GET"
    normalized["url"] = raw[url_col].fillna("/").astype(str) if url_col else "/"
    normalized["content"] = raw[content_col].fillna("").astype(str) if content_col else ""
    normalized["user_agent"] = raw[user_agent_col].fillna("").astype(str) if user_agent_col else ""
    normalized["raw_label"] = raw[label_col].fillna("").astype(str)
    normalized["label"] = normalized["raw_label"].str.lower().str.contains("anom|attack|malicious|1|true").astype(int)
    normalized["request_text"] = (
        normalized["method"] + " " + normalized["url"] + " " + normalized["content"] + " " + normalized["user_agent"]
    ).map(lambda value: urllib.parse.unquote_plus(str(value)))
    normalized = add_request_features(normalized)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(output_path, index=False)
    return normalized


def parse_apache_access_log(input_path: Path, output_path: Path) -> pd.DataFrame:
    rows = []
    with input_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            match = APACHE_COMBINED_RE.search(line.strip())
            if not match:
                continue
            item = match.groupdict()
            item["timestamp"] = pd.to_datetime(item["timestamp"], format="%d/%b/%Y:%H:%M:%S %z", errors="coerce")
            item["status_code"] = int(item["status_code"])
            item["bytes_sent"] = 0 if item["bytes_sent"] == "-" else int(item["bytes_sent"])
            item["raw_message"] = line.strip()
            rows.append(item)

    frame = pd.DataFrame(rows)
    if frame.empty:
        frame = pd.DataFrame(
            columns=[
                "timestamp",
                "source_ip",
                "method",
                "url",
                "protocol",
                "status_code",
                "bytes_sent",
                "referer",
                "user_agent",
                "raw_message",
            ]
        )
    else:
        frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        frame["request_text"] = (frame["method"] + " " + frame["url"] + " " + frame["user_agent"].fillna("")).map(
            lambda value: urllib.parse.unquote_plus(str(value))
        )
        frame = add_request_features(frame)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return frame


def parse_apache_error_log(input_path: Path, output_path: Path) -> pd.DataFrame:
    rows = []
    with input_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            raw_line = line.strip()
            if not raw_line:
                continue

            match = APACHE_ERROR_RE.search(raw_line)
            if match:
                item = match.groupdict()
                item["timestamp"] = pd.to_datetime(
                    item["timestamp"],
                    format="%a %b %d %H:%M:%S.%f %Y",
                    errors="coerce",
                )
                client = item.get("client") or ""
                item["source_ip"] = client.split(":")[0] if client else ""
                item["raw_message"] = raw_line
            else:
                item = {
                    "timestamp": pd.NaT,
                    "module": "",
                    "level": "unparsed",
                    "pid": "",
                    "tid": "",
                    "client": "",
                    "source_ip": "",
                    "message": raw_line,
                    "raw_message": raw_line,
                }
            rows.append(item)

    frame = pd.DataFrame(rows)
    if frame.empty:
        frame = pd.DataFrame(
            columns=["timestamp", "module", "level", "pid", "tid", "client", "source_ip", "message", "raw_message"]
        )
    else:
        frame["severity_score"] = frame["level"].map(error_severity_score).fillna(0.2)
        frame["event_label"] = frame["severity_score"].map(
            lambda value: "high_risk" if value >= 0.7 else ("review" if value >= 0.35 else "normal")
        )
        frame = frame.sort_values("timestamp", na_position="last").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return frame


def error_severity_score(level: str) -> float:
    normalized = str(level).lower()
    if normalized in {"emerg", "alert", "crit", "critical"}:
        return 0.95
    if normalized in {"error", "err"}:
        return 0.75
    if normalized in {"warn", "warning"}:
        return 0.45
    if normalized == "unparsed":
        return 0.35
    return 0.15


def add_request_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    text = result.get("request_text", pd.Series("", index=result.index)).fillna("").astype(str)
    url = result.get("url", pd.Series("", index=result.index)).fillna("").astype(str)
    user_agent = result.get("user_agent", pd.Series("", index=result.index)).fillna("").astype(str)

    decoded_text = text.map(lambda value: urllib.parse.unquote_plus(value))
    result["url_length"] = url.str.len()
    result["query_length"] = url.map(lambda value: len(urllib.parse.urlparse(value).query))
    result["special_char_count"] = decoded_text.str.count(r"[^A-Za-z0-9\s/_\.\-\?=&:%]")
    result["digit_count"] = decoded_text.str.count(r"\d")
    result["has_empty_user_agent"] = user_agent.str.strip().eq("").astype(int)
    result["has_automation_user_agent"] = user_agent.str.contains(r"curl|wget|python|sqlmap|nikto|nmap|bot", case=False, na=False).astype(int)

    for name, regex in SUSPICIOUS_PATTERNS.items():
        result[f"has_{name}"] = decoded_text.str.contains(regex).astype(int)

    if "status_code" in result.columns:
        result["is_error_status"] = result["status_code"].astype(str).str.match(r"4\d\d|5\d\d").astype(int)
    else:
        result["is_error_status"] = 0
    return result


def train_classifier(features_path: Path, model_output: Path, metadata_output: Path, config_path: Path | None) -> dict:
    settings = load_settings(config_path)
    model_cfg = settings.get("model", {})
    frame = pd.read_csv(features_path)
    if frame.empty:
        raise ValueError("El dataset normalizado esta vacio.")
    if "label" not in frame.columns:
        raise ValueError("El dataset debe tener una columna label.")

    text_col = "request_text"
    numeric_features = [
        "url_length",
        "query_length",
        "special_char_count",
        "digit_count",
        "has_empty_user_agent",
        "has_automation_user_agent",
        "has_sql_injection",
        "has_xss",
        "has_path_traversal",
        "has_sensitive_file",
        "has_command_injection",
        "is_error_status",
    ]
    for column in numeric_features:
        if column not in frame.columns:
            frame[column] = 0

    # Keep lexical payload signals as the primary supervised input; rule features remain available for explanations.
    x_train, x_test, y_train, y_test = train_test_split(
        frame[text_col].fillna("").astype(str),
        frame["label"].astype(int),
        test_size=float(model_cfg.get("test_size", 0.25)),
        random_state=int(model_cfg.get("random_state", 42)),
        stratify=frame["label"].astype(int),
    )

    model = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=8000)),
            (
                "classifier",
                LogisticRegression(
                    max_iter=int(model_cfg.get("max_iter", 1000)),
                    random_state=int(model_cfg.get("random_state", 42)),
                    class_weight=model_cfg.get("class_weight", "balanced"),
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]

    model_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output)

    scored = frame.copy()
    scored["risk_score"] = model.predict_proba(frame[text_col].fillna("").astype(str))[:, 1]
    scored["prediction_label"] = scored["risk_score"].map(lambda value: risk_label(value, settings))
    scored.to_csv(metadata_output.parent / "scored_events.csv", index=False)

    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    metadata = {
        "model_type": "LogisticRegression + char_wb TF-IDF",
        "sklearn_version": sklearn.__version__,
        "training_rows": int(len(frame)),
        "test_rows": int(len(y_test)),
        "label_distribution": frame["label"].value_counts().sort_index().astype(int).to_dict(),
        "classification_report": report,
        "confusion_matrix": confusion_matrix(y_test, predictions).astype(int).tolist(),
        "mean_test_risk_score": float(np.mean(probabilities)),
    }
    with metadata_output.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    return metadata


def risk_label(score: float, settings: dict) -> str:
    scoring = settings.get("scoring", {})
    if score >= float(scoring.get("high_risk_threshold", 0.70)):
        return "high_risk"
    if score >= float(scoring.get("review_threshold", 0.35)):
        return "review"
    return "normal"


def score_apache_events(input_path: Path, model_path: Path, output_path: Path, config_path: Path | None) -> pd.DataFrame:
    settings = load_settings(config_path)
    frame = pd.read_csv(input_path)
    if frame.empty:
        frame["risk_score"] = []
        frame["prediction_label"] = []
    else:
        model = joblib.load(model_path)
        text = frame["request_text"].fillna("").astype(str)
        frame["ml_risk_score"] = model.predict_proba(text)[:, 1]
        frame["heuristic_risk_score"] = frame.apply(heuristic_score, axis=1)
        frame["risk_score"] = frame[["ml_risk_score", "heuristic_risk_score"]].max(axis=1)
        frame["prediction_label"] = frame["risk_score"].map(lambda value: risk_label(value, settings))
        frame["reasons"] = frame.apply(explain_event, axis=1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return frame


def heuristic_score(row: pd.Series) -> float:
    score = 0.0
    weighted_flags = {
        "has_sql_injection": 0.85,
        "has_xss": 0.80,
        "has_path_traversal": 0.80,
        "has_command_injection": 0.90,
        "has_sensitive_file": 0.65,
        "has_automation_user_agent": 0.45,
        "is_error_status": 0.25,
    }
    for feature, weight in weighted_flags.items():
        if int(row.get(feature, 0) or 0) == 1:
            score = max(score, weight)
    return score


def explain_event(row: pd.Series) -> str:
    reasons = []
    for feature, label in (
        ("has_sql_injection", "patron SQLi"),
        ("has_xss", "patron XSS"),
        ("has_path_traversal", "path traversal"),
        ("has_sensitive_file", "ruta sensible"),
        ("has_command_injection", "command injection"),
        ("has_automation_user_agent", "user-agent automatizado"),
        ("is_error_status", "respuesta HTTP de error"),
    ):
        if int(row.get(feature, 0) or 0) == 1:
            reasons.append(label)
    return ", ".join(reasons) if reasons else "score ML elevado"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pipeline ML para deteccion de accesos web sospechosos.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    normalize = subparsers.add_parser("normalize-csic")
    normalize.add_argument("--input", required=True, type=Path)
    normalize.add_argument("--output", required=True, type=Path)

    parse = subparsers.add_parser("parse-access")
    parse.add_argument("--input", required=True, type=Path)
    parse.add_argument("--output", required=True, type=Path)

    parse_error = subparsers.add_parser("parse-error")
    parse_error.add_argument("--input", required=True, type=Path)
    parse_error.add_argument("--output", required=True, type=Path)

    train = subparsers.add_parser("train")
    train.add_argument("--input", required=True, type=Path)
    train.add_argument("--model-output", required=True, type=Path)
    train.add_argument("--metadata-output", required=True, type=Path)
    train.add_argument("--config", type=Path, default=Path("config/settings.yaml"))

    score = subparsers.add_parser("score-access")
    score.add_argument("--input", required=True, type=Path)
    score.add_argument("--model", required=True, type=Path)
    score.add_argument("--output", required=True, type=Path)
    score.add_argument("--config", type=Path, default=Path("config/settings.yaml"))
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    if args.command == "normalize-csic":
        normalize_csic_dataset(args.input, args.output)
    elif args.command == "parse-access":
        parse_apache_access_log(args.input, args.output)
    elif args.command == "parse-error":
        parse_apache_error_log(args.input, args.output)
    elif args.command == "train":
        train_classifier(args.input, args.model_output, args.metadata_output, args.config)
    elif args.command == "score-access":
        score_apache_events(args.input, args.model, args.output, args.config)


if __name__ == "__main__":
    main()
