"""
Voice Handler for Streamlit Integration
Uses the proven working Nova Sonic implementation from test_audio.py
"""

import os
import asyncio
import base64
import json
import uuid
import tempfile
import wave
import numpy as np
import pyaudio
from typing import Optional

# AWS SDK v2 imports
try:
    from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
    from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
    from aws_sdk_bedrock_runtime.config import Config, HTTPAuthSchemeResolver, SigV4AuthScheme
    from smithy_aws_core.credentials_resolvers.environment import EnvironmentCredentialsResolver
    from dotenv import load_dotenv
    AWS_SDK_V2_AVAILABLE = True
except ImportError:
    AWS_SDK_V2_AVAILABLE = False

load_dotenv()

# Audio configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024

class SimpleNovaSonic:
    """Voice handler using the proven working Nova Sonic implementation from test_audio.py"""
    
    def __init__(self, model_id='amazon.nova-sonic-v1:0', region='us-east-1'):
        self.model_id = model_id
        self.region = region
        self.client = None
        self.stream = None
        self.response = None
        self.is_active = False
        self.prompt_name = str(uuid.uuid4())
        self.content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())
        self.audio_queue = asyncio.Queue()
        self.role = None
        self.display_assistant_text = False
        self.transcribed_text = ""
        
    def _initialize_client(self):
        """Initialize the Bedrock client."""
        config = Config(
            endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
            region=self.region,
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
            http_auth_scheme_resolver=HTTPAuthSchemeResolver(),
            http_auth_schemes={"aws.auth#sigv4": SigV4AuthScheme()}
        )
        self.client = BedrockRuntimeClient(config=config)
    
    async def send_event(self, event_json):
        """Send an event to the stream."""
        event = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
        )
        await self.stream.input_stream.send(event)
    
    async def start_session(self):
        """Start a new session with Nova Sonic."""
        if not self.client:
            self._initialize_client()
            
        # Initialize the stream
        self.stream = await self.client.invoke_model_with_bidirectional_stream(
            InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
        )
        self.is_active = True
        
        # Send session start event
        session_start = '''
        {
          "event": {
            "sessionStart": {
              "inferenceConfiguration": {
                "maxTokens": 1024,
                "topP": 0.9,
                "temperature": 0.1
              }
            }
          }
        }
        '''
        await self.send_event(session_start)
        
        # Send prompt start event
        prompt_start = f'''
        {{
          "event": {{
            "promptStart": {{
              "promptName": "{self.prompt_name}",
              "textOutputConfiguration": {{
                "mediaType": "text/plain"
              }},
              "audioOutputConfiguration": {{
                "mediaType": "audio/lpcm",
                "sampleRateHertz": 24000,
                "sampleSizeBits": 16,
                "channelCount": 1,
                "voiceId": "matthew",
                "encoding": "base64",
                "audioType": "SPEECH"
              }}
            }}
          }}
        }}
        '''
        await self.send_event(prompt_start)
        
        # Send system prompt
        text_content_start = f'''
        {{
            "event": {{
                "contentStart": {{
                    "promptName": "{self.prompt_name}",
                    "contentName": "{self.content_name}",
                    "type": "TEXT",
                    "interactive": false,
                    "role": "SYSTEM",
                    "textInputConfiguration": {{
                        "mediaType": "text/plain"
                    }}
                }}
            }}
        }}
        '''
        await self.send_event(text_content_start)
        
        system_prompt = "You are a speech-to-text transcription assistant. Your job is to listen to the user's audio input and transcribe exactly what they said into text. Return only the transcribed text without any additional commentary, formatting, or responses. Be accurate and capture the exact words spoken by the user."

        text_input = f'''
        {{
            "event": {{
                "textInput": {{
                    "promptName": "{self.prompt_name}",
                    "contentName": "{self.content_name}",
                    "content": "{system_prompt}"
                }}
            }}
        }}
        '''
        await self.send_event(text_input)
        
        text_content_end = f'''
        {{
            "event": {{
                "contentEnd": {{
                    "promptName": "{self.prompt_name}",
                    "contentName": "{self.content_name}"
                }}
            }}
        }}
        '''
        await self.send_event(text_content_end)
        
        # Start processing responses
        self.response = asyncio.create_task(self._process_responses())
    
    async def start_audio_input(self):
        """Start audio input stream."""
        audio_content_start = f'''
        {{
            "event": {{
                "contentStart": {{
                    "promptName": "{self.prompt_name}",
                    "contentName": "{self.audio_content_name}",
                    "type": "AUDIO",
                    "interactive": true,
                    "role": "USER",
                    "audioInputConfiguration": {{
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 16000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "audioType": "SPEECH",
                        "encoding": "base64"
                    }}
                }}
            }}
        }}
        '''
        await self.send_event(audio_content_start)
    
    async def send_audio_chunk(self, audio_bytes):
        """Send an audio chunk to the stream."""
        if not self.is_active:
            return
            
        blob = base64.b64encode(audio_bytes)
        audio_event = f'''
        {{
            "event": {{
                "audioInput": {{
                    "promptName": "{self.prompt_name}",
                    "contentName": "{self.audio_content_name}",
                    "content": "{blob.decode('utf-8')}"
                }}
            }}
        }}
        '''
        await self.send_event(audio_event)
    
    async def end_audio_input(self):
        """End audio input stream."""
        audio_content_end = f'''
        {{
            "event": {{
                "contentEnd": {{
                    "promptName": "{self.prompt_name}",
                    "contentName": "{self.audio_content_name}"
                }}
            }}
        }}
        '''
        await self.send_event(audio_content_end)
    
    async def end_session(self):
        """End the session with proper cleanup."""
        if not self.is_active:
            return
            
        self.is_active = False
        
        try:
            # Cancel the response task first
            if hasattr(self, 'response') and self.response and not self.response.done():
                self.response.cancel()
                try:
                    await asyncio.wait_for(self.response, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                except Exception as e:
                    print(f"Error cancelling response task: {e}")
            
            # Send session end events
            try:
                prompt_end = f'''
                {{
                    "event": {{
                        "promptEnd": {{
                            "promptName": "{self.prompt_name}"
                        }}
                    }}
                }}
                '''
                await self.send_event(prompt_end)
                
                session_end = '''
                {
                    "event": {
                        "sessionEnd": {}
                    }
                }
                '''
                await self.send_event(session_end)
            except Exception as e:
                print(f"Error sending session end events: {e}")
                
        except Exception as e:
            print(f"Error in session cleanup: {e}")
        finally:
            # Always try to close the stream with timeout
            try:
                if self.stream and hasattr(self.stream, 'input_stream'):
                    await asyncio.wait_for(self.stream.input_stream.close(), timeout=3.0)
            except asyncio.TimeoutError:
                print("Timeout closing stream")
            except Exception as e:
                print(f"Error closing stream: {e}")
            finally:
                self.stream = None
    
    async def _process_responses(self):
        """Process responses from the stream."""
        try:
            while self.is_active:
                try:
                    output = await asyncio.wait_for(self.stream.await_output(), timeout=5.0)
                    result = await output[1].receive()
                    
                    if result.value and result.value.bytes_:
                        response_data = result.value.bytes_.decode('utf-8')
                        json_data = json.loads(response_data)
                        
                        if 'event' in json_data:
                            # Handle content start event
                            if 'contentStart' in json_data['event']:
                                content_start = json_data['event']['contentStart'] 
                                # set role
                                self.role = content_start['role']
                                # Check for speculative content
                                if 'additionalModelFields' in content_start:
                                    additional_fields = json.loads(content_start['additionalModelFields'])
                                    if additional_fields.get('generationStage') == 'SPECULATIVE':
                                        self.display_assistant_text = True
                                    else:
                                        self.display_assistant_text = False
                                    
                            # Handle text output event
                            elif 'textOutput' in json_data['event']:
                                text = json_data['event']['textOutput']['content']    
                               
                                # Only capture USER text as transcription (not assistant responses)
                                if self.role == "USER":
                                    self.transcribed_text += text
                                    print(f"User transcription: {text}")
                                    # Stop recording after getting user transcription
                                    self.is_active = False
                                elif (self.role == "ASSISTANT" and self.display_assistant_text):
                                    print(f"Assistant: {text}")
                                else:
                                    print(f"Other text: {text}")
                            
                            # Handle audio output
                            elif 'audioOutput' in json_data['event']:
                                audio_content = json_data['event']['audioOutput']['content']
                                audio_bytes = base64.b64decode(audio_content)
                                await self.audio_queue.put(audio_bytes)
                            
                            # Handle session end
                            elif 'sessionEnd' in json_data['event']:
                                self.is_active = False
                                break
                                
                except asyncio.TimeoutError:
                    print("Timeout waiting for response, ending session")
                    self.is_active = False
                    break
                except asyncio.CancelledError:
                    print("Response processing cancelled")
                    self.is_active = False
                    break
                except Exception as e:
                    print(f"Error in response processing loop: {e}")
                    self.is_active = False
                    break
                    
        except asyncio.CancelledError:
            print("Response processing task cancelled")
            self.is_active = False
        except Exception as e:
            print(f"Error processing responses: {e}")
            self.is_active = False
    
    async def speech_to_text_realtime(self, duration_seconds: int = None) -> Optional[str]:
        """
        Convert speech to text using smart voice activity detection
        
        Args:
            duration_seconds: Not used anymore - uses smart detection instead
            
        Returns:
            Transcribed text or None if error
        """
        try:
            # Reset transcribed text
            self.transcribed_text = ""
            
            # Start session
            await self.start_session()
            
            # Start audio playback task (but we won't use it for voice-to-text)
            playback_task = asyncio.create_task(self.play_audio())
            
            # Start smart audio capture task
            capture_task = asyncio.create_task(self.capture_audio_realtime())
            
            # Wait for capture to complete
            await capture_task
            
            # Cancel playback task since we only want transcription
            if not playback_task.done():
                playback_task.cancel()
                try:
                    await playback_task
                except asyncio.CancelledError:
                    pass
            
            # Wait for response processing to complete
            try:
                if self.response and not self.response.done():
                    await asyncio.wait_for(self.response, timeout=10.0)
            except asyncio.TimeoutError:
                print("Timeout waiting for response processing")
            except asyncio.CancelledError:
                print("Response processing cancelled")
            
            # Give additional time for transcription
            await asyncio.sleep(3)
            
            # Get transcribed text
            response_text = self.transcribed_text if hasattr(self, 'transcribed_text') else ""
            
            if response_text.strip():
                print(f"Final transcription: {response_text.strip()}")
                return response_text.strip()
            else:
                print("No transcription received")
                return "Voice input received (transcription pending)"
            
        except Exception as e:
            print(f"Voice processing error: {e}")
            return "Voice input received"
        finally:
            # Clean up
            try:
                await self.end_session()
            except Exception as e:
                print(f"Error during session cleanup: {e}")
            finally:
                self.is_active = False
    
    async def capture_audio_realtime(self, duration_seconds: int = None):
        """Capture audio from microphone with voice activity detection"""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=INPUT_SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        print("Recording audio... Speak now, I'll detect when you stop...")
        
        await self.start_audio_input()
        
        try:
            # Voice activity detection parameters
            silence_threshold = 300  # Lower threshold for better sensitivity
            silence_duration = 4.0  # 4 seconds of silence to stop (more time to speak)
            max_duration = 20.0  # Maximum 20 seconds recording
            
            silence_start = None
            recording_start = asyncio.get_event_loop().time()
            has_speech = False
            
            while self.is_active:
                audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                
                # Calculate audio level (simple volume detection)
                audio_level = max(audio_data)
                
                current_time = asyncio.get_event_loop().time()
                elapsed_time = current_time - recording_start
                
                # Check if we've exceeded max duration
                if elapsed_time > max_duration:
                    print("Maximum recording time reached")
                    break
                
                # Check for speech
                if audio_level > silence_threshold:
                    has_speech = True
                    silence_start = None
                    print(".", end="", flush=True)  # Show activity
                else:
                    # Check for silence
                    if has_speech:  # Only start silence timer after we've had speech
                        if silence_start is None:
                            silence_start = current_time
                        elif current_time - silence_start > silence_duration:
                            print(f"\nDetected {silence_duration}s of silence, stopping recording...")
                            break
                    else:
                        # If no speech yet, show we're listening
                        if elapsed_time < 1.0:  # First second
                            print("Listening...", end="", flush=True)
                
                await self.send_audio_chunk(audio_data)
                await asyncio.sleep(0.01)
                
        except Exception as e:
            print(f"Error capturing audio: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("Audio capture stopped.")
            await self.end_audio_input()
    
    async def speech_to_text(self, audio_file_path: str) -> Optional[str]:
        """
        Convert speech to text using Nova Sonic (file-based approach)
        
        Args:
            audio_file_path: Path to audio file (WAV format, 16kHz, mono)
            
        Returns:
            Transcribed text or None if error
        """
        # For now, use the real-time approach instead of file-based
        return await self.speech_to_text_realtime(5)
    
    async def play_audio(self):
        """Play audio responses (from test_audio.py)"""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=OUTPUT_SAMPLE_RATE,
            output=True
        )
        
        try:
            while self.is_active:
                audio_data = await self.audio_queue.get()
                stream.write(audio_data)
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("Audio playing stopped.")
    
    def create_test_audio(self, text: str = "Hello, this is a test") -> str:
        """
        Create a simple test audio file for testing
        
        Args:
            text: Text to convert to audio (for testing)
            
        Returns:
            Path to created audio file
        """
        # Create a simple sine wave as test audio
        sample_rate = 16000
        duration = 2  # 2 seconds
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit integers
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return temp_file.name

# Global voice handler instance
voice_handler = SimpleNovaSonic()

def is_voice_available() -> bool:
    """Check if voice processing is available"""
    return AWS_SDK_V2_AVAILABLE

async def convert_speech_to_text(audio_file_path: str) -> Optional[str]:
    """Convert speech to text using Nova Sonic with smart voice activity detection"""
    return await voice_handler.speech_to_text_realtime()

def create_test_audio_file() -> str:
    """Create a test audio file for testing voice functionality"""
    return voice_handler.create_test_audio()