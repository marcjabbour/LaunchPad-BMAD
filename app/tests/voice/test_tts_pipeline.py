"""Tests for Text-to-Speech pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.voice.tts_pipeline import (
    TTSPipeline,
    TTSConfig,
    TTSMetrics,
    SynthesisResult,
    SynthesisState,
    create_tts_pipeline,
)
from src.voice.config import ElevenLabsConfig


@pytest.fixture
def mock_elevenlabs_config() -> ElevenLabsConfig:
    """Create mock ElevenLabs configuration."""
    with patch.dict(
        "os.environ",
        {"ELEVENLABS_API_KEY": "test_key"},
        clear=False,
    ):
        return ElevenLabsConfig()


@pytest.fixture
def tts_config(mock_elevenlabs_config: ElevenLabsConfig) -> TTSConfig:
    """Create TTS configuration for testing."""
    return TTSConfig(
        elevenlabs_config=mock_elevenlabs_config,
        stability=0.5,
        similarity_boost=0.75,
    )


class TestTTSMetrics:
    """Tests for TTS metrics tracking."""

    def test_initial_metrics(self) -> None:
        """Test initial metrics are zero."""
        metrics = TTSMetrics()
        assert metrics.total_syntheses == 0
        assert metrics.successful_syntheses == 0
        assert metrics.failed_syntheses == 0
        assert metrics.average_latency_ms == 0.0

    def test_average_latency_calculation(self) -> None:
        """Test average latency is calculated correctly."""
        metrics = TTSMetrics(
            total_syntheses=10,
            successful_syntheses=10,
            total_latency_ms=3000.0,
        )
        assert metrics.average_latency_ms == 300.0

    def test_success_rate_calculation(self) -> None:
        """Test success rate calculation."""
        metrics = TTSMetrics(
            total_syntheses=100,
            successful_syntheses=98,
            failed_syntheses=2,
        )
        assert metrics.success_rate == 0.98

    def test_chars_per_second(self) -> None:
        """Test characters per second calculation."""
        metrics = TTSMetrics(
            total_audio_duration_ms=10000.0,  # 10 seconds
            total_characters_processed=1500,  # 1500 chars
        )
        assert metrics.average_chars_per_second == 150.0


class TestSynthesisResult:
    """Tests for synthesis result data class."""

    def test_result_creation(self) -> None:
        """Test synthesis result creation."""
        result = SynthesisResult(
            audio_data=b"audio_bytes",
            text="Hello world",
            duration_ms=1500.0,
            latency_ms=200.0,
            sample_rate=24000,
            voice_id="test_voice",
        )
        assert result.text == "Hello world"
        assert result.duration_ms == 1500.0
        assert result.latency_ms == 200.0
        assert result.sample_rate == 24000


class TestTTSPipeline:
    """Tests for TTS pipeline."""

    @patch("src.voice.tts_pipeline.elevenlabs.TTS")
    def test_pipeline_initialization(
        self, mock_tts_class: MagicMock, tts_config: TTSConfig
    ) -> None:
        """Test pipeline initializes correctly."""
        pipeline = TTSPipeline(config=tts_config)
        assert pipeline.state == SynthesisState.IDLE
        assert pipeline.metrics.total_syntheses == 0
        mock_tts_class.assert_called_once()

    @patch("src.voice.tts_pipeline.elevenlabs.TTS")
    def test_get_metrics(
        self, mock_tts_class: MagicMock, tts_config: TTSConfig
    ) -> None:
        """Test getting metrics."""
        pipeline = TTSPipeline(config=tts_config)
        metrics = pipeline.get_metrics()
        assert isinstance(metrics, TTSMetrics)

    @patch("src.voice.tts_pipeline.elevenlabs.TTS")
    def test_reset_metrics(
        self, mock_tts_class: MagicMock, tts_config: TTSConfig
    ) -> None:
        """Test resetting metrics."""
        pipeline = TTSPipeline(config=tts_config)
        pipeline.metrics.total_syntheses = 100
        pipeline.reset_metrics()
        assert pipeline.metrics.total_syntheses == 0

    @patch("src.voice.tts_pipeline.elevenlabs.TTS")
    def test_tts_instance_property(
        self, mock_tts_class: MagicMock, tts_config: TTSConfig
    ) -> None:
        """Test TTS instance property."""
        pipeline = TTSPipeline(config=tts_config)
        assert pipeline.tts_instance is not None

    @patch("src.voice.tts_pipeline.elevenlabs.TTS")
    @pytest.mark.asyncio
    async def test_synthesize_empty_text_raises(
        self, mock_tts_class: MagicMock, tts_config: TTSConfig
    ) -> None:
        """Test synthesize raises on empty text."""
        pipeline = TTSPipeline(config=tts_config)
        with pytest.raises(ValueError, match="Cannot synthesize empty text"):
            await pipeline.synthesize("")

    @patch("src.voice.tts_pipeline.elevenlabs.TTS")
    @pytest.mark.asyncio
    async def test_synthesize_stream_empty_text_raises(
        self, mock_tts_class: MagicMock, tts_config: TTSConfig
    ) -> None:
        """Test synthesize_stream raises on empty text."""
        pipeline = TTSPipeline(config=tts_config)
        with pytest.raises(ValueError, match="Cannot synthesize empty text"):
            async for _ in pipeline.synthesize_stream("   "):
                pass


class TestCreateTTSPipeline:
    """Tests for TTS pipeline factory function."""

    @patch("src.voice.tts_pipeline.elevenlabs.TTS")
    @patch("src.voice.tts_pipeline.ElevenLabsConfig")
    def test_create_with_defaults(
        self, mock_config_class: MagicMock, mock_tts_class: MagicMock
    ) -> None:
        """Test factory creates pipeline with defaults."""
        mock_config_class.return_value = MagicMock(
            api_key="test",
            voice_id="test_voice",
            model_id="eleven_turbo_v2",
            sample_rate=24000,
        )
        pipeline = create_tts_pipeline()
        assert isinstance(pipeline, TTSPipeline)

    @patch("src.voice.tts_pipeline.elevenlabs.TTS")
    def test_create_with_custom_config(
        self, mock_tts_class: MagicMock, tts_config: TTSConfig
    ) -> None:
        """Test factory creates pipeline with custom config."""
        pipeline = create_tts_pipeline(config=tts_config)
        assert pipeline.config == tts_config
