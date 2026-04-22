# Deteccion De Accesos SSH Anomalos Con Machine Learning

## Aviso Importante

Este proyecto esta pensado para uso educativo y defensivo en entornos de laboratorio autorizados. El objetivo es detectar actividad anomala en accesos SSH a partir de logs y eventos observables, no automatizar intrusiones ni atacar sistemas de terceros.

## Documentacion Complementaria

Este proyecto tiene un documento ampliado para la evolucion operativa en Ubuntu 24:

- [Monitoreo en tiempo real con systemd](docs/monitoreo-tiempo-real-systemd.md)

Ese documento explica:

- como pasar del procesamiento manual por lotes a monitoreo continuo
- como usar `journalctl -u ssh -f` como fuente en tiempo real
- como plantear scoring continuo y persistencia de alertas
- como disenar respuestas preventivas graduales
- que componentes futuros conviene implementar con `systemd`

## Compatibilidad Entre Versiones

La version inicial por lotes sigue siendo la referencia estable del proyecto y no depende de la version avanzada.

Separacion actual:

- la version inicial usa `scripts/parse_ssh_logs.py`, `scripts/build_features.py`, `scripts/train_baseline.py` y `app/app.py` en modo CSV
- la version avanzada agrega `scripts/run_realtime_monitor.py`, SQLite y archivos `systemd`
- si no existe `data/processed/ssh_monitor.db`, la app vuelve automaticamente al modo baseline con `models/scored_events.csv`

Regla operativa recomendada:

- primero validar siempre el baseline
- despues activar la capa avanzada
- no mezclar pruebas del monitor continuo con los artefactos principales si no hace falta

## Desde Donde Empezar

Para evitar confusion, este proyecto se debe leer e implementar en este orden:

1. este `README.md`
2. la seccion `Ruta De Implementacion Recomendada`
3. la seccion `Flujo Baseline Paso A Paso`
4. la seccion `Validacion Del Baseline`
5. solo despues el documento [Monitoreo en tiempo real con systemd](docs/monitoreo-tiempo-real-systemd.md)

Regla simple:

- si todavia no tienes `models/scored_events.csv`, aun estas en la version inicial
- si ya validaste el baseline y quieres monitoreo continuo, entonces pasas al documento avanzado

## Objetivo

Construir una aplicacion reproducible con machine learning para detectar intentos anormales de acceso por SSH, usando datos de autenticacion del sistema, variables derivadas de comportamiento y un flujo de entrenamiento e inferencia que cualquier persona pueda replicar en su propio laboratorio.

## Problema A Resolver

En un servidor Linux expuesto a SSH suelen aparecer:

- intentos fallidos repetidos
- password spraying
- fuerza bruta distribuida o secuencial
- accesos en horarios anormales
- cambios de patron por IP, usuario o frecuencia

La meta del sistema es transformar esos eventos en:

- registros estructurados
- variables utiles para analisis
- un modelo que estime anomalia o riesgo
- una interfaz para revisar alertas

## Resultado Esperado

La aplicacion debe poder:

1. leer logs SSH desde archivos o `journalctl`
2. parsear eventos de autenticacion
3. generar features por ventana de tiempo, IP, usuario y host
4. entrenar un modelo de deteccion de anomalias o clasificacion
5. puntuar nuevos eventos
6. mostrar alertas y evidencias para analista

## Estructura Del Proyecto

```text
03-ML-deteccion-accesos-ssh/
├── app/              # interfaz o API de consulta
├── config/           # configuracion del pipeline
├── data/
│   ├── raw/          # logs originales
│   └── processed/    # datasets limpios y features
├── docs/             # notas de diseno y decisiones
├── models/           # artefactos entrenados
├── notebooks/        # exploracion y experimentacion
├── scripts/          # ingesta, entrenamiento y evaluacion
├── src/              # codigo fuente principal
└── README.md
```

## Requisitos Para Ubuntu 24 Desde Cero

