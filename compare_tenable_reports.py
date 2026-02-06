import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


FindingKey = Tuple[str, Optional[str], str]  # (plugin_id, cve, host)


def load_report(path: Path) -> Tuple[List[dict], Set[FindingKey], Dict[FindingKey, dict],
                                     Set[str], Set[str], Set[str],
                                     Dict[str, Set[str]]]:
    """
    Charge un rapport Tenable (CSV) et retourne :
    - lignes (list[dict])
    - findings_keys (set[(plugin_id, cve, host)])
    - key -> ligne (dict)
    - plugins (set[str])
    - cves (set[str])
    - hosts (set[str])
    - cve_hosts (dict[cve] -> set[host])
    """
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows: List[dict] = []
        findings_keys: Set[FindingKey] = set()
        key_to_row: Dict[FindingKey, dict] = {}
        plugins: Set[str] = set()
        cves: Set[str] = set()
        hosts: Set[str] = set()
        cve_hosts: Dict[str, Set[str]] = defaultdict(set)

        for row in reader:
            # Normalisation basique
            plugin_id = (row.get("Plugin ID") or "").strip()
            host = (row.get("Host") or "").strip()
            cve_raw = (row.get("CVE") or "").strip()
            cve = cve_raw or None

            if not plugin_id or not host:
                # Lignes incomplètes : on les ignore pour la comparaison
                continue

            key: FindingKey = (plugin_id, cve, host)

            rows.append(row)
            findings_keys.add(key)
            # Pour les différences, on veut pouvoir retrouver la ligne source
            key_to_row[key] = row

            plugins.add(plugin_id)
            hosts.add(host)
            if cve:
                cves.add(cve)
                cve_hosts[cve].add(host)

    return rows, findings_keys, key_to_row, plugins, cves, hosts, cve_hosts


