from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
SKILLS_PATH = Path(__file__).resolve().parent / "skills.json"
PORT = 8005
