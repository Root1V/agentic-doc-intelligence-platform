#!/usr/bin/env python
"""Seeds the minimal ``reference_employees`` table (category d validation)
with the employees appearing in the fixture corpus, so
``EmployeeCodeExistsInReferenceData``/``EmployeeNameExistsInReferenceData``
have real data to check against. Run: ``uv run python scripts/seed_reference_data.py``
"""

from __future__ import annotations

import asyncio

from idp.config import get_settings
from idp.persistence.db import get_session_factory
from idp.persistence.models import ReferenceEmployee
from sqlalchemy import select

SEED_EMPLOYEES = [
    ("70349965", "Salas Siguas, Katerin Karola"),  # boleta_pagos1.png (DNI used as code — no explicit employee_code on the document)
    ("21441884", "Negron Nuñez, Milagros Elizabeth"),  # boleta_pagos2.png
]


async def run() -> None:
    settings = get_settings()
    factory = get_session_factory(settings)
    async with factory() as session:
        for code, full_name in SEED_EMPLOYEES:
            existing = await session.execute(select(ReferenceEmployee).where(ReferenceEmployee.employee_code == code))
            if existing.scalar_one_or_none() is None:
                session.add(ReferenceEmployee(employee_code=code, full_name=full_name, active=True))
        await session.commit()
    print(f"Seeded {len(SEED_EMPLOYEES)} reference employee(s).")


if __name__ == "__main__":
    asyncio.run(run())
