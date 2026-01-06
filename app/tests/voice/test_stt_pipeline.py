"""Tests for Speech-to-Text pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.voice.stt_pipeline import (
    STTPipeline,
    STTConfig,
    STTMetrics,
    TranscriptionResult,
    TranscriptionState,
    create_stt_pipeline,
)
from src.voice.config import DeepgramConfig


@pytest.fixture
def mock_deepgram_config() -> DeepgramConfig:
    """Create mock Deepgram configuration."""
    with patch.dict(
        "os.environ",
        {"DEEPGRAM_API_KEY": "test_key"},
        clear=False,
    ):
        return DeepgramConfig()


@pytest.fixture
def stt_config(mock_deepgram_config: DeepgramConfig) -> STTConfig:
    """Create STT configuration for testing."""
    return STTConfig(
        deepgram_config=mock_deepgram_config,
        interim_results=True,
        punctuate=True,
    )


class TestSTTMetrics:
    """Tests for STT metrics tracking."""

    def test_initial_metrics(self) -> None:
        """Test initial metrics are zero."""
        metrics = STTMetrics()
        assert metrics.total_transcriptions == 0
        assert metrics.successful_transcriptions == 0
        assert metrics.failed_transcriptions == 0
        assert metrics.average_latency_ms == 0.0

    def test_average_latency_calculation(self) -> None:
        """Test average latency is calculated correctly."""
        metrics = STTMetrics(
            total_transcriptions=10,
            successful_transcriptions=10,
            total_latency_ms=5000.0,
        )
        assert metrics.average_latency_ms == 500.0

    def test_success_rate_calculation(self) -> None:
        """Test success rate calculation."""
        metrics = STTMetrics(
            total_transcriptions=100,
            successful_transcriptions=95,
            failed_transcriptions=5,
        )
        assert metrics.success_rate == 0.95

    def test_success_rate_zero_division(self) -> None:
        """Test success rate handles zero total."""
        metrics = STTMetrics()
        assert metrics.success_rate == 0.0


class TestTranscriptionResult:
    """Tests for transcription result data class."""

    def test_result_creation(self) -> None:
        """Test transcription result creation."""
        result = TranscriptionResult(
            text="Hello world",
            is_final=True,
            confidence=0.98,
            start_time=0.0,
            end_time=1.5,
            latency_ms=150.0,
            language="en",
        )
        assert result.text == "Hello world"
        assert result.is_final is True
        assert result.confidence == 0.98
        assert result.latency_ms == 150.0


class TestSTTPipeline:
    """Tests for STT pipeline."""

    @patch("src.voice.stt_pipeline.deepgram.STT")
    def test_pipeline_initialization(
        self, mock_stt_class: MagicMock, stt_config: STTConfig
    ) -> None:
        """Test pipeline initializes correctly."""
        pipeline = STTPipeline(config=stt_config)
        assert pipeline.state == TranscriptionState.IDLE
        assert pipeline.metrics.total_transcriptions == 0
        mock_stt_class.assert_called_once()

    @patch("src.voice.stt_pipeline.deepgram.STT")
    def test_set_transcription_callback(
        self, mock_stt_class: MagicMock, stt_config: STTConfig
    ) -> None:
        """Test setting transcription callback."""
        pipeline = STTPipeline(config=stt_config)
        callback = MagicMock()
        pipeline.set_transcription_callback(callback)
        assert pipeline._on_transcription == callback

    @patch("src.voice.stt_pipeline.deepgram.STT")
    def test_get_metrics(
        self, mock_stt_class: MagicMock, stt_config: STTConfig
    ) -> None:
        """Test getting metrics."""
        pipeline = STTPipeline(config=stt_config)
        metrics = pipeline.get_metrics()
        assert isinstance(metrics, STTMetrics)

    @patch("src.voice.stt_pipeline.deepgram.STT")
    def test_reset_metrics(
        self, mock_stt_class: MagicMock, stt_config: STTConfig
    ) -> None:
        """Test resetting metrics."""
        pipeline = STTPipeline(config=stt_config)
        pipeline.metrics.total_transcriptions = 100
        pipeline.reset_metrics()
        assert pipeline.metrics.total_transcriptions == 0

    @patch("src.voice.stt_pipeline.deepgram.STT")
    def test_stt_instance_property(
        self, mock_stt_class: MagicMock, stt_config: STTConfig
    ) -> None:
        """Test STT instance property."""
        pipeline = STTPipeline(config=stt_config)
        assert pipeline.stt_instance is not None


class TestCreateSTTPipeline:
    """Tests for STT pipeline factory function."""

    @patch("src.voice.stt_pipeline.deepgram.STT")
    @patch("src.voice.stt_pipeline.DeepgramConfig")
    def test_create_with_defaults(
        self, mock_config_class: MagicMock, mock_stt_class: MagicMock
    ) -> None:
        """Test factory creates pipeline with defaults."""
        mock_config_class.return_value = MagicMock(
            api_key="test", model="nova-2", language="en-US"
        )
        pipeline = create_stt_pipeline()
        assert isinstance(pipeline, STTPipeline)

    @patch("src.voice.stt_pipeline.deepgram.STT")
    def test_create_with_custom_config(
        self, mock_stt_class: MagicMock, stt_config: STTConfig
    ) -> None:
        """Test factory creates pipeline with custom config."""
        pipeline = create_stt_pipeline(config=stt_config)
        assert pipeline.config == stt_config
