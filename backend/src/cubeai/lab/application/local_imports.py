"""Compose existing source, metadata, and CubeVersion application boundaries."""

from dataclasses import dataclass

from cubeai.lab.application.cube_versions import (
    CubeVersionAssemblyResult,
    assemble_cube_version,
)
from cubeai.lab.application.imports import CubeSource, ImportResult, SourceRequest
from cubeai.lab.application.metadata import MetadataResolver
from cubeai.lab.application.repositories import DraftRepository


@dataclass(frozen=True, slots=True)
class LocalCubeImport:
    """A source-preserving import plus optional assembled local CubeVersion."""

    source_result: ImportResult
    assembly: CubeVersionAssemblyResult | None


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
        repository.save_cube_version(assembly.cube_version)
    return LocalCubeImport(imported, assembly)
