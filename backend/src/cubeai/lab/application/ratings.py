"""Load the reviewed, package-local CubeAI Bot v0 rating artifact."""

import json
from importlib.resources import files

from cubeai.lab.domain.bot import (
    RatingArtifact,
    RatingArtifactProvenance,
    RatingEntry,
)


def _required_text(payload: dict[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"raw-ranking-v0 artifact {field} must be a nonblank string")
    return value


def _required_finite_number(payload: dict[str, object], field: str) -> float:
    value = payload.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"raw-ranking-v0 artifact {field} must be numeric")
    return float(value)


def load_raw_ranking_v0_artifact() -> RatingArtifact:
    """Return the immutable package-local CubeAI-owned Bot v0 artifact."""

    resource = files("cubeai.lab").joinpath("resources/raw-ranking-v0.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("raw-ranking-v0 artifact must be an object")
    ratings = payload.get("ratings")
    if not isinstance(ratings, list):
        raise ValueError("raw-ranking-v0 artifact ratings must be an array")
    if any(not isinstance(item, dict) for item in ratings):
        raise ValueError("raw-ranking-v0 artifact ratings must contain objects")
    entries = tuple(
        RatingEntry(
            _required_text(item, "oracle_id"), _required_finite_number(item, "rating")
        )
        for item in ratings
    )
    fallback = payload.get("fallback")
    if not isinstance(fallback, dict):
        raise ValueError("raw-ranking-v0 artifact fallback must be an object")
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("raw-ranking-v0 artifact provenance must be an object")
    return RatingArtifact(
        _required_text(payload, "artifact_id"),
        _required_text(payload, "artifact_version"),
        _required_text(payload, "ownership"),
        _required_text(payload, "basis"),
        _required_text(payload, "rights"),
        entries,
        _required_finite_number(fallback, "rating"),
        RatingArtifactProvenance(
            _required_text(provenance, "source_name"),
            _required_text(provenance, "source_url"),
            _required_text(provenance, "source_updated"),
            _required_text(provenance, "acquired_date"),
            _required_text(provenance, "transformation_method"),
        ),
    )