Esta seccion describe lo minimo necesario para poner en funcionamiento la solucion en un servidor Ubuntu 24 limpio.

### Requisitos De Sistema

- Ubuntu 24.04 LTS
- acceso a `sudo`
- servicio SSH activo en el equipo de laboratorio
- conectividad de red entre el generador de ruido y el servidor monitoreado, si aplica
- al menos 2 vCPU, 4 GB de RAM y 20 GB libres para laboratorio pequeno

### Supuesto Operativo Del Laboratorio

Para esta implementacion se asume lo siguiente:

- la carpeta del proyecto se copiara en la raiz del servidor como `/03-ML-deteccion-accesos-ssh`
- el usuario operativo sera `admon`
- `admon` ya tiene privilegios de `sudo`
- `admon` ya pertenece al grupo `adm`

Por tanto, los comandos de esta guia se ejecutan pensando en ese contexto.

### Paquetes Del Sistema

Instalar primero las dependencias base:

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  python3-dev \
  build-essential \
  git \
  curl \
  jq \
  rsyslog \
  openssh-server
```

Verificar que SSH y logs esten disponibles:

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh

ls -l /var/log/auth.log
sudo tail -n 20 /var/log/auth.log
```

### Permisos Y Acceso A Logs

La solucion necesita leer eventos SSH. En Ubuntu 24 normalmente se usan:

- `/var/log/auth.log`
- `journalctl -u ssh`

Como `admon` ya pertenece al grupo `adm`, deberia poder leer `auth.log` sin cambios extra de grupos. Validar con:

```bash
groups
tail -n 20 /var/log/auth.log
```

### Preparacion De Python

Antes de crear el entorno virtual, asegúrate de que la carpeta ya pertenezca a `admon`:

```bash
sudo chown -R admon:admon /03-ML-deteccion-accesos-ssh
```

Desde la carpeta del proyecto:

```bash
cd /03-ML-deteccion-accesos-ssh

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
```

### Dependencias Python Recomendadas

El proyecto ya incluye un archivo `requirements.txt` con las dependencias base del pipeline:

```text
pandas
numpy
scikit-learn==1.5.2
joblib
matplotlib
seaborn
streamlit
pyyaml
python-dateutil
```

Instalar:

```bash
pip install -r requirements.txt
```

Importante:

- el baseline incluido fue generado con `scikit-learn 1.5.2`
- si tu entorno tenia otra version instalada, actualiza dependencias y reentrena el modelo una vez

En esta carpeta ya quedan incluidos:

- `requirements.txt`
- `config/settings.yaml`
- `scripts/parse_ssh_logs.py`
- `scripts/build_features.py`
- `scripts/train_baseline.py`
- `scripts/validate_baseline.py`
- `scripts/run_realtime_monitor.py`
- `scripts/retrain_model.py`
- `deploy/systemd/ssh-ml-monitor.service`
- `deploy/systemd/ssh-ml-retrain.service`
- `deploy/systemd/ssh-ml-retrain.timer`
- `app/app.py`
- `data/raw/sample_auth.log` como archivo de prueba incluido en el proyecto

### Estructura Minima Operativa

Para considerar que la solucion puede arrancar en Ubuntu 24, deberian existir al menos:

- un parser de logs SSH
- un generador de features
- un script de entrenamiento
- un modelo guardado en `models/`
- una interfaz o script de inferencia

## PROCESO DE IMPLEMENTACION

Esta es la ruta oficial para construir el proyecto sin mezclar etapas:

### Fase 1: Preparar El Servidor

Objetivo:

- dejar Ubuntu 24 listo con Python, SSH y permisos de lectura sobre logs

Resultado esperado:

- el usuario `admon` puede entrar al proyecto, activar `.venv` y leer `/var/log/auth.log`

### Fase 2: Construir La Version Inicial

Objetivo:

- parsear logs
- generar features
- entrenar el baseline
- levantar la app en modo CSV

