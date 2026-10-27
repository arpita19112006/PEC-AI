"""Ghost Data Still Exists - Flask REST API Backend."""
import csv
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_file
from flask_cors import CORS

# Add parent directories to path so we can import from code/main.py
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
import main as audit_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("ghost_api")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- Global state for audit runs ---
_audit_lock = threading.Lock()
_audit_state = {
    "status": "idle",  # idle, running, complete, error
    "started_at": None,
    "finished_at": None,
    "progress": 0,
    "total": 0,
    "error": None,
    "results": None,
}
_cached_results = None
_cached_at = None


def get_dataset_path():
    return Path(os.environ.get("DATASET_PATH", str(ROOT / "dataset")))


def get_output_path():
    return Path(os.environ.get("OUTPUT_PATH", str(ROOT / "output.csv")))


def load_results():
    global _cached_results, _cached_at
    out = get_output_path()
    if not out.exists():
        return []
    mtime = out.stat().st_mtime
    if _cached_results is None or _cached_at != mtime:
        rows = audit_engine.read_csv(out)
        _cached_results = rows
        _cached_at = mtime
    return _cached_results


def load_requests():
    ds = get_dataset_path()
    return audit_engine.read_csv(ds / "deletion_requests.csv")


def load_evidence_manifest():
    ds = get_dataset_path()
    return audit_engine.read_csv(ds / "evidence_files.csv")


# === Health ===
@app.route("/api/health")
def health():
    ds = get_dataset_path()
    out = get_output_path()
    checks = {
        "dataset_exists": ds.exists(),
        "deletion_requests_exists": (ds / "deletion_requests.csv").exists(),
        "evidence_dir_exists": (ds / "evidence").exists(),
        "output_exists": out.exists(),
        "python_version": sys.version,
        "audit_status": _audit_state["status"],
    }
    ok = all(v for k, v in checks.items() if isinstance(v, bool))
    return jsonify({"status": "ok" if ok else "degraded", "checks": checks}), 200


# === Dashboard ===
@app.route("/api/dashboard/stats")
def dashboard_stats():
    try:
        requests_list = load_requests()
        results = load_results()
        result_map = {r["case_id"]: r for r in results}
        
        total = len(requests_list)
        complete = sum(1 for r in results if r.get("deletion_status") == "COMPLETE")
        incomplete = sum(1 for r in results if r.get("deletion_status") == "INCOMPLETE")
        not_applicable = sum(1 for r in results if r.get("deletion_status") == "NOT_APPLICABLE")
        awaiting = total - len(results) if results else total

        # Count findings
        total_findings = 0
        active_risks = 0
        policy_violations = 0
        for r in results:
            try:
                steps = json.loads(r.get("steps_json", "[]"))
                findings = [s for s in steps if s.get("phase") == "FINDING"]
                total_findings += len(findings)
                active_risks += sum(1 for s in findings if s.get("operation") in {"REPORT_ACTIVE_DATA_FLOW", "REPORT_RESTORE_RISK"})
                policy_violations += sum(1 for s in findings if s.get("operation") in {"REPORT_REMAINING_RECORD", "REPORT_EXPOSED_PII"})
            except Exception:
                pass

        return jsonify({
            "total_requests": total,
            "complete": complete,
            "incomplete": incomplete,
            "not_applicable": not_applicable,
            "awaiting_investigation": awaiting,
            "total_findings": total_findings,
            "active_risks": active_risks,
            "policy_violations": policy_violations,
            "audit_status": _audit_state["status"],
            "last_audit_at": _audit_state["finished_at"],
        })
    except Exception as e:
        LOGGER.exception("Error computing dashboard stats")
        return jsonify({"error": str(e)}), 500


