"""Tests for voice configuration management."""

import os
import pytest
from unittest.mock import patch

from src.voice.config import (
    LiveKitConfig,
    DeepgramConfig,
    ElevenLabsConfig,
    VoiceProcessingConfig,
)


class TestLiveKitConfig:
    """Tests for LiveKit configuration."""

    def test_config_loads_from_env(self) -> None:
        """Test configuration loads from environment variables."""
        env_vars = {
            "LIVEKIT_API_KEY": "test_key",
            "LIVEKIT_API_SECRET": "test_secret",
            "LIVEKIT_URL": "wss://test.livekit.cloud",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = LiveKitConfig()
            assert config.api_key == "test_key"
            assert config.api_secret == "test_secret"
            assert config.url == "wss://test.livekit.cloud"

    def test_config_raises_on_missing_required(self) -> None:
        """Test configuration raises error when required fields missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):  # ValidationError
                LiveKitConfig()


class TestDeepgramConfig:
    """Tests for Deepgram STT configuration."""

    def test_config_loads_from_env(self) -> None:
        """Test configuration loads from environment variables."""
        env_vars = {"DEEPGRAM_API_KEY": "test_deepgram_key"}
        with patch.dict(os.environ, env_vars, clear=False):
            config = DeepgramConfig()
            assert config.api_key == "test_deepgram_key"
            assert config.model == "nova-2"  # default
            assert config.language == "en-US"  # default

    def test_config_custom_model(self) -> None:
        """Test configuration with custom model."""
        env_vars = {
            "DEEPGRAM_API_KEY": "test_key",
            "DEEPGRAM_MODEL": "nova-2-general",
            "DEEPGRAM_LANGUAGE": "es",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = DeepgramConfig()
            assert config.model == "nova-2-general"
            assert config.language == "es"


class TestElevenLabsConfig:
    """Tests for ElevenLabs TTS configuration."""

    def test_config_loads_from_env(self) -> None:
        """Test configuration loads from environment variables."""
        env_vars = {"ELEVENLABS_API_KEY": "test_elevenlabs_key"}
        with patch.dict(os.environ, env_vars, clear=False):
            config = ElevenLabsConfig()
            assert config.api_key == "test_elevenlabs_key"
            assert config.voice_id == "21m00Tcm4TlvDq8ikWAM"  # default
            assert config.sample_rate == 24000  # default

    def test_config_custom_voice(self) -> None:
        """Test configuration with custom voice."""
        env_vars = {
            "ELEVENLABS_API_KEY": "test_key",
            "ELEVENLABS_VOICE_ID": "custom_voice_id",
            "TTS_SAMPLE_RATE": "44100",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = ElevenLabsConfig()
            assert config.voice_id == "custom_voice_id"
            assert config.sample_rate == 44100


class TestVoiceProcessingConfig:
    """Tests for aggregate voice processing configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = VoiceProcessingConfig()
        assert config.environment == "development"
        assert config.target_total_latency_ms == 2000
        assert config.min_audio_quality_score == 6.0
        assert config.min_stt_accuracy == 0.95

    def test_latency_targets(self) -> None:
        """Test latency target values."""
        config = VoiceProcessingConfig()
        assert config.target_stt_latency_ms == 500
        assert config.target_tts_latency_ms == 500
        # Total should accommodate both plus processing
        assert config.target_total_latency_ms >= (
            config.target_stt_latency_ms + config.target_tts_latency_ms
        )