Resultado esperado:

- existen `data/processed/ssh_events.csv`, `data/processed/ssh_features.csv`, `models/ssh_anomaly_model.joblib`, `models/model_metadata.json` y `models/scored_events.csv`

### Fase 3: Validar La Version Inicial

Objetivo:

- confirmar que la base estable sigue funcionando antes de tocar la capa avanzada

Resultado esperado:

- `python scripts/validate_baseline.py` termina en estado `ok`

### Fase 4: Activar La Version Avanzada

Objetivo:

- pasar a monitoreo continuo con SQLite y `systemd`

Resultado esperado:

- existe `data/processed/ssh_monitor.db`
- la app muestra eventos y alertas desde SQLite

Importante:

- las fases 1 a 3 ocurren en este `README.md`
- la fase 4 se desarrolla en [Monitoreo en tiempo real con systemd](docs/monitoreo-tiempo-real-systemd.md)

## Flujo Baseline Paso A Paso

Este bloque corresponde solo a la version inicial.

Todos los comandos de esta seccion, salvo los que empiezan por `sudo`, deben ejecutarse con el entorno virtual activo:

```bash
cd /03-ML-deteccion-accesos-ssh
source .venv/bin/activate
```

#### Paso 1: Entrar al proyecto

```bash
cd /03-ML-deteccion-accesos-ssh
```

#### Paso 2: Crear entorno virtual e instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Paso 3: Obtener datos crudos

Opciones:

- copiar una muestra de `/var/log/auth.log` a `data/raw/`
- exportar eventos con `journalctl`

Ejemplo:

```bash
cp /var/log/auth.log data/raw/auth.log
```

o

```bash
journalctl -u ssh --since "2026-04-20 00:00:00" > data/raw/journal_ssh.log
```

#### Paso 4: Ejecutar parsing

Ejemplo esperado:

```bash
python scripts/parse_ssh_logs.py \
  parse \
  --input data/raw/auth.log \
  --output data/processed/ssh_events.csv
```

Que estamos haciendo en este paso:

- leemos el log crudo del sistema
- identificamos solo las lineas relevantes para autenticacion SSH
- extraemos campos utiles como fecha, host, IP origen, usuario, puerto y tipo de evento
- convertimos el texto libre del log en un dataset estructurado

Tecnica utilizada:

- parsing basado en expresiones regulares

Que detecta actualmente el parser:

- `Accepted password`
- `Failed password`
- `Invalid user`
- apertura de sesion SSH por `pam_unix(sshd:session)`

Por que este paso es importante:

- los logs crudos son dificiles de usar directamente en machine learning
- el modelo no trabaja con texto arbitrario, trabaja con columnas estructuradas
- este paso convierte evidencia operativa en datos analizables

Salida esperada:

- `data/processed/ssh_events.csv`

Contenido esperado del archivo:

- una fila por evento SSH reconocido
- columnas como `timestamp`, `source_ip`, `username`, `ssh_event_type`, `auth_result`, `raw_message`

#### Paso 5: Ejecutar feature engineering

```bash
python scripts/build_features.py \
  features \
  --input data/processed/ssh_events.csv \
  --output data/processed/ssh_features.csv
```

Que estamos haciendo en este paso:

- tomamos los eventos ya estructurados del paso anterior
- calculamos variables agregadas que describen comportamiento
- transformamos eventos aislados en patrones medibles por ventana de tiempo

Tecnicas utilizadas:

- agregacion temporal
- conteos por ventana deslizante
- variables derivadas de frecuencia
- analisis basico de comportamiento por IP y por usuario

Ejemplos de features que se generan:

- `failed_count_1m`
- `failed_count_5m`
- `failed_count_15m`
- `success_count_1m`
- `success_count_5m`
- `user_events_5m`
- `user_count_per_ip_5m`
- `ip_count_per_user_5m`
- `failure_success_ratio`
- `hour_of_day`
- `day_of_week`
- `is_weekend`

