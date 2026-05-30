from __future__ import annotations

import getpass
import os
import sys
from sqlalchemy import func, select

from app.config.settings import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.settings.service import seed_system_settings
from app.modules.users.models import BuiltInRole, Role, User
from app.modules.users.service import record_audit, seed_roles_and_permissions


def main() -> int:
    settings = get_settings()
    username = settings.storeops_admin_username or os.getenv("STOREOPS_ADMIN_USERNAME")
    email = settings.storeops_admin_email or os.getenv("STOREOPS_ADMIN_EMAIL")
    password = settings.storeops_admin_password or os.getenv("STOREOPS_ADMIN_PASSWORD")
    if (not username or not password) and sys.stdin.isatty():
        username = username or input("Super Admin username: ").strip()
        email = email or input("Super Admin email (optional): ").strip() or None
        password = password or getpass.getpass("Super Admin password: ")
    if not username or not password:
        print("STOREOPS_ADMIN_USERNAME and STOREOPS_ADMIN_PASSWORD are required in non-interactive mode. Password will not be printed.")
        return 2
    with SessionLocal() as db:
        user_count = db.scalar(select(func.count()).select_from(User)) or 0
        if user_count > 0:
            print("Users already exist; refusing to recreate the initial Super Admin.")
            return 0
        seed_roles_and_permissions(db)
        seed_system_settings(db)
        role = db.scalar(select(Role).where(Role.slug == BuiltInRole.super_admin.value))
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=BuiltInRole.super_admin,
            role_id=role.id if role else None,
            is_active=True,
            is_superuser=True,
            must_change_password=True,
            permissions=[],
        )
        db.add(user)
        db.flush()
        record_audit(db, "user_created", user.id, "users", "user", user.id, {"bootstrap": True})
        db.commit()
    print(f"Created initial Super Admin user '{username}'. Password was not printed. Change it on first login.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
