"""
LaunchPad Voice Agent - Main Entry Point

This module provides the main entry point for the LaunchPad voice agent,
integrating LiveKit, Deepgram STT, and ElevenLabs TTS into a cohesive
voice processing pipeline.

Story 1.1: Establishes the STT→TTS pipeline with latency tracking.
Story 1.2: Will add full LLM integration for intelligent responses.
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
from livekit.plugins import deepgram, elevenlabs, silero, openai

from src.voice.config import (
    LiveKitConfig,
    DeepgramConfig,
    ElevenLabsConfig,
    VoiceProcessingConfig,
)
from src.voice.audio_quality import LatencyTracker, LatencyPhase, AudioQualityMetrics

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


class SimpleEchoLLM(llm.LLM):
    """
    Simple echo LLM for testing the STT→TTS pipeline without external LLM.

    This allows validating the full voice pipeline (AC-7) without requiring
    an LLM API key. Story 1.2 will add real LLM integration.
    """

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        conn_options: llm.LLMOptions | None = None,
        fnc_ctx: llm.FunctionContext | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> llm.LLMStream:
        """Return echo response for testing."""
        return SimpleEchoStream(chat_ctx)


class SimpleEchoStream(llm.LLMStream):
    """Stream that echoes back the last user message for pipeline testing."""

    def __init__(self, chat_ctx: llm.ChatContext):
        super().__init__(chat_ctx=chat_ctx, conn_options=llm.LLMOptions())
        self._chat_ctx = chat_ctx

    async def _run(self) -> None:
        """Generate echo response."""
        # Get the last user message
        last_user_msg = ""
        for msg in reversed(self._chat_ctx.messages):
            if msg.role == "user" and msg.content:
                last_user_msg = msg.content
                break

        # Generate echo response
        if last_user_msg:
            response = f"I heard you say: {last_user_msg}"
        else:
            response = "Hello! I'm the LaunchPad voice assistant. How can I help you today?"

        # Track latency for this processing phase
        latency_tracker.mark_phase_start(LatencyPhase.PROCESSING_START)

        # Emit the response as a single chunk
        self._event_ch.send_nowait(
            llm.ChatChunk(
                choices=[
                    llm.Choice(
                        delta=llm.ChoiceDelta(
                            role="assistant",
                            content=response,
                        ),
                        index=0,
                    )
                ],
            )
        )

        latency_tracker.mark_phase_end(LatencyPhase.PROCESSING_END)

    async def aclose(self) -> None:
        """Close the stream."""
        pass


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

    This function is called when the agent joins a room and sets up
    the complete STT→Processing→TTS voice pipeline.
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

    # Initialize VAD (Voice Activity Detection)
    vad = ctx.proc.userdata.get("vad") or silero.VAD.load()

    # Initialize STT (Speech-to-Text) with Deepgram
    stt = deepgram.STT(
        api_key=deepgram_config.api_key,
        model=deepgram_config.model,
        language=deepgram_config.language,
    )

    # Initialize TTS (Text-to-Speech) with ElevenLabs
    tts = elevenlabs.TTS(
        api_key=elevenlabs_config.api_key,
        voice_id=elevenlabs_config.voice_id,
        model_id=elevenlabs_config.model_id,
    )

    # Initialize LLM - use SimpleEchoLLM for Story 1.1 pipeline validation
    # Story 1.2 will replace this with a real LLM (OpenAI/Anthropic)
    echo_llm = SimpleEchoLLM()

    # Create initial context for the agent
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
        llm_type="SimpleEchoLLM",
    )

    # Wait for a participant to connect
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info("participant_connected", participant=participant.identity)

    # Start pipeline latency tracking
    latency_tracker.start_pipeline()
    latency_tracker.mark_phase_start(LatencyPhase.STT_START)

    # Create and start the VoiceAssistant with full STT→LLM→TTS pipeline
    assistant = VoiceAssistant(
        vad=vad,
        stt=stt,
        llm=echo_llm,
        tts=tts,
        chat_ctx=initial_ctx,
    )

    # Start the assistant - this connects STT→Processing→TTS
    assistant.start(ctx.room, participant)

    logger.info(
        "voice_agent_ready",
        room=ctx.room.name,
        target_latency_ms=voice_config.target_total_latency_ms,
        pipeline_status="STT→Processing→TTS connected",
    )

    # Log pipeline status - all components now connected
    logger.info(
        "pipeline_status",
        stt="connected",
        tts="connected",
        vad="connected",
        llm="echo_mode",
        note="Story 1.2 will add real LLM integration",
    )

    # Keep the agent running
    await assistant.say("Hello! I'm the LaunchPad voice assistant. I'm ready to help.")

    # Wait indefinitely (agent will process voice until disconnected)
    # The VoiceAssistant handles the continuous STT→LLM→TTS loop
    try:
        await asyncio.sleep(float("inf"))
    except asyncio.CancelledError:
        logger.info("agent_shutting_down")
        latency_tracker.complete_pipeline()
        logger.info(
            "final_latency_metrics",
            **latency_tracker.get_average_latencies(),
        )


if __name__ == "__main__":
    logger.info("starting_launchpad_agent")

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
