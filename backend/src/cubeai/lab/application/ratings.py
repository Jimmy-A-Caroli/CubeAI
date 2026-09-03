"""Load the reviewed, package-local CubeAI Bot v0 rating artifact."""

import json
from importlib.resources import files

from cubeai.lab.domain.bot import RatingArtifact, RatingEntry


def load_raw_ranking_v0_artifact() -> RatingArtifact:
    """Return the immutable package-local CubeAI-owned Bot v0 artifact."""

    resource = files("cubeai.lab").joinpath("resources/raw-ranking-v0.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("raw-ranking-v0 artifact must be an object")
    ratings = payload.get("ratings")
    if not isinstance(ratings, list):
        raise ValueError("raw-ranking-v0 artifact ratings must be an array")
    entries = tuple(
        RatingEntry(item["oracle_id"], item["rating"])
        for item in ratings
        if isinstance(item, dict)
    )
    if len(entries) != len(ratings):
        raise ValueError("raw-ranking-v0 artifact ratings must contain objects")
    return RatingArtifact(
        payload["artifact_id"],
        payload["artifact_version"],
        payload["ownership"],
        payload["basis"],
        payload["rights"],
        entries,
    )
