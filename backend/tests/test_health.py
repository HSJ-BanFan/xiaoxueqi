def test_h1_healthz(client):
    response = client.get("/api/v1/system/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_h2_readyz_database_ok(client):
    response = client.get("/api/v1/system/readyz")

    assert response.status_code == 200
    assert response.json()["checks"]["database"]["ok"] is True
