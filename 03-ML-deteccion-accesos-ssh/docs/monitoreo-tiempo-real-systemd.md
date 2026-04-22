# Monitoreo En Tiempo Real Con systemd En Ubuntu 24

## Objetivo

Describir una version ampliada del sistema para monitorear accesos SSH en tiempo real en Ubuntu 24, usando `systemd` como fuente principal de eventos y separando claramente:

- ingesta continua
- scoring continuo
- persistencia de alertas
- respuesta preventiva controlada

Este documento complementa el `README.md` principal y sirve como hoja de ruta para una evolucion operativa del laboratorio.

## Nota De Compatibilidad

Esta version ampliada no reemplaza la version inicial del proyecto.

La base estable sigue siendo el pipeline por lotes:

- `scripts/parse_ssh_logs.py`
- `scripts/build_features.py`
- `scripts/train_baseline.py`

La capa avanzada debe entenderse como un modulo adicional.

Antes de activar monitoreo continuo o servicios `systemd`, conviene validar el baseline con:

```bash
python scripts/validate_baseline.py
```

## Punto De Inicio De Este Documento

Este archivo no es la guia principal del proyecto.

Debes llegar aqui solo cuando ya hiciste lo siguiente en `README.md`:

1. preparar Ubuntu 24
2. construir el baseline por lotes
3. validar el baseline con `python scripts/validate_baseline.py`

En otras palabras:

- `README.md` = implementacion base y estable
- este documento = ampliacion operativa para tiempo real

Orden recomendado dentro de este documento:

1. leer `Meta De Esta Version`
2. revisar `Arquitectura Propuesta`
3. usar `Estado Actual De Implementacion`
4. aplicar `Despliegue con systemd`

## Secuencia Operativa De La Version Avanzada

Si ya validaste el baseline y ahora quieres pasar a monitoreo continuo, sigue esta secuencia exacta:

1. entrar al proyecto y activar `.venv`
2. confirmar que el modelo baseline ya existe y esta alineado con el entorno
3. ejecutar `run_realtime_monitor.py` en modo manual
4. verificar que se crea `data/processed/ssh_monitor.db`
5. abrir la app para comprobar que ahora lee desde SQLite
6. probar reentrenamiento manual con `retrain_model.py`
7. recien despues instalar y habilitar los servicios `systemd`

Resumen de scripts de esta etapa:

- `scripts/run_realtime_monitor.py` = monitoreo continuo, parseo incremental, scoring y persistencia en SQLite
- `scripts/retrain_model.py` = reprocesa el log real y reentrena el baseline

## Flujo Avanzado Paso A Paso

La idea de esta etapa es:

1. tomar eventos reales en continuo desde `auth.log` o `journald`
2. convertirlos en eventos estructurados
3. calcular features incrementales
4. puntuar cada evento
5. guardar eventos y alertas en SQLite
6. leerlos desde la app

### Vista General Del Flujo

```text
/var/log/auth.log o journalctl -u ssh -f
  -> run_realtime_monitor.py
  -> parser incremental
  -> feature updater
  -> modelo baseline + reglas
  -> ssh_monitor.db
  -> app/app.py
```

## Antes De Ejecutar Comandos

Salvo que el comando comience por `sudo` o sea una unidad de `systemd`, los ejemplos de este documento deben ejecutarse con `.venv` activo:

```bash
cd /03-ML-deteccion-accesos-ssh
source .venv/bin/activate
```

Si vas a consultar la base SQLite desde consola, asegúrate de tener instalado `sqlite3` en Ubuntu 24:

```bash
sudo apt install -y sqlite3
```

### Paso 1: Confirmar prerequisitos de la capa avanzada

Antes de seguir, verifica que ya existe la base del proyecto:

- `models/ssh_anomaly_model.joblib`
- `models/model_metadata.json`
- `models/scored_events.csv`

Que estamos validando:

- que el baseline ya fue construido
- que la capa avanzada tendra un modelo para puntuar eventos en tiempo real

### Paso 2: Ejecutar el monitor en modo manual sobre un archivo real

Este es el primer comando que conviene probar en la version avanzada:

```bash
python scripts/run_realtime_monitor.py \
  --input-file /var/log/auth.log \
  --replay-existing \
  --follow-file
```

