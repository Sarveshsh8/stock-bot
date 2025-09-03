import os
import asyncio
import base64
import json
import uuid
import pyaudio
import wave
from dotenv import load_dotenv
import boto3

# Load environment variables
load_dotenv()

# Audio configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024

class SimpleNovaSonic:
    def __init__(self, model_id='amazon.nova-sonic-v1:0', region='us-east-1', profile_arn=None):
        self.model_id = model_id
        self.region = region
        self.profile_arn = profile_arn
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
        
    def _initialize_client(self):
        """Initialize the Bedrock client with ARN profile support."""
        try:
            # Use boto3 client with ARN profile if provided
            if self.profile_arn:
                print(f"Using ARN profile: {self.profile_arn}")
                # For ARN profiles, we'll use the standard boto3 client
                self.client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=self.region,
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
            else:
                # Fallback to environment credentials
                self.client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=self.region,
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
            print("Bedrock client initialized successfully")
        except Exception as e:
            print(f"Error initializing Bedrock client: {e}")
            raise
    
    async def send_event(self, event_json):
        """Send an event to the stream."""
        try:
            event = {
                "event": json.loads(event_json)
            }
            # For boto3 client, we'll use invoke_model_with_response_stream
            # This is a simplified approach for testing
            print(f"Sending event: {event}")
        except Exception as e:
            print(f"Error sending event: {e}")
    
    async def start_session(self):
        """Start a new session with Nova Sonic."""
        if not self.client:
            self._initialize_client()
            
        print("Starting Nova Sonic session...")
        self.is_active = True
        
        # Send session start event
        session_start = '''
        {
          "event": {
            "sessionStart": {
              "inferenceConfiguration": {
                "maxTokens": 1024,
                "topP": 0.9,
                "temperature": 0.7
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
                    "interactive": true,
                    "role": "SYSTEM",
                    "textInputConfiguration": {{
                        "mediaType": "text/plain"
                    }}
                }}
            }}
        }}
        '''
        await self.send_event(text_content_start)
        
        system_prompt = "You are a friendly financial assistant. The user and you will engage in a spoken dialog " \
            "exchanging the transcripts of a natural real-time conversation. Keep your responses short, " \
            "generally two or three sentences for chatty scenarios."

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
        
        print("Session started successfully")
    
    async def test_audio_file(self, audio_file_path):
        """Test audio file processing with Nova Sonic."""
        if not os.path.exists(audio_file_path):
            print(f"Audio file not found: {audio_file_path}")
            return
        
        print(f"Testing audio file: {audio_file_path}")
        
        # Read audio file
        try:
            with wave.open(audio_file_path, 'rb') as wav_file:
                # Get audio properties
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                print(f"Audio properties:")
                print(f"  Channels: {channels}")
                print(f"  Sample width: {sample_width} bytes")
                print(f"  Frame rate: {frame_rate} Hz")
                print(f"  Duration: {n_frames / frame_rate:.2f} seconds")
                
                # Read audio data
                audio_data = wav_file.readframes(n_frames)
                
                # Convert to base64 for testing
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                print(f"Audio data encoded to base64 (length: {len(audio_b64)})")
                
                # Simulate sending audio to Nova Sonic
                print("Simulating audio input to Nova Sonic...")
                
                # Start audio input
                await self.start_audio_input()
                
                # Send audio in chunks
                chunk_size = 1024
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    await self.send_audio_chunk(chunk)
                    await asyncio.sleep(0.1)  # Small delay between chunks
                
                # End audio input
                await self.end_audio_input()
                
                print("Audio file test completed")
                
        except Exception as e:
            print(f"Error processing audio file: {e}")
    
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
        print("Audio input started")
    
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
        print("Audio input ended")
    
    async def end_session(self):
        """End the session."""
        if not self.is_active:
            return
            
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
        
        self.is_active = False
        print("Session ended")

async def main():
    # Your ARN profile
    profile_arn = "arn:aws:bedrock:ap-southeast-2:295386645352:inference-profile/apac.amazon.nova-sonic-v1:0"
    
    # Create Nova Sonic client
    nova_client = SimpleNovaSonic(
        model_id='amazon.nova-sonic-v1:0',
        region='us-east-1',
        profile_arn=profile_arn
    )
    
    try:
        # Start session
        await nova_client.start_session()
        
        # Test with the audio file we created
        audio_file = "data/audio/test_tone.wav"
        await nova_client.test_audio_file(audio_file)
        
        # Wait a bit for processing
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        # End session
        await nova_client.end_session()
        print("Test completed")

if __name__ == "__main__":
    print("Testing Nova Sonic with ARN Profile")
    print("=" * 50)
    
    # Check if required packages are installed
    try:
        import pyaudio
        print("✓ PyAudio is available")
    except ImportError:
        print("✗ PyAudio not found. Install with: pip install pyaudio")
        exit(1)
    
    try:
        import boto3
        print("✓ Boto3 is available")
    except ImportError:
        print("✗ Boto3 not found. Install with: pip install boto3")
        exit(1)
    
    # Check environment variables
    if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("✓ AWS credentials found in environment")
    else:
        print("✗ AWS credentials not found. Check your .env file")
        exit(1)
    
    print("\nStarting Nova Sonic test...")
    asyncio.run(main())
