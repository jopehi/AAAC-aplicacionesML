from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ssh_pipeline import build_feature_frame, load_settings, parse_ssh_log, train_baseline_model


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Valida que el pipeline baseline siga funcionando.")
    parser.add_argument("--config", type=Path, default=Path("config/settings.yaml"))
    parser.add_argument("--input-log", type=Path, default=Path("data/raw/sample_auth.log"))
    parser.add_argument("--events-output", type=Path, default=Path("data/processed/baseline_validation_events.csv"))
    parser.add_argument("--features-output", type=Path, default=Path("data/processed/baseline_validation_features.csv"))
    parser.add_argument("--model-output", type=Path, default=Path("models/baseline_validation_model.joblib"))
    parser.add_argument("--metadata-output", type=Path, default=Path("models/baseline_validation_metadata.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("models/baseline_validation_summary.json"))
    parser.add_argument("--year", type=int, default=2026)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    settings = load_settings(args.config)
    windows = settings.get("features", {}).get("windows_minutes", [1, 5, 15])
    model_cfg = settings.get("model", {})

    events = parse_ssh_log(args.input_log, args.events_output, args.year)
    features = build_feature_frame(args.events_output, args.features_output, windows)
    metadata = train_baseline_model(
        args.features_output,
        args.model_output,
        args.metadata_output,
        contamination=float(model_cfg.get("contamination", 0.08)),
        random_state=int(model_cfg.get("random_state", 42)),
    )

    summary = {
        "status": "ok",
        "input_log": str(args.input_log),
        "parsed_events": int(len(events)),
        "feature_rows": int(len(features)),
        "model_type": metadata["model_type"],
        "high_risk_count": int(metadata["high_risk_count"]),
        "note": "La validacion usa archivos separados para no alterar los artefactos principales del baseline.",
    }

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    with args.summary_output.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
