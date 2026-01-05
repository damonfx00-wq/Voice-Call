# Voice Call AI Assistant - Frontend

A modern voice-call interface for interacting with an AI assistant powered by MCP server and NVIDIA API.

## Features

- 🎤 **Voice-Only Interface**: Continuous listening with automatic speech recognition
- 📞 **Phone-Style UI**: Familiar dial pad and call interface
- 🎨 **Google-Inspired Design**: Modern, clean aesthetics with dark mode support
- 🔊 **Text-to-Speech**: Natural voice responses from AI
- 📊 **Audio Visualization**: Real-time audio level indicators
- ⚡ **HD Voice Quality**: Enhanced audio capture with noise suppression

## Quick Start

```bash
cd frontend
bun install
bun dev
```

Visit `http://localhost:5173` and start calling!

## Usage

1. Click the green call button (or dial a number first)
2. Wait for AI greeting
3. Speak naturally - mic is always on
4. AI responds with voice automatically
5. Click red button to end call

## Configuration

Create `.env`:
```
VITE_API_URL=http://localhost:8000
```

## Browser Support

Best on Chrome/Edge (requires Web Speech API)

## License

MIT
