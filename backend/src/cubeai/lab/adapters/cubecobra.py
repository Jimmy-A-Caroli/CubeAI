"""Bounded CubeCobra JSON adapter using the frozen public contract."""

import json
import urllib.error
import urllib.request
from datetime import datetime, UTC
from typing import Any
from cubeai.lab.application.imports import (
    CandidateResolution,
    CubeSource,
    DiagnosticCode,
    DiagnosticSeverity,
    ImportCandidate,
    ImportDiagnostic,
    ImportResult,
    SourceRequest,
    SourceSnapshotReference,
)


class CubeCobraAdapterError(RuntimeError):
    def __init__(self, code: DiagnosticCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CubeCobraSource(CubeSource):
    def __init__(
        self,
        *,
        base_url: str = "https://cubecobra.com",
        timeout: float = 10.0,
        retries: int = 1,
        user_agent: str = "CubeAI/0.1",
    ) -> None:
        if timeout <= 0 or not 0 <= retries <= 2:
            raise ValueError("invalid timeout or retries")
        self.base_url, self.timeout, self.retries, self.user_agent = (
            base_url.rstrip("/"),
            timeout,
            retries,
            user_agent,
        )

    @staticmethod
    def endpoint(identifier: str) -> str:
        value = identifier.strip()
        if not value or any(char in value for char in "/?#"):
            raise CubeCobraAdapterError(
                DiagnosticCode.INVALID_SOURCE_RECORD, "invalid CubeCobra identifier"
            )
        return value

    def import_cube(self, request: SourceRequest) -> ImportResult:
        if request.source.lower() != "cubecobra":
            raise CubeCobraAdapterError(
                DiagnosticCode.UNSUPPORTED_SOURCE_CONTRACT, "unsupported source"
            )
        identifier = self.endpoint(request.identifier)
        url = f"{self.base_url}/cube/api/cubeJSON/{identifier}"
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    if response.status != 200:
                        raise CubeCobraAdapterError(
                            DiagnosticCode.TRANSPORT_FAILURE, f"HTTP {response.status}"
                        )
                    payload = json.loads(response.read())
                return self._map(payload, url)
            except CubeCobraAdapterError:
                raise
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                if attempt == self.retries:
                    raise CubeCobraAdapterError(
                        DiagnosticCode.TRANSPORT_FAILURE, "CubeCobra request failed"
                    ) from exc
        raise AssertionError

    def _map(self, payload: Any, url: str) -> ImportResult:
        if not isinstance(payload, dict) or any(
            not isinstance(payload.get(k), str) or not payload[k].strip()
            for k in ("id", "name")
        ):
            raise CubeCobraAdapterError(
                DiagnosticCode.INVALID_SOURCE_RECORD, "invalid CubeCobra response"
            )
        if payload.get("visibility") != "pu":
            raise CubeCobraAdapterError(
                DiagnosticCode.UNSUPPORTED_SOURCE_CONTRACT, "cube is not public"
            )
        cards = payload.get("cards")
        if not isinstance(cards, dict):
            raise CubeCobraAdapterError(
                DiagnosticCode.INVALID_SOURCE_RECORD, "cards must be an object"
            )
        rows = cards.get("mainboard") if isinstance(cards, dict) else None
        if not isinstance(rows, list) or not rows:
            raise CubeCobraAdapterError(
                DiagnosticCode.INVALID_SOURCE_RECORD, "mainboard must be nonempty"
            )
        snapshot = SourceSnapshotReference(
            "cubecobra", payload["id"], datetime.now(UTC).isoformat(), url
        )
        candidates = []
        for pos, row in enumerate(rows):
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("cardID"), str)
                or not row["cardID"].strip()
            ):
                raise CubeCobraAdapterError(
                    DiagnosticCode.INVALID_SOURCE_RECORD, "invalid mainboard row"
                )
            details: dict[str, Any] = (
                row["details"] if isinstance(row.get("details"), dict) else {}
            )
            printing = details.get("scryfall_id")
            tags: list[Any] = row["tags"] if isinstance(row.get("tags"), list) else []
            candidates.append(
                ImportCandidate(
                    f"{payload['id']}:{pos}",
                    snapshot,
                    pos,
                    row["cardID"],
                    row.get("board"),
                    tuple(t for t in tags if isinstance(t, str) and t.strip()),
                    row.get("notes")
                    if isinstance(row.get("notes"), str) and row["notes"]
                    else None,
                    printing if isinstance(printing, str) and printing else None,
                    row.get("custom_name")
                    if isinstance(row.get("custom_name"), str) and row["custom_name"]
                    else None,
                    CandidateResolution.RESOLUTION_HINTED
                    if printing
                    else CandidateResolution.UNRESOLVED,
                    ("details.oracle_id",) if details.get("oracle_id") else (),
                )
            )
        diagnostics = tuple(
            ImportDiagnostic(
                DiagnosticCode.UNSUPPORTED_SOURCE_CONTRACT,
                DiagnosticSeverity.WARNING,
                f"non-mainboard data ignored: {name}",
                snapshot,
            )
            for name, value in cards.items()
            if name != "mainboard" and isinstance(value, list) and value
        )
        return ImportResult(snapshot, tuple(candidates), diagnostics)
