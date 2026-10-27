from __future__ import annotations

import csv
from pathlib import Path


def load_rules(dataset_path: str | Path) -> list[dict[str, str]]:
    path = Path(dataset_path) / 'deletion_rules.csv'
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def required_action_for_category(category: str, rules: list[dict[str, str]]) -> str:
    for rule in rules:
        if rule.get('data_category', '').strip() == category:
            return rule.get('required_action', 'DELETE').strip()
    return 'DELETE'
