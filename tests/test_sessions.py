"""Tests for session management."""

import sqlite3
import tempfile
import time
from pathlib import Path

import pytest

from finscrape.sessions import SessionCookie, SessionManager


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def session_mgr(db_path):
    mgr = SessionManager(db_path)
    yield mgr
    mgr.close()


class TestSessionCookie:
    def test_non_expired(self):
        c = SessionCookie(name="sid", value="abc", domain=".example.com")
        assert not c.is_expired

    def test_expired(self):
        c = SessionCookie(name="sid", value="abc", domain=".example.com",
                          expires=time.time() - 3600)
        assert c.is_expired

    def test_future_not_expired(self):
        c = SessionCookie(name="sid", value="abc", domain=".example.com",
                          expires=time.time() + 3600)
        assert not c.is_expired

    def test_roundtrip(self):
        c = SessionCookie(name="sid", value="xyz", domain=".test.com",
                          path="/api", expires=999999.0, secure=True, http_only=True)
        d = c.to_dict()
        c2 = SessionCookie.from_dict(d)
        assert c2.name == c.name
        assert c2.value == c.value
        assert c2.domain == c.domain
        assert c2.secure == c.secure
        assert c2.http_only == c.http_only


class TestSessionManager:
    def test_save_and_get_cookies(self, session_mgr):
        cookies = [
            SessionCookie(name="sid", value="abc123", domain=".bloomberg.com"),
            SessionCookie(name="pref", value="dark", domain=".bloomberg.com"),
        ]
        session_mgr.save_cookies("bloomberg", cookies)
        result = session_mgr.get_cookies("bloomberg")
        assert len(result) == 2
        names = {c.name for c in result}
        assert "sid" in names
        assert "pref" in names

    def test_expired_cookies_filtered(self, session_mgr):
        cookies = [
            SessionCookie(name="good", value="yes", domain=".test.com",
                          expires=time.time() + 3600),
            SessionCookie(name="bad", value="no", domain=".test.com",
                          expires=time.time() - 3600),
        ]
        session_mgr.save_cookies("test", cookies)
        result = session_mgr.get_cookies("test")
        assert len(result) == 1
        assert result[0].name == "good"

    def test_cookie_header(self, session_mgr):
        cookies = [
            SessionCookie(name="a", value="1", domain=".test.com"),
            SessionCookie(name="b", value="2", domain=".test.com"),
        ]
        session_mgr.save_cookies("test", cookies)
        header = session_mgr.get_cookie_header("test")
        assert "a=1" in header
        assert "b=2" in header

    def test_source_isolation(self, session_mgr):
        session_mgr.save_cookies("src1", [
            SessionCookie(name="x", value="1", domain=".a.com"),
        ])
        session_mgr.save_cookies("src2", [
            SessionCookie(name="y", value="2", domain=".b.com"),
        ])
        assert len(session_mgr.get_cookies("src1")) == 1
        assert len(session_mgr.get_cookies("src2")) == 1
        assert session_mgr.get_cookies("src1")[0].name == "x"

    def test_cookie_update(self, session_mgr):
        session_mgr.save_cookies("test", [
            SessionCookie(name="sid", value="old", domain=".test.com"),
        ])
        session_mgr.save_cookies("test", [
            SessionCookie(name="sid", value="new", domain=".test.com"),
        ])
        result = session_mgr.get_cookies("test")
        assert len(result) == 1
        assert result[0].value == "new"

    def test_metadata(self, session_mgr):
        session_mgr.set_metadata("bloomberg", user_agent="TestAgent/1.0", login_type="cookie")
        meta = session_mgr.get_metadata("bloomberg")
        assert meta is not None
        assert meta["user_agent"] == "TestAgent/1.0"
        assert meta["login_type"] == "cookie"
        assert meta["last_login"] is not None

    def test_has_session(self, session_mgr):
        assert not session_mgr.has_session("test")
        session_mgr.save_cookies("test", [
            SessionCookie(name="s", value="v", domain=".test.com"),
        ])
        assert session_mgr.has_session("test")

    def test_clear_source(self, session_mgr):
        session_mgr.save_cookies("test", [
            SessionCookie(name="s", value="v", domain=".test.com"),
        ])
        session_mgr.set_metadata("test", user_agent="UA")
        session_mgr.clear_source("test")
        assert not session_mgr.has_session("test")
        assert session_mgr.get_metadata("test") is None

    def test_save_from_dicts(self, session_mgr):
        dicts = [
            {"name": "a", "value": "1", "domain": ".t.com", "path": "/", "expires": 0,
             "secure": False, "httpOnly": True},
        ]
        session_mgr.save_cookies_from_dicts("test", dicts)
        result = session_mgr.get_cookies("test")
        assert len(result) == 1
        assert result[0].http_only is True
