from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__(__file__)).resolve().parents[1]
DATASET = ROOT / "dataset"
OUTPUT = ROOT / "output.csv"
LOGGER = logging.getLogger("ghost_data_auditor")
HEADER = ["case_id", "deletion_status", "steps_json"]

SYSTEM_FOR_TABLE = {
    "customer_profiles": "account_service",
    "customer_search_documents": "search_service",
    "customer_analytics_profiles": "analytics_platform",
    "support_records": "support_platform",
    "customer_exports": "export_service",
    "connector_subscriptions": "integration_service",
    "backup_restore_entries": "backup_service",
    "security_audit_records": "security_service",
    "marketing_profiles": "marketing_platform",
    "email_delivery_logs": "notification_service",
    "account_tombstones": "identity_service",
    "identity_tombstones": "identity_service",
    "tombstone_records": "identity_service",
}

SYSTEM_CATEGORY = {
    "account_service": "USER_PROFILE",
    "search_service": "SEARCH_INDEX_ENTRY",
    "analytics_platform": "ANALYTICS_PROFILE",
    "support_platform": "SUPPORT_MESSAGE",
    "export_service": "USER_EXPORT",
    "integration_service": "SECONDARY_IDENTIFIER",
    "backup_service": "BACKUP_ARCHIVE",
    "security_service": "SECURITY_AUDIT_LOG",
    "marketing_platform": "MARKETING_PROFILE",
    "notification_service": "EMAIL_DELIVERY_LOG",
    "cache_service": "CACHE_ENTRY",
    "telemetry_service": "PRODUCT_TELEMETRY",
    "identity_service": "ACCOUNT_TOMBSTONE",
}

DIRECT_FIELDS = {
    "email", "email_hash", "phone", "name", "full_name",
    "customer_email", "owner_email", "requester_email",
    "requester_name", "requester_phone", "display_name",
}

OPERATION_ORDER = {
    "REPORT_REMAINING_RECORD": 0, "REPORT_EXPOSED_PII": 1,
    "REPORT_ACTIVE_DATA_FLOW": 2, "REPORT_RESTORE_RISK": 3,
}

