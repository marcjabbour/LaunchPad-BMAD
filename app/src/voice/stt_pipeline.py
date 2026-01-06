"""Speech-to-Text pipeline using Deepgram via LiveKit Agents."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator, Callable, Optional
from enum import Enum
from functools import wraps

import structlog
from livekit.agents import stt
from livekit.plugins import deepgram

from .config import DeepgramConfig

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
                    "retry_attempt",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay=delay,
                    error=str(e),
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "retry_exhausted",
                    max_retries=max_retries,
                    error=str(e),
                )
    raise last_exception


class TranscriptionState(Enum):
    """State of the transcription pipeline."""

    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class TranscriptionResult:
    """Result from speech-to-text processing."""

    text: str
    is_final: bool
    confidence: float
    start_time: float
    end_time: float
    latency_ms: float
    language: str = "en"


@dataclass
class STTMetrics:
    """Metrics for STT pipeline performance."""

    total_transcriptions: int = 0
    successful_transcriptions: int = 0
    failed_transcriptions: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0
    total_audio_duration_ms: float = 0.0

    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.successful_transcriptions == 0:
            return 0.0
        return self.total_latency_ms / self.successful_transcriptions

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_transcriptions == 0:
            return 0.0
        return self.successful_transcriptions / self.total_transcriptions


@dataclass
class STTConfig:
    """Configuration for STT pipeline."""

    deepgram_config: DeepgramConfig
    interim_results: bool = True
    punctuate: bool = True
    smart_format: bool = True
    vad_enabled: bool = True
    endpointing_ms: int = 300


@dataclass
class STTPipeline:
    """
    Speech-to-Text pipeline using Deepgram.

    Handles:
    - Audio stream processing
    - Real-time transcription with interim results
    - Error handling and retry logic
    - Performance metrics collection
    """

    config: STTConfig
    metrics: STTMetrics = field(default_factory=STTMetrics)
    state: TranscriptionState = TranscriptionState.IDLE
    _stt: Optional[stt.STT] = field(default=None, init=False)
    _on_transcription: Optional[Callable[[TranscriptionResult], None]] = None

    def __post_init__(self) -> None:
        """Initialize the Deepgram STT instance."""
        self._stt = deepgram.STT(
            api_key=self.config.deepgram_config.api_key,
            model=self.config.deepgram_config.model,
            language=self.config.deepgram_config.language,
            interim_results=self.config.interim_results,
            punctuate=self.config.punctuate,
            smart_format=self.config.smart_format,
        )
        logger.info(
            "stt_pipeline_initialized",
            model=self.config.deepgram_config.model,
            language=self.config.deepgram_config.language,
        )

    def set_transcription_callback(
        self, callback: Callable[[TranscriptionResult], None]
    ) -> None:
        """Set callback for transcription results."""
        self._on_transcription = callback

    async def process_audio_stream(
        self, audio_stream: stt.SpeechStream
    ) -> AsyncIterator[TranscriptionResult]:
        """
        Process an audio stream and yield transcription results.

        Args:
            audio_stream: The speech stream to process

        Yields:
            TranscriptionResult for each transcription event
        """
        self.state = TranscriptionState.LISTENING
        logger.info("stt_processing_started")

        try:
            async for event in audio_stream:
                if event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                    result = await self._handle_transcript(event, is_final=True)
                    if result:
                        yield result
                        if self._on_transcription:
                            self._on_transcription(result)

                elif event.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
                    result = await self._handle_transcript(event, is_final=False)
                    if result:
                        yield result
                        if self._on_transcription:
                            self._on_transcription(result)

                elif event.type == stt.SpeechEventType.END_OF_SPEECH:
                    logger.debug("end_of_speech_detected")

        except Exception as e:
            self.state = TranscriptionState.ERROR
            self.metrics.failed_transcriptions += 1
            logger.error("stt_processing_error", error=str(e))
            raise

        finally:
            self.state = TranscriptionState.IDLE
            logger.info(
                "stt_processing_completed",
                total_transcriptions=self.metrics.total_transcriptions,
                success_rate=self.metrics.success_rate,
            )

    async def _handle_transcript(
        self, event: stt.SpeechEvent, is_final: bool
    ) -> Optional[TranscriptionResult]:
        """Handle a transcription event and create result."""
        if not event.alternatives:
            return None

        best_alternative = event.alternatives[0]
        if not best_alternative.text.strip():
            return None

        # Calculate latency (time from speech end to transcription)
        receive_time = datetime.now(timezone.utc).timestamp()
        latency_ms = (receive_time - event.alternatives[0].start_time) * 1000

        result = TranscriptionResult(
            text=best_alternative.text,
            is_final=is_final,
            confidence=best_alternative.confidence if hasattr(best_alternative, 'confidence') else 0.95,
            start_time=best_alternative.start_time if hasattr(best_alternative, 'start_time') else 0.0,
            end_time=best_alternative.end_time if hasattr(best_alternative, 'end_time') else 0.0,
            latency_ms=latency_ms,
            language=self.config.deepgram_config.language,
        )

        # Update metrics
        self.metrics.total_transcriptions += 1
        if is_final:
            self.metrics.successful_transcriptions += 1
            self.metrics.total_latency_ms += latency_ms
            self.metrics.min_latency_ms = min(self.metrics.min_latency_ms, latency_ms)
            self.metrics.max_latency_ms = max(self.metrics.max_latency_ms, latency_ms)

        logger.debug(
            "transcription_received",
            text=result.text[:50] + "..." if len(result.text) > 50 else result.text,
            is_final=is_final,
            latency_ms=round(latency_ms, 2),
        )

        return result

    async def transcribe_audio(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        max_retries: int = 3,
    ) -> str:
        """
        Transcribe a single audio buffer with retry support.

        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate in Hz
            max_retries: Maximum retry attempts for transient failures

        Returns:
            Transcribed text
        """
        self.state = TranscriptionState.PROCESSING
        start_time = datetime.now(timezone.utc)

        async def _do_transcribe():
            return await self._stt.recognize(
                buffer=audio_data,
                sample_rate=sample_rate,
            )

        try:
            # Use recognize for single-shot transcription with retry
            result = await retry_async(_do_transcribe, max_retries=max_retries)

            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            text = result.text if result else ""

            self.metrics.total_transcriptions += 1
            self.metrics.successful_transcriptions += 1
            self.metrics.total_latency_ms += latency_ms

            logger.info(
                "audio_transcribed",
                text_length=len(text),
                latency_ms=round(latency_ms, 2),
            )

            return text

        except Exception as e:
            self.metrics.total_transcriptions += 1
            self.metrics.failed_transcriptions += 1
            self.state = TranscriptionState.ERROR
            logger.error("transcription_failed", error=str(e))
            raise

        finally:
            self.state = TranscriptionState.IDLE

    def get_metrics(self) -> STTMetrics:
        """Get current STT metrics."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = STTMetrics()

    @property
    def stt_instance(self) -> stt.STT:
        """Get the underlying STT instance for LiveKit Agents integration."""
        if self._stt is None:
            raise RuntimeError("STT not initialized")
        return self._stt


def create_stt_pipeline(config: Optional[STTConfig] = None) -> STTPipeline:
    """
    Factory function to create an STT pipeline.

    Args:
        config: Optional configuration, loads from environment if not provided

    Returns:
        Configured STTPipeline instance
    """
    if config is None:
        deepgram_config = DeepgramConfig()
        config = STTConfig(deepgram_config=deepgram_config)
    return STTPipeline(config=config)
