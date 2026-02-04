import os
import sys
import pathlib
import pytest
from fastapi.testclient import TestClient

# Ensure project root is on PYTHONPATH for pytest import-mode variations.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure laws path resolves during tests
os.environ.setdefault("LAWS_JSON_PATH", "backend/data/laws.json")

@pytest.fixture()
def client():
    from backend.main import app
    return TestClient(app)
