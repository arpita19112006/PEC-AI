# Ghost Data Still Exists
## AI-Powered Data Deletion Audit Agent

An automated data deletion auditing system that helps identify whether requested data deletion has been completed, remains incomplete, or is not applicable. The project provides a web-based dashboard for monitoring deletion requests, reviewing evidence, running audits, and examining audit results.

---

## 1. Project Overview

When a user requests deletion of personal information, an organization may need to verify whether the relevant records have actually been deleted across its systems.

In practice, data may remain in backups, logs, replicated databases, archived files, or other storage locations. A deletion request should therefore be evaluated using the available evidence and the applicable deletion rules.

**Ghost Data Still Exists** is a project designed to audit deletion requests using a dataset, evidence files, and predefined rules. It includes a React-based frontend and a Python Flask backend to provide an interactive interface for reviewing audit information.

### Problem Statement

Organizations may face difficulties verifying data deletion because:

- Deletion requests can involve multiple systems.
- Records may remain in storage after a deletion request.
- Evidence may be distributed across different files and logs.
- Manual verification can be time-consuming.
- Audit results need to be recorded in a consistent format.
- Reviewers need a convenient way to monitor requests and identify potential risks.

### Proposed Solution

The project provides a centralized dashboard that connects to a backend audit engine. It reads deletion-request data, evaluates available evidence according to the implemented audit logic, and exposes results through API endpoints.

The dashboard is intended to make deletion-audit information easier to review, monitor, and investigate.

---

## 2. Objectives

The primary objectives of the project are:

1. Read and process deletion-request records from CSV datasets.
2. Evaluate requests using the configured deletion rules and available evidence.
3. Classify requests according to the audit engine's supported statuses.
4. Generate structured audit output in CSV format.
5. Display request statistics and audit information in a web dashboard.
6. Provide request-level details for investigation.
7. Allow users to explore available evidence and remediation information.
8. Expose REST API endpoints for communication between the frontend and backend.
9. Validate the generated output against the required format.
10. Provide a foundation for improving deletion verification and audit reporting.

---

## 3. Key Features

### 3.1 Dashboard

The dashboard provides an overview of the audit system, including available request statistics, findings, and audit status.

Expected features include:

- Total deletion requests
- Complete, incomplete, and not-applicable classifications, where supported by the backend
- Audit status and progress
- Dataset and output-file availability
- Recent deletion requests
- Audit-related charts and summaries

The values should come from the backend rather than hardcoded frontend examples.

### 3.2 Deletion Request Management

The deletion-request interface allows users to review records loaded from the dataset.

It can be used to inspect request identifiers, deletion status, and other fields returned by the backend.

### 3.3 Request Details

The request details page is intended to display information associated with an individual deletion case. This helps users investigate why a request received a particular classification.

### 3.4 Evidence Explorer

The evidence explorer provides an interface for reviewing available evidence records and searching for relevant evidence.

The evidence available to the application depends on the supplied dataset and evidence files.

### 3.5 Remediation

The remediation section presents remediation-related information available from the backend. It can help reviewers understand what action may be required for unresolved findings.

### 3.6 Evaluation and Reporting

The evaluation page provides access to audit evaluation information and reports, where available.

The generated output should be checked for the required columns, row count, valid JSON fields, and sorting requirements specified by the challenge.

### 3.7 Run Audit

The Run Audit feature starts an audit through the backend API. The frontend can then check the audit status and refresh the dashboard when processing finishes.

### 3.8 Error Handling

The frontend should show meaningful loading and error messages when an API request fails, instead of silently displaying zero values.

---

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Audit logic and backend programming |
| Flask | REST API and backend web server |
| Flask-CORS | Cross-origin communication between frontend and backend |
| Pandas | Tabular data processing, where used by the audit implementation |
| React | Frontend user interface |
| Vite | Frontend development server and build tool |
| JavaScript / JSX | Frontend application logic |
| Axios | HTTP requests from frontend to backend |
| Recharts | Data visualization in the dashboard |
| HTML5 | Webpage structure |
| CSS3 | Styling and responsive layouts |
| CSV | Storage of request data and audit output |
| JSON | API responses and structured audit steps |

*Note: The technologies listed above reflect the project's described setup. Actual library usage should be confirmed against the source files and dependency manifests.*

---

## 5. System Architecture

The application follows a frontend-backend architecture.