Que hace este comando:

- lee primero el contenido existente de `/var/log/auth.log`
- procesa cada linea SSH reconocida
- calcula features incrementales en memoria
- aplica el modelo baseline y las reglas hibridas
- guarda eventos en `ssh_events`
- guarda alertas en `ssh_alerts`
- sigue escuchando nuevas lineas del mismo archivo

Resultado esperado:

- se crea `data/processed/ssh_monitor.db`
- aparecen datos en las tablas `ssh_events` y `ssh_alerts`

### Paso 3: Alternativa con journald

Si prefieres que la fuente principal sea `systemd`, usa:

```bash
python scripts/run_realtime_monitor.py \
  --follow-journal
```

Que hace este comando:

- se conecta a `journalctl -u ssh -f -o short-iso`
- toma eventos nuevos de SSH a medida que aparecen
- los procesa igual que en el modo archivo
- guarda resultados en SQLite

Cuando usarlo:

- cuando quieres un modo mas alineado con Ubuntu 24 y `systemd`
- cuando no quieres depender de leer directamente `/var/log/auth.log`

### Paso 4: Verificar resultados en la app

Una vez el monitor ya este escribiendo en SQLite, levanta la app:

```bash
streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501
```

Que estamos haciendo:

- comprobando que la app detecta `data/processed/ssh_monitor.db`
- confirmando que la interfaz ya no lee solo `scored_events.csv`
- revisando eventos y alertas recientes desde SQLite

### Paso 5: Reentrenamiento manual

Cuando quieras refrescar el modelo con el log real actual del servidor:

```bash
python scripts/retrain_model.py \
  --input-log /var/log/auth.log
```

Que hace este comando:

- vuelve a parsear el log real
- vuelve a generar `ssh_events.csv`
- vuelve a generar `ssh_features.csv`
- reentrena `Isolation Forest`
- actualiza `models/ssh_anomaly_model.joblib`
- actualiza `models/model_metadata.json`
- deja un resumen en `models/retrain_summary.json`

Cuando usarlo:

- despues de instalar dependencias por primera vez
- cuando cambiaste de version de `scikit-learn`
- cuando quieres refrescar el baseline con datos mas recientes

### Paso 6: Pasar a systemd

Solo cuando ya validaste manualmente los pasos anteriores, instala las unidades de `systemd`.

## Operacion Del Sistema

Esta es la parte practica una vez ya creaste el servicio.

### 1. Iniciar y dejar habilitado el monitor

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ssh-ml-monitor.service
```

Que hace:

- recarga las unidades de `systemd`
- arranca el monitor ahora mismo
- deja el servicio habilitado para futuros reinicios

### 2. Ver si el servicio esta corriendo

```bash
sudo systemctl status ssh-ml-monitor.service
```

Que debes buscar:

- estado `active (running)`
- que no aparezcan errores de Python
- que el `ExecStart` apunte al proyecto correcto

Si quieres una salida corta:

```bash
systemctl is-active ssh-ml-monitor.service
```

Resultado esperado:

- debe responder `active`

### 3. Ver los logs del servicio

```bash
journalctl -u ssh-ml-monitor.service -n 50 --no-pager
```

Para seguirlo en vivo:

```bash
journalctl -u ssh-ml-monitor.service -f
```

Esto sirve para:

- ver si el script arranco
- detectar errores de modelo, permisos o rutas
- comprobar si el monitor esta procesando eventos nuevos

### 4. Ver si ya se creo la base SQLite

```bash
ls -lh /03-ML-deteccion-accesos-ssh/data/processed/ssh_monitor.db
```

Que significa:

- si el archivo existe, el monitor ya esta persistiendo datos
- si no existe, el servicio arranco mal o aun no proceso eventos SSH reconocidos

### 5. Ver si la base tiene eventos y alertas

Si tienes `sqlite3` instalado:

```bash
sqlite3 /03-ML-deteccion-accesos-ssh/data/processed/ssh_monitor.db "SELECT COUNT(*) FROM ssh_events;"
sqlite3 /03-ML-deteccion-accesos-ssh/data/processed/ssh_monitor.db "SELECT COUNT(*) FROM ssh_alerts;"
```

Tambien puedes revisar muestras:

```bash
sqlite3 /03-ML-deteccion-accesos-ssh/data/processed/ssh_monitor.db "SELECT timestamp, source_ip, username, ssh_event_type, auth_result FROM ssh_events ORDER BY id DESC LIMIT 10;"
sqlite3 /03-ML-deteccion-accesos-ssh/data/processed/ssh_monitor.db "SELECT created_at, source_ip, username, prediction_label, reason_summary FROM ssh_alerts ORDER BY id DESC LIMIT 10;"
```

Que estas comprobando:

- que el monitor si esta guardando eventos
- que las reglas o el modelo estan generando alertas

### 6. Ver el sistema desde la app

Con `.venv` activo:

```bash
cd /03-ML-deteccion-accesos-ssh
source .venv/bin/activate
streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501
```

Abre:

- `http://IP_DEL_SERVIDOR:8501`

