# Usage Report

## Final Dataset Run Summary

This usage report reflects the final full-dataset execution used to generate the repository-level `output.csv`.

- Execution entry point: `python code/main.py`
- Dataset: `dataset/deletion_requests.csv`
- Output file: `output.csv`
- Full-dataset run: 518 requests processed
- Status distribution:
  - `INCOMPLETE`: 394
  - `NOT_APPLICABLE`: 124
  - `COMPLETE`: 0

## Model Providers and Model Names

| Provider | Model | Calls | Input Tokens | Output Tokens | Cost |
| --- | --- | ---: | ---: | ---: | ---: |
| Local runtime / assistant | `MAI-Code-1.1-Flash` | 0 | 0 | 0 | $0.00 |
| External API provider | none | 0 | 0 | 0 | $0.00 |

> The final dataset run was a deterministic local program execution; no external LLM API calls were made during the challenge validation stage.

## Token and Cost Totals

- Total input tokens: 0
- Total output tokens: 0
- Total tokens: 0
- Average tokens per request: 0.00
- Estimated total cost: $0.00
- Estimated cost per request: $0.00

## Overall Totals

| Metric | Value |
| --- | ---: |
| Requests processed | 518 |
| Total input tokens | 0 |
| Total output tokens | 0 |
| Total tokens | 0 |
| Mean tokens/request | 0.00 |
| Estimated total cost | $0.00 |
| Estimated cost/request | $0.00 |

## Notes

- This repository’s challenge execution is based on local deterministic dataset processing rather than external model prompts.
- The official evaluation contract is satisfied by generating the exact root-level output file and archiving the required code bundle with the evaluation reports embedded under `code/evaluation/`.