Como interpretar estas variables:

- si una IP genera muchos fallos en pocos minutos, su comportamiento puede ser anomalo
- si una misma IP prueba muchos usuarios distintos, eso puede parecer password spraying
- si un usuario recibe accesos fuera de su horario habitual, eso puede elevar riesgo
- si la relacion fallo/exito es muy alta, puede indicar actividad sospechosa

Por que este paso es importante:

- el modelo no aprende bien solo con el texto del log
- aprende mejor con patrones numericos y temporales
- aqui se concentra gran parte del valor analitico del sistema

Salida esperada:

- `data/processed/ssh_features.csv`

Contenido esperado del archivo:

- las columnas originales mas un conjunto de variables numericas listas para entrenamiento
- una columna `label` inicial de apoyo, util para experimentos de laboratorio

#### Paso 6: Entrenar modelo baseline

```bash
python scripts/train_baseline.py \
  train \
  --input data/processed/ssh_features.csv \
  --model-output models/ssh_anomaly_model.joblib \
  --metadata-output models/model_metadata.json
```

Que estamos haciendo en este paso:

- cargamos el dataset de features
- seleccionamos las variables numericas relevantes
- entrenamos un modelo baseline de deteccion de anomalias
- calculamos un score de riesgo para cada evento
- guardamos el modelo y su metadata para reutilizarlo despues

Algoritmo utilizado actualmente:

- `Isolation Forest`

Por que se eligio este modelo:

- funciona bien como baseline cuando no hay muchas etiquetas confiables
- es rapido de entrenar
- es apropiado para encontrar observaciones raras en datasets operativos
- sirve bien para laboratorios donde hay mezcla de actividad normal y ruido controlado

Idea intuitiva de `Isolation Forest`:

- el modelo intenta aislar observaciones
- los eventos normales suelen requerir mas particiones para aislarse
- los eventos raros o extraños suelen aislarse mas rapido
- mientras mas facil es aislar un evento, mas sospechoso puede resultar

Que columnas usa el modelo:

- hora del evento
- dia de semana
- conteos de fallos y exitos
- cantidad de usuarios por IP
- cantidad de IPs por usuario
- ratio entre fallos y exitos

Que genera este paso:

- `models/ssh_anomaly_model.joblib`
- `models/model_metadata.json`
- `models/scored_events.csv`

Que significa cada salida:

- `ssh_anomaly_model.joblib`: el modelo serializado para volver a cargarlo
- `model_metadata.json`: configuracion, features usadas y resumen del entrenamiento
- `scored_events.csv`: dataset con score de riesgo y etiqueta predicha

Como interpretar el resultado:

- el modelo no afirma "ataque confirmado"
- produce una estimacion de rareza o riesgo
- los eventos `high_risk` deben verse como candidatos a revision
- el analista o docente interpreta luego el contexto

#### Paso 7: Levantar la app

Si la interfaz se construye con Streamlit:

```bash
streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501
```

Luego abrir en navegador:

- `http://IP_DEL_SERVIDOR:8501`

### Puertos Y Firewall

