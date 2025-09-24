#!/usr/bin/env python3
"""
Standalone Audio Inference Module
Analyzes audio files using AWS Bedrock Nova Sonic for speech-to-text and Nova Pro for analysis
"""

import boto3
import base64
import os
import json
import sys
import asyncio
import uuid
import tempfile
import wave
import numpy as np
import pyaudio
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
from dotenv import load_dotenv

# Audio Analysis Prompt - Edit this to customize analysis
AUDIO_ANALYSIS_PROMPT = """Analyze this audio transcription from a financial perspective. Please provide:

1. **Content Summary:** What is the main topic and message of this audio?
2. **Financial Context:** How does this relate to stocks, markets, or investments?
3. **Key Insights:** What are the most important financial insights or recommendations?
4. **Market Analysis:** What does this suggest about current market conditions?
5. **Investment Implications:** What actionable insights can investors derive?
6. **Risk Assessment:** What risks or opportunities are highlighted?
7. **Speaker Analysis:** If there are speakers, what are their key points and credibility?
8. **Action Items:** What specific actions should investors consider?

Please be specific and provide actionable financial analysis."""

# AWS SDK v2 imports for Nova Sonic
try:
    from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
    from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
    from aws_sdk_bedrock_runtime.config import Config, HTTPAuthSchemeResolver, SigV4AuthScheme
    from smithy_aws_core.credentials_resolvers.environment import EnvironmentCredentialsResolver
    AWS_SDK_V2_AVAILABLE = True
except ImportError:
    AWS_SDK_V2_AVAILABLE = False

