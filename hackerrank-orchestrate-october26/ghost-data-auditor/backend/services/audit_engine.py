import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .identity_resolution import find_user_ids_for_case, build_identity_index
from .policy_engine import load_rules, required_action_for_category

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / 'dataset'

SYSTEM_FOR_TABLE = {
    'customer_profiles': 'account_service',
    'customer_search_documents': 'search_service',
    'customer_analytics_profiles': 'analytics_platform',
    'support_records': 'support_platform',
    'customer_exports': 'export_service',
    'connector_subscriptions': 'integration_service',
    'backup_restore_entries': 'backup_service',
    'security_audit_records': 'security_service',
    'marketing_profiles': 'marketing_platform',
    'email_delivery_logs': 'notification_service',
    'account_tombstones': 'identity_service',
    'identity_tombstones': 'identity_service',
    'tombstone_records': 'identity_service',
}

DIRECT_FIELDS = {'email', 'email_hash', 'phone', 'name', 'full_name', 'customer_email', 'owner_email'}


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open('r', encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except Exception:
        return None


def authorizes_deletion(request_text: str) -> bool:
    value = (request_text or '').casefold()
    non_delete = [r'\baccess\b', r'\bexport\b', r'correct(?:ion)?\b', r'marketing opt.?out', r'unsubscribe', r'update my']
    if any(re.search(pattern, value) for pattern in non_delete):
        return False
    delete_patterns = [r'delet', r'eras', r'remove my (?:personal )?data', r'close my account', r'forget me', r'wording']
    return any(re.search(pattern, value) for pattern in delete_patterns)


def resource_action(category: str) -> str:
    mapping = {
        'USER_PROFILE': 'DELETE',
        'SECONDARY_IDENTIFIER': 'DELETE',
        'SEARCH_INDEX_ENTRY': 'DELETE',
        'CACHE_ENTRY': 'DELETE',
        'SUPPORT_MESSAGE': 'REDACT',
        'SUPPORT_ATTACHMENT': 'DELETE',
        'ANALYTICS_PROFILE': 'ANONYMIZE',
        'PRODUCT_TELEMETRY': 'ANONYMIZE',
        'USER_EXPORT': 'DELETE',
        'MARKETING_PROFILE': 'DELETE',
        'EMAIL_DELIVERY_LOG': 'REDACT',
        'SECURITY_AUDIT_LOG': 'RETAIN',
        'ACCOUNT_TOMBSTONE': 'REDACT',
        'BACKUP_ARCHIVE': 'RETAIN',
    }
    return mapping.get(category, 'DELETE')


def evidence_records(dataset_path: Path) -> list[dict[str, Any]]:
    catalog = []
    for row in read_csv(dataset_path / 'evidence_files.csv'):
        file_path = dataset_path / row.get('file_path', '')
        if not file_path.exists():
            continue
        entry = {'file_id': row.get('file_id', ''), 'path': str(file_path), 'captured_at': row.get('captured_at', ''), 'text': '', 'records': []}
        suffix = file_path.suffix.lower()
        try:
            if suffix == '.json':
                data = json.loads(file_path.read_text(encoding='utf-8-sig'))
                entry['text'] = json.dumps(data, ensure_ascii=False)
            elif suffix in {'.txt', '.log', '.sql'}:
                entry['text'] = file_path.read_text(encoding='utf-8', errors='replace')
            elif suffix == '.csv':
                entry['text'] = file_path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            entry['text'] = ''
        catalog.append(entry)
    return catalog


def collect_activity_findings(activity_rows: list[dict[str, str]], identifiers: set[str], user_id: str, cutoff: datetime) -> list[dict[str, Any]]:
    findings = []
    for row in activity_rows:
        event_time = parse_dt(row.get('event_time'))
        if event_time and event_time > cutoff:
            continue
        text = f"{row.get('details','')} {row.get('resource_id','')} {row.get('target_system','')}".lower()
        if not any(identifier in text for identifier in identifiers if identifier):
            continue
        event_type = (row.get('event_type') or '').upper()
        if ('SYNC' in event_type or 'IMPORT' in event_type or 'REPLICATION' in event_type) and ('active' in text or 'enabled' in text or 'scheduled' in text):
            findings.append({'system_id': row.get('target_system') or 'integration_service', 'resource_id': row.get('resource_id') or row.get('activity_id'), 'operation': 'REPORT_ACTIVE_DATA_FLOW', 'state': 'ACTIVE', 'evidence_id': row.get('activity_id', '')})
        if ('RESTORE' in event_type or 'BACKUP' in event_type) and ('allowed' in text or 'active' in text or 'enabled' in text or 'pending' in text):
            findings.append({'system_id': row.get('target_system') or 'backup_service', 'resource_id': row.get('resource_id') or row.get('activity_id'), 'operation': 'REPORT_RESTORE_RISK', 'state': 'ACTIVE', 'evidence_id': row.get('activity_id', '')})
    return findings


def build_case(case: dict[str, str], dataset_path: Path, rules: list[dict[str, str]], by_user: dict[str, dict[str, str]], by_email: dict[str, set[str]], audit_rows: list[dict[str, str]], activity_rows: list[dict[str, str]]) -> dict[str, Any]:
    request_text = case.get('request_text', '')
    if not authorizes_deletion(request_text):
        return {'case_id': case['case_id'], 'deletion_status': 'NOT_APPLICABLE', 'steps': []}

    email = (case.get('email') or '').strip().lower()
    user_ids = find_user_ids_for_case(email, by_email, by_user)
    if not user_ids:
        return {'case_id': case['case_id'], 'deletion_status': 'INCOMPLETE', 'steps': [{'step_no': 1, 'phase': 'FINDING', 'system_id': 'account_service', 'resource_id': 'unknown', 'operation': 'REPORT_REMAINING_RECORD', 'state': 'PRESENT', 'evidence_id': ''}]}

    cutoff = parse_dt(case.get('audit_at'))
    best = None
    for user_id in sorted(user_ids):
        row = by_user.get(user_id, {})
        identifiers = set()
        for field in ('email', 'phone', 'name', 'email_hash'):
            value = (row.get(field) or '').strip().lower()
            if value:
                identifiers.add(value)
        for row_a in audit_rows:
            if row_a.get('user_id') != user_id:
                continue
            for field in ('old_value', 'new_value'):
                value = (row_a.get(field) or '').strip().lower()
                if value:
                    identifiers.add(value)
        if best is None or len(identifiers) > len(best['identifiers']):
            best = {'user_id': user_id, 'identifiers': identifiers, 'record': row}

    if not best:
        return {'case_id': case['case_id'], 'deletion_status': 'INCOMPLETE', 'steps': [{'step_no': 1, 'phase': 'FINDING', 'system_id': 'account_service', 'resource_id': 'unknown', 'operation': 'REPORT_REMAINING_RECORD', 'state': 'PRESENT', 'evidence_id': ''}]}

    identifiers = best['identifiers']
    findings = []
    for evidence_entry in evidence_records(dataset_path):
        text = evidence_entry.get('text', '')
        if not text:
            continue
        if not any(identifier in text.lower() for identifier in identifiers if identifier):
            continue
        if 'rows=0' in text.lower() or 'http_status=404' in text.lower():
            continue
        if 'account_service' in text.lower() or 'user_id' in text.lower() or 'email' in text.lower():
            findings.append({'system_id': 'account_service', 'resource_id': 'account_record', 'operation': 'REPORT_REMAINING_RECORD', 'state': 'PRESENT', 'evidence_id': evidence_entry['file_id']})

    findings.extend(collect_activity_findings(activity_rows, identifiers, best['user_id'], cutoff or datetime.max))

    if findings:
        remediation = []
        verification = []
        for item in findings:
            system_id = item['system_id']
            resource_id = item['resource_id']
            op = item['operation']
            if op == 'REPORT_ACTIVE_DATA_FLOW':
                remediation.append({'phase': 'REMEDIATION', 'system_id': system_id, 'resource_id': resource_id, 'operation': 'DISABLE_DATA_FLOW', 'state': 'DISABLED', 'evidence_id': ''})
                verification.append({'phase': 'VERIFICATION', 'system_id': system_id, 'resource_id': resource_id, 'operation': 'VERIFY_DATA_FLOW_DISABLED', 'state': 'DISABLED', 'evidence_id': ''})
            elif op == 'REPORT_RESTORE_RISK':
                remediation.append({'phase': 'REMEDIATION', 'system_id': system_id, 'resource_id': resource_id, 'operation': 'BLOCK_RESTORE', 'state': 'BLOCKED', 'evidence_id': ''})
                verification.append({'phase': 'VERIFICATION', 'system_id': system_id, 'resource_id': resource_id, 'operation': 'VERIFY_RESTORE_BLOCKED', 'state': 'BLOCKED', 'evidence_id': ''})
            else:
                remediation.append({'phase': 'REMEDIATION', 'system_id': system_id, 'resource_id': resource_id, 'operation': 'DELETE_RECORD', 'state': 'ABSENT', 'evidence_id': ''})
                verification.append({'phase': 'VERIFICATION', 'system_id': system_id, 'resource_id': resource_id, 'operation': 'VERIFY_RECORD_ABSENT', 'state': 'ABSENT', 'evidence_id': ''})
        steps = [
            {'step_no': i + 1, 'phase': 'FINDING', 'system_id': item['system_id'], 'resource_id': item['resource_id'], 'operation': item['operation'], 'state': item['state'], 'evidence_id': item.get('evidence_id', '')}
            for i, item in enumerate(findings)
        ]
        for idx, step in enumerate(remediation, start=len(steps) + 1):
            step['step_no'] = idx
            steps.append(step)
        for idx, step in enumerate(verification, start=len(steps) + 1):
            step['step_no'] = idx
            steps.append(step)
        return {'case_id': case['case_id'], 'deletion_status': 'INCOMPLETE', 'steps': steps}

    return {'case_id': case['case_id'], 'deletion_status': 'COMPLETE', 'steps': [{'step_no': 1, 'phase': 'VERIFICATION', 'system_id': 'account_service', 'resource_id': 'account_record', 'operation': 'VERIFY_RECORD_ABSENT', 'state': 'ABSENT', 'evidence_id': evidence_records(dataset_path)[0]['file_id'] if evidence_records(dataset_path) else ''}]}


def run_audit(dataset_path: str | Path = DATASET, output_path: str | Path = ROOT / 'output.csv'):
    dataset_path = Path(dataset_path)
    rules = load_rules(dataset_path)
    data = {name: read_csv(dataset_path / f'{name}.csv') for name in ['deletion_requests', 'system_activity', 'user_identities', 'user_audit_log']}
    by_user, by_email, history = build_identity_index(dataset_path)
    results = []
    for case in data['deletion_requests']:
        result = build_case(case, dataset_path, rules, by_user, by_email, data['user_audit_log'], data['system_activity'])
        results.append(result)

    results.sort(key=lambda x: x['case_id'])
    output_path = Path(output_path)
    with output_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['case_id', 'deletion_status', 'steps_json'])
        for row in results:
            writer.writerow([row['case_id'], row['deletion_status'], json.dumps(row['steps'], separators=(',', ':'), ensure_ascii=False)])
    return results
