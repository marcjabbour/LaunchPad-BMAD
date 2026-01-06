"""Audio quality metrics and latency tracking for voice pipeline."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from statistics import mean, stdev

import structlog

logger = structlog.get_logger(__name__)


class LatencyPhase(Enum):
    """Phases of the voice processing pipeline."""

    STT_START = "stt_start"
    STT_END = "stt_end"
    PROCESSING_START = "processing_start"
    PROCESSING_END = "processing_end"
    TTS_START = "tts_start"
    TTS_END = "tts_end"
    TOTAL = "total"


@dataclass
class LatencyMeasurement:
    """Single latency measurement."""

    phase: LatencyPhase
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class PipelineLatency:
    """Complete pipeline latency breakdown."""

    stt_latency_ms: float
    processing_latency_ms: float
    tts_latency_ms: float
    total_latency_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def meets_target(self) -> bool:
        """Check if total latency meets the 2000ms target."""
        return self.total_latency_ms < 2000.0


@dataclass
class LatencyTracker:
    """
    Tracks latency across the voice processing pipeline.

    Provides:
    - Per-phase timing
    - Rolling averages
    - Target compliance tracking
    """

    target_total_ms: float = 2000.0
    target_stt_ms: float = 500.0
    target_tts_ms: float = 500.0
    window_size: int = 100

    _measurements: List[PipelineLatency] = field(default_factory=list)
    _current_phases: dict = field(default_factory=dict)
    _start_time: Optional[float] = None

    def start_pipeline(self) -> None:
        """Mark the start of a new pipeline execution."""
        self._start_time = time.perf_counter()
        self._current_phases = {}
        logger.debug("pipeline_latency_tracking_started")

    def mark_phase_start(self, phase: LatencyPhase) -> None:
        """Mark the start of a phase."""
        self._current_phases[f"{phase.value}_start"] = time.perf_counter()

    def mark_phase_end(self, phase: LatencyPhase) -> float:
        """
        Mark the end of a phase and return duration.

        Returns:
            Duration in milliseconds
        """
        end_time = time.perf_counter()
        start_key = f"{phase.value}_start"

        if start_key not in self._current_phases:
            logger.warning("phase_end_without_start", phase=phase.value)
            return 0.0

        duration_ms = (end_time - self._current_phases[start_key]) * 1000
        self._current_phases[f"{phase.value}_duration"] = duration_ms
        return duration_ms

    def complete_pipeline(self) -> PipelineLatency:
        """
        Complete pipeline tracking and record measurement.

        Returns:
            PipelineLatency with all phase durations
        """
        if self._start_time is None:
            raise RuntimeError("Pipeline tracking not started")

        total_ms = (time.perf_counter() - self._start_time) * 1000

        latency = PipelineLatency(
            stt_latency_ms=self._current_phases.get("stt_end_duration", 0.0),
            processing_latency_ms=self._current_phases.get("processing_end_duration", 0.0),
            tts_latency_ms=self._current_phases.get("tts_end_duration", 0.0),
            total_latency_ms=total_ms,
        )

        # Add to rolling window
        self._measurements.append(latency)
        if len(self._measurements) > self.window_size:
            self._measurements.pop(0)

        logger.info(
            "pipeline_latency_recorded",
            total_ms=round(total_ms, 2),
            stt_ms=round(latency.stt_latency_ms, 2),
            tts_ms=round(latency.tts_latency_ms, 2),
            meets_target=latency.meets_target,
        )

        # Reset for next pipeline
        self._start_time = None
        self._current_phases = {}

        return latency

    def get_average_latencies(self) -> dict:
        """Get average latencies across the measurement window."""
        if not self._measurements:
            return {
                "stt_avg_ms": 0.0,
                "processing_avg_ms": 0.0,
                "tts_avg_ms": 0.0,
                "total_avg_ms": 0.0,
                "sample_count": 0,
            }

        return {
            "stt_avg_ms": mean(m.stt_latency_ms for m in self._measurements),
            "processing_avg_ms": mean(m.processing_latency_ms for m in self._measurements),
            "tts_avg_ms": mean(m.tts_latency_ms for m in self._measurements),
            "total_avg_ms": mean(m.total_latency_ms for m in self._measurements),
            "sample_count": len(self._measurements),
        }

    def get_percentile_latency(self, percentile: float = 95.0) -> float:
        """Get the specified percentile of total latency."""
        if not self._measurements:
            return 0.0

        sorted_latencies = sorted(m.total_latency_ms for m in self._measurements)
        index = int(len(sorted_latencies) * (percentile / 100))
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    def get_target_compliance_rate(self) -> float:
        """Get the percentage of measurements meeting the target."""
        if not self._measurements:
            return 0.0

        compliant = sum(1 for m in self._measurements if m.meets_target)
        return compliant / len(self._measurements)


@dataclass
class AudioQualityMetrics:
    """
    Audio quality measurement and tracking.

    Provides:
    - Signal-to-noise ratio estimation
    - Voice activity detection stats
    - Quality scoring
    """

    quality_scores: List[float] = field(default_factory=list)
    window_size: int = 50

    # Quality thresholds
    excellent_threshold: float = 8.0
    good_threshold: float = 6.0
    acceptable_threshold: float = 4.0

    def record_quality_score(self, score: float, metadata: Optional[dict] = None) -> None:
        """
        Record a quality score (0-10 scale).

        Args:
            score: Quality score from 0 (worst) to 10 (best)
            metadata: Optional additional context
        """
        clamped_score = max(0.0, min(10.0, score))
        self.quality_scores.append(clamped_score)

        if len(self.quality_scores) > self.window_size:
            self.quality_scores.pop(0)

        quality_level = self._get_quality_level(clamped_score)
        logger.debug(
            "audio_quality_recorded",
            score=round(clamped_score, 2),
            level=quality_level,
            metadata=metadata or {},
        )

    def _get_quality_level(self, score: float) -> str:
        """Get quality level string from score."""
        if score >= self.excellent_threshold:
            return "excellent"
        elif score >= self.good_threshold:
            return "good"
        elif score >= self.acceptable_threshold:
            return "acceptable"
        else:
            return "poor"

    def get_average_quality(self) -> float:
        """Get average quality score."""
        if not self.quality_scores:
            return 0.0
        return mean(self.quality_scores)

    def get_quality_stats(self) -> dict:
        """Get comprehensive quality statistics."""
        if not self.quality_scores:
            return {
                "average": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std_dev": 0.0,
                "sample_count": 0,
                "acceptable_rate": 0.0,
            }

        return {
            "average": mean(self.quality_scores),
            "min": min(self.quality_scores),
            "max": max(self.quality_scores),
            "std_dev": stdev(self.quality_scores) if len(self.quality_scores) > 1 else 0.0,
            "sample_count": len(self.quality_scores),
            "acceptable_rate": sum(
                1 for s in self.quality_scores if s >= self.acceptable_threshold
            ) / len(self.quality_scores),
        }

    def meets_minimum_standard(self, min_score: float = 6.0) -> bool:
        """Check if average quality meets minimum standard."""
        return self.get_average_quality() >= min_score

    def reset(self) -> None:
        """Reset all quality measurements."""
        self.quality_scores = []


def create_latency_tracker(
    target_total_ms: float = 2000.0,
    window_size: int = 100,
) -> LatencyTracker:
    """Create a latency tracker with specified targets."""
    return LatencyTracker(
        target_total_ms=target_total_ms,
        window_size=window_size,
    )


def create_quality_metrics(window_size: int = 50) -> AudioQualityMetrics:
    """Create an audio quality metrics tracker."""
    return AudioQualityMetrics(window_size=window_size)