class AudioInference:
    """Standalone audio analysis using AWS Bedrock Nova Sonic and Nova Pro"""
    
    def __init__(self, region: str = "us-east-1", 
                 nova_sonic_model: str = "amazon.nova-sonic-v1:0",
                 nova_pro_model: str = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"):
        """
        Initialize the audio inference module
        
        Args:
            region: AWS region
            nova_sonic_model: Nova Sonic model ID for speech-to-text
            nova_pro_model: Nova Pro model ARN for text analysis
        """
        self.region = region
        self.nova_sonic_model = nova_sonic_model
        self.nova_pro_model = nova_pro_model
        self.max_tokens = 4000
        
        # Load environment variables
        load_dotenv()
        
        self._setup_logging()
        self._setup_bedrock_clients()
        self._setup_audio_config()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_bedrock_clients(self):
        """Setup Bedrock clients"""
        try:
            # Nova Pro client (boto3)
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            # Nova Sonic client (AWS SDK v2)
            if AWS_SDK_V2_AVAILABLE:
                try:
                    config = Config(region=self.region)
                    self.nova_sonic_client = BedrockRuntimeClient(config)
                except Exception as e:
                    self.logger.warning(f"AWS SDK v2 client creation failed: {e}")
                    self.nova_sonic_client = None
            else:
                self.nova_sonic_client = None
                self.logger.warning("AWS SDK v2 not available. Nova Sonic speech-to-text will not work.")
            
            self.logger.info(f"Bedrock clients initialized for region: {self.region}")
        except Exception as e:
            self.logger.error(f"Error setting up Bedrock clients: {str(e)}")
            raise
    
    def _setup_audio_config(self):
        """Setup audio configuration"""
        self.audio_config = {
            'input_sample_rate': 16000,
            'output_sample_rate': 24000,
            'channels': 1,
            'format': pyaudio.paInt16,
            'chunk_size': 1024
        }
        
        self.supported_formats = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma']
    
    def _convert_audio_format(self, input_path: str, output_path: str = None) -> str:
        """
        Convert audio to WAV format for Nova Sonic compatibility
        
        Args:
            input_path: Path to input audio file
            output_path: Path for output WAV file (optional)
            
        Returns:
            Path to converted WAV file
        """
        try:
            if output_path is None:
                output_path = tempfile.mktemp(suffix='.wav')
            
            # Use ffmpeg for conversion if available
            import subprocess
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-ar', str(self.audio_config['input_sample_rate']),
                '-ac', str(self.audio_config['channels']),
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Audio converted successfully: {output_path}")
                return output_path
            else:
                self.logger.warning(f"FFmpeg conversion failed: {result.stderr}")
                # Fallback: return original file if conversion fails
                return input_path
                
        except Exception as e:
            self.logger.warning(f"Audio conversion failed: {str(e)}")
            return input_path
    
    def _transcribe_audio_file(self, audio_path: str) -> str:
        """
        Transcribe audio file using Nova Sonic
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        if not AWS_SDK_V2_AVAILABLE or self.nova_sonic_client is None:
            return "Speech-to-text not available (AWS SDK v2 required)"
        
        try:
            # Convert audio to WAV if needed
            wav_path = self._convert_audio_format(audio_path)
            
            # Read audio file
            with open(wav_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Encode audio to base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare Nova Sonic request
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "audio": {
                                    "format": "wav",
                                    "source": {"bytes": audio_b64}
                                }
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 1000,
                    "temperature": 0.0,
                    "topP": 0.9
                }
            }
            
            # Create bidirectional stream input
            input_chunk = InvokeModelWithBidirectionalStreamInputChunk(
                body=json.dumps(request_body)
            )
            
            # Invoke Nova Sonic
            response = self.nova_sonic_client.invoke_model_with_bidirectional_stream(
                model_id=self.nova_sonic_model,
                input_stream=[input_chunk]
            )
            
            # Process response
            transcribed_text = ""
            for chunk in response.output_stream:
                if hasattr(chunk, 'chunk') and chunk.chunk:
                    chunk_data = json.loads(chunk.chunk.decode('utf-8'))
                    if 'event' in chunk_data and 'textOutput' in chunk_data['event']:
                        transcribed_text += chunk_data['event']['textOutput']['content']
            
            # Clean up temporary file
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)
            
            return transcribed_text.strip()
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {str(e)}")
            return f"Transcription error: {str(e)}"
    
    def analyze_audio(self, audio_path: str, prompt: str = None, 
                     temperature: float = 0.7, top_p: float = 0.9) -> Dict[str, str]:
        """
        Analyze audio file using Nova Sonic (speech-to-text) and Nova Pro (analysis)
        
        Args:
            audio_path: Path to the audio file
            prompt: Analysis prompt (optional, uses default financial analysis if not provided)
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Dictionary containing transcription and analysis results
        """
        try:
            print(f"Starting audio analysis for: {os.path.basename(audio_path)}")
            self.logger.info(f"Starting audio analysis for: {audio_path}")
            
            # Get file info
            file_size = os.path.getsize(audio_path) / (1024*1024)  # MB
            print(f"Audio Info: {os.path.basename(audio_path)}, Size: {file_size:.2f} MB")
            
            # Step 1: Transcribe audio using Nova Sonic
            print("Transcribing audio...")
            transcription = self._transcribe_audio_file(audio_path)
            
            if not transcription or "error" in transcription.lower():
                print(f"Transcription failed: {transcription}")
                return {
                    'transcription': transcription,
                    'analysis': 'Analysis skipped due to transcription failure',
                    'error': 'Transcription failed'
                }
            
            print(f"Transcription completed: {len(transcription)} characters")
            print(f"Transcription: {transcription[:200]}{'...' if len(transcription) > 200 else ''}")
            
            # Step 2: Analyze transcription using Nova Pro
            print("Analyzing transcription...")
            
            # Use default financial analysis prompt if none provided
            if prompt is None:
                prompt = AUDIO_ANALYSIS_PROMPT
            
            # Prepare analysis prompt
            analysis_prompt = f"""{prompt}

AUDIO TRANSCRIPTION:
===================
{transcription}

Please provide a comprehensive financial analysis based on the above audio transcription."""
            
            # Prepare request body for Nova Pro
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": analysis_prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": self.max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
            
            # Send request to Nova Pro
            print("Sending request to AWS Bedrock Nova Pro...")
            response = self.bedrock_runtime.invoke_model(
                modelId=self.nova_pro_model,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            analysis_result = response_body['output']['message']['content'][0]['text']
            
            print("Audio analysis completed successfully!")
            print("=" * 60)
            print("AUDIO ANALYSIS RESULT:")
            print("=" * 60)
            print(analysis_result)
            print("=" * 60)
            
            return {
                'transcription': transcription,
                'analysis': analysis_result,
                'file_info': {
                    'file_name': os.path.basename(audio_path),
                    'file_size_mb': file_size,
                    'transcription_length': len(transcription)
                }
            }
            
        except Exception as e:
            error_msg = f"Error in audio analysis: {str(e)}"
            print(f"Error: {error_msg}")
            self.logger.error(error_msg)
            return {
                'transcription': '',
                'analysis': '',
                'error': error_msg
            }
    
    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        Get basic information about an audio file
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary containing audio information
        """
        try:
            file_size = os.path.getsize(audio_path)
            file_name = os.path.basename(audio_path)
            file_ext = Path(audio_path).suffix.lower()
            
            return {
                'file_name': file_name,
                'file_size_mb': file_size / (1024*1024),
                'format': file_ext,
                'supported': file_ext in self.supported_formats,
                'nova_sonic_available': AWS_SDK_V2_AVAILABLE and self.nova_sonic_client is not None,
                'file_path': audio_path
            }
        except Exception as e:
            return {'error': str(e)}
    
    
    def validate_file(self, audio_path: str) -> tuple[bool, str]:
        """
        Validate if file is a supported audio format
        
        Args:
            audio_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(audio_path):
            return False, "File does not exist"
        
        file_ext = Path(audio_path).suffix.lower()
        
        if file_ext not in self.supported_formats:
            return False, f"Unsupported audio format: {file_ext}. Supported formats: {', '.join(self.supported_formats)}"
        
        return True, ""

if __name__ == "__main__":
    analyzer = AudioInference()
    path = "/Users/sarvesh/Desktop/freelance/Stock-Bot/stock-bot-deployment/data/audio.mp3"
    result = analyzer.analyze_audio(path)

    print(result)