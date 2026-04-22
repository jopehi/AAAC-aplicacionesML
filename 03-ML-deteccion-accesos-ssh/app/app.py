from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
SCORED_PATH = BASE_DIR / "models" / "scored_events.csv"
SQLITE_PATH = BASE_DIR / "data" / "processed" / "ssh_monitor.db"

st.set_page_config(page_title="SSH Anomaly Detection", layout="wide")
st.title("Deteccion de accesos SSH anomalos")
st.caption("Panel para revisar eventos procesados y alertas de riesgo. Si existe SQLite de monitoreo, se prioriza la vista avanzada.")

if SQLITE_PATH.exists():
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

    total_events = len(events)
    high_risk = int((alerts["prediction_label"] == "high_risk").sum()) if not alerts.empty else 0
    failures = int((events["auth_result"] == "failure").sum()) if not events.empty else 0
    successes = int((events["auth_result"] == "success").sum()) if not events.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Eventos", total_events)
    col2.metric("Fallos", failures)
    col3.metric("Exitos", successes)
    col4.metric("Alertas", len(alerts))

    st.subheader("Top IPs por alertas")
    if not alerts.empty:
        top_ips = (
            alerts.groupby("source_ip")
            .size()
            .reset_index(name="alert_count")
            .sort_values("alert_count", ascending=False)
        )
        st.dataframe(top_ips.head(10), use_container_width=True)
    else:
        st.info("Todavia no hay alertas persistidas.")

    st.subheader("Alertas recientes")
    if not alerts.empty:
        st.dataframe(alerts.sort_values("created_at", ascending=False), use_container_width=True)

    st.subheader("Eventos recientes")
    st.dataframe(events.sort_values("timestamp", ascending=False), use_container_width=True)
    st.stop()

if not SCORED_PATH.exists():
    st.warning("Todavia no existe models/scored_events.csv. Ejecuta primero el parser, features y entrenamiento.")
    st.stop()

frame = pd.read_csv(SCORED_PATH, parse_dates=["timestamp"])

if frame.empty:
    st.info("No hay datos procesados para mostrar.")
    st.stop()

total_events = len(frame)
high_risk = int((frame["prediction_label"] == "high_risk").sum())
failures = int((frame["auth_result"] == "failure").sum())
successes = int((frame["auth_result"] == "success").sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Eventos", total_events)
col2.metric("Fallos", failures)
col3.metric("Exitos", successes)
col4.metric("Alertas", high_risk)

st.subheader("Filtros")
left, right = st.columns(2)
selected_label = left.selectbox("Nivel de riesgo", ["Todos", "high_risk", "normal"])
selected_ip = right.selectbox("IP origen", ["Todas"] + sorted(frame["source_ip"].dropna().unique().tolist()))

filtered = frame.copy()
if selected_label != "Todos":
    filtered = filtered[filtered["prediction_label"] == selected_label]
if selected_ip != "Todas":
    filtered = filtered[filtered["source_ip"] == selected_ip]

st.subheader("Top IPs por alertas")
top_ips = (
    frame[frame["prediction_label"] == "high_risk"]
    .groupby("source_ip")
    .size()
    .reset_index(name="alert_count")
    .sort_values("alert_count", ascending=False)
)
st.dataframe(top_ips.head(10), use_container_width=True)

st.subheader("Eventos analizados")
st.dataframe(
    filtered[
        [
            "timestamp",
            "source_ip",
            "username",
            "ssh_event_type",
            "auth_result",
            "risk_score",
            "prediction_label",
            "raw_message",
        ]
    ].sort_values("timestamp", ascending=False),
    use_container_width=True,
)
