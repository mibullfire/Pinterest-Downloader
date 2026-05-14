#!/usr/bin/env python3
"""
Pinterest Board Downloader
Descarga tableros de Pinterest (incluyendo subtableros) usando gallery-dl.
Soporta tableros con miles de fotos en resolución original.
"""

import subprocess
import sys
import os
import json
import argparse
import shutil
from pathlib import Path


def check_gallery_dl():
    """Verifica que gallery-dl esté instalado y disponible."""
    if shutil.which("gallery-dl"):
        return "gallery-dl"

    # Buscar en ubicaciones comunes de pip
    candidates = [
        sys.executable.replace("python3", "gallery-dl").replace("python", "gallery-dl"),
        os.path.expanduser("~/.local/bin/gallery-dl"),
        "/usr/local/bin/gallery-dl",
    ]
    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    print("ERROR: gallery-dl no está instalado.")
    print("Instálalo con:  pip install gallery-dl")
    sys.exit(1)


def build_config(output_dir: str, cookies_file: str | None, threads: int = 4) -> dict:
    """Construye la configuración de gallery-dl para Pinterest."""
    config = {
        "extractor": {
            "pinterest": {
                # Siempre descargar en resolución original
                "images": "originals",
                # Incluir subtableros (secciones)
                "sections": True,
                # Nombre del archivo con metadatos para organización
                "filename": "{board[owner][username]}_{board[name]}_{num:>04}_{id}.{extension}",
                "directory": [
                    "{board[owner][username]}",
                    "{board[name]}",
                ],
                # Para subtableros, subarchivar en su propio directorio
                "section": {
                    "directory": [
                        "{board[owner][username]}",
                        "{board[name]}",
                        "{section[title]}",
                    ],
                    "filename": "{num:>04}_{id}.{extension}",
                },
            }
        },
        "downloader": {
            "http": {
                # Reintentos para tableros grandes
                "retries": 10,
                "retry-codes": [429, 500, 502, 503, 504],
                # Timeout generoso para archivos grandes
                "timeout": 60,
                # Rate limiting para evitar bloqueos
                "rate": None,
            },
            # Descargas paralelas (se configura aquí, no como flag CLI)
            "concurrent": threads,
        },
        "output": {
            "mode": "terminal",
            "progress": True,
        },
    }

    if cookies_file:
        config["extractor"]["pinterest"]["cookies"] = cookies_file

    return config


def write_config(config: dict, config_path: Path) -> None:
    """Escribe la configuración en un archivo temporal."""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def download_board(
    url: str,
    output_dir: str,
    cookies_file: str | None,
    gallery_dl_bin: str,
    extra_args: list[str],
    threads: int = 4,
) -> int:
    """Ejecuta gallery-dl para descargar un tablero."""
    config = build_config(output_dir, cookies_file, threads)
    config_path = Path(output_dir) / ".gallery-dl-pinterest.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    write_config(config, config_path)

    cmd = [
        gallery_dl_bin,
        "--config", str(config_path),
        # Directorio de destino
        "--destination", output_dir,
        # Guardar archivo de registro de URLs descargadas (evita re-descargar)
        "--download-archive", str(Path(output_dir) / ".download-archive.sqlite3"),
        # Mostrar progreso
        "--verbose",
        *extra_args,
        url,
    ]

    print(f"\n[+] Ejecutando: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n[!] Descarga interrumpida por el usuario.")
        return 1
    finally:
        # Limpiar config temporal
        if config_path.exists():
            config_path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Descarga tableros de Pinterest (con subtableros) en resolución original.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s https://www.pinterest.com/usuario/tablero/
  %(prog)s https://www.pinterest.com/usuario/tablero/ -o ./descargas
  %(prog)s https://www.pinterest.com/usuario/tablero/ --cookies cookies.txt
  %(prog)s https://www.pinterest.com/usuario/          # tablero completo del usuario
  %(prog)s urls.txt                                     # archivo con una URL por línea
        """,
    )
    parser.add_argument(
        "url",
        help="URL del tablero de Pinterest o archivo .txt con URLs (una por línea).",
    )
    parser.add_argument(
        "-o", "--output",
        default="./Pinterest",
        metavar="DIRECTORIO",
        help="Directorio de destino (por defecto: ./Pinterest)",
    )
    parser.add_argument(
        "--cookies",
        metavar="ARCHIVO",
        help=(
            "Archivo de cookies en formato Netscape (necesario para tableros privados). "
            "Exporta con la extensión 'Get cookies.txt LOCALLY' de tu navegador."
        ),
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="No guardar archivos de metadatos JSON junto a las imágenes.",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Simular descarga (listar URLs sin descargar).",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        metavar="N",
        help="Descargas paralelas (por defecto: 4).",
    )
    return parser.parse_args()


def collect_urls(url_arg: str) -> list[str]:
    """Devuelve lista de URLs: de un archivo .txt o una URL directa."""
    if os.path.isfile(url_arg):
        with open(url_arg, encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(f"[+] Cargadas {len(urls)} URLs desde '{url_arg}'")
        return urls
    return [url_arg]


def main() -> None:
    args = parse_args()
    gallery_dl_bin = check_gallery_dl()

    urls = collect_urls(args.url)
    output_dir = os.path.abspath(args.output)
    print(f"[+] Directorio de destino: {output_dir}")
    print(f"[+] gallery-dl: {gallery_dl_bin}")

    if args.cookies:
        if not os.path.isfile(args.cookies):
            print(f"ERROR: No se encontró el archivo de cookies: {args.cookies}")
            sys.exit(1)
        print(f"[+] Usando cookies: {args.cookies}")

    extra_args: list[str] = []
    if args.simulate:
        extra_args.append("--simulate")
        print("[!] Modo simulación: no se descargarán archivos.")
    if not args.no_metadata:
        extra_args.append("--write-metadata")

    failed = []
    for i, url in enumerate(urls, 1):
        if len(urls) > 1:
            print(f"\n{'='*60}")
            print(f"[{i}/{len(urls)}] {url}")
            print("=" * 60)

        code = download_board(
            url=url,
            output_dir=output_dir,
            cookies_file=args.cookies,
            gallery_dl_bin=gallery_dl_bin,
            extra_args=extra_args,
            threads=args.threads,
        )
        if code != 0:
            failed.append(url)

    print("\n" + "=" * 60)
    if failed:
        print(f"[!] {len(failed)} URL(s) fallaron:")
        for u in failed:
            print(f"    {u}")
        sys.exit(1)
    else:
        print(f"[+] Descarga completada. Archivos en: {output_dir}")


if __name__ == "__main__":
    main()
