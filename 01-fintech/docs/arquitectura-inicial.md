# Fintech Lab Inseguro

## Objetivo

Construir una aplicacion web en PHP con MySQL para explicar malas practicas de diseno y construccion segura de software dentro de un entorno controlado de laboratorio. La aplicacion debe vivir solo en `localhost` y usarse con fines didacticos, analisis de trazas y ejercicios posteriores de deteccion.

## Alcance funcional inicial

- Sitio publico de presentacion de la fintech.
- Seccion de portafolio de clientes.
- Catalogo de productos.
- Propuestas de inversiones digitales.
- Autenticacion basica para panel administrativo.
- Registro de acciones para auditoria y analitica posterior.

## Modulos propuestos

### 1. Sitio publico

- `index.php`: home con hero, resumen de servicios, cifras destacadas y CTA.
- `about.php`: historia, mision, equipo y mensaje comercial.
- `clients.php`: cartera de clientes y casos de uso.
- `products.php`: productos fintech y servicios.
- `investments.php`: propuestas de inversion digital.
- `contact.php`: formulario de contacto.

### 2. Panel administrativo

- `admin/login.php`: acceso de usuarios internos.
- `admin/dashboard.php`: resumen de actividad.
- `admin/clients/`: CRUD de clientes.
- `admin/products/`: CRUD de productos.
- `admin/investments/`: CRUD de propuestas.
- `admin/users/`: gestion simple de usuarios internos.
- `admin/logs/`: consulta de eventos registrados.

### 3. Logging de acciones

Registrar eventos como:

- login exitoso
- login fallido
- logout
- consulta de registros
- creacion
- actualizacion
- eliminacion
- errores de aplicacion

Campos sugeridos:

- `id`
- `user_id`
- `username_snapshot`
- `action_type`
- `entity_type`
- `entity_id`
- `details`
- `ip_address`
- `user_agent`
- `created_at`

## Enfoque tecnico deliberadamente inseguro

El laboratorio debe incluir practicas inseguras controladas para demostrar riesgos reales. La idea no es improvisar desorden, sino aislar malas decisiones concretas para analizarlas despues.

Ejemplos de patrones a incluir mas adelante:

- consultas SQL concatenadas manualmente
- credenciales en codigo fuente
- sesiones basicas con controles minimos
- validacion insuficiente de entradas
- sanitizacion inconsistente
- manejo pobre de errores
- separacion debil entre capas
- controles de autorizacion incompletos

No conviene introducir todas las debilidades al mismo tiempo sin etiquetarlas. Cada modulo debe documentar:

- que debilidad se esta ilustrando
- donde esta ubicada
- que evidencia genera en logs
- que tecnica de deteccion podria aplicarse despues

## Base de datos

Configuracion dada:

- base de datos: `fintech`
- host: `localhost`
- puerto: `3306`
- usuario: `root`
- password: `12345`

Entidades base sugeridas:

- `users`
- `clients`
- `products`
- `investment_proposals`
- `activity_logs`
- `contact_messages`

## Estructura del proyecto

```text
fintech/
├── admin/
├── assets/
│   ├── css/
│   ├── js/
│   ├── img/
│   └── vendor/
├── config/
├── docs/
├── includes/
├── skills/
├── sql/
├── index.php
├── about.php
├── clients.php
├── products.php
├── investments.php
└── contact.php
```

## Criterios de UI

- estilo moderno y fresco
- responsive desde el inicio
- assets separados por tipo
- misma identidad visual entre sitio publico y panel

Propuesta visual inicial:

- paleta azul oscuro, cian, verde lima y neutros claros
- tipografia fuerte para titulares y una sans moderna para contenido
- cards, metricas y secciones con gradientes suaves
- layout mobile-first

## Fases recomendadas

### Fase 1

- estructura de carpetas
- layout base
- conexion MySQL
- paginas publicas
- esquema SQL inicial

### Fase 2

- login y dashboard
- CRUD de clientes, productos e inversiones
- activity log basico

### Fase 3

- datos semilla
- escenarios inseguros etiquetados
- consultas sobre logs
- material para tecnicas de deteccion

