from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = Path(os.environ.get('DATASET_PATH', ROOT / 'dataset'))
OUTPUT_PATH = Path(os.environ.get('OUTPUT_PATH', ROOT / 'output.csv'))
EVIDENCE_PATH = DATASET_PATH / 'evidence'

ALLOWED_EXTENSIONS = {'.csv', '.json', '.txt', '.log', '.sql', '.pdf', '.png'}
