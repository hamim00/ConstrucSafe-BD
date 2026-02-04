def test_laws_violations(client):
    r = client.get("/api/v1/laws/violations")
    assert r.status_code == 200
    data = r.json()
    assert "violations" in data
    assert isinstance(data["violations"], list)
    assert len(data["violations"]) > 10
    # spot check one known violation id
    assert "EXCAVATION_NO_BARRICADE" in data["violations"]
