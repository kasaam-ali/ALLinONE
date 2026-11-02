"""Purpose: Unit tests for seed admin env alias resolution (GODMODE_* vs SEED_*)."""
import os

from app.seed import env_first


def test_env_first_prefers_godmode_over_seed(monkeypatch):
    monkeypatch.setenv("GODMODE_ADMIN_EMAIL", "godmode@example.com")
    monkeypatch.setenv("SEED_ADMIN_EMAIL", "seed@example.com")
    assert env_first("GODMODE_ADMIN_EMAIL", "SEED_ADMIN_EMAIL", default="admin@godmode.local") == "godmode@example.com"


def test_env_first_falls_back_to_seed(monkeypatch):
    monkeypatch.delenv("GODMODE_ADMIN_PASSWORD", raising=False)
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "from-seed-alias")
    assert env_first("GODMODE_ADMIN_PASSWORD", "SEED_ADMIN_PASSWORD", default="godmode123") == "from-seed-alias"


def test_env_first_default_when_unset(monkeypatch):
    monkeypatch.delenv("GODMODE_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("SEED_ADMIN_EMAIL", raising=False)
    assert env_first("GODMODE_ADMIN_EMAIL", "SEED_ADMIN_EMAIL", default="admin@godmode.local") == "admin@godmode.local"


def test_env_first_skips_blank(monkeypatch):
    monkeypatch.setenv("GODMODE_ADMIN_EMAIL", "   ")
    monkeypatch.setenv("SEED_ADMIN_EMAIL", "seed@example.com")
    assert env_first("GODMODE_ADMIN_EMAIL", "SEED_ADMIN_EMAIL", default="x") == "seed@example.com"
