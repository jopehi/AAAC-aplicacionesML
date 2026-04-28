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

Logs reales de Apache:

```text
/var/log/apache2/access.log
/var/log/apache2/error.log
```

## Estructura Actual

```text
04-ML-deteccion-accesos-weblogs/
|-- app/
|   `-- app.py
|-- config/
|   `-- settings.yaml
|-- data/
|   |-- raw/
|   |   |-- access.log
|   |   |-- error.log
|   |   `-- csic_database.csv
|   `-- processed/
|       |-- access_events.csv
|       |-- access_scored.csv
|       |-- csic_features.csv
|       `-- error_events.csv
|-- deploy/
|   `-- systemd/
|       |-- weblog-ml-dashboard.service
|       |-- weblog-ml-refresh.service
|       `-- weblog-ml-refresh.timer
|-- models/
|   |-- model_metadata.json
|   |-- scored_events.csv
|   `-- web_attack_model.joblib
|-- scripts/
|   |-- normalize_csic.py
|   |-- parse_access_log.py
|   |-- parse_error_log.py
|   |-- score_access_log.py
|   |-- train_model.py
|   `-- update_current_apache_logs.py
|-- src/
|   |-- __init__.py
|   `-- web_log_pipeline.py
|-- requirements.txt
`-- README.md
```

Los archivos en `data/raw/`, `data/processed/` y `models/` son artefactos locales. No deberian versionarse si contienen datos reales del laboratorio.

## Fuentes De Datos

Entrenamiento:

- `data/raw/csic_database.csv`

Logs iniciales copiados al proyecto:

- `data/raw/access.log`
- `data/raw/error.log`

Logs actuales del sistema en produccion/laboratorio:

- `/var/log/apache2/access.log`
- `/var/log/apache2/error.log`

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

Si la carpeta se copia al servidor como `root` o desde otro usuario, primero ajustar el dueno y permisos del proyecto:

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

Instalar dependencias:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential

cd /04-ML-deteccion-accesos-weblogs
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

## Flujo Baseline Inicial

Ejecutar desde `/04-ML-deteccion-accesos-weblogs` con `.venv` activo.

Este flujo se ejecuta para dejar lista la primera version funcional del sistema. Su objetivo es convertir el dataset CSIC en datos entrenables, entrenar el modelo y generar los artefactos que luego se usan para puntuar los logs actuales de Apache.

### 1. Normalizar Dataset CSIC

```bash
python scripts/normalize_csic.py normalize-csic \
  --input data/raw/csic_database.csv \
  --output data/processed/csic_features.csv
```

Que hace este paso:

- lee `data/raw/csic_database.csv`
- normaliza los nombres de columnas
- toma campos como `Method`, `URL`, `content`, `User-Agent` y `classification`
- construye una columna `request_text` con la informacion relevante de cada request
- decodifica caracteres URL cuando aplica
- crea variables defensivas como SQLi, XSS, path traversal, rutas sensibles y command injection
- convierte `classification` en la etiqueta numerica `label`

Entrada:

```text
data/raw/csic_database.csv
```

Salida:

```text
data/processed/csic_features.csv
```

Por que es necesario:

- el CSV original viene como dataset HTTP crudo
- el modelo no debe entrenarse directamente sobre columnas sin normalizar
- este paso deja el dataset en una estructura estable para entrenamiento

Validacion rapida:

```bash
ls -lh data/processed/csic_features.csv
head -n 2 data/processed/csic_features.csv
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

Que hace este paso:

- carga `data/processed/csic_features.csv`
- separa datos de entrenamiento y prueba
- transforma `request_text` en features numericas con TF-IDF por caracteres
- entrena una regresion logistica balanceada para clasificar requests normales vs sospechosos
- evalua el modelo con metricas de clasificacion
- guarda el modelo entrenado y la metadata del experimento

Entrada:

```text
data/processed/csic_features.csv
```

Salidas:

```text
models/web_attack_model.joblib
models/model_metadata.json
models/scored_events.csv
```

Que significa cada salida:

- `web_attack_model.joblib`: modelo entrenado que se reutiliza para puntuar `access.log`
- `model_metadata.json`: metricas, version de scikit-learn, cantidad de filas y matriz de confusion
- `scored_events.csv`: dataset CSIC con scores generados por el modelo, util para revisar comportamiento del baseline

Por que es necesario:

- sin este modelo no se puede ejecutar `score_access_log.py`
- el refresco automatico tambien depende de `models/web_attack_model.joblib`

Validacion rapida:

```bash
ls -lh models/web_attack_model.joblib models/model_metadata.json
cat models/model_metadata.json
```

### 3. Verificar Artefactos Minimos

Antes de pasar a logs reales, verificar que existan estos archivos:

```bash
test -f data/processed/csic_features.csv && echo "CSIC normalizado OK"
test -f models/web_attack_model.joblib && echo "Modelo OK"
test -f models/model_metadata.json && echo "Metadata OK"
```

