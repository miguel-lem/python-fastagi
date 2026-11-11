# Ejemplo básico de FastAGI con audios en Asterisk

`08_conexionagi.py` es un ejemplo **básico** para empezar a trabajar con audios en llamadas de Asterisk usando FastAGI. Contesta la llamada, reproduce un audio de menú, espera un dígito del usuario y reproduce otro audio según la opción elegida.

## Requisitos importantes

1. **El script debe ejecutarse dentro del servidor de Asterisk** (o en una máquina alcanzable por red desde él). Debes copiarlo al servidor, tener Python 3 instalado y dejarlo corriendo. Asterisk se conecta a él vía FastAGI (TCP).
2. **Los audios ya deben estar cargados en la carpeta de sonidos de Asterisk**, normalmente:

   ```
   /var/lib/asterisk/sounds/
   ```

   (o una subcarpeta, por ejemplo `/var/lib/asterisk/sounds/es/` o `/var/lib/asterisk/sounds/custom/`). El script **no sube ni convierte audios**: solo ordena a Asterisk reproducir archivos que ya existen.
3. Los audios deben estar en un formato que Asterisk entienda (`.wav` 8 kHz, 16 bit, mono, `.gsm`, `.sln`, `.ulaw`, `.alaw`, etc.).
4. Al referenciarlos **no se escribe la extensión**: `menu_principal` y no `menu_principal.wav`. Si están en una subcarpeta, se indica la ruta relativa: `custom/menu_principal`.

## Cómo funciona

```
Llamada ──► Asterisk ──(AGI)──► Script Python (puerto 4573)
                 ▲                      │
                 └──── comandos AGI ────┘
          (ANSWER, STREAM FILE, WAIT FOR DIGIT, HANGUP)
```

Flujo del script:

1. Lee el entorno AGI que envía Asterisk.
2. Contesta la llamada (`ANSWER`).
3. Lee las variables `AUDIO`, `AUDIO1`, `AUDIO2`, `AUDIO3`, `AUDIO4`, `AUDIO1_1` y `AUDIO1_2` (nombres de audios, sin extensión).
4. Reproduce `AUDIO` (menú principal) y espera un dígito.
5. Según el dígito:

| Tecla | Acción |
|-------|--------|
| `1` | Reproduce `AUDIO1` y espera un segundo dígito: `1` → `AUDIO1_1`, `2` → `AUDIO1_2`, otro → `AUDIO4` |
| `2` | Reproduce `AUDIO2` |
| `3` | Reproduce `AUDIO3` |
| otra / sin tecla | Reproduce `AUDIO4` (opción inválida) |

6. Cuelga la llamada (`HANGUP`).

## Instalación y ejecución

1. Copia `08_conexionagi.py` al servidor Asterisk.
2. Edita la IP y el puerto al final del archivo:

   ```python
   server = ThreadedTCPServer(("192.168.0.144", 4573), FastAGIHandler)
   ```

   - Usa la IP del servidor donde corre el script (o `"127.0.0.1"` si corre en el mismo Asterisk, o `"0.0.0.0"` para escuchar en todas las interfaces).
3. Ejecútalo (solo usa la librería estándar de Python, no hay que instalar nada):

   ```bash
   python3 08_conexionagi.py
   ```

   Debe mostrar: `Servidor FastAGI corriendo en puerto 4573 (multicliente)...`
4. Abre el puerto 4573 en el firewall si Asterisk y el script están en máquinas distintas.

## Configuración del dialplan de Asterisk

En `extensions.conf` (o el archivo de dialplan que uses), define las variables con los nombres de tus audios y llama al script con `AGI(agi://IP:PUERTO)`:

```ini
[menu-audios]
exten => 100,1,NoOp(Menu de audios FastAGI)
 same => n,Set(AUDIO=custom/menu_principal)
 same => n,Set(AUDIO1=custom/submenu_1)
 same => n,Set(AUDIO2=custom/opcion_2)
 same => n,Set(AUDIO3=custom/opcion_3)
 same => n,Set(AUDIO4=custom/opcion_invalida)
 same => n,Set(AUDIO1_1=custom/opcion_1_1)
 same => n,Set(AUDIO1_2=custom/opcion_1_2)
 same => n,AGI(agi://192.168.0.144:4573)
 same => n,Hangup()
```

Recarga el dialplan:

```bash
asterisk -rx "dialplan reload"
```

> Las variables también pueden venir desde AMI (por ejemplo en un `Originate`), siempre que se definan en el canal antes de ejecutar el AGI.

## Prueba rápida

Para verificar que todo funciona antes de usar tus audios, descomenta estas líneas en el script y usa el audio de ejemplo que trae Asterisk:

```python
self.send_command('STREAM FILE hello-world ""')
self.send_command('HANGUP')
```

Llama a la extensión `100` y deberías escuchar "Hello world". Mientras tanto, puedes ver la conversación AGI en la consola del script y en la CLI de Asterisk (`asterisk -rvvv`).

## Problemas comunes

| Síntoma | Causa probable |
|---------|----------------|
| No se oye el audio | El archivo no está en la carpeta de sonidos, el nombre/ruta es incorrecto, se incluyó la extensión o el formato no es compatible |
| La llamada cae enseguida | Asterisk no logra conectar al script: revisa IP, puerto, que el script esté corriendo y el firewall |
| Variables en `None` | No se definieron con `Set()` en el dialplan antes de llamar a `AGI()` |
| `Address already in use` | Ya hay otra instancia del script usando el puerto 4573 |

## Notas

- Es un **ejemplo educativo**: no valida errores ni maneja desconexiones del usuario a mitad de la llamada.
- El servidor es multihilo (`ThreadingMixIn`), por lo que atiende varias llamadas simultáneas.
- Los `print` sirven para depurar; puedes quitarlos en producción.
