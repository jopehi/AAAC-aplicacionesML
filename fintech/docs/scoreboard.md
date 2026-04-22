# Security Review Challenge

## Objetivo

Analizar la aplicacion `Fintech Nova` y descubrir la mayor cantidad posible de debilidades de diseno, implementacion y operacion. El reto evalua capacidad de revision tecnica, priorizacion, argumentacion y criterio defensivo.

El objetivo del ejercicio no es explotar sistemas reales ni automatizar abuso. El objetivo es revisar una aplicacion local de laboratorio y producir hallazgos tecnicos bien sustentados.

## Alcance

Se evaluan:

- autenticacion
- sesion
- autorizacion
- gestion de secretos
- validacion y manejo de entrada
- acciones sensibles
- diseno de base de datos
- logging y trazabilidad
- decisiones de arquitectura insegura
- deuda tecnica que habilite fallas futuras

No se evaluan:

- denegacion de servicio real
- ataques contra terceros
- herramientas ofensivas fuera del entorno del laboratorio
- alteraciones no autorizadas del host o del entorno docente

## Reglas Del Reto

1. Trabajar solo sobre la aplicacion de laboratorio.
2. Documentar cada hallazgo con evidencia.
3. No inventar vulnerabilidades que no puedan justificarse tecnicamente.
4. Priorizar calidad sobre cantidad.
5. Relacionar, cuando sea posible, el hallazgo con su posible deteccion.

## Formato De Entrega

Cada hallazgo debe incluir:

- `ID`
- `Titulo`
- `Categoria`
- `Severidad`
- `Archivo o ruta`
- `Descripcion`
- `Impacto`
- `Evidencia`
- `Recomendacion`
- `Deteccion posible`

## Categorias Sugeridas

- autenticacion
- sesion
- autorizacion
- gestion de credenciales
- entrada y validacion
- CSRF
- manejo de errores
- logging
- base de datos
- arquitectura insegura
- hardening faltante

## Sistema De Puntos

### Hallazgos

- `5 puntos`: debilidad baja o mejora de hardening bien identificada
- `10 puntos`: debilidad media con impacto real pero acotado
- `20 puntos`: debilidad alta en acciones sensibles, autenticacion o autorizacion
- `30 puntos`: hallazgo critico, transversal o muy bien argumentado

### Bonos

- `+10 puntos`: el hallazgo incluye una idea clara de deteccion o monitoreo
- `+10 puntos`: el hallazgo conecta dos o mas modulos y demuestra impacto sistémico
- `+5 puntos`: la recomendacion de remediacion es concreta y adecuada al contexto

### Penalizaciones

- `-10 puntos`: hallazgo incorrecto o sin evidencia tecnica
- `-5 puntos`: hallazgo duplicado respecto de otro ya reportado por el mismo equipo
- `-5 puntos`: severidad inflada sin justificacion

## Niveles

- `Bronce`: 30 a 50 puntos
- `Plata`: 51 a 90 puntos
- `Oro`: 91 a 140 puntos
- `Top Score`: 141 puntos o mas con hallazgos consistentes y bien priorizados

## Criterios De Evaluacion

### 1. Calidad Tecnica

- el hallazgo es real o altamente plausible
- la explicacion es coherente
- la ubicacion en codigo es correcta

### 2. Priorizacion

- distingue entre debilidad baja, media y alta
- no trata todo como critico

### 3. Evidencia

- cita archivo, ruta, flujo o comportamiento observable
- demuestra lectura real del sistema

### 4. Capacidad Defensiva

- propone mejoras razonables
- sugiere evidencia para logs o monitoreo

## Plantilla De Hallazgo

```text
ID:
Titulo:
Categoria:
Severidad:
Archivo o ruta:
Descripcion:
Impacto:
Evidencia:
Recomendacion:
Deteccion posible:
```

## Ejemplos De Preguntas Guia

- Que acciones sensibles dependen de `GET`?
- Que formularios carecen de proteccion adicional?
- Donde hay manejo debil de sesiones?
- Que secretos o configuraciones sensibles aparecen en codigo?
- Que controles de autorizacion son demasiado simples?
- Que decisiones de arquitectura facilitan errores futuros?
- Que eventos dejan evidencia en logs y cuales no?

## Uso Recomendado Con La Matriz

Usar este documento junto con:

- [matriz-superficies-riesgo.md](C:/webdev/laragon/www/fintech/docs/matriz-superficies-riesgo.md:1)

La matriz ayuda a localizar superficies. El scoreboard ayuda a evaluar la calidad del analisis.