Si alguno no existe, repetir los pasos anteriores antes de intentar capturar trafico actual de Apache.

## Capturar Trafico Actual De Apache

Despues de entrenar el modelo una vez, el trafico actual se actualiza leyendo directamente:

```text
/var/log/apache2/access.log
/var/log/apache2/error.log
```

Para refrescar manualmente los resultados:

```bash
python scripts/update_current_apache_logs.py
```

Antes de ejecutar este comando debe existir el modelo:

```text
models/web_attack_model.joblib
```

Ese comando ejecuta internamente:

- parseo de `/var/log/apache2/access.log`
- parseo de `/var/log/apache2/error.log`
- scoring ML del access log
- actualizacion de `data/processed/access_events.csv`
- actualizacion de `data/processed/error_events.csv`
- actualizacion de `data/processed/access_scored.csv`

Esta version reprocesa el archivo actual completo en cada ejecucion. Es intencional para mantener el flujo simple y estable en laboratorio. Si los logs crecen demasiado, el siguiente paso seria cambiar a persistencia incremental con SQLite y seguimiento de offsets.

Para probar con logs copiados en `data/raw/` en vez de los logs reales del sistema:

```bash
python scripts/update_current_apache_logs.py \
  --access-log data/raw/access.log \
  --error-log data/raw/error.log
```

## Comandos Manuales Separados

Si se quiere ejecutar cada paso por separado:

```bash
python scripts/parse_access_log.py parse-access \
  --input /var/log/apache2/access.log \
  --output data/processed/access_events.csv

python scripts/parse_error_log.py parse-error \
  --input /var/log/apache2/error.log \
  --output data/processed/error_events.csv

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

## Levantar Dashboard Manualmente

```bash
streamlit run app/app.py --server.address 0.0.0.0 --server.port 8503 --server.headless true
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

## Como Interpretar La Interfaz

La interfaz permite revisar tres fuentes:

- `Access log Apache`: resultados del archivo `access.log` ya puntuados
- `Error log Apache`: eventos parseados desde `error.log`
- `Dataset CSIC puntuado`: resultados del dataset usado para entrenar y revisar el baseline

### Metricas Superiores

En la parte superior se muestran:

- `Eventos`: cantidad de filas cargadas en la vista actual
- `Alto riesgo`: cantidad de eventos con etiqueta `high_risk`
- `Revision`: cantidad de eventos con etiqueta `review`
- `Score medio`: promedio del score de la fuente seleccionada

El `Score medio` no significa ataque confirmado. Solo resume que tan riesgosa se ve la muestra cargada.

### Scores En Access Log

Para `Access log Apache`, la tabla puede mostrar estos campos:

- `ml_risk_score`
- `heuristic_risk_score`
- `risk_score`
- `prediction_label`
- `reasons`

Interpretacion:

- `ml_risk_score`: probabilidad estimada por el modelo entrenado con CSIC. Valores cercanos a `1.0` indican que el request se parece mas a trafico anomalo del dataset.
- `heuristic_risk_score`: score basado en reglas explicables, por ejemplo SQLi, XSS, path traversal, rutas sensibles o user-agents automatizados.
- `risk_score`: score final usado para ordenar y etiquetar. Actualmente toma el mayor valor entre `ml_risk_score` y `heuristic_risk_score`.
- `prediction_label`: categoria final de riesgo.
- `reasons`: explicacion corta de las reglas que se activaron.

Umbrales actuales:

```text
0.00 - 0.34  => normal
0.35 - 0.69  => review
0.70 - 1.00  => high_risk
```

Estos umbrales se configuran en:

```text
config/settings.yaml
```

Ejemplo:

```yaml
scoring:
  high_risk_threshold: 0.70
  review_threshold: 0.35
```

### Etiquetas De Riesgo

`normal`:

- el evento no tiene senales fuertes de ataque
- no requiere accion inmediata
- aun asi puede aparecer si el trafico real cambia o si el modelo no reconoce una tecnica nueva

`review`:

- el evento tiene senales que justifican revision manual
- puede ser un falso positivo, por ejemplo un `404` normal o una ruta inexistente solicitada por un navegador
- conviene revisar IP, URL, user-agent, status code y frecuencia

`high_risk`:

- el evento tiene senales fuertes de actividad sospechosa
- puede indicar SQL injection, XSS, path traversal, busqueda de archivos sensibles o herramientas automatizadas
- debe revisarse con prioridad antes de tomar acciones como bloqueo

### Campo `reasons`

El campo `reasons` ayuda a explicar por que un evento fue marcado.

Ejemplos:

