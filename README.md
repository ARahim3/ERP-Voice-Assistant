# Flask ERP with Voice Assistant

Integrated ERP system with voice interaction capabilities.

## Features
- Traditional ERP functionality (CRM, Inventory, Orders, HR, Finance)
- Voice assistant button (bottom-right corner)
- Real-time audio streaming via WebSockets
- Speech-to-text (Whisper) and text-to-speech (PlayAI) processing
- Automatic UI updates via SocketIO

## Getting Started
1. Clone the repository:
```bash
git clone https://github.com/your-username/flask-erp-voice.git
cd flask-erp-voice
```

2. Install system dependencies:
```bash
sudo apt install ffmpeg
```

3. Install Python packages:
```bash
pip install -r requirements.txt
```

4. Create .env file with your Groq API key:
```bash
echo "GROQ_API_KEY=your_api_key_here" > .env
```

## Running the Application
1. Start ERP server (Flask/SocketIO):
```bash
python ERP.py
```

2. Start Voice Agent (FastAPI/WebSockets):
```bash
python voice_stream.py
```

3. Access ERP frontend: http://localhost:5000


## Usage
1. Click the 🎤 button to start voice interaction
2. Speak naturally to interact with the ERP system (e.g., "Create a new customer")
3. Click again to stop recording
4. Voice responses will play automatically

## Architecture
```
Browser Frontend (Vue.js)
│
├── HTTP/WebSocket ──▶ ERP Server (Flask/SocketIO on port 5000)
│                       ├── CRM
│                       ├── Inventory
│                       ├── Orders
│                       ├── HR
│                       └── Finance
│
└── WebSocket ─────────▶ Voice Agent (FastAPI on port 7860)
                          ├── Audio Reception
                          ├── STT (Whisper)
                          ├── AI Processing
                          └── TTS (PlayAI)
```

## Key Dependencies
- Flask & Flask-SocketIO (ERP server)
- FastAPI & WebSockets (Voice agent)
- Groq SDK (Speech-to-text and text-to-speech)
- pydub & ffmpeg (Audio processing)
- pandas (Data management)
- Vue.js (Frontend framework)

## Configuration
- Voice model: `whisper-large-v3-turbo`
- TTS voice: `Celeste-PlayAI`
- Audio format: WebM (input), MP3 (output)