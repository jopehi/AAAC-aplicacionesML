from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
SCORED_EVENTS = BASE_DIR / "models" / "scored_events.csv"
ACCESS_SCORED = BASE_DIR / "data" / "processed" / "access_scored.csv"
ERROR_EVENTS = BASE_DIR / "data" / "processed" / "error_events.csv"
METADATA = BASE_DIR / "models" / "model_metadata.json"


def load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_metadata() -> dict:
    if not METADATA.exists():
        return {}
    with METADATA.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_metrics(frame: pd.DataFrame) -> None:
    total = len(frame)
    label_col = "prediction_label" if "prediction_label" in frame.columns else "event_label"
    score_col = "risk_score" if "risk_score" in frame.columns else "severity_score"

    if total and label_col in frame.columns:
        high_risk = int((frame[label_col] == "high_risk").sum())
        review = int((frame[label_col] == "review").sum())
    else:
        high_risk = 0
        review = 0

    mean_score = float(frame[score_col].mean()) if total and score_col in frame.columns else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Eventos", total)
    col2.metric("Alto riesgo", high_risk)
    col3.metric("Revision", review)
    col4.metric("Score medio", f"{mean_score:.3f}")


def main() -> None:
    st.set_page_config(page_title="Weblogs ML", layout="wide")
    st.title("Deteccion ML de accesos web sospechosos")

    metadata = load_metadata()
    if metadata:
        st.caption(
            f"Modelo: {metadata.get('model_type', 'n/a')} | "
            f"filas entrenamiento: {metadata.get('training_rows', 'n/a')} | "
            f"scikit-learn: {metadata.get('sklearn_version', 'n/a')}"
        )

    source = st.radio(
        "Fuente",
        ["Access log Apache", "Error log Apache", "Dataset CSIC puntuado"],
        horizontal=True,
    )
    if source == "Access log Apache":
        frame = load_frame(ACCESS_SCORED)
    elif source == "Error log Apache":
        frame = load_frame(ERROR_EVENTS)
    else:
        frame = load_frame(SCORED_EVENTS)

    if frame.empty:
        st.info("Todavia no hay resultados. Ejecuta el flujo de normalizacion, entrenamiento y scoring.")
        return

    render_metrics(frame)

    label_col = "prediction_label" if "prediction_label" in frame.columns else "event_label"
    labels = sorted(frame[label_col].dropna().unique()) if label_col in frame.columns else []
    selected = st.multiselect("Filtrar por etiqueta", labels, default=labels)
    filtered = frame[frame[label_col].isin(selected)] if selected and label_col in frame.columns else frame

    if "risk_score" in filtered.columns:
        filtered = filtered.sort_values("risk_score", ascending=False)
    elif "severity_score" in filtered.columns:
        filtered = filtered.sort_values("severity_score", ascending=False)

    columns = [
        col
        for col in [
            "timestamp",
            "source_ip",
            "method",
            "url",
            "status_code",
            "risk_score",
            "ml_risk_score",
            "heuristic_risk_score",
            "prediction_label",
            "level",
            "severity_score",
            "event_label",
            "module",
            "message",
            "reasons",
            "raw_label",
            "request_text",
            "raw_message",
        ]
        if col in filtered.columns
    ]
    st.dataframe(filtered[columns].head(500), width="stretch", height=520)

    if metadata.get("classification_report"):
        with st.expander("Metricas del entrenamiento"):
            st.json(metadata["classification_report"])


if __name__ == "__main__":
    main()