Que deberias ver si la capa avanzada esta funcionando:

- metricas de `Eventos`, `Fallos`, `Exitos` y `Alertas`
- tabla `Top IPs por alertas`
- tabla `Alertas recientes`
- tabla `Eventos recientes`

Importante:

- si existe `data/processed/ssh_monitor.db`, la app prioriza SQLite
- si no existe, vuelve al modo baseline con `scored_events.csv`

### 7. Reiniciar o detener el servicio

Reiniciar:

```bash
sudo systemctl restart ssh-ml-monitor.service
```

Detener:

```bash
sudo systemctl stop ssh-ml-monitor.service
```

Deshabilitar:

```bash
sudo systemctl disable ssh-ml-monitor.service
```

### 8. Habilitar el reentrenamiento periodico

Cuando el monitor ya este estable, activa el timer:

```bash
sudo systemctl enable --now ssh-ml-retrain.timer
```

Ver estado:

```bash
sudo systemctl status ssh-ml-retrain.timer
systemctl list-timers --all | grep ssh-ml-retrain
```

Ver el ultimo reentrenamiento:

```bash
journalctl -u ssh-ml-retrain.service -n 50 --no-pager
```

### 9. Flujo minimo de verificacion en produccion o laboratorio

Si quieres comprobar rapido que todo esta bien, usa esta secuencia:

```bash
sudo systemctl status ssh-ml-monitor.service
ls -lh /03-ML-deteccion-accesos-ssh/data/processed/ssh_monitor.db
sqlite3 /03-ML-deteccion-accesos-ssh/data/processed/ssh_monitor.db "SELECT COUNT(*) FROM ssh_events;"
sqlite3 /03-ML-deteccion-accesos-ssh/data/processed/ssh_monitor.db "SELECT COUNT(*) FROM ssh_alerts;"
journalctl -u ssh-ml-monitor.service -n 20 --no-pager
```

Si esos pasos salen bien, el sistema ya esta ejecutandose.

## Contexto

En Ubuntu 24, `systemd` y `journald` son piezas centrales del sistema. Aunque `auth.log` puede seguir existiendo, una estrategia moderna de observabilidad debe contemplar:

- lectura directa desde `journalctl`
- servicios persistentes con `systemd`
- timers o demonios propios para procesamiento continuo

## Meta De Esta Version

Pasar de un pipeline manual por lotes a un flujo continuo:

```text
journalctl -u ssh -f
    -> parser
    -> feature updater
    -> scoring ML
    -> persistencia de alertas
    -> dashboard
    -> respuesta defensiva gradual
```

## Arquitectura Propuesta

### 1. Colector En Tiempo Real

Fuente recomendada:

```bash
journalctl -u ssh -f -o short-iso
```

Ventajas:

- formato consistente para Ubuntu 24
- no depende de copiar archivos
- permite seguir eventos nuevos en tiempo real

Responsabilidad:

- leer nuevas lineas del journal
- entregarlas al parser una por una o en micro-lotes

### 2. Parser Continuo

El parser debe:

- reconocer eventos SSH relevantes
- ignorar lineas irrelevantes
- producir eventos estructurados

Eventos minimos:

- `Accepted password`
- `Failed password`
- `Invalid user`
- apertura de sesion `pam_unix(sshd:session)`

Salida sugerida:

- eventos en memoria
- y opcionalmente persistidos en SQLite o CSV rotativo

### 3. Feature Updater Incremental

