"""Pytest configuration and fixtures."""

import os
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Provide mock environment variables for all tests."""
    env_vars = {
        "LIVEKIT_API_KEY": "test_livekit_key",
        "LIVEKIT_API_SECRET": "test_livekit_secret",
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "DEEPGRAM_API_KEY": "test_deepgram_key",
        "ELEVENLABS_API_KEY": "test_elevenlabs_key",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield


@pytest.fixture
def sample_audio_data() -> bytes:
    """Generate sample audio data for testing."""
    # Generate 1 second of silence at 16kHz, 16-bit mono
    sample_rate = 16000
    duration_seconds = 1
    num_samples = sample_rate * duration_seconds
    # 16-bit samples = 2 bytes per sample
    return b"\x00\x00" * num_samples