```text
                 USER
                   |
                   v
        React + Vite Frontend
          localhost:5173
                   |
                   | HTTP / REST API
                   v
            Flask Backend
          127.0.0.1:5000
                   |
          +--------+---------+
          |        |         |
          v        v         v
       Dataset   Evidence   Audit Engine
        CSV       Files    code/main.py
          |        |         |
          +--------+---------+
                   |
                   v
             Audit Results
                output.csv
                   |
                   v
           Dashboard / Reports
```

### Working Principle

1. The user opens the dashboard in a web browser.
2. The React frontend sends HTTP requests to the Flask backend.
3. The backend reads the configured dataset and evidence files.
4. The audit engine evaluates deletion requests according to its implemented rules.
5. The results are written to the configured output file when an audit is executed.
6. The frontend retrieves the available statistics and audit status.
7. The dashboard presents the returned information to the user.

---

## 6. Project Directory Structure

The main project directory is organized approximately as follows:

```text
hackerrank-orchestrate-october26/
│
├── README.md
├── code/
│   └── main.py
│
├── dataset/
│   ├── deletion_requests.csv
│   ├── deletion_rules.csv
│   ├── evidence_files.csv
│   ├── system_activity.csv
│   ├── user_audit_log.csv
│   ├── user_identities.csv
│   ├── sample_deletion_requests.csv
│   ├── sample_output.csv
│   ├── output.csv
│   └── evidence/
│       └── evidence files
│
├── output.csv
│
├── evaluation/
│   ├── evaluation_report.md
│   └── usage_report.md
│
└── ghost-data-auditor/
    │
    ├── backend/
    │   ├── app.py
    │   ├── config.py
    │   ├── requirements.txt
    │   ├── routes/
    │   ├── services/
    │   └── tests/
    │
    └── frontend/
        ├── package.json
        ├── index.html
        ├── vite.config.js
        └── src/
            ├── api/
            │   └── client.js
            ├── components/
            ├── pages/
            │   ├── Dashboard.jsx
            │   ├── DeletionRequests.jsx
            │   ├── RequestDetails.jsx
            │   ├── EvidenceExplorer.jsx
            │   ├── Remediation.jsx
            │   ├── Evaluation.jsx
            │   └── Settings.jsx
            ├── App.jsx
            ├── App.css
            └── main.jsx
```

The exact files may differ depending on the current version of the repository. Preserve the original challenge files and evaluation data.

### Important Files

- `code/main.py` — contains the core audit engine.
- `dataset/deletion_requests.csv` — contains deletion-request records.
- `dataset/deletion_rules.csv` — contains deletion rules used by the challenge.
- `dataset/evidence_files.csv` — contains evidence metadata.
- `dataset/evidence/` — contains evidence files.
- `output.csv` — stores the audit output at the configured location.
- `ghost-data-auditor/backend/app.py` — defines the Flask application and API endpoints.
- `ghost-data-auditor/backend/config.py` — defines dataset, evidence, and output paths.
- `ghost-data-auditor/frontend/src/api/client.js` — configures frontend API communication.
- `ghost-data-auditor/frontend/src/pages/Dashboard.jsx` — implements the main dashboard.

---

## 7. Installation and Setup

### Prerequisites

Install the following software before running the project:

- Python 3.11 or another compatible Python version
- Node.js and npm
- Visual Studio Code
- Git, if you are cloning the repository

Verify the installations:

```powershell
python --version
node --version
npm.cmd --version
git --version
```

### Step 1: Open the Project

Open VS Code and select **File → Open Folder**.

Choose the project directory:

```text
C:\Users\arpit\Desktop\GitProjects\hackerrank-orchestrate-october26
```

Open the integrated terminal using **Terminal → New Terminal**.

### Step 2: Install Backend Dependencies

Run:

```powershell
cd "C:\Users\arpit\Desktop\GitProjects\hackerrank-orchestrate-october26"
python -m pip install -r ghost-data-auditor/backend/requirements.txt
```

This installs the packages listed in the backend requirements file.

### Step 3: Install Frontend Dependencies

Open another terminal and run:

```powershell
cd "C:\Users\arpit\Desktop\GitProjects\hackerrank-orchestrate-october26\ghost-data-auditor\frontend"
npm.cmd install
```

The `npm.cmd` command can be used in Windows PowerShell if the PowerShell execution policy blocks `npm.ps1`.

