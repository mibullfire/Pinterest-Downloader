# Pinterest Downloader

Descarga tableros de Pinterest en resolución original usando `gallery-dl` como motor de descarga. Soporta subtableros (secciones), tableros privados con cookies, y tableros con miles de imágenes con reanudación automática.

---

## Requisitos

- Python 3.10 o superior
- `gallery-dl`

### Instalación de dependencias

```bash
pip install gallery-dl
```

Verifica que la instalación fue correcta:

```bash
gallery-dl --version
```

---

## Uso básico

```bash
python3 pinterest_downloader.py <URL>
```

### Ejemplos

```bash
# Descargar un tablero
python3 pinterest_downloader.py https://www.pinterest.com/usuario/mi-tablero/

# Descargar todos los tableros de un usuario
python3 pinterest_downloader.py https://www.pinterest.com/usuario/

# Especificar carpeta de destino
python3 pinterest_downloader.py https://www.pinterest.com/usuario/tablero/ -o ~/Descargas/Pinterest

# Tablero privado (requiere cookies)
python3 pinterest_downloader.py https://www.pinterest.com/usuario/tablero/ --cookies cookies.txt

# Múltiples tableros desde un archivo de texto
python3 pinterest_downloader.py mis_tableros.txt

# Simular sin descargar (ver qué se descargaría)
python3 pinterest_downloader.py https://www.pinterest.com/usuario/tablero/ --simulate
```

---

## Opciones

| Opción | Valor por defecto | Descripción |
|---|---|---|
| `url` | — | URL del tablero o archivo `.txt` con URLs (una por línea) |
| `-o`, `--output` | `./Pinterest` | Directorio donde se guardan las imágenes |
| `--cookies` | — | Archivo de cookies para tableros privados |
| `--threads` | `4` | Número de descargas en paralelo |
| `--no-metadata` | desactivado | No guardar archivos `.json` de metadatos |
| `--simulate` | desactivado | Listar URLs sin descargar nada |

---

## Tableros privados — Cookies

Los tableros privados requieren que hayas iniciado sesión en Pinterest. Para eso necesitas exportar tus cookies del navegador.

### Pasos

1. Instala la extensión **"Get cookies.txt LOCALLY"** en [Chrome](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) o Firefox.
2. Abre Pinterest en el navegador con tu sesión iniciada.
3. Haz clic en la extensión y exporta el archivo como `cookies.txt`.
4. Pasa el archivo al script:

```bash
python3 pinterest_downloader.py https://www.pinterest.com/usuario/tablero-privado/ --cookies cookies.txt
```

> Las cookies caducan. Si ves errores de autenticación, vuelve a exportarlas.

---

## Descarga de múltiples tableros

Crea un archivo de texto con una URL por línea. Las líneas que empiezan con `#` se ignoran:

```
# Tableros de diseño
https://www.pinterest.com/usuario/tipografia/
https://www.pinterest.com/usuario/paletas-de-color/

# Tableros de fotografía
https://www.pinterest.com/otrousuario/retrato/
https://www.pinterest.com/otrousuario/paisajes/
```

Luego ejecútalo:

```bash
python3 pinterest_downloader.py mis_tableros.txt -o ~/Fotos/Pinterest
```

---

## Estructura de archivos generada

```
Pinterest/
├── usuario/
│   └── nombre-tablero/
│       ├── usuario_nombre-tablero_0001_<id>.jpg
│       ├── usuario_nombre-tablero_0002_<id>.jpg
│       ├── usuario_nombre-tablero_0001_<id>.json   ← metadatos
│       │
│       └── Subtablero Ejemplo/                     ← sección/subtablero
│           ├── 0001_<id>.jpg
│           └── 0002_<id>.jpg
├── .download-archive.sqlite3                        ← registro de descargas
```

Los archivos `.json` contienen el título del pin, descripción, URL original y otros metadatos. Elimínalos con `--no-metadata` si no los necesitas.

---

## Reanudación de descargas interrumpidas

El script genera automáticamente un archivo `.download-archive.sqlite3` en el directorio de destino. Este archivo registra cada imagen descargada. Si la descarga se interrumpe (Ctrl+C, corte de red, etc.), simplemente vuelve a ejecutar el mismo comando: las imágenes ya descargadas se saltarán.

```bash
# Primera ejecución — descarga 3000 imágenes, se interrumpe en la 1500
python3 pinterest_downloader.py https://www.pinterest.com/usuario/tablero/ -o ./fotos

# Segunda ejecución — continúa desde la 1501
python3 pinterest_downloader.py https://www.pinterest.com/usuario/tablero/ -o ./fotos
```

> El archivo de archivo está ligado al directorio de salida (`-o`). Usar un directorio diferente reinicia la descarga desde cero.

---

## Configuración interna

El script genera automáticamente una configuración temporal de `gallery-dl` con los siguientes parámetros para Pinterest:

| Parámetro | Valor | Efecto |
|---|---|---|
| `images` | `originals` | Descarga siempre la resolución más alta disponible |
| `sections` | `True` | Incluye subtableros (secciones) del tablero |
| `retries` | `10` | Reintentos automáticos en errores de red |
| `retry-codes` | `429, 500-504` | Reintenta en rate limit y errores del servidor |
| `timeout` | `60s` | Tiempo de espera por archivo antes de reintentar |

### Configuración avanzada de gallery-dl

Si necesitas ajustes adicionales (proxies, rate limiting manual, filtros de formato, etc.), puedes crear un archivo `gallery-dl.conf` en tu directorio home y `gallery-dl` lo cargará automáticamente junto a la configuración del script.

Documentación completa: https://github.com/mikf/gallery-dl#configuration

---

## Solución de problemas

### `gallery-dl no está instalado`
```bash
pip install gallery-dl
# o si tienes múltiples versiones de Python:
pip3 install gallery-dl
```

### Error 401 / imágenes no descargadas en tableros privados
Las cookies han caducado o no son válidas. Vuelve a exportarlas desde el navegador con sesión activa en Pinterest.

### Error 429 (Too Many Requests)
Pinterest está limitando las peticiones. El script reintenta automáticamente, pero puedes reducir los hilos:
```bash
python3 pinterest_downloader.py <URL> --threads 1
```

### Las imágenes no son la resolución más alta
Asegúrate de usar `gallery-dl` versión 1.27 o superior:
```bash
gallery-dl --version
pip install --upgrade gallery-dl
```

---

## Notas

- Pinterest requiere autenticación para ver ciertos contenidos incluso si son públicos. Si faltan imágenes, prueba con `--cookies`.
- Los subtableros (secciones) se descargan en subdirectorios separados automáticamente.
- El script es compatible con macOS, Linux y Windows (con Python instalado).