def write_csv(output_path: Path, fieldnames: Iterable[str], rows: Iterable[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare deux rapports Tenable (CSV) espacés de deux semaines."
    )
    parser.add_argument("old_report", type=Path, help="Ancien rapport (CSV)")
    parser.add_argument("new_report", type=Path, help="Nouveau rapport (CSV)")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("comparison_output"),
        help="Dossier de sortie pour les CSV générés (défaut: comparison_output)",
    )
    args = parser.parse_args()

    old_path: Path = args.old_report
    new_path: Path = args.new_report

    (
        _old_rows,
        old_findings,
        old_key_to_row,
        old_plugins,
        old_cves,
        old_hosts,
        old_cve_hosts,
    ) = load_report(old_path)

    (
        new_rows,
        new_findings,
        new_key_to_row,
        new_plugins,
        new_cves,
        new_hosts,
        new_cve_hosts,
    ) = load_report(new_path)

    # On prend les en-têtes du nouveau fichier (plus complets en général)
    fieldnames = list(new_rows[0].keys()) if new_rows else []

    # 1) Findings patchées : présentes dans l'ancien, absentes dans le nouveau
    patched_findings_keys = old_findings - new_findings
    patched_rows = [old_key_to_row[k] for k in patched_findings_keys]

    # 2) Nouvelles findings : présentes dans le nouveau, absentes dans l'ancien
    new_findings_keys = new_findings - old_findings
    added_rows = [new_key_to_row[k] for k in new_findings_keys]


    # 3) Nouveaux Plugin ID / Plugin ID disparus
    new_plugin_ids = new_plugins - old_plugins
    removed_plugin_ids = old_plugins - new_plugins

    # 2bis) Classement par plugin / CVE / host (pour répondre à ta demande)
    # Hypothèse :
    # - "CVE patché" = (plugin, CVE, host) présent dans l'ancien mais plus dans le nouveau.
    # - "CVE non patché" = (plugin, CVE, host) présent dans le nouveau (peu importe s'il existait déjà).
    # - "Nouveau plugin" = plugin présent uniquement dans le nouveau rapport.
    per_plugin_patched = []
    for plugin_id, cve, host in patched_findings_keys:
        per_plugin_patched.append(
            {
                "Plugin ID": plugin_id,
                "CVE": cve or "",
                "Host": host,
            }
        )

    per_plugin_not_patched = []
    for plugin_id, cve, host in new_findings:
        per_plugin_not_patched.append(
            {
                "Plugin ID": plugin_id,
                "CVE": cve or "",
                "Host": host,
            }
        )

    new_plugins_details = []
    for plugin_id, cve, host in new_findings:
        if plugin_id in new_plugin_ids:
            new_plugins_details.append(
                {
                    "Plugin ID": plugin_id,
                    "CVE": cve or "",
                    "Host": host,
                }
            )

    # 4) Nouveaux CVE / CVE disparus (complètement)
    new_cves_only = new_cves - old_cves
    patched_cves_only = old_cves - new_cves

    # 5) Nouveaux hosts / hosts disparus
    new_hosts_only = new_hosts - old_hosts
    removed_hosts_only = old_hosts - new_hosts

    # 6) CVE existants mais détectés sur de nouveaux hosts
    cves_in_both = old_cves & new_cves
    cve_new_hosts: Dict[str, Set[str]] = {}
    for cve in cves_in_both:
        old_hosts_for_cve = old_cve_hosts.get(cve, set())
        new_hosts_for_cve = new_cve_hosts.get(cve, set())
        diff_hosts = new_hosts_for_cve - old_hosts_for_cve
        if diff_hosts:
            cve_new_hosts[cve] = diff_hosts

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Écriture des CSV détaillés pour les findings
    if fieldnames:
        write_csv(output_dir / "patched_findings.csv", fieldnames, patched_rows)
        write_csv(output_dir / "new_findings.csv", fieldnames, added_rows)

    # CSV répondant aux besoins par plugin
    write_csv(
        output_dir / "per_plugin_patched.csv",
        ["Plugin ID", "CVE", "Host"],
        per_plugin_patched,
    )
    write_csv(
        output_dir / "per_plugin_not_patched.csv",
        ["Plugin ID", "CVE", "Host"],
        per_plugin_not_patched,
    )
    write_csv(
        output_dir / "new_plugins_details.csv",
        ["Plugin ID", "CVE", "Host"],
        new_plugins_details,
    )

    # CSV pour "CVE existants mais nouveaux hosts"
    cve_new_hosts_rows: List[dict] = []
    for (plugin_id, cve, host), row in new_key_to_row.items():
        if not cve:
            continue
        if cve in cve_new_hosts and host in cve_new_hosts[cve]:
            cve_new_hosts_rows.append(row)

    if fieldnames:
        write_csv(output_dir / "existing_cve_new_hosts.csv", fieldnames, cve_new_hosts_rows)

    # Résumé texte
    print("=== Résumé de la comparaison ===")
    print(f"Ancien rapport : {old_path}")
    print(f"Nouveau rapport : {new_path}\n")

    print(f"Nombre total de findings (ancien) : {len(old_findings)}")
    print(f"Nombre total de findings (nouveau) : {len(new_findings)}\n")

    print(f"Findings patchées (plus présentes) : {len(patched_findings_keys)}")
    print(f"Nouvelles findings : {len(new_findings_keys)}\n")

    print(f"Nouveaux Plugin ID : {len(new_plugin_ids)}")
    print(f"Plugin ID disparus : {len(removed_plugin_ids)}\n")

    print(f"Nouveaux CVE : {len(new_cves_only)}")
    print(f"CVE totalement disparus : {len(patched_cves_only)}\n")

    print(f"Nouveaux hosts : {len(new_hosts_only)}")
    print(f"Hosts disparus : {len(removed_hosts_only)}\n")

    print(
        "CVE existants mais détectés sur de nouveaux hosts : "
        f"{len(cve_new_hosts)} (détails dans existing_cve_new_hosts.csv)"
    )

    print(f"\nCSV générés dans : {output_dir.resolve()}")


if __name__ == "__main__":
    main()

