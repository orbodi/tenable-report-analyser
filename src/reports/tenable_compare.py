import csv
from collections import defaultdict
from dataclasses import dataclass
from io import TextIOWrapper
from typing import Dict, Iterable, List, Optional, Set, Tuple


FindingKey = Tuple[str, Optional[str], str]  # (plugin_id, cve, host)


@dataclass
class ComparisonResult:
    per_plugin_patched: List[dict]
    per_plugin_not_patched: List[dict]
    new_plugins_details: List[dict]


def _load_report_from_fileobj(fileobj) -> Tuple[
    List[dict],
    Set[FindingKey],
    Dict[FindingKey, dict],
    Set[str],
]:
    # On suppose un UTF-8 ; adapter si besoin
    if isinstance(fileobj, TextIOWrapper):
        reader = csv.DictReader(fileobj)
    else:
        reader = csv.DictReader(TextIOWrapper(fileobj, encoding="utf-8"))

    rows: List[dict] = []
    findings_keys: Set[FindingKey] = set()
    key_to_row: Dict[FindingKey, dict] = {}
    plugins: Set[str] = set()

    for row in reader:
        plugin_id = (row.get("Plugin ID") or "").strip()
        host = (row.get("Host") or "").strip()
        cve_raw = (row.get("CVE") or "").strip()
        cve = cve_raw or None

        if not plugin_id or not host:
            continue

        key: FindingKey = (plugin_id, cve, host)
        rows.append(row)
        findings_keys.add(key)
        key_to_row[key] = row
        plugins.add(plugin_id)

    return rows, findings_keys, key_to_row, plugins


def compare_reports(old_file, new_file) -> ComparisonResult:
    (
        _old_rows,
        old_findings,
        _old_key_to_row,
        old_plugins,
    ) = _load_report_from_fileobj(old_file)

    (
        _new_rows,
        new_findings,
        _new_key_to_row,
        new_plugins,
    ) = _load_report_from_fileobj(new_file)

    patched_findings_keys = old_findings - new_findings
    new_plugin_ids = new_plugins - old_plugins

    per_plugin_patched: List[dict] = []
    for plugin_id, cve, host in patched_findings_keys:
        per_plugin_patched.append(
            {
                "plugin_id": plugin_id,
                "cve": cve or "",
                "host": host,
            }
        )

    per_plugin_not_patched: List[dict] = []
    for plugin_id, cve, host in new_findings:
        per_plugin_not_patched.append(
            {
                "plugin_id": plugin_id,
                "cve": cve or "",
                "host": host,
            }
        )

    new_plugins_details: List[dict] = []
    for plugin_id, cve, host in new_findings:
        if plugin_id in new_plugin_ids:
            new_plugins_details.append(
                {
                    "plugin_id": plugin_id,
                    "cve": cve or "",
                    "host": host,
                }
            )

    return ComparisonResult(
        per_plugin_patched=per_plugin_patched,
        per_plugin_not_patched=per_plugin_not_patched,
        new_plugins_details=new_plugins_details,
    )

