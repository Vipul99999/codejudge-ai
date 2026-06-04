from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "static-analysis-only"


def test_analyze_endpoint_records_benchmark() -> None:
    response = client.post("/api/analyze", json={"language": "python", "code": "def f(x):\n    return x + 1\n"})
    assert response.status_code == 200
    assert "overall_score" in response.json()

    summary = client.get("/api/benchmarks")
    assert summary.status_code == 200
    assert summary.json()["evaluations_performed"] >= 1
