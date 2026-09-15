from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_exposes_mausam_metrics():
    response = client.get("/metrics")

    assert response.status_code == 200

    body = response.text

    assert "mausam_provider_requests_total" in body
    assert "mausam_provider_retries_total" in body
    assert "mausam_provider_rate_limits_total" in body
    assert "mausam_provider_failures_total" in body
    assert (
        "mausam_provider_request_duration_seconds"
        in body
    )
    assert "mausam_cache_access_total" in body