# AAAC-aplicacionesML

Repositorio de laboratorio para el curso `Aprendizaje automatico aplicado a ciberseguridad`.

El objetivo es construir un entorno practico donde una aplicacion vulnerable o basica genera evidencia observable, y varios modulos de machine learning transforman esa evidencia en eventos, features, scores de riesgo e interfaces de analisis.

## Objetivo General

Este repositorio permite trabajar el ciclo completo:

1. desplegar una aplicacion de laboratorio
2. generar actividad normal y sospechosa
3. capturar logs reales del sistema
4. estructurar los eventos
5. entrenar modelos baseline
6. visualizar alertas
7. evolucionar hacia monitoreo continuo y respuesta operativa

El enfoque es educativo, defensivo y reproducible. No esta pensado para atacar sistemas de terceros.

## Estructura General

```text
AAAC-aplicacionesML/
|-- 01-fintech/
|-- 02-lab_hydra/
|-- 03-ML-deteccion-accesos-ssh/
|-- 04-ML-deteccion-accesos-weblogs/
`-- README.md
```

## 1. `01-fintech`

Aplicacion web de laboratorio construida con PHP y MySQL.

Sirve como sistema fuente para:

- practicar analisis de aplicaciones
- observar autenticacion, sesiones, clientes, cuentas, productos y administracion
- generar trazabilidad y eventos de uso
- identificar superficies de riesgo
- producir trafico web observable desde Apache

Incluye:

- portal publico
- login de clientes
- dashboard de clientes
- panel administrativo
- documentacion de arquitectura, riesgos y scoreboard
- estructura SQL base

Esta carpeta es la aplicacion que alimenta parte del laboratorio web.

## 2. `02-lab_hydra`

Material de laboratorio para generar ruido controlado en entornos autorizados.

Su funcion es apoyar ejercicios de:

- intentos de autenticacion
- observacion de patrones repetitivos
- recoleccion de evidencia
- correlacion con logs de sistema

Debe usarse solo en laboratorios propios o autorizados.

## 3. `03-ML-deteccion-accesos-ssh`

Modulo de machine learning para deteccion de accesos SSH anomalos.

Fuentes principales:

- `/var/log/auth.log`
- `journalctl -u ssh`

Capacidades:

- parseo de logs SSH
- generacion de eventos estructurados
- feature engineering por IP, usuario y ventanas temporales
- baseline con `Isolation Forest`
- scoring de eventos
- interfaz Streamlit
- validacion del baseline
- monitoreo continuo avanzado con SQLite y `systemd`
- archivos de despliegue `systemd`

Puerto recomendado de interfaz:

```text
8502
```

Documentacion principal:

```text
03-ML-deteccion-accesos-ssh/README.md
03-ML-deteccion-accesos-ssh/docs/monitoreo-tiempo-real-systemd.md
```

## 4. `04-ML-deteccion-accesos-weblogs`

Modulo de machine learning para deteccion de accesos web sospechosos en Apache.

Fuentes principales:

- `data/raw/csic_database.csv`
- `/var/log/apache2/access.log`
- `/var/log/apache2/error.log`

Capacidades:

- normalizacion del dataset CSIC 2010
- entrenamiento supervisado con `LogisticRegression + TF-IDF`
- parseo de `access.log`
- parseo de `error.log`
- scoring combinado con modelo ML y reglas explicables
- filtros por IP, etiqueta, metodo, status code, razon y fecha
- graficos de resumen
- top IPs sospechosas
- top rutas
- detalle de evento
- exportacion CSV
- dashboard Streamlit
- servicio `systemd` para el dashboard
- timer `systemd` para refrescar logs actuales cada minuto

Puerto recomendado de interfaz:

```text
8503
```

Ruta esperada en Ubuntu 24:

```text
/04-ML-deteccion-accesos-weblogs
```

Documentacion principal:

```text
04-ML-deteccion-accesos-weblogs/README.md
```

## Flujo Recomendado De Trabajo

Para un laboratorio completo, el orden sugerido es:

1. Revisar y desplegar `01-fintech`.
2. Verificar que Apache genere `access.log` y `error.log`.
3. Usar `02-lab_hydra` solo si se requiere ruido controlado autorizado.
4. Ejecutar el baseline de `03-ML-deteccion-accesos-ssh` para eventos SSH.
5. Ejecutar el baseline de `04-ML-deteccion-accesos-weblogs` para eventos web.
6. Levantar dashboards en puertos separados:

```text
SSH ML:      http://IP_DEL_SERVIDOR:8502
Weblogs ML: http://IP_DEL_SERVIDOR:8503
```

7. Activar servicios `systemd` cuando el baseline ya este validado.

## Puertos

```text
01-fintech                     Apache / puerto 80
03-ML-deteccion-accesos-ssh    Streamlit / puerto 8502
04-ML-deteccion-accesos-weblogs Streamlit / puerto 8503
```

Si `ufw` esta activo, abrir solo los puertos necesarios para el laboratorio:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 8502/tcp
sudo ufw allow 8503/tcp
sudo ufw status
```

## Datos Y Artefactos

Los modulos ML generan archivos en:

```text
data/raw/
data/processed/
models/
```

Regla practica:

- `data/raw/`: datos fuente, logs o datasets
- `data/processed/`: CSV generados por parsers y feature engineering
- `models/`: modelos entrenados, metadata y resultados puntuados

Los archivos reales de logs y datasets pueden contener informacion sensible. Revisar antes de versionar, compartir o publicar.

## Buenas Practicas

- Ejecutar los modulos en entornos virtuales `.venv` separados.
- No ejecutar dashboards como `root`.
- Usar un usuario operativo como `admon`.
- Validar permisos de lectura sobre logs antes de configurar `systemd`.
- Entrenar primero el baseline antes de activar timers o servicios.
- Revisar falsos positivos antes de automatizar acciones.
- Documentar cambios de umbrales y modelos.

## Alcance

Este repositorio no es una solucion cerrada de SIEM, WAF o EDR. Es una plataforma de laboratorio para aprender a:

- transformar logs en datos estructurados
- construir modelos baseline
- interpretar scores de riesgo
- disenar interfaces de analisis
- preparar automatizacion defensiva gradual

El siguiente paso natural es enriquecer persistencia, correlacion entre fuentes, versionado de modelos y acciones preventivas controladas.