# === Requests ===
@app.route("/api/requests")
def get_requests():
    try:
        requests_list = load_requests()
        results = load_results()
        result_map = {r["case_id"]: r for r in results}

        q = request.args.get("q", "").lower()
        status_filter = request.args.get("status", "")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        sort_by = request.args.get("sort_by", "case_id")
        sort_dir = request.args.get("sort_dir", "asc")

        merged = []
        for req in requests_list:
            result = result_map.get(req["case_id"], {})
            ds = result.get("deletion_status", "PENDING")
            steps = []
            try:
                steps = json.loads(result.get("steps_json", "[]"))
            except Exception:
                pass
            findings_count = sum(1 for s in steps if s.get("phase") == "FINDING")
            merged.append({
                "case_id": req["case_id"],
                "email": req.get("email", ""),
                "requested_at": req.get("requested_at", ""),
                "reported_status": req.get("reported_status", ""),
                "audit_at": req.get("audit_at", ""),
                "deletion_status": ds,
                "findings_count": findings_count,
            })

        if q:
            merged = [m for m in merged if q in m["case_id"].lower() or q in m["email"].lower()]
        if status_filter:
            merged = [m for m in merged if m["deletion_status"] == status_filter]

        reverse = sort_dir == "desc"
        merged.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)

        total = len(merged)
        start = (page - 1) * per_page
        page_items = merged[start:start + per_page]

        return jsonify({
            "items": page_items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        })
    except Exception as e:
        LOGGER.exception("Error loading requests")
        return jsonify({"error": str(e)}), 500


# === Request Details ===
@app.route("/api/requests/<case_id>")
def get_request_detail(case_id):
    try:
        requests_list = load_requests()
        results = load_results()
        req = next((r for r in requests_list if r["case_id"] == case_id), None)
        if not req:
            return jsonify({"error": "Case not found"}), 404
        result = next((r for r in results if r["case_id"] == case_id), {})
        steps = []
        try:
            steps = json.loads(result.get("steps_json", "[]"))
        except Exception:
            pass
        findings = [s for s in steps if s.get("phase") == "FINDING"]
        remediation = [s for s in steps if s.get("phase") == "REMEDIATION"]
        verification = [s for s in steps if s.get("phase") == "VERIFICATION"]
        return jsonify({
            "case_id": case_id,
            "request": req,
            "deletion_status": result.get("deletion_status", "PENDING"),
            "steps": steps,
            "findings": findings,
            "remediation": remediation,
            "verification": verification,
        })
    except Exception as e:
        LOGGER.exception("Error loading request detail")
        return jsonify({"error": str(e)}), 500


# === Audit Run ===
def _run_audit_thread():
    global _cached_results, _cached_at
    _audit_state["status"] = "running"
    _audit_state["started_at"] = datetime.now(timezone.utc).isoformat()
    _audit_state["finished_at"] = None
    _audit_state["progress"] = 0
    _audit_state["error"] = None
    try:
        dataset = get_dataset_path()
        output_path = get_output_path()
        requests_list = audit_engine.read_csv(dataset / "deletion_requests.csv")
        _audit_state["total"] = len(requests_list)

        def on_progress(current, total):
            _audit_state["progress"] = current
            _audit_state["total"] = total

        # Run via the engine with live progress
        results = audit_engine.run_audit(dataset, output_path, progress_callback=on_progress)
        _audit_state["progress"] = len(results)
        _audit_state["results"] = results
        # Invalidate cache
        _cached_results = None
        _cached_at = None
        _audit_state["status"] = "complete"
    except Exception as e:
        LOGGER.exception("Audit run failed")
        _audit_state["status"] = "error"
        _audit_state["error"] = str(e)
    finally:
        _audit_state["finished_at"] = datetime.now(timezone.utc).isoformat()



@app.route("/api/audit/run", methods=["POST"])
def run_audit():
    with _audit_lock:
        if _audit_state["status"] == "running":
            return jsonify({"error": "Audit already running", "status": "running"}), 409
        t = threading.Thread(target=_run_audit_thread, daemon=True)
        t.start()
    return jsonify({"status": "started", "message": "Audit started in background"})


@app.route("/api/audit/status")
def audit_status():
    return jsonify({
        "status": _audit_state["status"],
        "started_at": _audit_state["started_at"],
        "finished_at": _audit_state["finished_at"],
        "progress": _audit_state["progress"],
        "total": _audit_state["total"],
        "error": _audit_state["error"],
    })


# === Evidence ===
@app.route("/api/evidence")
def list_evidence():
    try:
        manifest = load_evidence_manifest()
        q = request.args.get("q", "").lower()
        file_type = request.args.get("type", "")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        items = []
        for m in manifest:
            fp = m.get("file_path", "")
            ext = fp.rsplit(".", 1)[-1].lower() if "." in fp else ""
            items.append({
                "file_id": m.get("file_id", ""),
                "file_path": fp,
                "origin": m.get("origin", ""),
                "captured_at": m.get("captured_at", ""),
                "file_type": ext,
            })

        if q:
            items = [i for i in items if q in i["file_id"].lower() or q in i["file_path"].lower() or q in i["origin"].lower()]
        if file_type:
            items = [i for i in items if i["file_type"] == file_type]

        total = len(items)
        start = (page - 1) * per_page
        return jsonify({
            "items": items[start:start + per_page],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        })
    except Exception as e:
        LOGGER.exception("Error listing evidence")
        return jsonify({"error": str(e)}), 500


