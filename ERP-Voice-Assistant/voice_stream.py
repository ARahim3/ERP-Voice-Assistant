import asyncio
import io
import os
import concurrent.futures

import numpy as np
from groq import Groq
from loguru import logger
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydub import AudioSegment
from agent_setup import agent, agent_config

# --- Logger Setup ---
logger.remove()
logger.add(
    lambda msg: print(msg),
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
)

# --- Client and App Initialization (Moved to Global Scope) ---
groq_client = Groq()
app = FastAPI()

# --- Middleware Configuration (Moved to Global Scope) ---
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Thread Pool and Processing Function (Global Scope) ---
executor = concurrent.futures.ThreadPoolExecutor()

def process_audio(webm_data: bytes) -> tuple:
    """Process WebM audio and return (response_text, is_navigation)"""
    try:
        # Convert WebM to WAV
        webm_audio = AudioSegment.from_file(io.BytesIO(webm_data), format="webm")
        wav_audio = webm_audio.set_frame_rate(16000).set_channels(1)
        wav_buffer = io.BytesIO()
        wav_audio.export(wav_buffer, format="wav")
        
        # Transcribe audio
        logger.info("🎙️ Processing audio input")
        transcript = groq_client.audio.transcriptions.create(
            file=("audio-file.wav", wav_buffer.getvalue()),
            model="whisper-large-v3-turbo",
            response_format="text",
        )
        logger.info(f'👂 Transcribed: "{transcript}"')
        
        # Run agent
        agent_response = agent.invoke(
            {"messages": [{"role": "user", "content": transcript}]}, config=agent_config
        )
        response_text = agent_response["messages"][-1].content
        logger.info(f'💬 Response: "{response_text}"')
        
        # Check for navigation keywords
        # navigation_keywords = [
        #     "create new", "new customer", "new product", "new invoice",
        #     "navigate to", "go to", "open", "switch to", "add new", "create"
        # ]
        # is_navigation = any(keyword in transcript.lower() for keyword in navigation_keywords)
        
        return response_text, transcript
            
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        return "Sorry, I encountered an error processing your request.", False

# --- API Routes (Global Scope) ---
@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    from starlette.websockets import WebSocketState
    origin = websocket.headers.get("origin")
    logger.info(f"Incoming WebSocket connection from origin: {origin}")
    
    if not (origin and (FRONTEND_URL in origin or "localhost" in origin or "127.0.0.1" in origin)):
        logger.warning(f"Rejecting connection from unauthorized origin: {origin}")
        await websocket.close(code=1008)
        return
        
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    try:
        while True:
            if websocket.client_state == WebSocketState.DISCONNECTED:
                logger.info("Client disconnected, stopping audio processing")
                break
                
            try:
                message = await websocket.receive_bytes()
                logger.info(f"📥 Received audio data: {len(message)} bytes")
            except Exception as e:
                if "1001" in str(e) or "going away" in str(e):
                    logger.info("Client disconnected during audio reception")
                    break
                else:
                    logger.error(f"Error receiving audio: {e}")
                    break
            
            # This function call doesn't change
            response_text, transcript = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: process_audio(message)
            )
            
            # ---- NEW CHANGE 1: Send the transcription to the frontend ----
            if transcript:
                logger.info("-=> Sending transcription to client")
                await websocket.send_json({"type": "transcription", "data": transcript})
            
            # ---- NEW CHANGE 2: Send the agent's text response to the frontend ----
            if response_text:
                logger.info("-=> Sending agent response to client")
                await websocket.send_json({"type": "agent_response", "data": response_text})

            # This part remains the same
            logger.info("🔊 Generating TTS audio...")
            tts_response = groq_client.audio.speech.create(
                model="playai-tts", voice="Celeste-PlayAI", response_format="mp3", input=response_text
            )
            
            mp3_data = b"".join(tts_response.iter_bytes())
            logger.info(f"🎵 Generated TTS audio: {len(mp3_data)} bytes")
            
            await websocket.send_bytes(mp3_data)
            logger.info("✅ Audio response sent successfully")
            
            # if is_navigation:
            #     audio = AudioSegment.from_file(io.BytesIO(mp3_data), format="mp3")
            #     duration_seconds = len(audio) / 1000.0
            #     await asyncio.sleep(duration_seconds + 0.5)
            #     logger.info("🚀 Sending navigation flag")
            #     await websocket.send_text("NAVIGATE_NOW")
            #     logger.info("✅ Navigation flag sent")
                
    except Exception as e:
        if "1001" in str(e) or "going away" in str(e):
            logger.info("Client disconnected normally")
        else:
            logger.error(f"WebSocket connection error: {e}")
    finally:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
            logger.info("🔌 WebSocket connection closed")

@app.get("/health")
async def health_check():
    return {"status": "ok"}


# --- Main Block for Local Development ONLY ---
if __name__ == "__main__":
    print(f"Starting local dev server. Accepting connections from {FRONTEND_URL}")
    uvicorn.run(app, host="0.0.0.0", port=7861)