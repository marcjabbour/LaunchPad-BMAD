"""Configuration management for voice processing."""

from pydantic_settings import BaseSettings
from pydantic import Field


class LiveKitConfig(BaseSettings):
    """LiveKit connection configuration."""

    api_key: str = Field(..., alias="LIVEKIT_API_KEY")
    api_secret: str = Field(..., alias="LIVEKIT_API_SECRET")
    url: str = Field(..., alias="LIVEKIT_URL")

    model_config = {"env_file": ".env", "extra": "ignore"}


class DeepgramConfig(BaseSettings):
    """Deepgram STT configuration."""

    api_key: str = Field(..., alias="DEEPGRAM_API_KEY")
    model: str = Field(default="nova-2", alias="DEEPGRAM_MODEL")
    language: str = Field(default="en-US", alias="DEEPGRAM_LANGUAGE")

    model_config = {"env_file": ".env", "extra": "ignore"}


class ElevenLabsConfig(BaseSettings):
    """ElevenLabs TTS configuration."""

    api_key: str = Field(..., alias="ELEVENLABS_API_KEY")
    voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM", alias="ELEVENLABS_VOICE_ID")
    model_id: str = Field(default="eleven_turbo_v2", alias="ELEVENLABS_MODEL_ID")
    sample_rate: int = Field(default=24000, alias="TTS_SAMPLE_RATE")

    model_config = {"env_file": ".env", "extra": "ignore"}


class VoiceProcessingConfig(BaseSettings):
    """Aggregate voice processing configuration."""

    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Latency targets (milliseconds)
    target_stt_latency_ms: int = Field(default=500)
    target_tts_latency_ms: int = Field(default=500)
    target_total_latency_ms: int = Field(default=2000)

    # Quality thresholds
    min_audio_quality_score: float = Field(default=6.0)
    min_stt_accuracy: float = Field(default=0.95)

    model_config = {"env_file": ".env", "extra": "ignore"}