@app.route("/api/evidence/search")
def search_evidence():
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify({"error": "Query too short"}), 400
    try:
        manifest = load_evidence_manifest()
        ds = get_dataset_path()
        results = []
        for m in manifest:
            fp = (ds / m["file_path"]).resolve()
            try:
                text = fp.read_text(encoding="utf-8", errors="replace") if fp.suffix in {".txt", ".log", ".sql"} else ""
                if q.lower() in text.lower():
                    idx = text.lower().find(q.lower())
                    snippet = text[max(0, idx-100):idx+200]
                    results.append({
                        "file_id": m["file_id"],
                        "file_path": m["file_path"],
                        "snippet": snippet,
                        "captured_at": m.get("captured_at", ""),
                    })
            except Exception:
                pass
        return jsonify({"results": results[:50], "query": q, "total": len(results)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Remediation ===
@app.route("/api/remediation")
def get_remediation():
    try:
        results = load_results()
        items = []
        for r in results:
            if r.get("deletion_status") != "INCOMPLETE":
                continue
            steps = json.loads(r.get("steps_json", "[]"))
            findings = [s for s in steps if s.get("phase") == "FINDING"]
            remediation = [s for s in steps if s.get("phase") == "REMEDIATION"]
            items.append({
                "case_id": r["case_id"],
                "findings_count": len(findings),
                "remediation_steps": remediation,
            })
        return jsonify({"items": items, "total": len(items)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Evaluation ===
@app.route("/api/evaluation/report")
def evaluation_report():
    try:
        ds = get_dataset_path()
        sample_requests = audit_engine.read_csv(ds / "sample_deletion_requests.csv")
        sample_outputs = audit_engine.read_csv(ds / "sample_output.csv")
        results = load_results()
        result_map = {r["case_id"]: r for r in results}
        expected_map = {r["case_id"]: r for r in sample_outputs}

        correct = 0
        total = 0
        confusion = {"COMPLETE": {"COMPLETE":0,"INCOMPLETE":0,"NOT_APPLICABLE":0},
                     "INCOMPLETE": {"COMPLETE":0,"INCOMPLETE":0,"NOT_APPLICABLE":0},
                     "NOT_APPLICABLE": {"COMPLETE":0,"INCOMPLETE":0,"NOT_APPLICABLE":0}}
        per_class = {"COMPLETE":{"tp":0,"fp":0,"fn":0},
                     "INCOMPLETE":{"tp":0,"fp":0,"fn":0},
                     "NOT_APPLICABLE":{"tp":0,"fp":0,"fn":0}}

        for case_id, expected in expected_map.items():
            predicted = result_map.get(case_id, {})
            exp_status = expected.get("deletion_status", "")
            pred_status = predicted.get("deletion_status", "PENDING")
            if not exp_status:
                continue
            total += 1
            if pred_status == exp_status:
                correct += 1
                per_class[exp_status]["tp"] += 1
            else:
                per_class[exp_status]["fn"] += 1
                if pred_status in per_class:
                    per_class[pred_status]["fp"] += 1
            if exp_status in confusion and pred_status in confusion.get(exp_status, {}):
                confusion[exp_status][pred_status] += 1

        accuracy = correct / total if total else 0
        per_class_metrics = {}
        for cls, counts in per_class.items():
            tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
            prec = tp / (tp + fp) if (tp + fp) else 0
            rec = tp / (tp + fn) if (tp + fn) else 0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
            per_class_metrics[cls] = {"precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3)}

        return jsonify({
            "total_evaluated": total,
            "correct": correct,
            "accuracy": round(accuracy, 3),
            "per_class": per_class_metrics,
            "confusion_matrix": confusion,
            "sample_cases": len(sample_requests),
            "total_processed": len(results),
        })
    except Exception as e:
        LOGGER.exception("Evaluation failed")
        return jsonify({"error": str(e)}), 500


# === Output Download ===
@app.route("/api/output/download")
def download_output():
    out = get_output_path()
    if not out.exists():
        return jsonify({"error": "output.csv not found. Run audit first."}), 404
    return send_file(str(out), as_attachment=True, download_name="output.csv", mimetype="text/csv")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
