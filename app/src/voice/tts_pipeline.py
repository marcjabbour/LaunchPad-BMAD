"""Text-to-Speech pipeline using ElevenLabs via LiveKit Agents."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator, Optional
from enum import Enum

import structlog
from livekit.agents import tts
from livekit.plugins import elevenlabs

from .config import ElevenLabsConfig

logger = structlog.get_logger(__name__)


async def retry_async(
    func,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    exponential_base: float = 2.0,
):
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async callable to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                logger.warning(
                    "tts_retry_attempt",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay=delay,
                    error=str(e),
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "tts_retry_exhausted",
                    max_retries=max_retries,
                    error=str(e),
                )
    raise last_exception


class SynthesisState(Enum):
    """State of the TTS synthesis pipeline."""

    IDLE = "idle"
    SYNTHESIZING = "synthesizing"
    STREAMING = "streaming"
    ERROR = "error"


@dataclass
class SynthesisResult:
    """Result from text-to-speech synthesis."""

    audio_data: bytes
    text: str
    duration_ms: float
    latency_ms: float
    sample_rate: int
    voice_id: str


@dataclass
class TTSMetrics:
    """Metrics for TTS pipeline performance."""

    total_syntheses: int = 0
    successful_syntheses: int = 0
    failed_syntheses: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0
    total_audio_duration_ms: float = 0.0
    total_characters_processed: int = 0

    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.successful_syntheses == 0:
            return 0.0
        return self.total_latency_ms / self.successful_syntheses

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_syntheses == 0:
            return 0.0
        return self.successful_syntheses / self.total_syntheses

    @property
    def average_chars_per_second(self) -> float:
        """Calculate average characters processed per second of audio."""
        if self.total_audio_duration_ms == 0:
            return 0.0
        return self.total_characters_processed / (self.total_audio_duration_ms / 1000)


@dataclass
class TTSConfig:
    """Configuration for TTS pipeline."""

    elevenlabs_config: ElevenLabsConfig
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True
    optimize_streaming_latency: int = 3  # 0-4, higher = more optimization


@dataclass
class TTSPipeline:
    """
    Text-to-Speech pipeline using ElevenLabs.

    Handles:
    - Text synthesis to audio
    - Streaming audio generation
    - Voice configuration
    - Performance metrics collection
    """

    config: TTSConfig
    metrics: TTSMetrics = field(default_factory=TTSMetrics)
    state: SynthesisState = SynthesisState.IDLE
    _tts: Optional[tts.TTS] = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Initialize the ElevenLabs TTS instance."""
        self._tts = elevenlabs.TTS(
            api_key=self.config.elevenlabs_config.api_key,
            voice_id=self.config.elevenlabs_config.voice_id,
            model_id=self.config.elevenlabs_config.model_id,
            sample_rate=self.config.elevenlabs_config.sample_rate,
        )
        logger.info(
            "tts_pipeline_initialized",
            voice_id=self.config.elevenlabs_config.voice_id,
            model_id=self.config.elevenlabs_config.model_id,
            sample_rate=self.config.elevenlabs_config.sample_rate,
        )

    async def synthesize(self, text: str, max_retries: int = 3) -> SynthesisResult:
        """
        Synthesize text to audio with retry support.

        Args:
            text: The text to synthesize
            max_retries: Maximum retry attempts for transient failures

        Returns:
            SynthesisResult containing audio data and metrics

        Raises:
            RuntimeError: If synthesis fails after all retries
        """
        if not text.strip():
            raise ValueError("Cannot synthesize empty text")

        self.state = SynthesisState.SYNTHESIZING
        start_time = datetime.now(timezone.utc)
        audio_chunks: list[bytes] = []

        logger.info("tts_synthesis_started", text_length=len(text))

        async def _collect_audio():
            nonlocal audio_chunks
            audio_chunks = []
            stream = self._tts.synthesize(text)
            async for chunk in stream:
                if chunk.frame and chunk.frame.data:
                    audio_chunks.append(chunk.frame.data.tobytes())
            return audio_chunks

        try:
            # Use streaming synthesis and collect all chunks with retry
            await retry_async(_collect_audio, max_retries=max_retries)

            audio_data = b"".join(audio_chunks)
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            # Estimate audio duration (assuming 16-bit samples)
            sample_rate = self.config.elevenlabs_config.sample_rate
            num_samples = len(audio_data) // 2  # 16-bit = 2 bytes per sample
            duration_ms = (num_samples / sample_rate) * 1000

            result = SynthesisResult(
                audio_data=audio_data,
                text=text,
                duration_ms=duration_ms,
                latency_ms=latency_ms,
                sample_rate=sample_rate,
                voice_id=self.config.elevenlabs_config.voice_id,
            )

            # Update metrics
            self.metrics.total_syntheses += 1
            self.metrics.successful_syntheses += 1
            self.metrics.total_latency_ms += latency_ms
            self.metrics.min_latency_ms = min(self.metrics.min_latency_ms, latency_ms)
            self.metrics.max_latency_ms = max(self.metrics.max_latency_ms, latency_ms)
            self.metrics.total_audio_duration_ms += duration_ms
            self.metrics.total_characters_processed += len(text)

            logger.info(
                "tts_synthesis_completed",
                text_length=len(text),
                audio_bytes=len(audio_data),
                duration_ms=round(duration_ms, 2),
                latency_ms=round(latency_ms, 2),
            )

            return result

        except Exception as e:
            self.state = SynthesisState.ERROR
            self.metrics.total_syntheses += 1
            self.metrics.failed_syntheses += 1
            logger.error("tts_synthesis_failed", error=str(e), text_length=len(text))
            raise RuntimeError(f"TTS synthesis failed: {e}") from e

        finally:
            self.state = SynthesisState.IDLE

    async def synthesize_stream(self, text: str) -> AsyncIterator[bytes]:
        """
        Stream synthesized audio chunks.

        Args:
            text: The text to synthesize

        Yields:
            Audio data chunks as they are generated
        """
        if not text.strip():
            raise ValueError("Cannot synthesize empty text")

        self.state = SynthesisState.STREAMING
        start_time = datetime.now(timezone.utc)
        first_chunk_time: Optional[datetime] = None
        total_bytes = 0

        logger.info("tts_streaming_started", text_length=len(text))

        try:
            stream = self._tts.synthesize(text)
            async for chunk in stream:
                if chunk.frame and chunk.frame.data:
                    if first_chunk_time is None:
                        first_chunk_time = datetime.now(timezone.utc)
                        ttfb_ms = (first_chunk_time - start_time).total_seconds() * 1000
                        logger.debug("tts_first_chunk", ttfb_ms=round(ttfb_ms, 2))

                    audio_bytes = chunk.frame.data.tobytes()
                    total_bytes += len(audio_bytes)
                    yield audio_bytes

            # Update metrics after streaming completes
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.metrics.total_syntheses += 1
            self.metrics.successful_syntheses += 1
            self.metrics.total_latency_ms += latency_ms
            self.metrics.total_characters_processed += len(text)

            logger.info(
                "tts_streaming_completed",
                text_length=len(text),
                total_bytes=total_bytes,
                latency_ms=round(latency_ms, 2),
            )

        except Exception as e:
            self.state = SynthesisState.ERROR
            self.metrics.total_syntheses += 1
            self.metrics.failed_syntheses += 1
            logger.error("tts_streaming_failed", error=str(e))
            raise

        finally:
            self.state = SynthesisState.IDLE

    def get_metrics(self) -> TTSMetrics:
        """Get current TTS metrics."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = TTSMetrics()

    @property
    def tts_instance(self) -> tts.TTS:
        """Get the underlying TTS instance for LiveKit Agents integration."""
        if self._tts is None:
            raise RuntimeError("TTS not initialized")
        return self._tts


def create_tts_pipeline(config: Optional[TTSConfig] = None) -> TTSPipeline:
    """
    Factory function to create a TTS pipeline.

    Args:
        config: Optional configuration, loads from environment if not provided

    Returns:
        Configured TTSPipeline instance
    """
    if config is None:
        elevenlabs_config = ElevenLabsConfig()
        config = TTSConfig(elevenlabs_config=elevenlabs_config)
    return TTSPipeline(config=config)