---

## 8. How to Run the Project

The frontend and backend run independently. Keep both terminal windows open.

### Terminal 1: Start the Flask Backend

From the project root, run:

```powershell
cd "C:\Users\arpit\Desktop\GitProjects\hackerrank-orchestrate-october26"
python ghost-data-auditor/backend/app.py
```

The backend should display an address similar to:

```text
Running on http://127.0.0.1:5000
```

Do not close this terminal while using the application.

### Terminal 2: Start the React Frontend

Open a new terminal and run:

```powershell
cd "C:\Users\arpit\Desktop\GitProjects\hackerrank-orchestrate-october26\ghost-data-auditor\frontend"
npm.cmd run dev
```

Vite should display a local development URL, commonly:

```text
http://localhost:5173/
```

Open that URL in your browser.

### Application URLs

| Component | URL |
|---|---|
| Frontend dashboard | http://localhost:5173/ |
| Flask backend | http://127.0.0.1:5000/ |
| Backend health check | http://127.0.0.1:5000/api/health |
| Dashboard statistics | http://127.0.0.1:5000/api/dashboard/stats |
| Deletion requests | http://127.0.0.1:5000/api/requests |

If the browser displays `ERR_CONNECTION_REFUSED`, verify that the corresponding server is running and that you are using the correct port.

---

## 9. Backend API Endpoints

The Flask backend exposes API endpoints for the frontend.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Checks backend health and resource availability |
| GET | `/api/dashboard/stats` | Retrieves dashboard statistics |
| GET | `/api/requests` | Retrieves deletion requests |
| GET | `/api/requests/<case_id>` | Retrieves details for a specific case |
| POST | `/api/audit/run` | Requests a new audit run |
| GET | `/api/audit/status` | Retrieves the current audit status |
| GET | `/api/evidence` | Retrieves available evidence records |
| GET | `/api/evidence/search` | Searches available evidence |
| GET | `/api/remediation` | Retrieves remediation-related information |
| GET | `/api/evaluation/report` | Retrieves evaluation information |
| GET | `/api/output/download` | Provides access to the audit output |

The exact response fields, query parameters, and error codes are defined by the implementation in `backend/app.py` and its supporting modules.

### Example: Health Check

Open:

```text
http://127.0.0.1:5000/api/health
```

A healthy response should indicate that the backend is operating and report the availability of configured resources.

### Example: Dashboard Statistics

Open:

```text
http://127.0.0.1:5000/api/dashboard/stats
```

The returned JSON contains the statistics used by the dashboard.

### Example: Retrieve Deletion Requests

Open:

```text
http://127.0.0.1:5000/api/requests
```

The endpoint returns deletion-request data in the format defined by the backend.

---

## 10. Audit Processing

The audit engine is implemented in `code/main.py`.

At a high level, the workflow is:

1. Load the deletion-request dataset.
2. Read the relevant rules and evidence records.
3. Evaluate each request according to the implemented audit logic.
4. Determine the applicable status and audit steps.
5. Produce structured results.
6. Write the output to the configured CSV file.
7. Validate the output against the challenge requirements.

### Audit Statuses

The dataset and backend use classifications such as:

- **COMPLETE** — indicates that the implemented audit criteria for completion have been satisfied.
- **INCOMPLETE** — indicates that the audit criteria for completion have not been satisfied.
- **NOT_APPLICABLE** — indicates that the applicable rules classify the case as not applicable.

The precise classification criteria must be taken from the actual rules and challenge specification. These labels alone do not prove that data has been physically deleted from every system.

### Output Format

The challenge output is expected to contain the following columns:

```csv
case_id,deletion_status,steps_json
```

- `case_id` identifies the deletion case.
- `deletion_status` contains the audit classification.
- `steps_json` contains structured audit steps in JSON format.

The generated output should preserve the required row count, ordering, field names, and JSON validity specified by the challenge.

---

## 11. Testing and Verification

### Check Backend Health

Run this command in a separate terminal:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/api/health').read().decode())"
```

### Check Dashboard Statistics

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/api/dashboard/stats').read().decode())"
```

### Check Request Count

```powershell
python -c "import urllib.request,json; d=json.loads(urllib.request.urlopen('http://127.0.0.1:5000/api/requests?page=1&per_page=3').read().decode()); print('Total requests:',d['total']); print('Records returned:',len(d['items']))"
```

