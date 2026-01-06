"""LiveKit client wrapper for voice agent infrastructure."""

import asyncio
from dataclasses import dataclass, field
from typing import Callable, Optional
from datetime import datetime, timezone

import structlog
from livekit import rtc, api
from livekit.agents import JobContext, WorkerOptions, cli

from .config import LiveKitConfig

logger = structlog.get_logger(__name__)


@dataclass
class ConnectionMetrics:
    """Metrics for LiveKit connection health."""

    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    reconnect_count: int = 0
    last_error: Optional[str] = None
    is_connected: bool = False


@dataclass
class LiveKitClient:
    """
    LiveKit client wrapper providing connection management and room operations.

    This client handles:
    - Connection lifecycle (connect, disconnect, reconnect)
    - Room management
    - Audio track publishing/subscribing
    - Connection health monitoring
    """

    config: LiveKitConfig
    metrics: ConnectionMetrics = field(default_factory=ConnectionMetrics)
    _room: Optional[rtc.Room] = field(default=None, init=False)
    _api_client: Optional[api.LiveKitAPI] = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Initialize the LiveKit API client."""
        self._api_client = api.LiveKitAPI(
            url=self.config.url,
            api_key=self.config.api_key,
            api_secret=self.config.api_secret,
        )
        logger.info("livekit_client_initialized", url=self.config.url)

    async def connect_to_room(
        self,
        room_name: str,
        participant_identity: str,
        on_track_subscribed: Optional[Callable] = None,
    ) -> rtc.Room:
        """
        Connect to a LiveKit room.

        Args:
            room_name: Name of the room to join
            participant_identity: Identity for this participant
            on_track_subscribed: Callback when a new track is subscribed

        Returns:
            The connected Room instance

        Raises:
            ConnectionError: If connection fails after retries
        """
        logger.info(
            "connecting_to_room",
            room_name=room_name,
            participant_identity=participant_identity,
        )

        # Generate access token
        token = (
            api.AccessToken(self.config.api_key, self.config.api_secret)
            .with_identity(participant_identity)
            .with_name(participant_identity)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .to_jwt()
        )

        # Create and connect to room
        self._room = rtc.Room()

        # Set up event handlers
        @self._room.on("track_subscribed")
        def on_track_subscribed_handler(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ) -> None:
            logger.info(
                "track_subscribed",
                track_sid=track.sid,
                track_kind=track.kind,
                participant=participant.identity,
            )
            if on_track_subscribed:
                on_track_subscribed(track, publication, participant)

        @self._room.on("disconnected")
        def on_disconnected() -> None:
            logger.warning("room_disconnected")
            self.metrics.is_connected = False
            self.metrics.disconnected_at = datetime.now(timezone.utc)

        @self._room.on("reconnecting")
        def on_reconnecting() -> None:
            logger.info("room_reconnecting")
            self.metrics.reconnect_count += 1

        @self._room.on("reconnected")
        def on_reconnected() -> None:
            logger.info("room_reconnected")
            self.metrics.is_connected = True

        try:
            await self._room.connect(self.config.url, token)
            self.metrics.is_connected = True
            self.metrics.connected_at = datetime.now(timezone.utc)
            logger.info("room_connected", room_name=room_name)
            return self._room

        except Exception as e:
            self.metrics.last_error = str(e)
            logger.error("room_connection_failed", error=str(e))
            raise ConnectionError(f"Failed to connect to room: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the current room."""
        if self._room:
            await self._room.disconnect()
            self._room = None
            self.metrics.is_connected = False
            self.metrics.disconnected_at = datetime.now(timezone.utc)
            logger.info("disconnected_from_room")

    async def publish_audio_track(self, source: rtc.AudioSource) -> rtc.LocalAudioTrack:
        """
        Publish an audio track to the room.

        Args:
            source: The audio source to publish

        Returns:
            The published LocalAudioTrack

        Raises:
            RuntimeError: If not connected to a room
        """
        if not self._room or not self.metrics.is_connected:
            raise RuntimeError("Not connected to a room")

        track = rtc.LocalAudioTrack.create_audio_track("agent-voice", source)
        options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        publication = await self._room.local_participant.publish_track(track, options)

        logger.info("audio_track_published", track_sid=publication.sid)
        return track

    def get_connection_metrics(self) -> ConnectionMetrics:
        """Get current connection metrics."""
        return self.metrics

    @property
    def room(self) -> Optional[rtc.Room]:
        """Get the current room instance."""
        return self._room

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to a room."""
        return self.metrics.is_connected


def create_livekit_client(config: Optional[LiveKitConfig] = None) -> LiveKitClient:
    """
    Factory function to create a LiveKit client.

    Args:
        config: Optional configuration, loads from environment if not provided

    Returns:
        Configured LiveKitClient instance
    """
    if config is None:
        config = LiveKitConfig()
    return LiveKitClient(config=config)
