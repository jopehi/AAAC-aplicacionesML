# AAAC-aplicacionesML

Este repositorio esta orientado a apoyar el desarrollo del componente practico del curso `Aprendizaje automatico aplicado a ciberseguridad`.

La idea general es contar con recursos de laboratorio que permitan:

- generar datos y ruido controlado
- observar eventos de seguridad en entornos reales o semisimulados
- construir prototipos de analitica y deteccion con machine learning
- documentar procesos reproducibles para que otras personas puedan recrear los ejercicios

## Alcance

Este repositorio debe entenderse como una idea inicial de trabajo, no como una solucion cerrada.

Cada laboratorio, cada institucion y cada necesidad tecnica puede requerir:

- nuevos flujos de datos
- cambios en infraestructura
- otras tecnicas de deteccion
- diferentes niveles de automatizacion
- nuevas funcionalidades en interfaz, respuesta o monitoreo

Por eso, el contenido actual sirve como base de partida para evolucionar segun el contexto del curso o del laboratorio.

## Estructura General

Actualmente el repositorio se organiza en tres carpetas principales.

### 1. `01-fintech`

Contiene una aplicacion web de laboratorio construida con PHP y MySQL.

Su objetivo es servir como sistema de practica para:

- revisar conceptos de diseno y construccion de software
- observar autenticacion, sesiones, productos, transacciones y logs
- analizar superficies de riesgo y trazabilidad
- generar datos utiles para ejercicios de deteccion y comportamiento de usuarios

Incluye:

- portal publico de una fintech ficticia
- acceso de clientes
- panel administrativo
- auditoria y visualizacion de logs
- documentacion de hallazgos, matriz de riesgo y scoreboard

Esta carpeta funciona como base para ejercicios de analisis de aplicaciones y generacion de eventos.

### 2. `02-lab_hydra`

Contiene material de laboratorio para generar ruido controlado en un entorno autorizado.

Su funcion principal es apoyar ejercicios de:

- observacion de intentos de autenticacion
- recoleccion de evidencia en logs
- analisis de patrones repetitivos
- correlacion de actividad sospechosa

Esta carpeta debe usarse solo en laboratorios controlados y autorizados, con enfoque educativo y defensivo.

Su valor dentro del repositorio es servir como fuente de datos y actividad observable para otros componentes practicos del curso.

### 3. `03-ML-deteccion-accesos-ssh`

Contiene un proyecto de deteccion de accesos SSH anómalos con machine learning.

Su objetivo es mostrar un camino reproducible para:

- parsear logs SSH
- estructurar eventos
- generar features
- entrenar un baseline con `Isolation Forest`
- mostrar resultados en una interfaz web
- evolucionar a monitoreo continuo con `systemd`, SQLite y respuesta operativa

Incluye:

- pipeline baseline por lotes
- validacion del baseline
- monitor continuo
- persistencia en SQLite
- interfaz Streamlit
- documentacion operativa y tecnica

Esta carpeta representa la linea mas cercana al componente de aprendizaje automatico aplicado a ciberseguridad dentro del repositorio.

## Forma De Uso Recomendada

La recomendacion general es trabajar por capas:

1. entender el laboratorio o sistema fuente
2. generar o capturar eventos observables
3. estructurar datos
4. construir una primera deteccion baseline
5. iterar con nuevas reglas, modelos y automatizaciones

## Nota Final

El repositorio esta pensado para crecer.

Lo que hoy aparece como una base funcional puede evolucionar hacia:

- mas fuentes de datos
- nuevas tecnicas de ML
- mejores interfaces
- integracion con respuesta automatizada
- ejercicios mas avanzados para clase

La idea no es cerrar el problema, sino ofrecer una plataforma inicial de trabajo practico sobre la cual seguir construyendo.
