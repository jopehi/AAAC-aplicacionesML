# Deteccion De Accesos Web Sospechosos Con Machine Learning

Aplicacion defensiva para analizar `access.log` y `error.log` de Apache en Ubuntu 24, entrenando un baseline supervisado con el dataset `csic_database.csv` de CSIC 2010.

## Contexto Operativo

Ruta esperada en el servidor:

```bash
/04-ML-deteccion-accesos-weblogs
```

Puerto de la interfaz:

```text
8503
```

Se usa `8503` para no chocar con la aplicacion de `03-ML-deteccion-accesos-ssh`, que queda en `8502`.

## Estructura Actual

```text
04-ML-deteccion-accesos-weblogs/
├── app/
│   └── app.py
├── config/
│   └── settings.yaml
├── data/
│   ├── raw/
│   │   ├── access.log
│   │   ├── error.log
│   │   └── csic_database.csv
│   └── processed/
│       ├── access_events.csv
│       ├── access_scored.csv
│       ├── csic_features.csv
│       └── error_events.csv
├── models/
│   ├── model_metadata.json
│   ├── scored_events.csv
│   └── web_attack_model.joblib
├── scripts/
│   ├── normalize_csic.py
│   ├── parse_access_log.py
│   ├── parse_error_log.py
│   ├── score_access_log.py
│   └── train_model.py
├── deploy/
│   └── systemd/
│       └── weblog-ml-dashboard.service
├── src/
│   ├── __init__.py
│   └── web_log_pipeline.py
├── requirements.txt
└── README.md
```

Los archivos en `data/raw/`, `data/processed/` y `models/` son artefactos locales. No deberian versionarse si contienen datos reales del laboratorio.

## Fuentes De Datos

Entrenamiento:

- `data/raw/csic_database.csv`

Logs iniciales de Apache:

- `data/raw/access.log`
- `data/raw/error.log`

El dataset CSIC debe contener columnas como:

- `Method`
- `User-Agent`
- `content`
- `classification`
- `URL`

La columna `classification` se convierte a:

- `0`: normal
- `1`: sospechoso/anomalo

## Preparacion En Ubuntu 24

Si la carpeta se copia al servidor como `root` o desde otro usuario, primero ajustar el dueño y permisos del proyecto:

```bash
sudo chown -R admon:admon /04-ML-deteccion-accesos-weblogs
sudo find /04-ML-deteccion-accesos-weblogs -type d -exec chmod 750 {} \;
sudo find /04-ML-deteccion-accesos-weblogs -type f -exec chmod 640 {} \;
sudo chmod -R u+rwX /04-ML-deteccion-accesos-weblogs
```

Si el usuario `admon` debe leer logs directamente desde `/var/log/apache2`, validar que tenga acceso al grupo correspondiente:

```bash
groups admon
sudo usermod -aG adm admon
```

Despues de agregar el grupo, cerrar sesion y volver a entrar para que el cambio aplique.

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential

cd /04-ML-deteccion-accesos-weblogs
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

## Flujo Baseline Completo

Ejecutar desde `/04-ML-deteccion-accesos-weblogs` con `.venv` activo.

### 1. Normalizar Dataset CSIC

```bash
python scripts/normalize_csic.py normalize-csic \
  --input data/raw/csic_database.csv \
  --output data/processed/csic_features.csv
```

### 2. Entrenar Modelo

```bash
python scripts/train_model.py train \
  --input data/processed/csic_features.csv \
  --model-output models/web_attack_model.joblib \
  --metadata-output models/model_metadata.json
```

El modelo baseline usa:

- `TfidfVectorizer` por caracteres sobre requests HTTP
- `LogisticRegression`
- etiquetas supervisadas desde `classification`

### 3. Parsear `access.log`

```bash
python scripts/parse_access_log.py parse-access \
  --input data/raw/access.log \
  --output data/processed/access_events.csv
```

### 4. Parsear `error.log`

```bash
python scripts/parse_error_log.py parse-error \
  --input data/raw/error.log \
  --output data/processed/error_events.csv
```

### 5. Puntuar Access Log

```bash
python scripts/score_access_log.py score-access \
  --input data/processed/access_events.csv \
  --model models/web_attack_model.joblib \
  --output data/processed/access_scored.csv
```

La salida incluye:

- `ml_risk_score`
- `heuristic_risk_score`
- `risk_score`
- `prediction_label`: `normal`, `review`, `high_risk`
- `reasons`

## Levantar Dashboard

```bash
streamlit run app/app.py --server.address 0.0.0.0 --server.port 8503
```

Abrir:

```text
http://IP_DEL_SERVIDOR:8503
```

Si `ufw` esta activo:

```bash
sudo ufw allow 8503/tcp
sudo ufw status
```

## Servicio Systemd Opcional

El proyecto incluye un servicio de referencia:

```text
deploy/systemd/weblog-ml-dashboard.service
```

Instalacion sugerida en Ubuntu 24:

```bash
sudo cp deploy/systemd/weblog-ml-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weblog-ml-dashboard
sudo systemctl start weblog-ml-dashboard
sudo systemctl status weblog-ml-dashboard
```

El servicio asume:

- ruta del proyecto: `/04-ML-deteccion-accesos-weblogs`
- usuario operativo: `admon`
- entorno virtual: `/04-ML-deteccion-accesos-weblogs/.venv`
- puerto: `8503`

## Flujo Rapido

```bash
cd /04-ML-deteccion-accesos-weblogs
source .venv/bin/activate

python scripts/normalize_csic.py normalize-csic --input data/raw/csic_database.csv --output data/processed/csic_features.csv
python scripts/train_model.py train --input data/processed/csic_features.csv --model-output models/web_attack_model.joblib --metadata-output models/model_metadata.json
python scripts/parse_access_log.py parse-access --input data/raw/access.log --output data/processed/access_events.csv
python scripts/parse_error_log.py parse-error --input data/raw/error.log --output data/processed/error_events.csv
python scripts/score_access_log.py score-access --input data/processed/access_events.csv --model models/web_attack_model.joblib --output data/processed/access_scored.csv
streamlit run app/app.py --server.address 0.0.0.0 --server.port 8503
```

## Nota De Seguridad

Esta aplicacion produce priorizacion de riesgo, no confirmacion absoluta de ataque. Las alertas `high_risk` deben revisarse con el contexto de Apache, la aplicacion `01-fintech` y la actividad esperada del laboratorio.