OPERATIONS_MAP = {
    "DELETE": ("DELETE_RECORD", "ABSENT", "VERIFY_RECORD_ABSENT"),
    "REDACT": ("REDACT_RECORD", "REDACTED", "VERIFY_RECORD_REDACTED"),
    "ANONYMIZE": ("ANONYMIZE_RECORD", "ANONYMIZED", "VERIFY_RECORD_ANONYMIZED"),
    "RETAIN": (None, "PRESENT", "VERIFY_RECORD_PRESENT"),
    "DISABLE_DATA_FLOW": ("DISABLE_DATA_FLOW", "DISABLED", "VERIFY_DATA_FLOW_DISABLED"),
    "BLOCK_RESTORE": ("BLOCK_RESTORE", "BLOCKED", "VERIFY_RESTORE_BLOCKED"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def at_or_before(value: Any, cutoff: datetime) -> bool:
    parsed = timestamp(value)
    return parsed is None or parsed <= cutoff


def walk_records(obj: Any, system: str = "unknown", table: str = ""):
    if isinstance(obj, dict):
        local_system = str(obj.get("data_store") or obj.get("system_id") or system)
        local_table = str(obj.get("collection") or obj.get("table") or table)
        if local_table in SYSTEM_FOR_TABLE:
            local_system = SYSTEM_FOR_TABLE[local_table]
        records = obj.get("records")
        if isinstance(records, list):
            for record in records:
                if isinstance(record, dict):
                    yield from walk_records(record, local_system, local_table)
        elif obj.get("resource_id"):
            yield obj, local_system, local_table
        for key, value in obj.items():
            if key not in {"records"} and isinstance(value, (dict, list)):
                child_system = SYSTEM_FOR_TABLE.get(
                    key, key if key.endswith(("_service", "_platform")) else local_system
                )
                yield from walk_records(value, child_system, key)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk_records(item, system, table)


def evidence_catalog(dataset: Path) -> list[dict[str, Any]]:
    catalog = []
    for manifest in read_csv(dataset / "evidence_files.csv"):
        path = (dataset / manifest["file_path"]).resolve()
        try:
            path.relative_to((dataset / "evidence").resolve())
        except ValueError:
            LOGGER.warning("Evidence path outside evidence root skipped: %s", manifest["file_id"])
            continue
        entry: dict[str, Any] = {**manifest, "path": path, "text": "", "records": [], "errors": []}
        try:
            suffix = path.suffix.lower()
            if suffix == ".json":
                obj = json.loads(path.read_text(encoding="utf-8-sig"))
                entry["text"] = json.dumps(obj, ensure_ascii=False)
                entry["records"] = list(walk_records(obj))
            elif suffix == ".sql":
                sql = path.read_text(encoding="utf-8", errors="replace")
                entry["text"] = sql
                db = sqlite3.connect(":memory:")
                try:
                    db.executescript(sql)
                    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                    for tbl in tables:
                        try:
                            cols = [row[1] for row in db.execute(f'PRAGMA table_info("{tbl}")')]
                            for row in db.execute(f'SELECT * FROM "{tbl}"'):
                                record = dict(zip(cols, row))
                                if record.get("resource_id"):
                                    entry["records"].append((record, SYSTEM_FOR_TABLE.get(tbl, tbl), tbl))
                        except sqlite3.Error as exc:
                            entry["errors"].append(f"{tbl}: {exc}")
                except sqlite3.Error as exc:
                    entry["errors"].append(f"SQL parse: {exc}")
                finally:
                    db.close()
            elif suffix in {".log", ".txt"}:
                entry["text"] = path.read_text(encoding="utf-8", errors="replace")
            elif suffix == ".pdf":
                try:
                    from pypdf import PdfReader
                    entry["text"] = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
                except Exception as exc:
                    entry["errors"].append(f"PDF extraction unavailable: {exc}")
            elif suffix == ".png":
                try:
                    import pytesseract
                    from PIL import Image
                    entry["text"] = pytesseract.image_to_string(Image.open(path))
                except Exception as exc:
                    entry["errors"].append(f"Image OCR unavailable: {exc}")
        except Exception as exc:
            entry["errors"].append(str(exc))
        catalog.append(entry)
    return catalog


def identity_maps(dataset: Path):
    identities = read_csv(dataset / "user_identities.csv")
    audits = read_csv(dataset / "user_audit_log.csv")
    by_email: dict[str, set[str]] = {}
    by_user = {row["user_id"]: dict(row) for row in identities}
    history: dict[str, set[str]] = {uid: set() for uid in by_user}
    for row in identities:
        by_email.setdefault(row["email"].strip().lower(), set()).add(row["user_id"])
    for row in audits:
        field = row["field_name"].lower()
        if field in {"email", "phone", "name", "email_hash"}:
            history.setdefault(row["user_id"], set()).update(
                v.strip().lower() for v in (row["old_value"], row["new_value"]) if v
            )
        if field == "email" and row["old_value"]:
            by_email.setdefault(row["old_value"].strip().lower(), set()).add(row["user_id"])
    return by_user, by_email, history, audits


def authorizes_deletion(text: str) -> bool:
    value = text.casefold()
    non_delete = [
        r"\baccess\b", r"\bexport\b", r"correct(?:ion)?\b", r"update my",
        r"marketing opt.?out", r"unsubscribe", r"stop marketing",
    ]
    if any(re.search(p, value) for p in non_delete):
        return False
    delete_patterns = [
        r"delet", r"eras", r"remove my (?:personal )?data", r"close my account",
        r"forget me", r"effacer", r"supprimer", r"loschen", r"eliminar",
        r"borrar", r"hapus",
    ]
    return any(re.search(p, value) for p in delete_patterns)


def classify_record(record, system, table, user_id, ids, hashes):
    normalized = {str(k).lower(): str(v).strip().lower() for k, v in record.items() if v is not None}
    matched = (
        any(val and val in ids | hashes for val in normalized.values())
        or user_id.lower() in normalized.values()
    )
    if not matched:
        return None
    resource_id = str(record.get("resource_id", ""))
    cat = SYSTEM_CATEGORY.get(system, "SECONDARY_IDENTIFIER")
    hay = f"{system} {table} {json.dumps(record, ensure_ascii=False)}".lower()
    if "tombstone" in hay or str(record.get("account_status", "")).upper() == "DELETED":
        cat = "ACCOUNT_TOMBSTONE"; system = "identity_service"
    elif "security_audit" in table or "security_audit" in system:
        cat = "SECURITY_AUDIT_LOG"; system = "security_service"
    elif "support" in table and "attachment" not in table:
        cat = "SUPPORT_MESSAGE"; system = "support_platform"
    elif "attachment" in table or "attachment" in hay:
        cat = "SUPPORT_ATTACHMENT"; system = "support_platform"
    elif "marketing" in system or "marketing" in table:
        cat = "MARKETING_PROFILE"; system = "marketing_platform"
    elif "email_delivery" in table or "notification" in system:
        cat = "EMAIL_DELIVERY_LOG"; system = "notification_service"
    elif "backup" in table or "backup" in system:
        cat = "BACKUP_ARCHIVE"; system = "backup_service"
    elif "connector" in table or "data_flow" in hay or "connector" in system:
        cat = "SECONDARY_IDENTIFIER"; system = "integration_service"
    action = {
        "USER_PROFILE": "DELETE", "SECONDARY_IDENTIFIER": "DELETE",
        "SEARCH_INDEX_ENTRY": "DELETE", "CACHE_ENTRY": "DELETE",
        "SUPPORT_MESSAGE": "REDACT", "SUPPORT_ATTACHMENT": "DELETE",
        "ANALYTICS_PROFILE": "ANONYMIZE", "PRODUCT_TELEMETRY": "ANONYMIZE",
        "USER_EXPORT": "DELETE", "MARKETING_PROFILE": "DELETE",
        "EMAIL_DELIVERY_LOG": "REDACT", "SECURITY_AUDIT_LOG": "RETAIN",
        "LEGAL_HOLD_RECORD": "RETAIN", "BACKUP_ARCHIVE": "RETAIN",
        "ACCOUNT_TOMBSTONE": "REDACT",
    }.get(cat, "DELETE")
    has_pii = any(k in DIRECT_FIELDS and str(v).strip() for k, v in record.items())
    if cat == "ACCOUNT_TOMBSTONE" and has_pii:
        operation = "REPORT_EXPOSED_PII"
    elif action == "RETAIN":
        operation = "VERIFY_RECORD_PRESENT"
    elif action == "REDACT" and has_pii:
        operation = "REPORT_EXPOSED_PII"
    elif action == "ANONYMIZE":
        operation = "REPORT_EXPOSED_PII"
    else:
        operation = "REPORT_REMAINING_RECORD"
    return {
        "system_id": system if system != "unknown" else "account_service",
        "resource_id": resource_id, "category": cat,
        "required_action": action, "operation": operation, "record": record,
    }


def activity_findings(rows, ids, user_id, cutoff):
    found = []
    for row in rows:
        if not at_or_before(row.get("event_time"), cutoff):
            continue
        content = f"{row.get('details', '')} {row.get('resource_id', '')}".lower()
        if user_id.lower() not in content and not any(val and val in content for val in ids):
            continue
        event = row.get("event_type", "").upper()
        if any(k in event for k in ("SYNC", "IMPORT", "REPLICATION")) and any(
            k in content for k in ("active", "enabled", "running", "scheduled")
        ):
            found.append({
                "system_id": row.get("target_system") or row.get("source_system") or "unknown",
                "resource_id": row.get("resource_id") or row.get("activity_id"),
                "operation": "REPORT_ACTIVE_DATA_FLOW", "state": "ACTIVE",
                "evidence_id": row.get("activity_id"), "required_action": "DISABLE_DATA_FLOW",
            })
        if any(k in event for k in ("RESTORE", "BACKUP")) and any(
            k in content for k in ("allowed", "active", "enabled", "pending")
        ):
            found.append({
                "system_id": row.get("target_system") or row.get("source_system") or "backup_service",
                "resource_id": row.get("resource_id") or row.get("activity_id"),
                "operation": "REPORT_RESTORE_RISK", "state": "ACTIVE",
                "evidence_id": row.get("activity_id"), "required_action": "BLOCK_RESTORE",
            })
    return found


def extract_log_records(text, identifiers, item_file_id):
    found = []
    if not (text and any(val and val in text.lower() for val in identifiers)):
        return found
    for match in re.finditer(r"resource_id=([A-Za-z0-9_-]+)", text):
        ls = max(0, text.rfind("\n", 0, match.start()) + 1)
        le = text.find("\n", match.end())
        line = text[ls:(le if le >= 0 else len(text))]
        if not any(val and val in line.lower() for val in identifiers):
            continue
        if "rows=0" in line or "http_status=404" in line:
            continue
        svc = re.search(r"service=([A-Za-z0-9_-]+)", line)
        found.append({
            "system_id": svc.group(1) if svc else "unknown",
            "resource_id": match.group(1), "category": "SECONDARY_IDENTIFIER",
            "required_action": "DELETE", "operation": "REPORT_REMAINING_RECORD",
            "evidence_id": item_file_id, "record": {"resource_id": match.group(1)},
        })
    return found


def build_remediation_and_verification(findings):
    remediation = []
    verification = []
    for item in findings:
        action = item.get("required_action")
        if action not in {"DISABLE_DATA_FLOW", "BLOCK_RESTORE"}:
            continue
        op, state, verify = OPERATIONS_MAP[action]
        if op:
            remediation.append({"phase": "REMEDIATION", "system_id": item["system_id"],
                "resource_id": item["resource_id"], "operation": op, "state": state, "evidence_id": ""})
        verification.append({"phase": "VERIFICATION", "system_id": item["system_id"],
            "resource_id": item["resource_id"], "operation": verify, "state": state, "evidence_id": ""})
    for item in findings:
        action = item.get("required_action")
        if action in {"DISABLE_DATA_FLOW", "BLOCK_RESTORE"} or not action:
            continue
        op, state, verify = OPERATIONS_MAP.get(action, (None, "ABSENT", "VERIFY_RECORD_ABSENT"))
        if op:
            remediation.append({"phase": "REMEDIATION", "system_id": item["system_id"],
                "resource_id": item["resource_id"], "operation": op, "state": state, "evidence_id": ""})
        if action != "RETAIN":
            verification.append({"phase": "VERIFICATION", "system_id": item["system_id"],
                "resource_id": item["resource_id"], "operation": verify, "state": state, "evidence_id": ""})
    return remediation, verification


def build_case(case, dataset, catalog, maps, activity_rows):
    by_user, by_email, history, audits = maps
    if not authorizes_deletion(case.get("request_text", "")):
        return {"case_id": case["case_id"], "deletion_status": "NOT_APPLICABLE",
                "steps": [], "findings": [], "identifiers": []}
    email = case.get("email", "").strip().lower()
    user_ids = by_email.get(email, set())
    if not user_ids:
        user_ids = {uid for uid, row in by_user.items() if row.get("email_hash", "").lower() == email}
    cutoff = timestamp(case.get("audit_at")) or datetime.max.replace(tzinfo=timezone.utc)
    for uid in sorted(user_ids):
        identity = by_user[uid]
        identifiers = {v.strip().lower() for v in (
            identity.get("email", ""), identity.get("phone", ""),
            identity.get("name", ""), identity.get("email_hash", ""),
        ) if v}
        identifiers.update(history.get(uid, set()))
        all_hashes = {identity.get("email_hash", "").lower()} | {
            v for v in history.get(uid, set()) if re.fullmatch(r"[a-f0-9]{32,64}", v)
        }
        for row in audits:
            if row["user_id"] == uid and at_or_before(row.get("event_time"), cutoff):
                for val in (row.get("old_value"), row.get("new_value")):
                    if val:
                        identifiers.add(val.strip().lower())
                        if re.fullmatch(r"[a-f0-9]{32,64}", val.strip().lower()):
                            all_hashes.add(val.strip().lower())
        records = []
        for item in catalog:
            if not at_or_before(item.get("captured_at"), cutoff):
                continue
            for rec, system, table in item.get("records", []):
                if not at_or_before(rec.get("captured_at") or rec.get("updated_at") or rec.get("observed_at"), cutoff):
                    continue
                finding = classify_record(rec, system, table, uid, identifiers, all_hashes)
                if finding:
                    finding["evidence_id"] = item["file_id"]
                    records.append(finding)
            records.extend(extract_log_records(item.get("text", ""), identifiers, item["file_id"]))
        unique = {}
        catalog_time = {e["file_id"]: e.get("captured_at", "") for e in catalog}
        for finding in records:
            key = (finding["system_id"], finding["resource_id"], finding["operation"])
            prev = unique.get(key)
            if not prev or (timestamp(catalog_time.get(finding["evidence_id"], "")) or datetime.min.replace(tzinfo=timezone.utc)) > (timestamp(catalog_time.get(prev["evidence_id"], "")) or datetime.min.replace(tzinfo=timezone.utc)):
                unique[key] = finding
        records = list(unique.values())
        records.extend(activity_findings(activity_rows, identifiers, uid, cutoff))
        findings = sorted(records, key=lambda x: (
            OPERATION_ORDER.get(x.get("operation"), 9),
            x.get("system_id", ""), x.get("resource_id", ""), x.get("evidence_id", ""),
        ))
        if findings:
            phase_steps = []
            for item in findings:
                state = "PRESENT" if item["operation"] in {"REPORT_REMAINING_RECORD", "REPORT_EXPOSED_PII"} else "ACTIVE"
                phase_steps.append({"phase": "FINDING", "system_id": item["system_id"],
                    "resource_id": item["resource_id"], "operation": item["operation"],
                    "state": state, "evidence_id": item.get("evidence_id", "")})
            remediation, verification = build_remediation_and_verification(findings)
            steps = phase_steps + remediation + verification
            status = "INCOMPLETE"
        else:
            status = "COMPLETE"
            steps = []
            for item in catalog:
                if not at_or_before(item.get("captured_at"), cutoff) or not item.get("text"):
                    continue
                text = item["text"]
                if any(v and v in text.lower() for v in identifiers) and ("rows=0" in text or "http_status=404" in text):
                    for match in re.finditer(r"resource_id=([A-Za-z0-9_-]+)", text):
                        ls = max(0, text.rfind("\n", 0, match.start()) + 1)
                        le = text.find("\n", match.end())
                        line = text[ls:(le if le >= 0 else len(text))]
                        if any(v and v in line.lower() for v in identifiers) and ("rows=0" in line or "http_status=404" in line):
                            steps.append({"phase": "VERIFICATION", "system_id": "account_service",
                                "resource_id": match.group(1), "operation": "VERIFY_RECORD_ABSENT",
                                "state": "ABSENT", "evidence_id": item["file_id"]})
            steps.sort(key=lambda x: (x["system_id"], x["resource_id"], x["evidence_id"]))
            if not steps:
                status = "INCOMPLETE"
                num = uid.removeprefix("user_")
                steps = [
                    {"phase": "FINDING", "system_id": "account_service", "resource_id": f"account_{num}",
                     "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": ""},
                    {"phase": "REMEDIATION", "system_id": "account_service", "resource_id": f"account_{num}",
                     "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": ""},
                    {"phase": "VERIFICATION", "system_id": "account_service", "resource_id": f"account_{num}",
                     "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""},
                ]
        for number, step in enumerate(steps, 1):
            step["step_no"] = number
        return {"case_id": case["case_id"], "deletion_status": status, "steps": steps,
                "findings": findings if status == "INCOMPLETE" else [],
                "identifiers": sorted(identifiers), "user_id": uid}
    return {"case_id": case["case_id"], "deletion_status": "INCOMPLETE",
            "steps": [], "findings": [], "identifiers": [], "error": "No identity match"}


def run_audit(dataset: Path = DATASET, output_path: Path = OUTPUT, progress_callback: Any = None):
    LOGGER.info("Loading dataset from %s", dataset)
    requests = read_csv(dataset / "deletion_requests.csv")
    catalog = evidence_catalog(dataset)
    LOGGER.info("Evidence catalog: %d entries", len(catalog))
    maps = identity_maps(dataset)
    LOGGER.info("Identity maps: %d users", len(maps[0]))
    activity_rows = read_csv(dataset / "system_activity.csv")
    LOGGER.info("Activity rows: %d", len(activity_rows))
    results = []
    total_cases = len(requests)
    for i, case in enumerate(requests, 1):
        result = build_case(case, dataset, catalog, maps, activity_rows)
        results.append(result)
        if progress_callback:
            try:
                progress_callback(i, total_cases)
            except Exception:
                pass
        elif i % 50 == 0:
            LOGGER.info("Processed %d/%d", i, total_cases)
    results.sort(key=lambda x: x["case_id"])
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader()
        for result in results:
            writer.writerow({"case_id": result["case_id"], "deletion_status": result["deletion_status"],
                "steps_json": json.dumps(result["steps"], separators=(",", ":"), ensure_ascii=False)})
    LOGGER.info("Output written to %s", output_path)
    return results



def validate_output(path: Path, requests):
    rows = read_csv(path)
    expected = sorted(r["case_id"] for r in requests)
    actual = [r["case_id"] for r in rows]
    assert list(rows[0]) == HEADER, "Header mismatch"
    assert len(rows) == len(requests) and actual == expected, f"Row count mismatch: {len(rows)} vs {len(requests)}"
    for row in rows:
        steps = json.loads(row["steps_json"])
        assert isinstance(steps, list)
        if steps:
            assert [s["step_no"] for s in steps] == list(range(1, len(steps) + 1))
            rk = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}
            assert all(set(s) == rk for s in steps), f"Step fields mismatch in {row['case_id']}"
    return {"rows": len(rows), "header": HEADER, "sorted": actual == expected, "valid_json": True}


def main():
    parser = argparse.ArgumentParser(description="Run evidence-based deletion audits")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = run_audit(args.dataset, args.output)
    counts = dict(Counter(x["deletion_status"] for x in results))
    validation = validate_output(args.output, read_csv(args.dataset / "deletion_requests.csv"))
    print(json.dumps({"output": str(args.output), "requests": len(results),
        "status_counts": counts, "validation": validation}, indent=2))


if __name__ == "__main__":
    main()
