#!/usr/bin/env python3
"""
Télécharge Tailwind, jQuery, DataTables et Alpine.js dans src/static/vendor/
pour que l'app puisse les servir elle-même (accès depuis des postes sans Internet).

À exécuter une fois sur la VM (avec Internet) :
  python scripts/download_vendor_assets.py
"""
import urllib.request
from pathlib import Path

# Répertoire de destination : src/static/vendor en local, /app/static/vendor en Docker
ROOT = Path(__file__).resolve().parent.parent
VENDOR_DIR = (ROOT / "src" / "static" / "vendor") if (ROOT / "src").exists() else (ROOT / "static" / "vendor")

ASSETS = [
    ("https://cdn.tailwindcss.com", "tailwind.js"),
    ("https://code.jquery.com/jquery-3.7.1.min.js", "jquery-3.7.1.min.js"),
    (
        "https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css",
        "jquery.dataTables.min.css",
    ),
    (
        "https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js",
        "jquery.dataTables.min.js",
    ),
    (
        "https://unpkg.com/alpinejs@3.13.3/dist/cdn.min.js",
        "alpine-3.13.3.min.js",
    ),
]


def main():
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Téléchargement des assets dans {VENDOR_DIR}...")
    for url, filename in ASSETS:
        path = VENDOR_DIR / filename
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                path.write_bytes(resp.read())
            print(f"  OK {filename}")
        except Exception as e:
            print(f"  ERREUR {filename}: {e}")
    print("Terminé. Les templates peuvent utiliser {% static 'vendor/...' %}.")


if __name__ == "__main__":
    main()
