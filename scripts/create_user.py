#!/usr/bin/env python
"""Creates a login user for the frontend — no self-signup (internal tool).
Run: ``uv run python scripts/create_user.py --name "Victor Espiritu" --email victor@example.com --password secret123``
"""

from __future__ import annotations

import argparse
import asyncio

from idp.auth.security import hash_password
from idp.config import get_settings
from idp.persistence.db import get_session_factory
from idp.persistence.repositories import UserRepository


async def run(name: str, email: str, password: str) -> None:
    settings = get_settings()
    factory = get_session_factory(settings)
    async with factory() as session:
        repo = UserRepository(session)
        existing = await repo.get_by_email(email)
        if existing is not None:
            print(f"User already exists: {email}")
            return
        await repo.create(name=name, email=email, password_hash=hash_password(password))
        await session.commit()
    print(f"Created user: {name} <{email}>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    asyncio.run(run(args.name, args.email, args.password))
