"""
Simple Voice Q&A System
Records audio, converts to text, retrieves context, and answers questions
"""

import os
import asyncio
import base64
import json
import uuid
import pyaudio
import tempfile
import wave
import numpy as np
from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
from aws_sdk_bedrock_runtime.config import Config, HTTPAuthSchemeResolver, SigV4AuthScheme
from smithy_aws_core.credentials_resolvers.environment import EnvironmentCredentialsResolver
from dotenv import load_dotenv

load_dotenv()

# Audio configuration
INPUT_SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024
RECORD_SECONDS = 5  # Record for 5 seconds

class SimpleVoiceQA:
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
        
        # Send system prompt for speech-to-text
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
        
        system_prompt = "You are a speech-to-text assistant. Convert the user's speech to text accurately. Only return the transcribed text, nothing else."

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
    
    async def _process_responses(self):
        """Process responses from the stream."""
        try:
            while self.is_active:
                try:
                    output = await asyncio.wait_for(self.stream.await_output(), timeout=30.0)
                    result = await output[1].receive()
                    
                    if result.value and result.value.bytes_:
                        response_data = result.value.bytes_.decode('utf-8')
                        json_data = json.loads(response_data)
                        
                        if 'event' in json_data:
                            # Handle content start event
                            if 'contentStart' in json_data['event']:
                                content_start = json_data['event']['contentStart'] 
                                self.role = content_start['role']
                                if 'additionalModelFields' in content_start:
                                    additional_fields = json.loads(content_start['additionalModelFields'])
                                    if additional_fields.get('generationStage') == 'SPECULATIVE':
                                        self.display_assistant_text = True
                                    else:
                                        self.display_assistant_text = False
                                    
                            # Handle text output event
                            elif 'textOutput' in json_data['event']:
                                text = json_data['event']['textOutput']['content']    
                               
                                if (self.role == "ASSISTANT" and self.display_assistant_text):
                                    self.transcribed_text += text
                                elif self.role == "USER":
                                    self.transcribed_text += text
                            
                            # Handle session end
                            elif 'sessionEnd' in json_data['event']:
                                self.is_active = False
                                break
                                
                except asyncio.TimeoutError:
                    print("Timeout waiting for response, ending session")
                    self.is_active = False
                    break
                except Exception as e:
                    print(f"Error in response processing loop: {e}")
                    self.is_active = False
                    break
                    
        except Exception as e:
            print(f"Error processing responses: {e}")
            self.is_active = False
    
    async def record_audio(self):
        """Record audio from microphone."""
        print("🎤 Recording audio... Speak now!")
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=INPUT_SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        frames = []
        for i in range(0, int(INPUT_SAMPLE_RATE / CHUNK_SIZE * RECORD_SECONDS)):
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("✅ Recording complete!")
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(INPUT_SAMPLE_RATE)
            wf.writeframes(b''.join(frames))
        
        return temp_file.name
    
    async def speech_to_text(self, audio_file_path):
        """Convert speech to text using Nova Sonic."""
        try:
            # Start session
            await self.start_session()
            
            # Start audio input
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
            
            # Read and send audio file
            with open(audio_file_path, 'rb') as f:
                audio_bytes = f.read()
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
            
            # End audio input
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
            
            # Wait for transcription
            if self.response:
                try:
                    await asyncio.wait_for(self.response, timeout=30.0)
                except asyncio.TimeoutError:
                    print("Timeout waiting for transcription")
                    self.response.cancel()
            
            return self.transcribed_text.strip()
            
        except Exception as e:
            print(f"Speech-to-text error: {e}")
            return None
        finally:
            # Clean up
            try:
                if self.stream and self.is_active:
                    await self.end_session()
            except Exception as e:
                print(f"Error during session cleanup: {e}")
            finally:
                self.is_active = False
                if hasattr(self, 'response') and self.response and not self.response.done():
                    try:
                        self.response.cancel()
                    except:
                        pass
    
    async def end_session(self):
        """End the session."""
        if not self.is_active:
            return
            
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
        finally:
            try:
                if self.stream and hasattr(self.stream, 'input_stream'):
                    await self.stream.input_stream.close()
            except Exception as e:
                print(f"Error closing stream: {e}")
            self.is_active = False

async def simple_voice_qa():
    """Simple voice Q&A workflow."""
    print("🚀 Starting Simple Voice Q&A System")
    print("=" * 50)
    
    # Initialize voice QA system
    voice_qa = SimpleVoiceQA()
    
    try:
        # Step 1: Record audio
        audio_file = await voice_qa.record_audio()
        print(f"📁 Audio saved to: {audio_file}")
        
        # Step 2: Convert speech to text
        print("🔄 Converting speech to text...")
        transcribed_text = await voice_qa.speech_to_text(audio_file)
        
        if transcribed_text:
            print(f"📝 Transcribed text: '{transcribed_text}'")
            
            # Step 3: Here you would integrate with your QA system
            # For now, we'll just show the question
            print("\n🤖 Question Analysis:")
            print(f"Question: {transcribed_text}")
            print("✅ Ready to process with your QA system!")
            
            # TODO: Integrate with your existing QA system here
            # answer = await your_qa_system.answer_question(transcribed_text)
            # print(f"Answer: {answer}")
            
        else:
            print("❌ Could not transcribe audio")
        
        # Clean up
        os.unlink(audio_file)
        print("🧹 Cleaned up temporary files")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n✅ Voice Q&A session complete!")

if __name__ == "__main__":
    asyncio.run(simple_voice_qa())
