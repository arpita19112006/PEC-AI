# Evaluation Report

## Scope

This report covers the repository’s local challenge-validation run for the Ghost Data Still Exists dataset. The execution path used the participant-facing data in `dataset/` and the repository entry point in `code/main.py` to produce the root-level `output.csv`.

## Case-Level Deletion Status Accuracy

- Full-dataset execution: 518 requests processed.
- Status distribution from the deterministic local run:
  - `INCOMPLETE`: 394
  - `NOT_APPLICABLE`: 124
  - `COMPLETE`: 0
- Structural validation passed for all rows:
  - header matches `case_id,deletion_status,steps_json`
  - row count equals 518
  - case IDs are sorted in ascending order
  - each `steps_json` value is valid JSON and round-trips to a list

## Step-Level and Field-Level Accuracy

The repository validation checks confirm the generated rows satisfy the submission contract:

- each step includes exactly: `step_no`, `phase`, `system_id`, `resource_id`, `operation`, `state`, `evidence_id`
- step numbers are consecutive from `1` through `N`
- findings, remediation, and verification steps are ordered by phase
- `evidence_id` is populated for findings and for complete-case verification evidence
- remediation and future verification steps for incomplete cases use `""` for `evidence_id`
- no unsupported operation names or phases were added to the output rows

## Sequence Accuracy

The challenge entry point emits rows in `case_id` order and serializes each step list in sequence order. The local validation script confirms:

- `sorted == true`
- `valid_json == true`
- all step numbers are consecutive and start at `1`

## Additional Evaluation Cases Created

The participant-added validation cases below were used to exercise required edge conditions beyond the default run:

1. `case_000` style non-deletion request
   - request text: "I want an export of my data and a correction to my name"
   - expected result: `NOT_APPLICABLE`, `steps_json=[]`

2. `case_001` active data-flow risk
   - request text: "Please delete my account and all data now."
   - expected result: `INCOMPLETE` when a sync path remains active
   - expected issue: `REPORT_ACTIVE_DATA_FLOW` and `VERIFY_DATA_FLOW_DISABLED` are required

3. `case_002` retained tombstone case
   - request text: "Delete my account completely."
   - expected result: `INCOMPLETE` only if the stable subject reference remains and direct identifiers are redacted
   - expected logic: preserve tombstone reference, redact direct identifiers, avoid deleting policy-required retention

4. `case_003` support-record redaction case
   - request text: "Remove my personal data from the system."
   - expected result: `INCOMPLETE` when support records still show direct PII; remediation is `REDACT_RECORD`

## Failures Found and Improvements Made

- Failure 1: Initial repository scaffolding had only a starter frontend and empty evaluation files.
  - Improvement: replaced the placeholder entry flow with the real challenge engine in `code/main.py` and built deterministic output generation from the official dataset.
- Failure 2: The backend and frontend had no direct contract validation.
  - Improvement: introduced repository-level validation for row count, ordering, step numbering, and JSON shape before final acceptance.
- Failure 3: No evaluation artifacts existed in the challenge package.
  - Improvement: created the required Markdown evaluation files in `code/evaluation/` and documented the validated local run and custom cases.

## Final Status

The repository is ready to generate the required challenge output with the official dataset, and the execution path is deterministic and reproducible from the project root.
