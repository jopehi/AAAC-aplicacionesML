from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.web_log_pipeline import (
    load_settings,
    parse_apache_access_log,
    parse_apache_error_log,
    score_apache_events,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Actualiza resultados ML usando logs actuales de Apache.")
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config" / "settings.yaml")
    parser.add_argument("--access-log", type=Path, default=None)
    parser.add_argument("--error-log", type=Path, default=None)
    parser.add_argument("--access-events-output", type=Path, default=PROJECT_ROOT / "data" / "processed" / "access_events.csv")
    parser.add_argument("--error-events-output", type=Path, default=PROJECT_ROOT / "data" / "processed" / "error_events.csv")
    parser.add_argument("--model", type=Path, default=PROJECT_ROOT / "models" / "web_attack_model.joblib")
    parser.add_argument("--scored-output", type=Path, default=PROJECT_ROOT / "data" / "processed" / "access_scored.csv")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    settings = load_settings(args.config)
    apache_settings = settings.get("apache", {})

    access_log = args.access_log or resolve_project_path(apache_settings.get("access_log", "/var/log/apache2/access.log"))
    error_log = args.error_log or resolve_project_path(apache_settings.get("error_log", "/var/log/apache2/error.log"))

    for required_path, description in (
        (access_log, "access log"),
        (error_log, "error log"),
        (args.model, "trained model"),
    ):
        if not required_path.exists():
            raise FileNotFoundError(f"No existe {description}: {required_path}")

    access_events = parse_apache_access_log(access_log, args.access_events_output)
    error_events = parse_apache_error_log(error_log, args.error_events_output)
    scored_events = score_apache_events(args.access_events_output, args.model, args.scored_output, args.config)

    summary = {
        "access_log": str(access_log),
        "error_log": str(error_log),
        "access_events": int(len(access_events)),
        "error_events": int(len(error_events)),
        "scored_events": int(len(scored_events)),
        "high_risk_access_events": int((scored_events.get("prediction_label", "") == "high_risk").sum()),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
