"""Seed referential-integrity regression.

``seed_data_if_empty`` once inserted an AuditEntry whose ``action_id``
pointed at ``a1b2c3d4-0009-...`` — an ApprovalAction that the mock set
never defines (only ...-0001..0008). SQLite does not enforce the
``audit_entries.action_id -> approval_actions.id`` foreign key by default,
so the suite and the sqlite demo stack happily seeded a dangling
reference. Postgres DOES enforce it: the FK violation aborted the seed
transaction and every fresh Postgres boot (CI frontend E2E, the local
demo stack, staging) came up with zero approvals and an empty audit log
while the lifespan swallowed the failure.

This test pins the invariant on the data itself — it fails on any
backend (including sqlite) whenever a non-null seeded ``action_id`` does
not reference a seeded ApprovalAction.
"""

import pytest
from sqlalchemy import select

from ecommerce_ops.models.db import ApprovalAction, AuditEntry
from ecommerce_ops.models.seed import seed_data_if_empty


@pytest.mark.asyncio
async def test_seed_audit_entries_reference_seeded_actions(db_session):
    """Seeding must commit and every non-null audit action_id must exist."""
    from unittest.mock import patch

    class _Factory:
        def __call__(self):
            return _SessionWrapper(db_session)

    class _SessionWrapper:
        def __init__(self, session):
            self._session = session

        async def __aenter__(self):
            return self._session

        async def __aexit__(self, *exc):
            return False

    with patch(
        "ecommerce_ops.models.seed.async_session_factory",
        _Factory(),
    ):
        await seed_data_if_empty()

    actions = (await db_session.execute(select(ApprovalAction))).scalars().all()
    audits = (await db_session.execute(select(AuditEntry))).scalars().all()

    assert len(actions) > 0, "seed must create ApprovalAction rows"
    assert len(audits) > 0, "seed must create AuditEntry rows"

    action_ids = {a.id for a in actions}
    dangling = [
        e.action_id for e in audits if e.action_id is not None and e.action_id not in action_ids
    ]
    assert dangling == [], f"audit entries reference missing actions: {dangling}"
