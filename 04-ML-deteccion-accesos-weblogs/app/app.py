from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
SCORED_EVENTS = BASE_DIR / "models" / "scored_events.csv"
ACCESS_SCORED = BASE_DIR / "data" / "processed" / "access_scored.csv"
ERROR_EVENTS = BASE_DIR / "data" / "processed" / "error_events.csv"
METADATA = BASE_DIR / "models" / "model_metadata.json"

TABLE_COLUMNS = [
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
    "user_agent",
    "raw_label",
    "request_text",
    "raw_message",
]


def load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    for column in ("risk_score", "ml_risk_score", "heuristic_risk_score", "severity_score", "status_code"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    if "url" in frame.columns:
        frame["route_path"] = frame["url"].fillna("").astype(str).map(extract_route_path)
    return frame


def extract_route_path(value: str) -> str:
    parsed = urlparse(value)
    return parsed.path or value.split("?")[0] or "/"


def load_metadata() -> dict:
    if not METADATA.exists():
        return {}
    with METADATA.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def label_column(frame: pd.DataFrame) -> str | None:
    if "prediction_label" in frame.columns:
        return "prediction_label"
    if "event_label" in frame.columns:
        return "event_label"
    return None


def score_column(frame: pd.DataFrame) -> str | None:
    if "risk_score" in frame.columns:
        return "risk_score"
    if "severity_score" in frame.columns:
        return "severity_score"
    return None


def render_metrics(frame: pd.DataFrame) -> None:
    total = len(frame)
    label_col = label_column(frame)
    score_col = score_column(frame)

    high_risk = int((frame[label_col] == "high_risk").sum()) if total and label_col else 0
    review = int((frame[label_col] == "review").sum()) if total and label_col else 0
    mean_score = float(frame[score_col].mean()) if total and score_col else 0.0
    unique_ips = int(frame["source_ip"].replace("", pd.NA).dropna().nunique()) if "source_ip" in frame.columns else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Eventos", total)
    col2.metric("Alto riesgo", high_risk)
    col3.metric("Revision", review)
    col4.metric("IPs origen", unique_ips)
    col5.metric("Score medio", f"{mean_score:.3f}")


def apply_sidebar_filters(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame.copy()
    label_col = label_column(filtered)

    st.sidebar.header("Filtros")
    if label_col:
        labels = sorted(filtered[label_col].dropna().astype(str).unique())
        selected = st.sidebar.multiselect("Etiqueta", labels, default=labels)
        if selected:
            filtered = filtered[filtered[label_col].astype(str).isin(selected)]

    if "source_ip" in filtered.columns:
        ips = sorted(ip for ip in filtered["source_ip"].dropna().astype(str).unique() if ip)
        selected_ips = st.sidebar.multiselect("IP origen", ips)
        if selected_ips:
            filtered = filtered[filtered["source_ip"].astype(str).isin(selected_ips)]

    if "method" in filtered.columns:
        methods = sorted(filtered["method"].dropna().astype(str).unique())
        selected_methods = st.sidebar.multiselect("Metodo HTTP", methods, default=methods)
        if selected_methods:
            filtered = filtered[filtered["method"].astype(str).isin(selected_methods)]

    if "status_code" in filtered.columns:
        status_codes = sorted(filtered["status_code"].dropna().astype(int).unique().tolist())
        selected_status = st.sidebar.multiselect("Status code", status_codes)
        if selected_status:
            filtered = filtered[filtered["status_code"].isin(selected_status)]

    if "reasons" in filtered.columns:
        reason_values = sorted(
            {
                reason.strip()
                for value in filtered["reasons"].dropna().astype(str)
                for reason in value.split(",")
                if reason.strip()
            }
        )
        selected_reasons = st.sidebar.multiselect("Razon", reason_values)
        if selected_reasons:
            pattern = "|".join(selected_reasons)
            filtered = filtered[filtered["reasons"].fillna("").str.contains(pattern, case=False, regex=True)]

    if "timestamp" in filtered.columns and filtered["timestamp"].notna().any():
        min_date = filtered["timestamp"].min().date()
        max_date = filtered["timestamp"].max().date()
        selected_range = st.sidebar.date_input("Rango de fechas", value=(min_date, max_date))
        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start, end = selected_range
            start_ts = pd.Timestamp(start)
            end_ts = pd.Timestamp(end) + pd.Timedelta(days=1)
            timestamps = filtered["timestamp"].dt.tz_localize(None)
            filtered = filtered[(timestamps >= start_ts) & (timestamps < end_ts)]

    search = st.sidebar.text_input("Buscar en URL/mensaje")
    if search:
        searchable_cols = [col for col in ("url", "message", "raw_message", "request_text", "user_agent") if col in filtered.columns]
        if searchable_cols:
            mask = pd.Series(False, index=filtered.index)
            for col in searchable_cols:
                mask = mask | filtered[col].fillna("").astype(str).str.contains(search, case=False, regex=False)
            filtered = filtered[mask]

    return filtered


def render_charts(frame: pd.DataFrame) -> None:
    label_col = label_column(frame)
    score_col = score_column(frame)
    left, right = st.columns(2)

    with left:
        if label_col:
            counts = frame[label_col].value_counts().rename_axis("etiqueta").reset_index(name="eventos")
            st.subheader("Eventos por etiqueta")
            st.bar_chart(counts, x="etiqueta", y="eventos")

    with right:
        if "status_code" in frame.columns:
            status = frame["status_code"].dropna().astype(int).value_counts().sort_index().rename_axis("status").reset_index(name="eventos")
            st.subheader("Status codes")
            st.bar_chart(status, x="status", y="eventos")
        elif "level" in frame.columns:
            levels = frame["level"].fillna("unknown").value_counts().rename_axis("level").reset_index(name="eventos")
            st.subheader("Niveles error.log")
            st.bar_chart(levels, x="level", y="eventos")

    left, right = st.columns(2)
    with left:
        if "source_ip" in frame.columns and score_col:
            top_ips = (
                frame.assign(source_ip=frame["source_ip"].replace("", pd.NA))
                .dropna(subset=["source_ip"])
                .groupby("source_ip")
                .agg(eventos=(score_col, "size"), score_maximo=(score_col, "max"))
                .sort_values(["score_maximo", "eventos"], ascending=False)
                .head(10)
                .reset_index()
            )
            st.subheader("Top IPs sospechosas")
            st.dataframe(top_ips, width="stretch", height=280)

    with right:
        if "route_path" in frame.columns and score_col:
            top_routes = (
                frame.groupby("route_path")
                .agg(eventos=(score_col, "size"), score_maximo=(score_col, "max"))
                .sort_values(["score_maximo", "eventos"], ascending=False)
                .head(10)
                .reset_index()
            )
            st.subheader("Top rutas")
            st.dataframe(top_routes, width="stretch", height=280)

    if "timestamp" in frame.columns and frame["timestamp"].notna().any() and label_col:
        timeline = (
            frame.dropna(subset=["timestamp"])
            .assign(hora=lambda item: item["timestamp"].dt.floor("h"))
            .groupby(["hora", label_col])
            .size()
            .reset_index(name="eventos")
            .pivot(index="hora", columns=label_col, values="eventos")
            .fillna(0)
        )
        st.subheader("Eventos por hora")
        st.line_chart(timeline)


def render_event_detail(frame: pd.DataFrame) -> None:
    if frame.empty:
        return

    score_col = score_column(frame)
    ordered = frame.sort_values(score_col, ascending=False) if score_col else frame
    options = ordered.head(200).index.tolist()

    def format_event(index: int) -> str:
        row = ordered.loc[index]
        score = row.get(score_col, 0.0) if score_col else 0.0
        label = row.get(label_column(ordered) or "", "n/a")
        target = row.get("url") or row.get("message") or row.get("raw_message") or ""
        return f"#{index} | {label} | {float(score):.3f} | {str(target)[:90]}"

    st.subheader("Detalle de evento")
    selected_index = st.selectbox("Evento", options, format_func=format_event)
    row = ordered.loc[selected_index]

    c1, c2, c3 = st.columns(3)
    if score_col:
        c1.metric("Score final", f"{float(row.get(score_col, 0.0)):.3f}")
    if "ml_risk_score" in row:
        c2.metric("Score ML", f"{float(row.get('ml_risk_score', 0.0)):.3f}")
    if "heuristic_risk_score" in row:
        c3.metric("Score reglas", f"{float(row.get('heuristic_risk_score', 0.0)):.3f}")

    detail_cols = [col for col in TABLE_COLUMNS if col in row.index and pd.notna(row[col])]
    st.json({col: str(row[col]) for col in detail_cols})


def render_export(frame: pd.DataFrame) -> None:
    csv_data = frame.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar vista filtrada CSV",
        data=csv_data,
        file_name="weblog_alertas_filtradas.csv",
        mime="text/csv",
    )


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

    filtered = apply_sidebar_filters(frame)
    render_metrics(filtered)

    tabs = st.tabs(["Resumen", "Eventos", "Detalle", "Modelo"])
    with tabs[0]:
        render_charts(filtered)

    with tabs[1]:
        if filtered.empty:
            st.warning("No hay eventos con los filtros actuales.")
        else:
            score_col = score_column(filtered)
            sorted_frame = filtered.sort_values(score_col, ascending=False) if score_col else filtered
            columns = [col for col in TABLE_COLUMNS if col in sorted_frame.columns]
            st.dataframe(sorted_frame[columns].head(1000), width="stretch", height=560)
            render_export(sorted_frame[columns])

    with tabs[2]:
        if filtered.empty:
            st.warning("No hay eventos para detallar.")
        else:
            render_event_detail(filtered)

    with tabs[3]:
        if metadata.get("classification_report"):
            st.json(metadata["classification_report"])
        else:
            st.info("No hay metadata del modelo disponible.")


if __name__ == "__main__":
    main()
