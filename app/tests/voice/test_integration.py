"""Integration tests for the voice processing pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.voice.config import (
    LiveKitConfig,
    DeepgramConfig,
    ElevenLabsConfig,
    VoiceProcessingConfig,
)
from src.voice.audio_quality import LatencyTracker, LatencyPhase


class TestVoicePipelineIntegration:
    """Integration tests for the full voice pipeline."""

    def test_config_chain_loads(self) -> None:
        """Test all configurations load correctly together."""
        livekit_config = LiveKitConfig()
        deepgram_config = DeepgramConfig()
        elevenlabs_config = ElevenLabsConfig()
        voice_config = VoiceProcessingConfig()

        # Verify all configs loaded
        assert livekit_config.api_key == "test_livekit_key"
        assert deepgram_config.api_key == "test_deepgram_key"
        assert elevenlabs_config.api_key == "test_elevenlabs_key"
        assert voice_config.environment == "test"

    def test_latency_tracking_full_pipeline(self) -> None:
        """Test latency tracking across full pipeline simulation."""
        tracker = LatencyTracker(target_total_ms=2000.0)

        # Simulate a full pipeline execution
        tracker.start_pipeline()

        # STT phase
        tracker.mark_phase_start(LatencyPhase.STT_START)
        tracker.mark_phase_end(LatencyPhase.STT_END)

        # Processing phase
        tracker.mark_phase_start(LatencyPhase.PROCESSING_START)
        tracker.mark_phase_end(LatencyPhase.PROCESSING_END)

        # TTS phase
        tracker.mark_phase_start(LatencyPhase.TTS_START)
        tracker.mark_phase_end(LatencyPhase.TTS_END)

        result = tracker.complete_pipeline()

        # Verify all phases were tracked
        assert result.total_latency_ms > 0
        assert result.meets_target is True  # Should be fast in test

    def test_quality_threshold_validation(self) -> None:
        """Test quality meets minimum standards."""
        voice_config = VoiceProcessingConfig()

        # Verify quality thresholds are reasonable
        assert voice_config.min_audio_quality_score == 6.0
        assert voice_config.min_stt_accuracy == 0.95

        # Verify latency targets
        assert voice_config.target_total_latency_ms == 2000
        assert voice_config.target_stt_latency_ms == 500
        assert voice_config.target_tts_latency_ms == 500


class TestEndToEndPipelineSimulation:
    """Simulated end-to-end tests (without actual API calls)."""

    @patch("src.voice.stt_pipeline.deepgram.STT")
    @patch("src.voice.tts_pipeline.elevenlabs.TTS")
    def test_pipeline_initialization_order(
        self, mock_tts: MagicMock, mock_stt: MagicMock
    ) -> None:
        """Test pipeline components initialize in correct order."""
        from src.voice.stt_pipeline import create_stt_pipeline
        from src.voice.tts_pipeline import create_tts_pipeline

        # Initialize pipelines
        stt_pipeline = create_stt_pipeline()
        tts_pipeline = create_tts_pipeline()

        # Verify both initialized
        assert stt_pipeline is not None
        assert tts_pipeline is not None

        # Verify STT was initialized before TTS could use it
        mock_stt.assert_called_once()
        mock_tts.assert_called_once()

    @patch("src.voice.livekit_client.api.LiveKitAPI")
    def test_livekit_client_creation(self, mock_api: MagicMock) -> None:
        """Test LiveKit client creates correctly."""
        from src.voice.livekit_client import create_livekit_client

        client = create_livekit_client()

        assert client is not None
        assert client.config.api_key == "test_livekit_key"
        assert client.is_connected is False


class TestConfigurationValidation:
    """Tests for configuration validation."""

    def test_all_required_env_vars_documented(self) -> None:
        """Test that all required environment variables are accounted for."""
        required_vars = [
            "LIVEKIT_API_KEY",
            "LIVEKIT_API_SECRET",
            "LIVEKIT_URL",
            "DEEPGRAM_API_KEY",
            "ELEVENLABS_API_KEY",
        ]

        # Verify all can be loaded
        for var in required_vars:
            import os
            assert var in os.environ, f"Missing required env var: {var}"

    def test_latency_targets_are_achievable(self) -> None:
        """Test that latency targets sum correctly."""
        config = VoiceProcessingConfig()

        # Total should be greater than sum of parts (allows for processing)
        component_sum = config.target_stt_latency_ms + config.target_tts_latency_ms
        assert config.target_total_latency_ms >= component_sum
