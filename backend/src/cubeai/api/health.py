"""Minimal health endpoint for the local connectivity slice."""

import json


def health_response() -> dict[str, str]:
    return {"status": "ok"}


def application(environ: dict[str, object], start_response: object) -> list[bytes]:
    if environ.get("PATH_INFO") == "/health" and environ.get("REQUEST_METHOD") == "GET":
        status, body = "200 OK", json.dumps(health_response()).encode()
    else:
        status, body = "404 Not Found", b"Not found"
    assert callable(start_response)
    start_response(status, [("Content-Type", "application/json")])
    return [body]