En vez de recalcular todo el dataset completo, el sistema puede mantener estructuras temporales para:

- conteo de fallos por IP
- conteo de usuarios por IP
- conteo de IPs por usuario
- ratio de fallos/exitos
- ventanas de 1, 5 y 15 minutos

Tecnicas recomendadas:

- `deque` por IP y por usuario
- diccionarios en memoria
- limpieza por expiracion de ventana

Nota breve:

- `deque` es una estructura de Python tipo cola doble (`double-ended queue`) que permite agregar eventos nuevos al final y eliminar rapido los mas antiguos del inicio, algo util para mantener ventanas de tiempo como 1, 5 o 15 minutos sin recalcular todo el historial

Beneficio:

- menor costo computacional
- respuesta casi inmediata

### 4. Motor De Scoring

Dos enfoques:

#### A. Modelo ML

Aplicar el modelo baseline entrenado a cada nuevo evento o micro-lote.

Salida:

- `risk_score`
- `prediction_label`

#### B. Reglas Deterministicas

Aplicar reglas simples de seguridad operativa.

Ejemplos:

- demasiados fallos desde una misma IP
- demasiados usuarios distintos desde una misma IP
- login exitoso despues de una rafaga de fallos
- acceso administrativo fuera de horario

#### C. Enfoque Hibrido

Es el recomendado:

- reglas estaticas para condiciones claras
- score ML para priorizacion adicional

## Persistencia De Resultados

Para una version operativa, conviene dejar de depender solo de CSV.

Opciones:

- SQLite para laboratorio simple
- PostgreSQL si el proyecto crece

Tablas sugeridas:

- `ssh_events`
- `ssh_alerts`
- `response_actions`

Campos utiles en `ssh_alerts`:

- `created_at`
- `source_ip`
- `username`
- `risk_score`
- `prediction_label`
- `reason_summary`
- `rule_hits`
- `status`

## Dashboard En Tiempo Real

La app puede evolucionar para leer de una base de datos o de un archivo de alertas actualizado continuamente.

Vistas recomendadas:

- alertas recientes
- top IPs sospechosas
- top usuarios atacados
- detalle por alerta
- historial de eventos de una IP
- historial de bloqueos preventivos

## Respuesta Preventiva Gradual

La respuesta automatica no debe empezar con bloqueos agresivos. Se recomienda una evolucion por niveles.

### Nivel 1: Observacion

- guardar evento
- calcular score
- mostrar en dashboard

### Nivel 2: Alerta

- guardar alerta
- etiquetar como `review` o `high_risk`

### Nivel 3: Cuarentena Temporal

- agregar IP a una lista temporal
- generar una accion sugerida

### Nivel 4: Bloqueo Automatizado

Posibles integraciones:

- `fail2ban`
- `ufw`
- `nftables`
- `ipset`

## Condiciones Sugeridas Para Respuesta

Ejemplos de politicas hibridas:

- `failed_count_5m >= 8`
- `user_count_per_ip_5m >= 4`
- `risk_score >= umbral_alto`
- `sin exitos y actividad persistente`

Ejemplo de criterio combinado:

```text
Si una IP tiene 8 o mas fallos en 5 minutos
y prueba 4 o mas usuarios distintos
y el modelo la marca como high_risk
entonces generar alerta de alta prioridad
```

## Integracion Con systemd

En esta seccion hay dos piezas distintas. No hacen lo mismo y no compiten entre si; normalmente se usan juntas.

Idea general:

- una cosa es monitorear eventos nuevos en tiempo real
- otra cosa es reentrenar el modelo cada cierto tiempo

Diferencia corta:

- `Servicio Residente` = proceso siempre encendido para vigilar eventos nuevos
- `Timer De Reentrenamiento` = tarea programada que se ejecuta en momentos definidos para refrescar el modelo

En otras palabras:

- el servicio observa
- el timer mantiene actualizado el modelo

Ejemplo practico:

- `ssh-ml-monitor.service` corre todo el tiempo y escribe alertas nuevas en SQLite
- `ssh-ml-retrain.timer` dispara `ssh-ml-retrain.service` cada cierto intervalo para volver a entrenar el baseline

Por que conviene separarlos:

