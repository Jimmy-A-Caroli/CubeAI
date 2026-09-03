from cubeai.api.health import application, health_response


def test_health_response() -> None:
    assert health_response() == {"status": "ok"}


def test_health_application_serves_the_connectivity_endpoint() -> None:
    received: list[tuple[str, list[tuple[str, str]]]] = []

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        received.append((status, headers))

    body = application(
        {"PATH_INFO": "/health", "REQUEST_METHOD": "GET"},
        start_response,
    )

    assert received == [("200 OK", [("Content-Type", "application/json")])]
    assert body == [b'{"status": "ok"}']
