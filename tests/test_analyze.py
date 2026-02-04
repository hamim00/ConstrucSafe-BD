import base64


def _sample_image_bytes() -> bytes:
    """
    Return a valid tiny JPEG (1x1) as bytes.
    No external files and no Pillow dependency -> CI-safe + Pylance-safe.
    """
    b64 = (
        "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAEBAQEBAQEBAQEBAQEBAQEBA hooking "
        "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wCEAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/"
        "wAARCAAQABADASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAb/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAwT/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCkA//Z"
    )
    # NOTE: if you copy/paste, ensure no spaces/newlines inside the base64 string.
    return base64.b64decode(b64)


async def _fake_analyze_image(self, image_bytes: bytes, mode: str = "fast"):
    """
    Fake VisionAnalyzer output used by tests.
    Must contain keys your router expects (violations, flagged_for_review, image_quality).
    """
    return {
        "success": True,
        "violations": [
            {
                "violation_type": "PPE_GLOVES_MISSING",
                "description": "One worker is not wearing gloves while handling materials.",
                "severity": "medium",
                "confidence": "high",
                "location": "left foreground",
                "affected_parties": ["workers"],
            }
        ],
        "flagged_for_review": [],
        "image_quality": "good",
    }


def test_analyze_fast_mocked(client, monkeypatch):
    from backend.services import vision_analyzer

    monkeypatch.setattr(
        vision_analyzer.VisionAnalyzer,
        "analyze_image",
        _fake_analyze_image,
        raising=True,
    )

    files = {"file": ("sample.jpg", _sample_image_bytes(), "image/jpeg")}
    r = client.post("/api/v1/analyze?mode=fast&include_laws=true", files=files)

    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["violations_found"] >= 1
    assert isinstance(data.get("violations", []), list)


def test_analyze_accurate_mocked(client, monkeypatch):
    from backend.services import vision_analyzer

    monkeypatch.setattr(
        vision_analyzer.VisionAnalyzer,
        "analyze_image",
        _fake_analyze_image,
        raising=True,
    )

    files = {"file": ("sample.jpg", _sample_image_bytes(), "image/jpeg")}
    r = client.post("/api/v1/analyze?mode=accurate&include_laws=true", files=files)

    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["violations_found"] >= 1
    assert isinstance(data.get("violations", []), list)