Si la app se expone en red local para laboratorio:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 3306/tcp
sudo ufw allow 8501/tcp
sudo ufw enable
sudo ufw status
```

### Buenas Practicas Operativas Minimas

- no entrenar modelos con logs contaminados sin separar periodos
- conservar una copia del log crudo original
- no ejecutar la app como `root`
- separar datos de entrenamiento y validacion
- versionar el modelo y su lista de features
- registrar fecha de entrenamiento y fuente de datos

### Checklist De Validacion En Ubuntu 24

Antes de considerar el despliegue listo, verificar:

- `whoami` devuelve `admon`
- `pwd` dentro del proyecto apunta a `/03-ML-deteccion-accesos-ssh`
- `python3 --version`
- `pip --version`
- `systemctl status ssh`
- lectura de `/var/log/auth.log`
- entorno virtual funcional
- dependencias instaladas
- parser genera `ssh_events.csv`
- feature engineering genera `ssh_features.csv`
- entrenamiento produce modelo en `models/`
- interfaz responde en el puerto configurado

## Arquitectura De Referencia

### 1. Capa De Ingesta

Fuentes posibles:

- `/var/log/auth.log`
- `/var/log/secure`
- salida de `journalctl -u ssh`
- exportaciones CSV desde SIEM o agentes

Responsabilidades:

- leer archivos o streams
- normalizar timestamps
- identificar eventos SSH relevantes
- conservar campos originales para trazabilidad

### 2. Capa De Parsing

Eventos utiles:

- `Failed password`
- `Accepted password`
- `Invalid user`
- `Connection closed`
- `Disconnecting`
- bloqueos de `fail2ban` si existen

Campos base sugeridos:

- `timestamp`
- `hostname`
- `source_ip`
- `source_port`
- `username`
- `ssh_event_type`
- `auth_result`
- `raw_message`

### 3. Capa De Feature Engineering

Variables sugeridas por ventana de tiempo:

- intentos por IP en 1, 5 y 15 minutos
- intentos por usuario en 1, 5 y 15 minutos
- cantidad de usuarios distintos por IP
- cantidad de IPs distintas por usuario
- ratio de fallos sobre exitos
- primer acceso del dia para usuario
- hora del evento
- dia de semana
- distancia respecto al horario habitual del usuario
- secuencia `invalid user -> failed password -> disconnect`
- numero de hosts objetivo por origen, si aplica

### 4. Capa De Modelado

Dos caminos razonables:

#### Opcion A: Deteccion De Anomalias

Cuando no hay etiquetas confiables.

Modelos posibles:

- `Isolation Forest`
- `Local Outlier Factor`
- `One-Class SVM`

Ventajas:

- util cuando solo hay datos historicos normales o poco etiquetados
- rapido para prototipos de laboratorio

#### Opcion B: Clasificacion Supervisada

Cuando ya hay etiquetas `normal` vs `sospechoso`.

Modelos posibles:

- `Logistic Regression`
- `Random Forest`
- `XGBoost` o `LightGBM`

Ventajas:

- mejor interpretabilidad comparativa
- permite medir precision, recall y F1

### 5. Capa De Inferencia

Salida sugerida por evento o ventana:

- `risk_score`
- `prediction_label`
- `top_features`
- `reason_summary`

Ejemplos de etiquetas:

- `normal`
- `review`
- `high_risk`

### 6. Capa De Visualizacion

Opciones viables:

- `Streamlit` para una interfaz rapida
- `FastAPI` para API + frontend liviano
- `Flask` si se quiere una UI simple y controlada

Pantallas sugeridas:

- resumen de actividad SSH
- alertas recientes
- top IPs sospechosas
- top usuarios atacados
- detalle de una alerta con su contexto
- historial de riesgo por IP o usuario

## Explicacion Conceptual Del Proyecto

Esta seccion ya no describe el orden operativo de implementacion. Su funcion es explicar el diseno tecnico del sistema.

## Flujo De Construccion Reproducible

Esta es una vista conceptual de como se penso el proyecto. Si vas a implementarlo, sigue primero `Ruta De Implementacion Recomendada` y `Flujo Baseline Paso A Paso`.

### Paso 1: Preparar El Entorno

Stack sugerido:

- Python 3.11+
- `pandas`
- `numpy`
- `scikit-learn`
- `matplotlib`
- `seaborn`
- `joblib`
- `streamlit` o `fastapi`

Recomendacion:

- crear un entorno virtual
- fijar dependencias en `requirements.txt`
- versionar configuracion y scripts

### Paso 2: Recolectar Datos

Usar solo logs del laboratorio autorizado.

Estrategias:

- recopilar ventanas normales de uso
- generar ruido controlado en el laboratorio
- conservar tambien periodos sin incidentes

Fuentes de datos para laboratorio:

- logs naturales del servidor SSH
- actividad administrativa legitima
- ruido de laboratorio autorizado desde `02-lab_hydra`

### Paso 3: Parsear Y Estructurar

Crear un script de parsing que convierta logs crudos a un CSV o parquet estructurado.

Salida recomendada:

- `data/processed/ssh_events.csv`

### Paso 4: Etiquetar O Definir Estrategia

Escenarios:

- si no hay etiquetas, iniciar con anomaly detection
- si hay eventos claramente artificiales o revisados, crear etiquetas

Etiquetas sugeridas:

- `0 = normal`
- `1 = sospechoso`

### Paso 5: Generar Features

Crear ventanas temporales y agregaciones por:

- IP
- usuario
- host
- combinacion `IP + usuario`

Salida recomendada:

- `data/processed/ssh_features.csv`

### Paso 6: Entrenar El Modelo

Recomendacion inicial:

- baseline no supervisado con `Isolation Forest`
- baseline supervisado con `Logistic Regression` o `Random Forest`

Guardar:

- modelo entrenado
- scaler si se usa
- lista de features
- metricas del experimento

Salida sugerida:

- `models/ssh_anomaly_model.joblib`
- `models/feature_columns.json`

### Paso 7: Evaluar

Metricas segun enfoque:

#### Para clasificacion

- precision
- recall
- F1-score
- matriz de confusion
- ROC-AUC

#### Para anomalias

- tasa de alertas
- precision en top-N alertas revisadas
- estabilidad por ventanas
- utilidad analitica de los falsos positivos

### Paso 8: Construir La Aplicacion

La app debe permitir:

- cargar nuevos eventos
- calcular features
- ejecutar inferencia
- mostrar score y explicacion

Componentes minimos:

- cargador de archivo o ruta de log
- panel de resultados
- tabla de alertas
- detalle de cada evento sospechoso

### Paso 9: Operacionalizar

Si el sistema madura:

- ejecucion programada cada N minutos
- guardado de resultados en base de datos
- integracion con SIEM o dashboard
- versionado de modelos

## Diseño De Datos

### Dataset De Eventos

Columnas sugeridas:

- `timestamp`
- `hostname`
- `source_ip`
- `source_port`
- `username`
- `auth_result`
- `ssh_event_type`
- `raw_message`

### Dataset De Features

Columnas sugeridas:

- `window_start`
- `window_end`
- `source_ip`
- `username`
- `failed_count_1m`
- `failed_count_5m`
- `user_count_per_ip_5m`
- `ip_count_per_user_5m`
- `success_count_15m`
- `failure_success_ratio`
- `hour_of_day`
- `is_weekend`
- `label`

## Diseño Del Modelo Inicial

### Baseline 1: Isolation Forest

Uso recomendado:

- cuando se parte con pocos datos etiquetados

Entrada:

- features numericas agregadas por ventana

Salida:

- score de anomalia
- clasificacion binaria usando umbral

### Baseline 2: Random Forest

Uso recomendado:

- cuando se dispone de etiquetas de laboratorio

Ventajas:

- robusto
- facil de comparar
- interpretacion aceptable con feature importance

## Diseño De La App

### Interfaz Sugerida

#### Vista 1: Resumen

- total de eventos procesados
- total de fallos
- total de exitos
- alertas generadas

#### Vista 2: Top Riesgo

- top IPs por score
- top usuarios mas atacados
- franjas horarias mas anormales

#### Vista 3: Alertas

- timestamp
- IP
- usuario
- score
- etiqueta
- razon principal

#### Vista 4: Evidencia

- evento crudo
- features calculadas
- contexto de ventana
- historial de esa IP o usuario

## Roadmap Recomendado

### Fase 1

- parsing de logs
- dataset estructurado
- exploracion inicial

### Fase 2

- engineering de features
- primer modelo baseline
- evaluacion

### Fase 3

- app de consulta
- filtros y alertas
- reporte de razones

### Fase 4

- mejora de modelos
- explicabilidad
- versionado y monitoreo

## Buenas Practicas De Reproduccion

- fijar version de dependencias
- guardar muestras anonimizadas
- documentar columnas y features
- separar datos crudos de procesados
- no sobreescribir modelos sin version
- registrar metricas de cada experimento

## Entregables Minimos

Para considerar el proyecto reproducible, deberia incluir:

- `README.md` completo
- script de parsing
- script de features
- script de entrenamiento
- modelo baseline
- ejemplos de datos
- una app o dashboard minimo

## Proximo Paso Sugerido

Implementar primero el pipeline minimo:

1. parser de `auth.log`
2. dataset `ssh_events.csv`
3. feature engineering simple
4. `Isolation Forest`
5. dashboard basico

Ese camino da una primera version funcional rapidamente y deja base para evolucionar a modelos supervisados.

## Ejecucion Rapida De Prueba

Con los archivos incluidos puedes probar el pipeline sin depender aun del `auth.log` real. Esta prueba usa el archivo demo `data/raw/sample_auth.log`, mientras que el flujo operativo normal usa `data/raw/auth.log`:

Ejecuta estos comandos con `.venv` activo:

```bash
python scripts/parse_ssh_logs.py parse \
  --input data/raw/sample_auth.log \
  --output data/processed/ssh_events.csv

