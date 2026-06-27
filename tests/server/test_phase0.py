"""Phase 0 pytest wrappers around the docker-free self-check.

The migration-SQL checks run everywhere (stdlib only). The settings/schema checks
need the `server` dep group (pydantic); they're skipped if it isn't installed, so
the existing finscrape test env stays green without pulling FastAPI in.
"""

import pytest

from tests.server import selfcheck


def test_migration_sql_well_formed():
    selfcheck.check_migration_sql()


def test_settings_defaults():
    pytest.importorskip("pydantic_settings")
    assert selfcheck.check_settings() is True


def test_schemas_accept_finevent():
    pytest.importorskip("pydantic")
    pytest.importorskip("pydantic_settings")
    if not selfcheck.check_settings():
        pytest.skip("server deps not installed")
    selfcheck.check_schemas()
