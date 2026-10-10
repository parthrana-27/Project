import pytest
from fastapi.testclient import TestClient
from nl2code.backend.app.main import app
from nl2code.backend.app.models.db import init_db

init_db()
client = TestClient(app)

def test_start_compilation_async():
    response = client.post(
        "/api/compile",
        json={
            "prompt": "Write a function that returns the k most frequent elements in an array",
            "language": "python",
            "max_repairs": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "started"
    assert "/api/compile/" in data["stream_url"]

def test_sync_compilation_and_history():
    # 1. Run sync compile
    response = client.post(
        "/api/compile/sync",
        json={
            "prompt": "Write a function that returns the k most frequent elements in an array",
            "language": "python",
            "max_repairs": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "completed"
    assert "def top_k_frequent" in data["generated_code"]
    assert data["ir"] is not None
    job_id = data["job_id"]

    # 2. Check history list
    hist_resp = client.get("/api/history")
    assert hist_resp.status_code == 200
    records = hist_resp.json()
    assert len(records) > 0
    assert any(r["id"] == job_id for r in records)

    # 3. Check history detail
    detail_resp = client.get(f"/api/history/{job_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == job_id
    assert detail["success"] is True
    assert detail["ir"]["function_name"] == "top_k_frequent"
    assert detail["test_summary"]["passed_tests"] == detail["test_summary"]["total_tests"]

    # 4. Export JSON
    export_resp = client.get(f"/api/history/{job_id}/export")
    assert export_resp.status_code == 200
    export_json = export_resp.json()
    assert export_json["id"] == job_id

    # 5. Delete record
    del_resp = client.delete(f"/api/history/{job_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # 6. Verify 404 after delete
    verify_resp = client.get(f"/api/history/{job_id}")
    assert verify_resp.status_code == 404
