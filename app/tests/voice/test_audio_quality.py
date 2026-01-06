"""Tests for audio quality metrics and latency tracking."""

import pytest
import time
from unittest.mock import patch

from src.voice.audio_quality import (
    LatencyTracker,
    LatencyPhase,
    PipelineLatency,
    AudioQualityMetrics,
    create_latency_tracker,
    create_quality_metrics,
)


class TestPipelineLatency:
    """Tests for pipeline latency data class."""

    def test_meets_target_under_threshold(self) -> None:
        """Test meets_target returns True when under 2000ms."""
        latency = PipelineLatency(
            stt_latency_ms=300.0,
            processing_latency_ms=200.0,
            tts_latency_ms=400.0,
            total_latency_ms=900.0,
        )
        assert latency.meets_target is True

    def test_meets_target_over_threshold(self) -> None:
        """Test meets_target returns False when over 2000ms."""
        latency = PipelineLatency(
            stt_latency_ms=800.0,
            processing_latency_ms=500.0,
            tts_latency_ms=900.0,
            total_latency_ms=2200.0,
        )
        assert latency.meets_target is False

    def test_meets_target_at_threshold(self) -> None:
        """Test meets_target returns False at exactly 2000ms."""
        latency = PipelineLatency(
            stt_latency_ms=700.0,
            processing_latency_ms=600.0,
            tts_latency_ms=700.0,
            total_latency_ms=2000.0,
        )
        assert latency.meets_target is False


class TestLatencyTracker:
    """Tests for latency tracking."""

    def test_initial_state(self) -> None:
        """Test tracker starts with empty measurements."""
        tracker = LatencyTracker()
        averages = tracker.get_average_latencies()
        assert averages["sample_count"] == 0
        assert averages["total_avg_ms"] == 0.0

    def test_start_pipeline(self) -> None:
        """Test starting pipeline tracking."""
        tracker = LatencyTracker()
        tracker.start_pipeline()
        assert tracker._start_time is not None

    def test_mark_phase(self) -> None:
        """Test marking phase start and end."""
        tracker = LatencyTracker()
        tracker.start_pipeline()
        tracker.mark_phase_start(LatencyPhase.STT_START)
        time.sleep(0.01)  # Small delay
        duration = tracker.mark_phase_end(LatencyPhase.STT_END)
        assert duration > 0

    def test_complete_pipeline(self) -> None:
        """Test completing pipeline tracking."""
        tracker = LatencyTracker()
        tracker.start_pipeline()
        tracker.mark_phase_start(LatencyPhase.STT_START)
        tracker.mark_phase_end(LatencyPhase.STT_END)
        tracker.mark_phase_start(LatencyPhase.TTS_START)
        tracker.mark_phase_end(LatencyPhase.TTS_END)

        result = tracker.complete_pipeline()
        assert isinstance(result, PipelineLatency)
        assert result.total_latency_ms > 0

    def test_complete_pipeline_without_start_raises(self) -> None:
        """Test completing pipeline without start raises error."""
        tracker = LatencyTracker()
        with pytest.raises(RuntimeError, match="Pipeline tracking not started"):
            tracker.complete_pipeline()

    def test_rolling_window(self) -> None:
        """Test measurements maintain rolling window."""
        tracker = LatencyTracker(window_size=5)

        for _ in range(10):
            tracker.start_pipeline()
            tracker.complete_pipeline()

        averages = tracker.get_average_latencies()
        assert averages["sample_count"] == 5

    def test_get_percentile_latency(self) -> None:
        """Test percentile latency calculation."""
        tracker = LatencyTracker()

        # Add some measurements
        for _ in range(10):
            tracker.start_pipeline()
            tracker.complete_pipeline()

        p95 = tracker.get_percentile_latency(95.0)
        assert p95 >= 0

    def test_get_percentile_latency_empty(self) -> None:
        """Test percentile returns 0 for empty measurements."""
        tracker = LatencyTracker()
        assert tracker.get_percentile_latency(95.0) == 0.0

    def test_target_compliance_rate(self) -> None:
        """Test target compliance rate calculation."""
        tracker = LatencyTracker(target_total_ms=2000.0)

        # All measurements should be under target (fast execution)
        for _ in range(5):
            tracker.start_pipeline()
            tracker.complete_pipeline()

        rate = tracker.get_target_compliance_rate()
        assert rate == 1.0  # All should meet target


class TestAudioQualityMetrics:
    """Tests for audio quality metrics."""

    def test_initial_state(self) -> None:
        """Test metrics start empty."""
        metrics = AudioQualityMetrics()
        assert metrics.get_average_quality() == 0.0
        assert len(metrics.quality_scores) == 0

    def test_record_quality_score(self) -> None:
        """Test recording quality scores."""
        metrics = AudioQualityMetrics()
        metrics.record_quality_score(8.5)
        metrics.record_quality_score(7.0)
        assert len(metrics.quality_scores) == 2
        assert metrics.get_average_quality() == 7.75

    def test_score_clamping(self) -> None:
        """Test scores are clamped to 0-10 range."""
        metrics = AudioQualityMetrics()
        metrics.record_quality_score(-5.0)
        metrics.record_quality_score(15.0)
        assert metrics.quality_scores == [0.0, 10.0]

    def test_rolling_window(self) -> None:
        """Test quality scores maintain rolling window."""
        metrics = AudioQualityMetrics(window_size=5)

        for i in range(10):
            metrics.record_quality_score(float(i))

        assert len(metrics.quality_scores) == 5
        # Should have scores 5, 6, 7, 8, 9
        assert metrics.quality_scores == [5.0, 6.0, 7.0, 8.0, 9.0]

    def test_get_quality_stats(self) -> None:
        """Test comprehensive quality statistics."""
        metrics = AudioQualityMetrics()
        metrics.record_quality_score(6.0)
        metrics.record_quality_score(8.0)
        metrics.record_quality_score(7.0)

        stats = metrics.get_quality_stats()
        assert stats["average"] == 7.0
        assert stats["min"] == 6.0
        assert stats["max"] == 8.0
        assert stats["sample_count"] == 3

    def test_meets_minimum_standard(self) -> None:
        """Test minimum standard check."""
        metrics = AudioQualityMetrics()
        metrics.record_quality_score(7.0)
        metrics.record_quality_score(8.0)

        assert metrics.meets_minimum_standard(min_score=6.0) is True
        assert metrics.meets_minimum_standard(min_score=8.0) is False

    def test_reset(self) -> None:
        """Test resetting metrics."""
        metrics = AudioQualityMetrics()
        metrics.record_quality_score(8.0)
        metrics.reset()
        assert len(metrics.quality_scores) == 0


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_latency_tracker(self) -> None:
        """Test latency tracker factory."""
        tracker = create_latency_tracker(target_total_ms=1500.0, window_size=50)
        assert tracker.target_total_ms == 1500.0
        assert tracker.window_size == 50

    def test_create_quality_metrics(self) -> None:
        """Test quality metrics factory."""
        metrics = create_quality_metrics(window_size=25)
        assert metrics.window_size == 25
