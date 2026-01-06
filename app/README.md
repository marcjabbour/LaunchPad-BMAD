# LaunchPad Voice Agent

Voice-first AI agent platform for real-time meeting collaboration.

## Overview

LaunchPad enables AI agents to join meetings via voice, providing expert technical assistance in real-time using LiveKit for voice infrastructure, Deepgram for speech-to-text, and ElevenLabs for text-to-speech.

## Quick Start

### Prerequisites

- Python 3.11+
- LiveKit Cloud account (or self-hosted LiveKit server)
- Deepgram API key
- ElevenLabs API key

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `LIVEKIT_URL` | LiveKit server URL (e.g., `wss://your-project.livekit.cloud`) |
| `DEEPGRAM_API_KEY` | Deepgram API key for STT |
| `ELEVENLABS_API_KEY` | ElevenLabs API key for TTS |

### Running the Agent

```bash
python main.py start
```

### Running with Docker

```bash
docker-compose up --build
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy src/
```

## Architecture

```
app/
├── src/
│   ├── voice/           # Voice processing pipeline
│   │   ├── config.py    # Configuration management
│   │   ├── livekit_client.py   # LiveKit integration
│   │   ├── stt_pipeline.py     # Speech-to-text
│   │   ├── tts_pipeline.py     # Text-to-speech
│   │   └── audio_quality.py    # Quality metrics
│   ├── agent/           # Agent logic (Story 1.2)
│   └── utils/           # Utilities
├── tests/               # Test suite
├── main.py              # Entry point
└── pyproject.toml       # Project configuration
```

## License

Proprietary - All rights reserved.
