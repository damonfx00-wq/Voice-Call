# Hotel Booking Voice Assistant

A real-time voice-powered hotel booking system with AI assistant capabilities.

## Features

- 🎤 **Voice-Activated Interface** - Natural voice conversations for hotel bookings
- 🏨 **Hotel Room Search** - Search available rooms by dates, guests, room type, and price
- 📅 **Booking Management** - Create, view, and cancel hotel reservations
- 🤖 **AI Assistant** - Intelligent agent powered by NVIDIA API for natural conversations
- 💬 **Real-time Communication** - Instant responses with speech recognition and text-to-speech
- 📝 **Transcript Saving** - Automatic call transcript storage

## Project Structure

```
Voice-Call/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── agent.py          # AI agent for hotel bookings
│   │   └── tools/
│   │       └── hotel_tools.py    # Hotel booking tools
│   ├── data/                      # Hotel data storage
│   ├── transcripts/               # Call transcripts
│   ├── main.py                    # FastAPI server
│   └── test_mcp.py               # Test suite
└── frontend/
    └── src/
        └── components/
            └── VoiceCallInterface.tsx  # Voice call UI
```

## Setup

### Backend

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
NVIDIA_API_KEY=your_nvidia_api_key_here
```

3. Run the server:
```bash
./start.sh
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

## Available Hotel Rooms

- **R101** - Standard Single ($100/night) - 1 guest
- **R102** - Standard Double ($150/night) - 2 guests
- **R201** - Deluxe Suite ($250/night) - 2 guests
- **R202** - Family Suite ($350/night) - 4 guests
- **R301** - Presidential Suite ($500/night) - 4 guests

## Voice Commands Examples

- "I need a hotel room for 2 people from January 15 to January 17"
- "Show me available deluxe rooms"
- "Book room R201 for John Smith"
- "What's my booking status?"
- "Cancel my booking"

## API Endpoints

### Chat
- `POST /api/chat` - Send message to AI assistant
- `POST /api/transcript/save` - Save call transcript

### Hotel Booking Tools
- Search rooms by criteria
- Book a room
- Get booking details
- Cancel booking
- List all bookings

## Testing

Run the test suite:
```bash
cd backend
python test_mcp.py
```

## Technologies

- **Backend**: FastAPI, Python, NVIDIA API
- **Frontend**: React, TypeScript, Vite
- **AI**: OpenAI-compatible API via NVIDIA
- **Voice**: Web Speech API (Speech Recognition & Synthesis)

## License

MIT
