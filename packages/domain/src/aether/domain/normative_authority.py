from collections.abc import Iterable

from aether.contracts import (
    ActorPosition,
    AuthorityContext,
    MembershipStatus,
    OrganizationAuthorityGrant,
    OrganizationMembership,
)


def validate_institutional_authority(
    context: AuthorityContext,
    membership: OrganizationMembership | None,
    grants: Iterable[OrganizationAuthorityGrant],
    position: ActorPosition | None,
) -> None:
    if membership is None or membership.status != MembershipStatus.ACTIVE:
        raise PermissionError("Actor is not an active organization member")
    if position is None or position.location_id != context.location_id:
        raise PermissionError("Actor position does not match the authorized location")
    formal_grants = tuple(
        grant
        for grant in grants
        if grant.formal
        and grant.status.value == "active"
        and grant.role_code in membership.formal_roles
    )
    if not any(
        context.permission_code in grant.permission_codes for grant in formal_grants
    ):
        raise PermissionError(
            f"Actor lacks formal permission: {context.permission_code}"
        )