The response fields may differ if the backend API has been changed.

### Build the Frontend

From the frontend directory:

```powershell
npm.cmd run build
```

A successful build checks whether the frontend can be compiled. It does not, by itself, verify that the backend integration or audit results are correct.

### Validate the Audit Output

The project includes validation logic in `code/main.py`. After confirming the expected function signature, run:

```powershell
python -c "import sys; sys.path.insert(0,'code'); import main; from pathlib import Path; print(main.validate_output(Path('output.csv'),main.read_csv(Path('dataset/deletion_requests.csv'))))"
```

This command checks the output using the project's own validation function. Run it only if those functions are present with the shown signatures in your current version.

### Important Testing Notes

- Verify the output after a new audit run.
- Compare the results against the official challenge requirements.
- Do not overwrite `dataset/sample_output.csv` or other original evaluation files.
- Do not assume that a valid CSV is equivalent to a correct audit.
- Record any failed tests and investigate them before submission.

---

## 12. Troubleshooting

### Problem 1: `localhost` refused to connect

**Possible cause:** The frontend server is not running.

**Solution:**

```powershell
npm.cmd run dev
```

Run this from the frontend directory and use the local URL shown in the terminal.

### Problem 2: Backend is unavailable

**Possible cause:** Flask is stopped or running on a different port.

**Solution:**

```powershell
python ghost-data-auditor/backend/app.py
```

Run this from the project root.

### Problem 3: Dashboard displays zeros

**Possible causes:**

- The frontend cannot reach the backend.
- An API request is failing.
- The response structure does not match the frontend's expectations.
- The backend is reading a different dataset or output file.

**Solution:** Check `/api/health`, `/api/dashboard/stats`, and `/api/requests` directly in the browser. Then inspect the browser developer console and terminal logs.

### Problem 4: PowerShell blocks npm

**Solution:** Use:

```powershell
npm.cmd install
npm.cmd run dev
```

### Problem 5: Dataset or output file is missing

**Possible cause:** The backend configuration points to an incorrect path.

**Solution:** Inspect `ghost-data-auditor/backend/config.py` and confirm that the configured paths point to the intended project-root files.

### Problem 6: Audit does not finish

**Possible cause:** An exception occurred during processing or the audit status is not being updated.

**Solution:** Inspect the Flask terminal logs, the `/api/audit/status` response, and the audit engine's error handling.

---

## 13. Security and Limitations

This project is intended for local development and challenge evaluation.

- Flask's development server is not intended for production deployment.
- The dashboard should not be considered proof of physical deletion without independent verification.
- Audit conclusions depend on the completeness and accuracy of the supplied evidence and rules.
- The application should be tested against the challenge's official evaluation requirements.
- Sensitive production data should not be exposed through an unauthenticated development server.
- Production deployment would require appropriate authentication, authorization, logging, secure configuration, and operational monitoring.

---

## 14. Future Enhancements

Possible improvements include:

1. Add authentication and role-based access control.
2. Improve audit progress tracking and failure recovery.
3. Add advanced evidence filtering and search.
4. Provide downloadable audit reports.
5. Add stronger validation and automated regression tests.
6. Improve visualizations of incomplete requests and risk categories.
7. Add audit history and comparison between runs.
8. Integrate with authorized storage systems for independent deletion verification.
9. Add secure audit logs and a record of remediation actions.
10. Deploy the application using a production-grade web server and secure configuration.

These are proposed enhancements, not claims that the current implementation already supports them.

---

## 15. Conclusion

**Ghost Data Still Exists — AI-Powered Data Deletion Audit Agent** provides a framework for evaluating data deletion requests using a Python audit engine, a Flask API, and a React web dashboard.

By centralizing request records, audit classifications, evidence, and evaluation information, the project aims to make deletion audits easier to inspect and manage. Its reliability ultimately depends on the correctness of the implemented audit rules, the quality of the evidence, and successful verification against the official challenge requirements.

---

## 16. Project Information

- **Project Name:** Ghost Data Still Exists
- **Project Type:** Data Deletion Audit Agent
- **Frontend:** React + Vite
- **Backend:** Python + Flask
- **Data Format:** CSV and JSON
- **Development Environment:** Visual Studio Code
- **Challenge:** HackerRank Orchestrate — October 2026

**Repository:** Add your GitHub repository URL here after publishing the project.

**Author:** Add your name or team members here.