- el monitoreo continuo debe ser ligero y estable
- el reentrenamiento consume mas CPU y cambia artefactos del modelo
- separar ambas funciones evita mezclar una tarea de observacion permanente con una tarea periodica de mantenimiento

Secuencia recomendada:

1. primero levantar el servicio residente
2. validar que genera eventos y alertas
3. despues activar el timer de reentrenamiento

Si solo habilitas el servicio:

- tendras monitoreo y alertas
- pero el modelo no se refrescara automaticamente

Si solo habilitas el timer:

- el modelo se reentrenara periodicamente
- pero no tendras monitoreo continuo ni alertas en tiempo real

Por eso, en una version operativa completa, ambos componentes se complementan.

### Opcion A: Servicio Residente

Crear un servicio del tipo:

- `ssh-ml-monitor.service`

Responsabilidad:

- arrancar el proceso de monitoreo continuo
- leer `journalctl -u ssh -f`
- procesar eventos

### Opcion B: Timer De Reentrenamiento

Crear un timer del tipo:

- `ssh-ml-retrain.timer`

Responsabilidad:

- reentrenar el modelo cada cierto tiempo
- por ejemplo diario o semanal

### Archivos Esperados En Una Version Futura

- `scripts/run_realtime_monitor.py`
- `scripts/retrain_model.py`
- `deploy/systemd/ssh-ml-monitor.service`
- `deploy/systemd/ssh-ml-retrain.service`
- `deploy/systemd/ssh-ml-retrain.timer`

## Recomendacion De Implementacion

Orden sugerido:

1. crear `run_realtime_monitor.py`
2. persistir alertas en SQLite
3. adaptar `app.py` para leer alertas persistidas
4. agregar servicio `systemd`
5. agregar reglas hibridas de respuesta
6. solo despues evaluar bloqueos automatizados

## Estado Actual De Implementacion

Ya se implemento una primera base funcional de esta version avanzada:

- `scripts/run_realtime_monitor.py`
- persistencia en SQLite en `data/processed/ssh_monitor.db`
- lectura de alertas persistidas desde `app/app.py`

Capacidades actuales:

- reprocesar un archivo existente con `--replay-existing`
- seguir un archivo en crecimiento con `--follow-file`
- seguir eventos reales de `journalctl` con `--follow-journal`
- guardar eventos SSH en `ssh_events`
- guardar alertas en `ssh_alerts`
- aplicar reglas hibridas simples junto con el modelo baseline

### Despliegue con systemd

Los archivos ya quedaron creados en `deploy/systemd/`:

- `ssh-ml-monitor.service`
- `ssh-ml-retrain.service`
- `ssh-ml-retrain.timer`

Instalacion sugerida:

```bash
sudo cp deploy/systemd/ssh-ml-monitor.service /etc/systemd/system/
sudo cp deploy/systemd/ssh-ml-retrain.service /etc/systemd/system/
sudo cp deploy/systemd/ssh-ml-retrain.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now ssh-ml-monitor.service
sudo systemctl enable --now ssh-ml-retrain.timer
```

Que estamos haciendo:

- instalando el monitor continuo como servicio persistente
- habilitando un timer para reentrenamiento periodico
- dejando la version avanzada operando al arranque del servidor

Verificacion operativa:

```bash
sudo systemctl status ssh-ml-monitor.service
sudo systemctl status ssh-ml-retrain.timer
journalctl -u ssh-ml-monitor.service -n 50 --no-pager
journalctl -u ssh-ml-retrain.service -n 50 --no-pager
```

## Riesgos Operativos

- falsos positivos que bloqueen administradores legitimos
- sobreajuste del modelo a un laboratorio pequeno
- logs incompletos o contaminados
- decisiones automáticas sin contexto suficiente

## Buenas Practicas

- mantener lista blanca de IPs administrativas
- registrar toda accion automatica
- no bloquear solo por score ML
- exigir combinacion de score y regla
- revisar alertas antes de activar respuestas duras

## Trabajo Futuro

- monitoreo continuo sobre `journalctl -u ssh -f`
- almacenamiento en SQLite o PostgreSQL
- modo stream para `app.py`
- reglas hibridas configurables
- servicio `systemd` para el monitor
- timer `systemd` para reentrenamiento
- integracion controlada con `fail2ban` o `ufw`
