# Tenable Report Analyser

Application web Django pour comparer deux rapports Tenable (Nessus) CSV espacés de deux semaines. Permet d’identifier les vulnérabilités patchées, non patchées et les nouveaux plugins, avec historique et export CSV.

## Fonctionnalités

- **Upload** : envoi de deux rapports CSV (ancien / nouveau) via un formulaire
- **Comparaison** : analyse des différences par triplet (Plugin ID, CVE, Host)
- **Résultats** :
  - **Patchés** : vulnérabilités présentes dans l’ancien rapport et plus dans le nouveau
  - **Non patchés** : vulnérabilités encore présentes dans le nouveau rapport
  - **Nouveaux plugins** : plugins introduits dans le nouveau rapport
- **Historique** : conservation des comparaisons avec consultation ultérieure
- **Export CSV** : téléchargement des listes (patchés, non patchés, nouveaux plugins)
- **Interface** : thème Tenable (navbar, sidebar), DataTables avec filtrage et lignes alternées

## Stack technique

- **Backend** : Django 5.x
- **Base de données** : SQLite (développement) ou PostgreSQL (Docker)
- **Frontend** : Tailwind CSS (CDN), Alpine.js, DataTables, jQuery

## Prérequis

- Python 3.11+
- Optionnel : Docker et Docker Compose pour l’exécution avec PostgreSQL

## Installation et lancement (local)

```bash
# Cloner ou se placer dans le projet
cd tenable-report-analyser

# Environnement virtuel
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # Linux / macOS

# Dépendances
pip install -r requirements.txt

# Migrations (SQLite par défaut)
cd src
python manage.py migrate
python manage.py runserver
```

Ouvrir **http://127.0.0.1:8000/**.

## Lancement avec Docker (PostgreSQL)

```bash
cd tenable-report-analyser
docker compose up --build
```

- **App** : http://localhost:8000
- **PostgreSQL** : port 5432 (utilisateur `tenable`, base `tenable_reports`)

Les variables d’environnement pour la base sont définies dans `docker-compose.yml` (`POSTGRES_*`, `SECRET_KEY`, `DEBUG`).

## Structure du projet

```
tenable-report-analyser/
├── src/
│   ├── manage.py
│   ├── tenable_web/          # Projet Django (settings, urls, wsgi)
│   ├── reports/             # App comparaison (views, models, templates)
│   ├── templates/           # Base HTML (navbar, sidebar)
│   ├── entrypoint.sh        # Attente PostgreSQL + migrate (Docker)
│   └── media/               # Fichiers uploadés (créé à l’usage)
├── compare_tenable_reports.py   # Script CLI de comparaison (hors web)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Utilisation sans accès Internet

### 1. Préparer les paquets sur une machine connectée

Sur un PC **avec** Internet, dans le dossier du projet :

```bash
# Télécharger toutes les dépendances Python (sans les installer)
pip download -r requirements.txt -d wheels
```

Copier sur la machine hors ligne : tout le projet **et** le dossier `wheels/`.

### 2. Lancer l’app sur la machine hors ligne (sans Docker)

Sur le PC **sans** Internet :

```bash
cd tenable-report-analyser

python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # Linux / macOS

# Installer depuis les wheels (aucun accès réseau)
pip install --no-index --find-links=wheels -r requirements.txt

cd src
python manage.py migrate
python manage.py runserver
```

L’app utilise **SQLite** par défaut (pas besoin de PostgreSQL ni d’Internet). Ouvrir **http://127.0.0.1:8000/**.

### 3. Accès depuis une machine sans Internet (navigateur)

Si l’app tourne sur une **VM avec Internet** et que vous y accédez depuis un **poste sans Internet** (navigateur), les assets (Tailwind, jQuery, DataTables, Alpine) doivent être servis par l’app et non par des CDN.

**Sur la VM (avec Internet), exécuter une fois :**

```bash
python scripts/download_vendor_assets.py
```

Cela télécharge les librairies dans `src/static/vendor/`. L’app les sert ensuite via `/static/vendor/...`. Les postes clients n’ont plus besoin d’accéder aux CDN.

---

## Script CLI (sans interface web)

Pour comparer deux CSV en ligne de commande et générer des CSV dans un dossier de sortie :

```bash
python compare_tenable_reports.py "chemin/ancien_rapport.csv" "chemin/nouveau_rapport.csv" -o comparison_output
```

Fichiers produits : `patched_findings.csv`, `new_findings.csv`, `per_plugin_patched.csv`, `per_plugin_not_patched.csv`, `new_plugins_details.csv`, etc.

## Licence

Usage interne / projet personnel.
