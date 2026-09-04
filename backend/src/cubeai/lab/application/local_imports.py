"""Compose existing source, metadata, and CubeVersion application boundaries."""

from dataclasses import dataclass, replace

from cubeai.lab.application.cube_versions import (
    CubeVersionAssemblyResult,
    assemble_cube_version,
)
from cubeai.lab.application.imports import CubeSource, ImportResult, SourceRequest
from cubeai.lab.application.metadata import MetadataResolver
from cubeai.lab.application.repositories import DraftRepository
from cubeai.lab.domain.cube import CubeVersion


@dataclass(frozen=True, slots=True)
class LocalCubeImport:
    """A source-preserving import plus optional assembled local CubeVersion."""

    source_result: ImportResult
    assembly: CubeVersionAssemblyResult | None


def _same_immutable_snapshot(persisted: CubeVersion, assembled: CubeVersion) -> bool:
    """Compare durable source content, ignoring local labels and retrieval time."""

    return (
        persisted.id == assembled.id
        and persisted.content_fingerprint == assembled.content_fingerprint
        and persisted.cube.id == assembled.cube.id
        and persisted.cube.source_reference == assembled.cube.source_reference
        and persisted.source_reference == assembled.source_reference
        and persisted.cards == assembled.cards
    )


def import_local_cube(
    repository: DraftRepository,
    source: CubeSource,
    resolver: MetadataResolver,
    *,
    source_name: str,
    identifier: str,
    cube_name: str,
    offline: bool = False,
) -> LocalCubeImport:
    """Import, resolve, assemble, and durably retain a version when possible."""

    imported = source.import_cube(SourceRequest(source_name, identifier))
    if imported.snapshot is None:
        return LocalCubeImport(imported, None)
    resolution = resolver.resolve(imported.candidates, offline=offline)
    assembly = assemble_cube_version(
        imported,
        resolution,
        cube_id=imported.snapshot.snapshot_id,
        cube_name=cube_name,
    )
    if assembly.cube_version is not None:
        assembled = assembly.cube_version
        persisted = repository.load_cube_version(assembled.id)
        if persisted is None:
            repository.save_cube_version(assembled)
        elif _same_immutable_snapshot(persisted, assembled):
            assembly = replace(assembly, cube_version=persisted)
        else:
            repository.save_cube_version(assembled)
    return LocalCubeImport(imported, assembly)
