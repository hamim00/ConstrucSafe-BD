import pathlib

def _sample_image_bytes():
    p = pathlib.Path(__file__).parent / "test_images" / "sample.jfif"
    return p.read_bytes()

async def _fake_analyze_image(self, image_bytes: bytes, mode: str = "fast"):
    # Return dict that matches what backend.routers.analyze expects.
    # IMPORTANT: DetectedViolation requires specific fields and enums.
    return {
        "success": True,
        "violations": [
            {
                "violation_type": "EXCAVATION_NO_BARRICADE",
                "description": f"Excavation area lacks barricades. (mode={mode})",
                "severity": "high",
                "confidence": "high",
                "location": "excavation edge",
                "affected_parties": ["workers", "public"],
            }
        ],
    }

def test_analyze_fast_mocked(client, monkeypatch):
    from backend.services import vision_analyzer

    monkeypatch.setattr(vision_analyzer.VisionAnalyzer, "analyze_image", _fake_analyze_image, raising=True)

    files = {"file": ("sample.jfif", _sample_image_bytes(), "image/jpeg")}
    r = client.post("/api/v1/analyze?include_laws=true&mode=fast", files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["success"] is True
    assert data["violations_found"] == 1
    assert len(data["violations"]) == 1
    v0 = data["violations"][0]["violation"]
    assert v0["violation_type"] == "EXCAVATION_NO_BARRICADE"

def test_analyze_accurate_mocked(client, monkeypatch):
    from backend.services import vision_analyzer

    monkeypatch.setattr(vision_analyzer.VisionAnalyzer, "analyze_image", _fake_analyze_image, raising=True)

    files = {"file": ("sample.jfif", _sample_image_bytes(), "image/jpeg")}
    r = client.post("/api/v1/analyze?include_laws=true&mode=accurate", files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["success"] is True
    assert data["violations_found"] == 1
