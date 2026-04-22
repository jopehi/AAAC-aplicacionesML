# Matriz De Superficies De Riesgo

## Objetivo

Documentar los puntos de entrada y acciones sensibles de la aplicacion para revisiones de seguridad, endurecimiento gradual y ejercicios posteriores de deteccion. Esta matriz no describe tecnicas de explotacion; describe superficies, impacto y evidencia observable.

## Leyenda

- `GET lectura`: parametro usado para consultar o precargar datos
- `GET accion`: parametro usado para ejecutar cambios de estado o borrados
- `POST formulario`: envio de formularios de creacion, edicion o autenticacion
- `Riesgo bajo`: la ruta ya usa controles razonables y prepared statements
- `Riesgo medio`: la ruta funciona, pero tiene debilidades de diseno o defensa insuficiente
- `Riesgo alto`: la ruta mezcla accion sensible y control insuficiente, o expone un patron claramente fragil

## Superficies Principales

| Ruta | Entrada | Tipo | Accion | Riesgo | Observacion | Evidencia esperada |
|---|---|---|---|---|---|---|
| `login.php` | `POST username,password` | POST formulario | autenticacion | medio | No hay CSRF ni rate limiting. La consulta usa prepared statement. | `login`, `login_failed` en `activity_logs` |
| `logout.php` | acceso directo | GET accion | cierre de sesion | bajo | Es una accion simple pero sigue siendo disparable por GET. | `logout` en `activity_logs` |
| `dashboard.php` | `POST action=new_transaction` | POST formulario | deposito/retiro | medio | Tiene prepared statements y validacion basica, pero no tiene CSRF ni controles avanzados de sesion. | `transaction_deposit`, `transaction_withdraw` |
| `admin/dashboard.php` | acceso directo | GET lectura | lectura de metricas y logs | medio | Requiere rol admin. Usa una consulta de conteo con nombre de tabla concatenado en codigo. | consultas visibles y navegacion admin |
| `admin/clients/index.php?edit=` | `GET edit` | GET lectura | precarga de cliente | bajo | Ruta de lectura para editar. Requiere admin. | navegacion y futuras trazas de consulta si se agregan |
| `admin/clients/index.php?delete=` | `GET delete` | GET accion | elimina cliente | alto | Accion destructiva por GET. No hay token CSRF. | `delete` sobre `clients` |
| `admin/clients/index.php` | formulario alta/edicion | POST formulario | crea/edita cliente | medio | Prepared statements, pero sin CSRF. | `create`, `update` sobre `clients` |
| `admin/products/index.php?edit=` | `GET edit` | GET lectura | precarga de producto | bajo | Ruta de lectura para editar. | navegacion admin |
| `admin/products/index.php?delete=` | `GET delete` | GET accion | elimina producto | alto | Accion destructiva por GET. No hay token CSRF. | `delete` sobre `products` |
| `admin/products/index.php` | formulario alta/edicion | POST formulario | crea/edita producto | medio | Prepared statements, pero sin CSRF. | `create`, `update` sobre `products` |
| `admin/users/index.php?client_id=` | `GET client_id` | GET lectura | precarga cliente para crear acceso | bajo | Uso de conveniencia, no ejecuta cambios. | navegacion admin |
| `admin/users/index.php?edit=` | `GET edit` | GET lectura | precarga usuario | bajo | Prepared statement y rol admin. | navegacion admin |
| `admin/users/index.php?delete=` | `GET delete` | GET accion | elimina usuario | alto | Accion destructiva por GET. No hay token CSRF. | `delete` sobre `users` |
| `admin/users/index.php` | formulario alta/edicion | POST formulario | crea/edita usuario | medio | Prepared statements y validaciones de unicidad basicas, pero sin CSRF. | `create`, `update` sobre `users` |
| `admin/accounts/index.php?client_id=` | `GET client_id` | GET lectura | filtro por cliente | bajo | Solo filtra resultados. | navegacion admin |
| `admin/accounts/index.php?edit=` | `GET edit` | GET lectura | precarga producto de cliente | bajo | Prepared statement y rol admin. | navegacion admin |
| `admin/accounts/index.php?toggle=&status=` | `GET accion` | GET accion | abre/cierra producto | alto | Cambio de estado por GET. No hay token CSRF. | `open_product`, `close_product` |
| `admin/accounts/index.php` | formulario alta/edicion | POST formulario | asigna o actualiza producto de cliente | medio | Tiene controles basicos de datos y prepared statements, pero sin CSRF. | `create`, `update` sobre `client_products` |

## Debilidades Transversales

### 1. Acciones sensibles por GET

Archivos implicados:

- `admin/clients/index.php`
- `admin/products/index.php`
- `admin/users/index.php`
- `admin/accounts/index.php`

Riesgo:

- disparo accidental o inducido de acciones destructivas
- falta de intencionalidad fuerte en cambios de estado y borrados

Deteccion futura:

- secuencias inusuales de `delete`
- aperturas o cierres masivos de productos
- patrones anormales por IP o usuario admin

### 2. Falta de CSRF en formularios y acciones

Archivos implicados:

- login
- dashboard cliente
- todos los modulos admin con formularios

Riesgo:

- envios no intencionales si el navegador mantiene sesion valida

Deteccion futura:

- cambios administrativos sin flujo de navegacion previo coherente
- multiples acciones seguidas sin tiempos normales de uso

### 3. Manejo basico de sesion

Archivos implicados:

- `includes/auth.php`
- `login.php`

Riesgo:

- no hay regeneracion explicita de sesion al autenticar
- no hay expiracion por inactividad
- no hay endurecimiento visible de cookie de sesion

Deteccion futura:

- reuso sospechoso de sesiones
- saltos de comportamiento entre rutas y perfiles

### 4. Secretos en codigo

Archivos implicados:

- `config/database.php`
- referencias documentales del proyecto

Riesgo:

- exposicion de credenciales
- uso de `root` como cuenta de aplicacion

Deteccion futura:

- esto no se detecta por logs de aplicacion; se detecta por revision de configuracion y repositorio

### 5. Patron mixto de acceso a base de datos

Estado actual:

- varias rutas sensibles ya usan `mysqli_prepare`
- aun existen rutas con `mysqli_query` y logica pegada a la capa de vista

Riesgo:

- deuda tecnica que facilita introducir vulnerabilidades al crecer
- consistencia desigual entre modulos

Deteccion futura:

- mas de codigo que de logs; conviene rastrear commits y revisiones

## Priorizacion Recomendada

### Prioridad 1

- migrar acciones destructivas de `GET` a `POST`
- agregar tokens CSRF

### Prioridad 2

- endurecer sesiones
- eliminar credenciales hardcodeadas
- reemplazar `root` por un usuario MySQL dedicado

### Prioridad 3

- unificar acceso a datos en una capa comun
- instrumentar mejor las consultas de lectura administrativa

## Uso En El Laboratorio

Esta matriz sirve para:

- explicar por que una ruta es mas sensible que otra
- decidir que eventos deben quedar en logs
- construir reglas de deteccion por comportamiento
- justificar prioridades de remediacion sin necesidad de explotar la app

