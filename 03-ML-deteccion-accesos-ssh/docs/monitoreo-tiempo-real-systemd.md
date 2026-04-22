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

Ejemplo de uso con archivo real:

```bash
python scripts/run_realtime_monitor.py \
  --input-file /var/log/auth.log \
  --replay-existing \
  --follow-file
```

Ejemplo de uso con `journald`:

```bash
python scripts/run_realtime_monitor.py \
  --follow-journal
```

Ejemplo de reentrenamiento manual:

```bash
python scripts/retrain_model.py \
  --input-log /var/log/auth.log
```

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
