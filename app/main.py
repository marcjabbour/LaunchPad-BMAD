"""
LaunchPad Voice Agent - Main Entry Point

This module provides the main entry point for the LaunchPad voice agent,
integrating LiveKit, Deepgram STT, and ElevenLabs TTS into a cohesive
voice processing pipeline.
"""

import asyncio
import logging
from typing import Optional

import structlog
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, elevenlabs, silero

from src.voice.config import (
    LiveKitConfig,
    DeepgramConfig,
    ElevenLabsConfig,
    VoiceProcessingConfig,
)
from src.voice.audio_quality import LatencyTracker, AudioQualityMetrics

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global metrics trackers
latency_tracker = LatencyTracker()
quality_metrics = AudioQualityMetrics()


def prewarm(proc: JobProcess) -> None:
    """
    Prewarm function called when the worker starts.

    Loads models and initializes resources that should be ready
    before accepting jobs.
    """
    logger.info("prewarming_agent")

    # Prewarm VAD model for faster startup
    proc.userdata["vad"] = silero.VAD.load()

    logger.info("prewarm_complete")


async def entrypoint(ctx: JobContext) -> None:
    """
    Main entrypoint for the voice agent.

    This function is called when the agent joins a room and should
    set up the voice processing pipeline.
    """
    logger.info(
        "agent_entrypoint_started",
        room=ctx.room.name,
        participant_identity=ctx.room.local_participant.identity,
    )

    # Load configurations
    voice_config = VoiceProcessingConfig()
    deepgram_config = DeepgramConfig()
    elevenlabs_config = ElevenLabsConfig()

    # Initialize components
    vad = ctx.proc.userdata.get("vad") or silero.VAD.load()

    stt = deepgram.STT(
        api_key=deepgram_config.api_key,
        model=deepgram_config.model,
        language=deepgram_config.language,
    )

    tts = elevenlabs.TTS(
        api_key=elevenlabs_config.api_key,
        voice_id=elevenlabs_config.voice_id,
        model_id=elevenlabs_config.model_id,
    )

    # Create a simple initial context for the agent
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a helpful voice assistant. You are friendly, concise, "
            "and speak naturally. Keep responses brief and conversational."
        ),
    )

    logger.info(
        "voice_pipeline_configured",
        stt_model=deepgram_config.model,
        tts_voice=elevenlabs_config.voice_id,
    )

    # Wait for a participant to connect
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info("participant_connected", participant=participant.identity)

    # Note: Full VoiceAssistant requires an LLM plugin
    # This is a basic setup - Story 1.2 will add the LLM integration
    logger.info(
        "voice_agent_ready",
        room=ctx.room.name,
        target_latency_ms=voice_config.target_total_latency_ms,
    )

    # For now, log that the pipeline is ready
    # Full implementation will come with Story 1.2 (LLM integration)
    logger.info(
        "pipeline_status",
        stt="ready",
        tts="ready",
        vad="ready",
        llm="pending_story_1_2",
    )


if __name__ == "__main__":
    logger.info("starting_launchpad_agent")

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
