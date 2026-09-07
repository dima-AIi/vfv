"""Bootstrap a platform administrator.

Usage:
    cd backend
    uv run python ../scripts/bootstrap_admin.py admin@example.com s3cure-passw0rd

Assigns the platform_admin role (organization_id = NULL) to an existing user or
creates the user first if needed.
"""

import asyncio
import sys


async def main(email: str, password: str) -> int:
    from app.core.database import session_factory
    from app.modules.identity.schemas import RegisterIn
    from app.modules.identity.service import IdentityService
    from app.modules.rbac.seed import ensure_system_seed
    from app.modules.rbac.service import RbacService

    await ensure_system_seed()

    normalized_email = email.strip().lower()
    async with session_factory() as session:
        identity_service = IdentityService(session)
        rbac_service = RbacService(session)

        existing = await identity_service.users.get_by_email(normalized_email)
        if existing is None:
            user_out = await identity_service.register(
                RegisterIn(
                    email=normalized_email,
                    password=password,
                    displayName="Platform Admin",
                ),
            )
            user_id = user_out.id
            print(f"created user {user_out.email}")
        else:
            user_id = existing.id
            print(f"user already exists: {existing.email}")

        await rbac_service.ensure_user_role(
            user_id=user_id,
            role_name="platform_admin",
            organization_id=None,
        )
        codes = await rbac_service.list_role_codes(user_id)
        print(f"platform_admin assigned; roles now: {', '.join(codes)}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: uv run python ../scripts/bootstrap_admin.py <email> <password>")
        sys.exit(2)
    sys.exit(asyncio.run(main(sys.argv[1], sys.argv[2])))
