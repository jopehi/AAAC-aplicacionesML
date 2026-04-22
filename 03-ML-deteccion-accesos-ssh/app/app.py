from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
SCORED_PATH = BASE_DIR / "models" / "scored_events.csv"
SQLITE_PATH = BASE_DIR / "data" / "processed" / "ssh_monitor.db"
SETTINGS_PATH = BASE_DIR / "config" / "settings.yaml"
MODEL_METADATA_PATH = BASE_DIR / "models" / "model_metadata.json"
RETRAIN_SUMMARY_PATH = BASE_DIR / "models" / "retrain_summary.json"


def load_thresholds() -> dict:
    if not SETTINGS_PATH.exists():
        return {
            "high_failure_threshold_5m": 8,
            "distinct_users_threshold_5m": 4,
            "successful_after_failures_threshold_5m": 5,
            "risk_score_threshold": 0.1,
        }

    with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    realtime = data.get("realtime", {})
    return {
        "high_failure_threshold_5m": int(realtime.get("high_failure_threshold_5m", 8)),
        "distinct_users_threshold_5m": int(realtime.get("distinct_users_threshold_5m", 4)),
        "successful_after_failures_threshold_5m": int(realtime.get("successful_after_failures_threshold_5m", 5)),
        "risk_score_threshold": float(realtime.get("risk_score_threshold", 0.1)),
    }


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --shell-bg: linear-gradient(135deg, #08111f 0%, #10233d 55%, #17314e 100%);
            --shell-border: rgba(135, 180, 255, 0.18);
            --shell-text: #f5f8ff;
            --shell-copy: #d7e5ff;
            --soft-card-bg: linear-gradient(180deg, rgba(17, 29, 46, 0.96) 0%, rgba(10, 20, 34, 0.98) 100%);
            --soft-card-border: rgba(140, 180, 230, 0.14);
            --soft-card-text: #e7eefb;
            --muted-text: #a9bdd9;
            --accent: #8ec5ff;
            --danger-bg: linear-gradient(135deg, #4b0d14 0%, #7b1220 48%, #a61b2d 100%);
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        .app-shell {
            background: var(--shell-bg);
            border: 1px solid var(--shell-border);
            border-radius: 20px;
            padding: 1.25rem 1.25rem 0.85rem 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
        }
        .app-kicker {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: var(--accent);
            font-size: 0.78rem;
            margin-bottom: 0.45rem;
        }
        .app-title {
            font-size: 2rem;
            font-weight: 700;
            color: var(--shell-text);
            margin-bottom: 0.35rem;
        }
        .app-copy {
            color: var(--shell-copy);
            font-size: 0.98rem;
            line-height: 1.5;
            max-width: 68rem;
        }
        .badge-row {
            display: flex;
            gap: 0.65rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }
        .badge {
            padding: 0.5rem 0.8rem;
            border-radius: 999px;
            font-size: 0.84rem;
            border: 1px solid rgba(255,255,255,0.15);
            color: #eff6ff;
            background: rgba(255,255,255,0.08);
        }
        .panel-card {
            border-radius: 18px;
            padding: 1rem 1rem 0.85rem 1rem;
            border: 1px solid var(--soft-card-border);
            background: var(--soft-card-bg);
            color: var(--soft-card-text);
            margin-bottom: 1rem;
        }
        .risk-banner {
            border-radius: 18px;
            padding: 1rem 1rem 0.85rem 1rem;
            background: var(--danger-bg);
            color: white;
            margin-bottom: 1rem;
            border: 1px solid rgba(255,255,255,0.14);
        }
        .risk-banner h3 {
            margin: 0 0 0.3rem 0;
            color: #fff4f4;
        }
        .risk-banner p {
            margin: 0;
            color: #ffe0e0;
        }
        .info-card {
            border-radius: 18px;
            padding: 1rem 1rem 0.85rem 1rem;
            background: var(--soft-card-bg);
            border: 1px solid var(--soft-card-border);
            color: var(--soft-card-text);
            margin-bottom: 1rem;
        }
        .info-card strong {
            color: #ffffff;
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--soft-card-border);
            border-radius: 18px;
            background: rgba(8, 17, 31, 0.48);
            overflow: hidden;
        }
        [data-testid="stExpander"] details summary {
            background: rgba(10, 20, 34, 0.92);
            color: var(--shell-text);
            border-bottom: 1px solid rgba(140, 180, 230, 0.12);
        }
        [data-testid="stExpander"] details > div {
            background: rgba(9, 18, 31, 0.96);
            color: var(--soft-card-text);
        }
        [data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(140, 180, 230, 0.10);
        }
        [data-testid="stMetric"] {
            background: rgba(12, 23, 39, 0.82);
            border: 1px solid rgba(140, 180, 230, 0.12);
            padding: 0.6rem 0.8rem;
            border-radius: 16px;
        }
        [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
            color: var(--shell-text);
        }
        .stMarkdown, .stText, p, li, label {
            color: var(--soft-card-text);
        }
        code {
            color: #d8ecff;
            background: rgba(110, 180, 255, 0.10);
            border-radius: 8px;
            padding: 0.12rem 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(mode: str, thresholds: dict) -> None:
    st.markdown(
        f"""
        <div class="app-shell">
            <div class="app-kicker">SSH Abuse Detection Console</div>
            <div class="app-title">Deteccion de accesos SSH anomalos</div>
            <div class="app-copy">
                Panel orientado a triage operativo. Prioriza candidatos a bloqueo por abuso,
                actividad repetitiva y alertas que combinan reglas con modelo baseline.
            </div>
            <div class="badge-row">
                <div class="badge">Modo: {mode}</div>
                <div class="badge">Umbral fallos 5m: {thresholds['high_failure_threshold_5m']}</div>
                <div class="badge">Usuarios distintos/IP 5m: {thresholds['distinct_users_threshold_5m']}</div>
                <div class="badge">Risk score: {thresholds['risk_score_threshold']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_rule_hits(value: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, float) and pd.isna(value):
        return []
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def load_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def classify_block_status(rule_hits: list[str], prediction_label: str) -> str:
    high_abuse_hits = {"high_failures_5m", "many_users_per_ip_5m", "success_after_failures"}
    hits = set(rule_hits)
    if len(hits & high_abuse_hits) >= 2:
        return "candidate_block"
    if "ml_high_risk" in hits and len(hits & high_abuse_hits) >= 1:
        return "candidate_block"
    if "risk_score_threshold" in hits or "ml_high_risk" in hits:
        return "review"
    if prediction_label == "high_risk":
        return "review"
    return "observe"


def status_label(status: str) -> str:
    return {
        "candidate_block": "Candidato a bloqueo",
        "review": "Revisar",
        "observe": "Observar",
    }.get(status, status)


def prepare_alerts(alerts: pd.DataFrame) -> pd.DataFrame:
    if alerts.empty:
        return alerts

    prepared = alerts.copy()
    prepared["rule_hits_list"] = prepared["rule_hits"].apply(parse_rule_hits)
    prepared["rule_count"] = prepared["rule_hits_list"].apply(lambda values: len(values) if isinstance(values, list) else 0)
    prepared["block_status"] = prepared.apply(
        lambda row: classify_block_status(row["rule_hits_list"], row["prediction_label"]),
        axis=1,
    )
    prepared["block_label"] = prepared["block_status"].apply(status_label)
    prepared["severity"] = prepared["block_status"].map(
        {"candidate_block": 3, "review": 2, "observe": 1}
    ).fillna(1)
    prepared["rule_hits_display"] = prepared["rule_hits_list"].apply(
        lambda values: ", ".join(values) if values else "sin reglas"
    )
    return prepared


def prepare_baseline(frame: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    prepared = frame.copy()
    prepared["rule_hits_list"] = prepared.apply(
        lambda row: [
            hit
            for hit, condition in (
                ("high_failures_5m", row.get("failed_count_5m", 0) >= thresholds["high_failure_threshold_5m"]),
                (
                    "many_users_per_ip_5m",
                    row.get("user_count_per_ip_5m", 0) >= thresholds["distinct_users_threshold_5m"],
                ),
                ("risk_score_threshold", row.get("risk_score", 0.0) >= thresholds["risk_score_threshold"]),
                ("ml_high_risk", row.get("prediction_label", "normal") == "high_risk"),
            )
            if condition
        ],
        axis=1,
    )
    prepared["rule_count"] = prepared["rule_hits_list"].apply(lambda values: len(values) if isinstance(values, list) else 0)
    prepared["block_status"] = prepared.apply(
        lambda row: classify_block_status(row["rule_hits_list"], row["prediction_label"]),
        axis=1,
    )
    prepared["block_label"] = prepared["block_status"].apply(status_label)
    prepared["severity"] = prepared["block_status"].map(
        {"candidate_block": 3, "review": 2, "observe": 1}
    ).fillna(1)
    prepared["rule_hits_display"] = prepared["rule_hits_list"].apply(
        lambda values: ", ".join(values) if values else "sin reglas"
    )
    return prepared


def render_priority_banner(candidates: pd.DataFrame) -> None:
    if candidates.empty:
        st.markdown(
            """
            <div class="panel-card">
                <strong>Estado actual:</strong> no hay registros marcados como candidato a bloqueo.
                El panel sigue mostrando alertas y eventos para revision.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    top_ip = candidates["source_ip"].mode().iloc[0] if not candidates["source_ip"].dropna().empty else "desconocida"
    st.markdown(
        f"""
        <div class="risk-banner">
            <h3>Prioridad operativa</h3>
            <p>
                Hay <strong>{len(candidates)}</strong> registros marcados como <strong>candidato a bloqueo</strong>.
                La IP con mayor presencia en ese grupo es <strong>{top_ip}</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(total_events: int, failures: int, successes: int, alerts_count: int, candidate_count: int) -> None:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Eventos", total_events)
    col2.metric("Fallos", failures)
    col3.metric("Exitos", successes)
    col4.metric("Alertas", alerts_count)
    col5.metric("Candidatos bloqueo", candidate_count)


def render_model_context(thresholds: dict, live_events: int) -> None:
    metadata = load_json_file(MODEL_METADATA_PATH)
    retrain_summary = load_json_file(RETRAIN_SUMMARY_PATH)

    with st.expander("Modelo, tecnica y contexto de evaluacion", expanded=False):
        st.markdown(
            """
            <div class="info-card">
                <strong>Tecnica principal:</strong> Isolation Forest como baseline de deteccion de anomalias.<br>
                <strong>Enfoque operativo:</strong> reglas hibridas + score del modelo.<br>
                <strong>Uso esperado:</strong> priorizar revision y posible bloqueo por abuso, no confirmar un ataque por si solo.
            </div>
            """,
            unsafe_allow_html=True,
        )

        left, middle, right = st.columns(3)
        left.metric("Modelo", metadata.get("model_type", "No disponible"))
        middle.metric("Filas entrenamiento", int(metadata.get("training_rows", 0) or 0))
        right.metric("High risk entrenamiento", int(metadata.get("high_risk_count", 0) or 0))

        st.subheader("Parametros del modelo")
        params = pd.DataFrame(
            [
                {"parametro": "contamination", "valor": metadata.get("contamination", "n/d")},
                {"parametro": "random_state", "valor": metadata.get("random_state", "n/d")},
                {"parametro": "scikit-learn", "valor": metadata.get("sklearn_version", "n/d")},
                {"parametro": "fallos 5m", "valor": thresholds["high_failure_threshold_5m"]},
                {"parametro": "usuarios distintos/IP 5m", "valor": thresholds["distinct_users_threshold_5m"]},
                {"parametro": "risk_score_threshold", "valor": thresholds["risk_score_threshold"]},
            ]
        )
        st.dataframe(params, use_container_width=True, hide_index=True)

        st.subheader("Features usadas por el modelo")
        feature_columns = metadata.get("feature_columns", [])
        if feature_columns:
            st.code(", ".join(feature_columns))
        else:
            st.info("Todavia no hay metadata de features disponible.")

        st.subheader("Lectura rapida del entrenamiento")
        if metadata:
            training_rows = int(metadata.get("training_rows", 0) or 0)
            high_risk_count = int(metadata.get("high_risk_count", 0) or 0)
            ratio = round((high_risk_count / training_rows) * 100, 2) if training_rows else 0.0
            st.write(
                f"El baseline se entreno con **{training_rows}** registros y marco **{high_risk_count}** "
                f"como `high_risk` durante ese entrenamiento ({ratio}%)."
            )
        else:
            st.info("No existe metadata del entrenamiento actual.")

        st.subheader("Ultimo reentrenamiento conocido")
        if retrain_summary:
            retrain_rows = pd.DataFrame(
                [
                    {"dato": "input_log", "valor": retrain_summary.get("input_log", "n/d")},
                    {"dato": "parsed_events", "valor": retrain_summary.get("parsed_events", "n/d")},
                    {"dato": "feature_rows", "valor": retrain_summary.get("feature_rows", "n/d")},
                    {"dato": "eventos visibles ahora", "valor": live_events},
                ]
            )
            st.dataframe(retrain_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No hay resumen de reentrenamiento disponible todavia.")

        st.subheader("Como leer este panel")
        st.markdown(
            """
            - `Candidato a bloqueo`: combinacion fuerte de reglas de abuso y/o apoyo del modelo.
            - `Revisar`: anomalia o riesgo suficiente para analisis manual, pero no bloqueo inmediato.
            - `Observar`: evento visible sin evidencia suficiente para accion dura.
            - `risk_score`: medida de rareza operativa; no equivale por si sola a incidente confirmado.
            """
        )


def build_ip_summary(alerts: pd.DataFrame) -> pd.DataFrame:
    if alerts.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for source_ip, group in alerts.groupby("source_ip", dropna=False):
        rows.append(
            {
                "source_ip": source_ip,
                "alert_count": int(len(group)),
                "candidate_block_count": int((group["block_status"] == "candidate_block").sum()),
                "high_risk_count": int((group["prediction_label"] == "high_risk").sum()),
                "max_risk_score": round(float(group["risk_score"].max()), 4) if "risk_score" in group else 0.0,
                "top_users": ", ".join(group["username"].fillna("desconocido").astype(str).value_counts().head(3).index),
                "last_seen": group["created_at"].max() if "created_at" in group else pd.NaT,
            }
        )

    summary = pd.DataFrame(rows).sort_values(
        ["candidate_block_count", "alert_count", "max_risk_score"],
        ascending=[False, False, False],
    )
    return summary


def render_sidebar_filters(alerts: pd.DataFrame) -> tuple[str, str, str]:
    st.sidebar.header("Filtros operativos")
    status_options = ["Todos", "candidate_block", "review", "observe"]
    selected_status = st.sidebar.selectbox("Estado de respuesta", status_options, format_func=lambda v: "Todos" if v == "Todos" else status_label(v))
    ip_options = ["Todas"] + sorted(alerts["source_ip"].dropna().astype(str).unique().tolist()) if not alerts.empty else ["Todas"]
    selected_ip = st.sidebar.selectbox("IP origen", ip_options)
    user_options = ["Todos"] + sorted(alerts["username"].dropna().astype(str).unique().tolist()) if not alerts.empty else ["Todos"]
    selected_user = st.sidebar.selectbox("Usuario", user_options)
    return selected_status, selected_ip, selected_user


def filter_alerts(alerts: pd.DataFrame, selected_status: str, selected_ip: str, selected_user: str) -> pd.DataFrame:
    filtered = alerts.copy()
    if selected_status != "Todos":
        filtered = filtered[filtered["block_status"] == selected_status]
    if selected_ip != "Todas":
        filtered = filtered[filtered["source_ip"].astype(str) == selected_ip]
    if selected_user != "Todos":
        filtered = filtered[filtered["username"].astype(str) == selected_user]
    return filtered


def render_sqlite_mode(thresholds: dict) -> None:
    conn = sqlite3.connect(SQLITE_PATH)
    alerts = pd.read_sql_query(
        """
        SELECT created_at, source_ip, username, ssh_event_type, auth_result,
               risk_score, prediction_label, reason_summary, rule_hits, raw_message
        FROM ssh_alerts
        ORDER BY id DESC
        LIMIT 500
        """,
        conn,
        parse_dates=["created_at"],
    )
    events = pd.read_sql_query(
        """
        SELECT timestamp, source_ip, username, ssh_event_type, auth_result, raw_message
        FROM ssh_events
        ORDER BY id DESC
        LIMIT 1000
        """,
        conn,
        parse_dates=["timestamp"],
    )
    conn.close()

    if alerts.empty and events.empty:
        st.info("La base SQLite existe pero aun no tiene eventos o alertas.")
        st.stop()

    alerts = prepare_alerts(alerts)
    candidates = alerts[alerts["block_status"] == "candidate_block"] if not alerts.empty else pd.DataFrame()
    render_header("Monitoreo continuo con SQLite", thresholds)
    render_priority_banner(candidates)

    total_events = len(events)
    failures = int((events["auth_result"] == "failure").sum()) if not events.empty else 0
    successes = int((events["auth_result"] == "success").sum()) if not events.empty else 0
    render_metrics(total_events, failures, successes, len(alerts), len(candidates))
    render_model_context(thresholds, total_events)

    selected_status, selected_ip, selected_user = render_sidebar_filters(alerts)
    filtered_alerts = filter_alerts(alerts, selected_status, selected_ip, selected_user)

    st.subheader("IPs con mayor prioridad operativa")
    ip_summary = build_ip_summary(alerts)
    if not ip_summary.empty:
        st.dataframe(ip_summary.head(15), use_container_width=True)
    else:
        st.info("Todavia no hay alertas persistidas.")

    st.subheader("Registros con criterio de posible bloqueo")
    if not candidates.empty:
        st.dataframe(
            candidates[
                [
                    "created_at",
                    "source_ip",
                    "username",
                    "ssh_event_type",
                    "risk_score",
                    "prediction_label",
                    "rule_hits_display",
                    "reason_summary",
                ]
            ].sort_values(["created_at", "risk_score"], ascending=[False, False]),
            use_container_width=True,
        )
    else:
        st.info("Todavia no hay registros que cumplan criterio de posible bloqueo.")

    st.subheader("Alertas filtradas")
    if not filtered_alerts.empty:
        filtered_alerts_sorted = filtered_alerts.sort_values(["severity", "created_at"], ascending=[False, False])
        st.dataframe(
            filtered_alerts_sorted[
                [
                    "created_at",
                    "block_label",
                    "source_ip",
                    "username",
                    "ssh_event_type",
                    "auth_result",
                    "risk_score",
                    "prediction_label",
                    "rule_hits_display",
                    "reason_summary",
                ]
            ],
            use_container_width=True,
        )
    else:
        st.info("No hay alertas para los filtros seleccionados.")

    st.subheader("Eventos recientes")
    st.dataframe(events.sort_values("timestamp", ascending=False).head(100), use_container_width=True)
    st.stop()


def render_baseline_mode(thresholds: dict) -> None:
    if not SCORED_PATH.exists():
        st.warning("Todavia no existe models/scored_events.csv. Ejecuta primero el parser, features y entrenamiento.")
        st.stop()

    frame = pd.read_csv(SCORED_PATH, parse_dates=["timestamp"])
    if frame.empty:
        st.info("No hay datos procesados para mostrar.")
        st.stop()

    frame = prepare_baseline(frame, thresholds)
    candidates = frame[frame["block_status"] == "candidate_block"]

    render_header("Baseline por lotes con CSV", thresholds)
    render_priority_banner(candidates)

    total_events = len(frame)
    failures = int((frame["auth_result"] == "failure").sum())
    successes = int((frame["auth_result"] == "success").sum())
    high_risk = int((frame["prediction_label"] == "high_risk").sum())
    render_metrics(total_events, failures, successes, high_risk, len(candidates))
    render_model_context(thresholds, total_events)

    st.sidebar.header("Filtros operativos")
    selected_status = st.sidebar.selectbox(
        "Estado de respuesta",
        ["Todos", "candidate_block", "review", "observe"],
        format_func=lambda v: "Todos" if v == "Todos" else status_label(v),
    )
    selected_ip = st.sidebar.selectbox("IP origen", ["Todas"] + sorted(frame["source_ip"].dropna().astype(str).unique().tolist()))

    filtered = frame.copy()
    if selected_status != "Todos":
        filtered = filtered[filtered["block_status"] == selected_status]
    if selected_ip != "Todas":
        filtered = filtered[filtered["source_ip"].astype(str) == selected_ip]

    st.subheader("Registros con criterio de posible bloqueo")
    if not candidates.empty:
        st.dataframe(
            candidates[
                [
                    "timestamp",
                    "source_ip",
                    "username",
                    "ssh_event_type",
                    "failed_count_5m",
                    "user_count_per_ip_5m",
                    "risk_score",
                    "prediction_label",
                    "rule_hits_display",
                ]
            ].sort_values(["timestamp", "risk_score"], ascending=[False, False]),
            use_container_width=True,
        )
    else:
        st.info("Todavia no hay registros que cumplan criterio de posible bloqueo en el baseline.")

    st.subheader("Top IPs por abuso o alertas")
    ip_summary = (
        frame.groupby("source_ip")
        .agg(
            event_count=("source_ip", "size"),
            candidate_block_count=("block_status", lambda values: int((pd.Series(values) == "candidate_block").sum())),
            high_risk_count=("prediction_label", lambda values: int((pd.Series(values) == "high_risk").sum())),
            max_risk_score=("risk_score", "max"),
        )
        .reset_index()
        .sort_values(["candidate_block_count", "high_risk_count", "max_risk_score"], ascending=[False, False, False])
    )
    st.dataframe(ip_summary.head(15), use_container_width=True)

    st.subheader("Eventos analizados")
    st.dataframe(
        filtered[
            [
                "timestamp",
                "block_label",
                "source_ip",
                "username",
                "ssh_event_type",
                "auth_result",
                "failed_count_5m",
                "user_count_per_ip_5m",
                "risk_score",
                "prediction_label",
                "rule_hits_display",
                "raw_message",
            ]
        ].sort_values(["severity", "timestamp"], ascending=[False, False]),
        use_container_width=True,
    )


st.set_page_config(page_title="SSH Anomaly Detection", layout="wide")
inject_styles()
thresholds = load_thresholds()

if SQLITE_PATH.exists():
    render_sqlite_mode(thresholds)
else:
    render_baseline_mode(thresholds)
