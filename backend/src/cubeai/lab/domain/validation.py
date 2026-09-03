"""Deterministic validation of immutable CubeVersion values before drafting."""

from dataclasses import dataclass
from enum import StrEnum

from cubeai.lab.domain.cube import CubeVersion, ResolutionStatus
from cubeai.lab.domain.draft import DraftConfiguration


class CubeValidationSeverity(StrEnum):
    ERROR = "error"
    INFO = "info"


class CubeValidationCode(StrEnum):
    UNRESOLVED_MEMBERSHIP = "unresolved_membership"
    CUSTOM_MEMBERSHIP = "custom_membership"
    INSUFFICIENT_USABLE_MEMBERSHIPS = "insufficient_usable_memberships"
    EXCESS_USABLE_MEMBERSHIPS = "excess_usable_memberships"


@dataclass(frozen=True, slots=True)
class CubeValidationDiagnostic:
    code: CubeValidationCode
    severity: CubeValidationSeverity
    message: str
    membership_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, CubeValidationCode):
            raise ValueError("code must be a CubeValidationCode")
        if not isinstance(self.severity, CubeValidationSeverity):
            raise ValueError("severity must be a CubeValidationSeverity")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be a nonblank string")
        if self.membership_id is not None and (
            not isinstance(self.membership_id, str) or not self.membership_id.strip()
        ):
            raise ValueError("membership_id must be a nonblank string or None")


@dataclass(frozen=True, slots=True)
class CubeValidationResult:
    cube_version_id: str
    configuration: DraftConfiguration
    usable_membership_count: int
    diagnostics: tuple[CubeValidationDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.cube_version_id, str)
            or not self.cube_version_id.strip()
        ):
            raise ValueError("cube_version_id must be a nonblank string")
        if not isinstance(self.configuration, DraftConfiguration):
            raise ValueError("configuration must be a DraftConfiguration")
        if (
            not isinstance(self.usable_membership_count, int)
            or isinstance(self.usable_membership_count, bool)
            or self.usable_membership_count < 0
        ):
            raise ValueError("usable_membership_count must be a nonnegative integer")
        diagnostics = tuple(self.diagnostics)
        if any(not isinstance(item, CubeValidationDiagnostic) for item in diagnostics):
            raise ValueError("diagnostics must contain CubeValidationDiagnostic values")
        object.__setattr__(self, "diagnostics", diagnostics)

    @property
    def is_draftable(self) -> bool:
        return not any(
            diagnostic.severity is CubeValidationSeverity.ERROR
            for diagnostic in self.diagnostics
        )


def validate_cube_version(
    version: CubeVersion, configuration: DraftConfiguration
) -> CubeValidationResult:
    """Return stable diagnostics without mutating the CubeVersion.

    Exact membership count is not required: excess resolved memberships are
    permitted, and M1-010 will own the later deterministic selection policy.
    """

    if not isinstance(version, CubeVersion):
        raise ValueError("version must be a CubeVersion")
    if not isinstance(configuration, DraftConfiguration):
        raise ValueError("configuration must be a DraftConfiguration")

    diagnostics: list[CubeValidationDiagnostic] = []
    usable_memberships = 0
    for card in version.cards:
        if card.resolution_status is ResolutionStatus.RESOLVED:
            usable_memberships += 1
        elif card.resolution_status is ResolutionStatus.CUSTOM:
            diagnostics.append(
                CubeValidationDiagnostic(
                    CubeValidationCode.CUSTOM_MEMBERSHIP,
                    CubeValidationSeverity.ERROR,
                    f"Membership {card.id} is custom and cannot be drafted yet.",
                    card.id,
                )
            )
        else:
            diagnostics.append(
                CubeValidationDiagnostic(
                    CubeValidationCode.UNRESOLVED_MEMBERSHIP,
                    CubeValidationSeverity.ERROR,
                    f"Membership {card.id} has no resolved printing identity.",
                    card.id,
                )
            )

    required = configuration.card_count
    configuration_description = _configuration_description(configuration)
    if usable_memberships < required:
        diagnostics.append(
            CubeValidationDiagnostic(
                CubeValidationCode.INSUFFICIENT_USABLE_MEMBERSHIPS,
                CubeValidationSeverity.ERROR,
                (
                    f"Draft configuration requires {required} resolved memberships "
                    f"but this CubeVersion has {usable_memberships} "
                    f"({configuration_description})."
                ),
            )
        )
    elif usable_memberships > required:
        diagnostics.append(
            CubeValidationDiagnostic(
                CubeValidationCode.EXCESS_USABLE_MEMBERSHIPS,
                CubeValidationSeverity.INFO,
                (
                    f"CubeVersion has {usable_memberships - required} excess resolved "
                    "memberships; deterministic selection is deferred to M1-010 "
                    f"({configuration_description})."
                ),
            )
        )

    return CubeValidationResult(
        version.id, configuration, usable_memberships, tuple(diagnostics)
    )


def _configuration_description(configuration: DraftConfiguration) -> str:
    return (
        f"{configuration.seats} seat(s) x {configuration.packs_per_seat} "
        f"pack(s)/seat x {configuration.pack_size} card(s)/pack"
    )
