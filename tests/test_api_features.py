import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from api import app

def test_extract_problem_preset():
    client = app.test_client()
    res = client.post("/api/extract-problem", json={"text": "nelder mead function"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "Rosenbrock" in data["name"]
    assert "x1" in data["objective"]
    assert data["dimensions"] == 2

def test_extract_problem_custom_formula():
    client = app.test_client()
    res = client.post("/api/extract-problem", json={"text": "x1**2 + x2**2"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["objective"] == "x1**2 + x2**2"

def test_ask_info_local_fallback():
    client = app.test_client()
    res = client.post("/api/ask-info", json={
        "question": "how does Nelder-Mead behave?",
        "objective": "x1**2 + x2**2"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["answer"]) > 20