- `patron SQLi`: posible SQL injection
- `patron XSS`: posible intento de cross-site scripting
- `path traversal`: intento de acceder a rutas fuera del directorio esperado
- `ruta sensible`: acceso a rutas como `.env`, `.git`, `/admin`, `/phpmyadmin` o similares
- `command injection`: posible intento de inyectar comandos
- `user-agent automatizado`: herramientas como `curl`, `wget`, `sqlmap`, `nikto`, `nmap` o bots
- `respuesta HTTP de error`: status `4xx` o `5xx`

### Scores En Error Log

Para `Error log Apache`, el sistema no usa el modelo CSIC. En su lugar usa severidad del log:

- `severity_score`
- `event_label`
- `level`
- `module`
- `message`

Interpretacion de severidad:

```text
notice/info/debug  => normal
warn/warning       => review
error/err          => high_risk
crit/alert/emerg   => high_risk
unparsed           => review
```

El `error.log` debe interpretarse como contexto operativo. No todo `warning` o `error` es un ataque; puede ser configuracion, reinicios de Apache, permisos, rutas faltantes o errores de aplicacion.

### Forma Recomendada De Analisis

1. Revisar primero `Access log Apache` filtrando `high_risk`.
2. Ordenar mentalmente por `risk_score` mas alto.
3. Leer `url`, `source_ip`, `user_agent`, `status_code` y `reasons`.
4. Cambiar a `Error log Apache` para ver si hay errores cerca del mismo periodo.
5. Confirmar contexto antes de bloquear IPs o tomar acciones.

Regla practica:

- `high_risk` no significa ataque confirmado
- `review` significa revisar contexto
- `normal` no significa garantia absoluta de seguridad

## Servicio Systemd Del Dashboard

El proyecto incluye un servicio de referencia:

```text
deploy/systemd/weblog-ml-dashboard.service
```

Si se instala y habilita este servicio, ya no es necesario iniciar el dashboard manualmente con `streamlit run` despues de cada reinicio. `systemd` se encarga de levantarlo automaticamente en el puerto `8503` cuando inicia el servidor y de reiniciarlo si el proceso falla.

Instalacion sugerida en Ubuntu 24:

```bash
sudo cp deploy/systemd/weblog-ml-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weblog-ml-dashboard
sudo systemctl start weblog-ml-dashboard
sudo systemctl status weblog-ml-dashboard
```

Despues de este paso, el acceso normal sera directamente:

```text
http://IP_DEL_SERVIDOR:8503
```

Comandos utiles:

```bash
sudo systemctl restart weblog-ml-dashboard
sudo systemctl stop weblog-ml-dashboard
sudo journalctl -u weblog-ml-dashboard -f
```

## Refresco Automatico De Logs Con Systemd Timer

El dashboard muestra lo que exista en `data/processed/`. Para que esos archivos se actualicen con el trafico actual de Apache sin ejecutar comandos manuales, instalar el timer:

```bash
sudo cp deploy/systemd/weblog-ml-refresh.service /etc/systemd/system/
sudo cp deploy/systemd/weblog-ml-refresh.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weblog-ml-refresh.timer
sudo systemctl start weblog-ml-refresh.timer
sudo systemctl status weblog-ml-refresh.timer
```

El timer ejecuta cada minuto:

```bash
python scripts/update_current_apache_logs.py
```

Esto no reinicia el dashboard. Solo actualiza los CSV que el dashboard lee. En el navegador basta refrescar la pagina o cambiar de filtro/fuente para ver los datos nuevos.

El servicio de refresco se ejecuta como `admon` y usa el grupo suplementario `adm` para leer `/var/log/apache2`. Si `admon` no pertenece a `adm`, corregirlo con:

```bash
sudo usermod -aG adm admon
```

Luego cerrar sesion y volver a entrar, o reiniciar el servicio si ya estaba instalado.

Comandos utiles:

```bash
sudo systemctl start weblog-ml-refresh.service
sudo systemctl list-timers | grep weblog-ml
sudo journalctl -u weblog-ml-refresh.service -f
```

## Flujo Rapido Recomendado

```bash
cd /04-ML-deteccion-accesos-weblogs
source .venv/bin/activate

python scripts/normalize_csic.py normalize-csic --input data/raw/csic_database.csv --output data/processed/csic_features.csv
python scripts/train_model.py train --input data/processed/csic_features.csv --model-output models/web_attack_model.joblib --metadata-output models/model_metadata.json
python scripts/update_current_apache_logs.py

sudo cp deploy/systemd/weblog-ml-dashboard.service /etc/systemd/system/
sudo cp deploy/systemd/weblog-ml-refresh.service /etc/systemd/system/
sudo cp deploy/systemd/weblog-ml-refresh.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now weblog-ml-dashboard
sudo systemctl enable --now weblog-ml-refresh.timer
```

## Nota De Seguridad

Esta aplicacion produce priorizacion de riesgo, no confirmacion absoluta de ataque. Las alertas `high_risk` deben revisarse con el contexto de Apache, la aplicacion `01-fintech` y la actividad esperada del laboratorio.
