import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    print("--- Testing /health Endpoint ---")
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "insight-copilot-backend"
    print(f"[PASS] /health returned: {data}")


def test_dataset_profile_endpoint():
    print("--- Testing /api/dataset/profile Endpoint ---")
    response = client.get("/api/dataset/profile")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("total_rows") > 50000
    assert "price" in data.get("metrics_summary", {}) or "Sales" in data.get("metrics_summary", {})
    print(f"[PASS] /api/dataset/profile returned {data['total_rows']:,} rows, {len(data['columns'])} columns.")


def test_threads_endpoint():
    print("--- Testing /api/threads/{thread_id} Endpoint ---")
    response = client.get("/api/threads/test-empty-thread")
    assert response.status_code == 200
    data = response.json()
    assert data.get("thread_id") == "test-empty-thread"
    assert "messages" in data
    print(f"[PASS] /api/threads/test-empty-thread returned: {data}")


if __name__ == "__main__":
    test_health_endpoint()
    test_dataset_profile_endpoint()
    test_threads_endpoint()
    print("\nALL FASTAPI ENDPOINT TESTS PASSED SUCCESSFULLY!")
