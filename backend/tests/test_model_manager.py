"""Tests for model manager — LLM profile discovery."""

import os

from app.services.model_manager import list_profiles, get_profile


class TestListProfiles:
    def test_returns_empty_when_no_api_key(self, monkeypatch):
        """When LLM_API_KEY is empty, no profiles are returned."""
        monkeypatch.setenv("LLM_API_KEY", "")
        # Also clear any LLM_*_KEY env vars
        for key in list(os.environ):
            if key.startswith("LLM_") and key.endswith("_KEY"):
                monkeypatch.delenv(key)

        profiles = list_profiles()
        assert "default" not in profiles

    def test_returns_default_profile_when_key_set(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "sk-test-abc")
        monkeypatch.setenv("LLM_API_BASE_URL", "https://api.openai.com")
        monkeypatch.setenv("LLM_MODEL", "gpt-4")

        profiles = list_profiles()
        assert "default" in profiles
        assert profiles["default"]["key"] == "sk-test-abc"
        assert profiles["default"]["base_url"] == "https://api.openai.com"
        assert profiles["default"]["model"] == "gpt-4"

    def test_discovers_named_profiles(self, monkeypatch):
        """LLM_COPILOT_KEY should create a 'copilot' profile."""
        monkeypatch.setenv("LLM_COPILOT_KEY", "copilot-token")
        monkeypatch.setenv("LLM_COPILOT_BASE_URL", "http://proxy:4141/v1")
        monkeypatch.setenv("LLM_COPILOT_MODEL", "gpt-4.1")

        profiles = list_profiles()
        assert "copilot" in profiles
        assert profiles["copilot"]["key"] == "copilot-token"
        assert profiles["copilot"]["base_url"] == "http://proxy:4141/v1"
        assert profiles["copilot"]["model"] == "gpt-4.1"

    def test_skips_llm_api_key_duplicate(self, monkeypatch):
        """LLM_API_KEY is reserved for 'default', should not appear as 'api'."""
        monkeypatch.setenv("LLM_API_KEY", "sk-default")
        profiles = list_profiles()
        assert "api" not in profiles

    def test_skips_empty_env_values(self, monkeypatch):
        """Env vars with empty values are ignored."""
        monkeypatch.setenv("LLM_API_KEY", "")
        monkeypatch.setenv("LLM_GPT_KEY", "")
        profiles = list_profiles()
        assert "default" not in profiles
        assert "gpt" not in profiles


class TestGetProfile:
    def test_returns_none_for_missing_profile(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "")
        assert get_profile("nonexistent") is None

    def test_returns_default_profile(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "sk-test")
        profile = get_profile("default")
        assert profile is not None
        assert profile["key"] == "sk-test"

    def test_returns_named_profile(self, monkeypatch):
        monkeypatch.setenv("LLM_DEEPSEEK_KEY", "sk-deep")
        monkeypatch.setenv("LLM_DEEPSEEK_MODEL", "deepseek-chat")
        profile = get_profile("deepseek")
        assert profile is not None
        assert profile["key"] == "sk-deep"
        assert profile["model"] == "deepseek-chat"
