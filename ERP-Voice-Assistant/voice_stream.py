import asyncio
import numpy as np
from groq import Groq
from loguru import logger
from fastapi import FastAPI, WebSocket
import uvicorn
import io
from pydub import AudioSegment
from agent_setup import agent, agent_config
import os

logger.remove()
logger.add(
    lambda msg: print(msg),
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
)

groq_client = Groq()

# Remove FastRTC-related code since we're using custom WebSocket endpoint

if __name__ == "__main__":
    import concurrent.futures
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI()
    
    # Add CORS middleware
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=["http://localhost:5000"],
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5000")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    
    # Create thread pool executor for concurrency
    executor = concurrent.futures.ThreadPoolExecutor()
    
    # Define audio processing function
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
            navigation_keywords = [
                "create new", "new customer", "new product", "new invoice",
                "navigate to", "go to", "open", "switch to"
            ]
            is_navigation = any(keyword in transcript.lower() for keyword in navigation_keywords)
            
            return response_text, is_navigation
                
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return "Sorry, I encountered an error processing your request.", False
    
    @app.websocket("/")
    async def websocket_endpoint(websocket: WebSocket):
        from starlette.websockets import WebSocketState
        # Validate origin before accepting connection
        origin = websocket.headers.get("origin")
        logger.info(f"Incoming WebSocket connection from origin: {origin}")
        
        # Allow any localhost origin for development
        if not (origin and ("localhost" in origin or "127.0.0.1" in origin)):
            logger.warning(f"Rejecting connection from unauthorized origin: {origin}")
            await websocket.close(code=1008)  # Policy violation
            return
            
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        try:
            while True:
                # Check connection state before receiving
                from starlette.websockets import WebSocketState
                if websocket.client_state == WebSocketState.DISCONNECTED:
                    logger.info("Client disconnected, stopping audio processing")
                    break
                    
                try:
                    # Receive WebM audio from frontend
                    logger.info("🎧 Waiting for audio input...")
                    message = await websocket.receive_bytes()
                    logger.info(f"📥 Received audio data: {len(message)} bytes")
                except asyncio.CancelledError:
                    logger.info("Audio reception cancelled")
                    break
                except Exception as e:
                    # Handle specific "bytes" error
                    if "bytes" in str(e).lower():
                        logger.info("Connection closed during audio reception")
                        break
                    # Handle other disconnection errors
                    elif "1001" in str(e) or "going away" in str(e):
                        logger.info("Client disconnected during audio reception")
                        break
                    else:
                        logger.error(f"Error receiving audio: {e}")
                        break
                
                # Process audio in separate thread
                logger.info("⚙️ Starting audio processing...")
                # Process audio and get response text + navigation flag
                # Process audio and get response text + navigation flag
                response_text, is_navigation = await asyncio.get_event_loop().run_in_executor(
                    executor,
                    lambda: process_audio(message)
                )
                logger.info(f"⚙️ Audio processing complete, got response text")
                
                # Generate TTS audio
                logger.info("🔊 Generating TTS audio...")
                tts_response = groq_client.audio.speech.create(
                    model="playai-tts",
                    voice="Celeste-PlayAI",
                    response_format="mp3",
                    input=response_text,
                )
                
                # Read all content from the streaming response
                mp3_data = b""
                for chunk in tts_response.iter_bytes():
                    mp3_data += chunk
                logger.info(f"🎵 Generated TTS audio: {len(mp3_data)} bytes")
                
                # Calculate audio duration
                audio = AudioSegment.from_file(io.BytesIO(mp3_data), format="mp3")
                duration_seconds = len(audio) / 1000.0
                
                # Send audio data to client
                logger.info(f"📤 Sending audio response ({len(mp3_data)} bytes)")
                await websocket.send_bytes(mp3_data)
                logger.info("✅ Audio response sent successfully")
                
                # Send navigation flag after audio with delay
                if is_navigation:
                    # Wait for audio to play before sending navigation
                    logger.info(f"⏳ Waiting {duration_seconds:.1f}s before navigation")
                    await asyncio.sleep(duration_seconds + 0.5)
                    logger.info("🚀 Sending navigation flag")
                    await websocket.send_text("NAVIGATE_NOW")
                    logger.info("✅ Navigation flag sent")
        except asyncio.CancelledError:
            logger.info("WebSocket connection cancelled")
        except asyncio.CancelledError:
            logger.info("WebSocket connection cancelled")
        except Exception as e:
            # Handle disconnection errors more gracefully
            if "1001" in str(e) or "going away" in str(e):
                logger.info("Client disconnected normally")
            else:
                logger.error(f"WebSocket connection error: {e}")
        finally:
            # Correct way to check WebSocket state
            from starlette.websockets import WebSocketState
            if websocket.client_state != WebSocketState.DISCONNECTED:
                try:
                    await websocket.close()
                    logger.info("🔌 WebSocket connection closed")
                except Exception:
                    pass  # Ignore errors during closing
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    uvicorn.run(app, host="0.0.0.0", port=7861)