python scripts/build_features.py features \
  --input data/processed/ssh_events.csv \
  --output data/processed/ssh_features.csv

python scripts/train_baseline.py train \
  --input data/processed/ssh_features.csv \
  --model-output models/ssh_anomaly_model.joblib \
  --metadata-output models/model_metadata.json

streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501
```

## Validacion Del Baseline

Antes de probar cambios grandes o la capa avanzada, puedes validar que la version inicial siga funcionando sin tocar sus artefactos principales:

Ejecuta este comando con `.venv` activo:

```bash
python scripts/validate_baseline.py
```

Este chequeo:

- usa `data/raw/sample_auth.log`
- genera archivos separados de validacion
- no sobreescribe `models/ssh_anomaly_model.joblib`
- no altera `models/model_metadata.json`
- deja un resumen en `models/baseline_validation_summary.json`

## Paso Siguiente: Version Avanzada

Cuando ya hayas completado y validado el baseline, continua aqui:

- [Monitoreo en tiempo real con systemd](docs/monitoreo-tiempo-real-systemd.md)

Ese documento cubre:

- `run_realtime_monitor.py`
- SQLite como persistencia operativa
- seguimiento continuo de `auth.log` o `journald`
- reentrenamiento con `retrain_model.py`
- despliegue con `systemd`

## Ejecucion Avanzada

Resumen corto. El detalle formal vive en el documento avanzado.

### Replay y seguimiento continuo

Primero puedes reprocesar el log actual y luego seguir eventos nuevos sin copiar archivos:

Ejecuta este comando con `.venv` activo:

```bash
python scripts/run_realtime_monitor.py \
  --input-file /var/log/auth.log \
  --replay-existing \
  --follow-file
```

Si prefieres usar `systemd` como fuente principal:

Ejecuta este comando con `.venv` activo:

```bash
python scripts/run_realtime_monitor.py \
  --follow-journal
```

### Reentrenamiento manual

Para refrescar el baseline con el log real del servidor:

Ejecuta este comando con `.venv` activo:

```bash
python scripts/retrain_model.py \
  --input-log /var/log/auth.log
```

Este comando:

- parsea el log real
- regenera `ssh_events.csv`
- recalcula `ssh_features.csv`
- entrena de nuevo `Isolation Forest`
- actualiza `models/model_metadata.json`
- deja un resumen en `models/retrain_summary.json`

Si antes habias creado el entorno con otra version de `scikit-learn`, este paso tambien corrige los avisos de incompatibilidad de version del modelo.
