import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def load_dataset(dataset_path: str | Path) -> dict[str, list[dict[str, str]]]:
    dataset_path = Path(dataset_path)
    files = {
        'requests': dataset_path / 'deletion_requests.csv',
        'rules': dataset_path / 'deletion_rules.csv',
        'evidence_manifest': dataset_path / 'evidence_files.csv',
        'identities': dataset_path / 'user_identities.csv',
        'audit_log': dataset_path / 'user_audit_log.csv',
        'activity': dataset_path / 'system_activity.csv',
        'sample_requests': dataset_path / 'sample_deletion_requests.csv',
        'sample_output': dataset_path / 'sample_output.csv',
    }
    payload = {}
    for name, file_path in files.items():
        payload[name] = read_csv(file_path) if file_path.exists() else []
    return payload


def safe_json_loads(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []
