import re
from pathlib import Path
from typing import Any


def normalize_identifier(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip().lower()


def build_identity_index(dataset_path: str | Path) -> tuple[dict[str, dict[str, str]], dict[str, set[str]], dict[str, set[str]]]:
    dataset_path = Path(dataset_path)
    identities = []
    with (dataset_path / 'user_identities.csv').open('r', encoding='utf-8-sig', newline='') as handle:
        import csv
        identities = list(csv.DictReader(handle))

    by_user: dict[str, dict[str, str]] = {}
    by_email: dict[str, set[str]] = {}
    history: dict[str, set[str]] = {}

    for row in identities:
        user_id = row.get('user_id', '')
        by_user[user_id] = row
        history.setdefault(user_id, set())
        for field in ('email', 'phone', 'name', 'email_hash'):
            value = normalize_identifier(row.get(field))
            if value:
                history[user_id].add(value)
        email = normalize_identifier(row.get('email'))
        if email:
            by_email.setdefault(email, set()).add(user_id)

    with (dataset_path / 'user_audit_log.csv').open('r', encoding='utf-8-sig', newline='') as handle:
        import csv
        for row in csv.DictReader(handle):
            user_id = row.get('user_id', '')
            history.setdefault(user_id, set())
            for field in ('old_value', 'new_value'):
                value = normalize_identifier(row.get(field))
                if value:
                    history[user_id].add(value)
            old_value = normalize_identifier(row.get('old_value'))
            new_value = normalize_identifier(row.get('new_value'))
            if old_value:
                by_email.setdefault(old_value, set()).add(user_id)
            if new_value:
                by_email.setdefault(new_value, set()).add(user_id)

    return by_user, by_email, history


def find_user_ids_for_case(email: str, by_email: dict[str, set[str]], by_user: dict[str, dict[str, str]]) -> set[str]:
    target = normalize_identifier(email)
    matches = set(by_email.get(target, set()))
    if not matches:
        for user_id, row in by_user.items():
            if normalize_identifier(row.get('email_hash')) == target:
                matches.add(user_id)
    return matches


def extract_identifier_set(user_id: str, identity_row: dict[str, str], audit_rows: list[dict[str, str]]) -> set[str]:
    identifiers: set[str] = set()
    for field in ('email', 'phone', 'name', 'email_hash'):
        value = normalize_identifier(identity_row.get(field))
        if value:
            identifiers.add(value)
    for row in audit_rows:
        if row.get('user_id') != user_id:
            continue
        for field in ('old_value', 'new_value'):
            value = normalize_identifier(row.get(field))
            if value:
                identifiers.add(value)
                if re.fullmatch(r'[a-f0-9]{32,64}', value):
                    identifiers.add(value)
    return identifiers
