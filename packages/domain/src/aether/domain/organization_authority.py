from collections.abc import Iterable

from aether.contracts import (
    MembershipStatus,
    OrganizationAuthorityGrant,
    OrganizationMembership,
    OrganizationPlanStep,
)

from .errors import OrganizationAuthorityError


def required_organization_permissions(
    step: OrganizationPlanStep,
) -> set[str]:
    required = set(step.required_permission_codes)
    for effect in step.resource_effects:
        action = "consume-resource" if effect.delta < 0 else "produce-resource"
        required.add(f"{action}:{effect.resource_code}")
    return required


def validate_organization_authority(
    membership: OrganizationMembership | None,
    grants: Iterable[OrganizationAuthorityGrant],
    step: OrganizationPlanStep,
) -> None:
    if membership is None or membership.status != MembershipStatus.ACTIVE:
        raise OrganizationAuthorityError(
            "Responsible character is not an active organization member"
        )
    active_formal = [grant for grant in grants if grant.formal]
    permissions = {
        permission
        for grant in active_formal
        for permission in grant.permission_codes
    }
    if not any(
        grant.role_code in membership.formal_roles for grant in active_formal
    ):
        raise OrganizationAuthorityError(
            "Responsible member has no formal authority role"
        )
    missing = sorted(required_organization_permissions(step) - permissions)
    if missing:
        raise OrganizationAuthorityError(
            "Responsible member lacks authority permission(s): "
            + ", ".join(missing)
        )
