from cubeai.api.health import health_response


def test_health_response() -> None:
    assert health_response() == {"status": "ok"}
