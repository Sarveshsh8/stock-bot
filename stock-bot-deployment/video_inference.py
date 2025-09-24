#!/usr/bin/env python3
"""
Standalone Video Inference Module
Analyzes videos using AWS Bedrock Nova Pro with financial analysis focus
"""

import boto3
import base64
import os
import json
import sys
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Video Analysis Prompt - Edit this to customize analysis
VIDEO_ANALYSIS_PROMPT = """Analyze this video from a financial perspective. Please provide:

1. **Content Summary:** What is the main content and message of this video?
2. **Financial Context:** How does this relate to stocks, markets, or investments?
3. **Key Insights:** What are the most important financial insights or data points?
4. **Market Analysis:** What does this suggest about current market conditions?
5. **Investment Implications:** What actionable insights can investors derive from this data?
6. **Risk Assessment:** What risks or opportunities are highlighted in the data?
7. **Speaker Analysis:** If there are speakers, what are their key points and credibility?

Please be specific and provide actionable financial analysis with concrete examples from the data."""

class VideoInference:
    """Standalone video analysis using AWS Bedrock Nova Pro"""
    
    def __init__(self, region: str = "us-east-1", model_id: str = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"):
        """
        Initialize the video inference module
        
        Args:
            region: AWS region
            model_id: Bedrock model ARN
        """
        self.region = region
        self.model_id = model_id
        self.max_tokens = 4000
        
        # Load environment variables
        load_dotenv()
        
        self._setup_logging()
        self._setup_bedrock_client()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_bedrock_client(self):
        """Setup Bedrock client"""
        try:
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.logger.info(f"Bedrock client initialized for region: {self.region}")
        except Exception as e:
            self.logger.error(f"Error setting up Bedrock client: {str(e)}")
            raise
    
    def _get_video_format(self, video_path: str) -> str:
        """Get the format of a video based on extension"""
        ext = os.path.splitext(video_path)[1].lower()
        format_mapping = {
            '.mp4': 'mp4', '.avi': 'avi', '.mov': 'mov', '.wmv': 'wmv',
            '.flv': 'flv', '.webm': 'webm', '.mkv': 'mkv', '.m4v': 'mp4',
            '.3gp': '3gp', '.ogv': 'ogv', '.mpg': 'mpeg', '.mpeg': 'mpeg'
        }
        return format_mapping.get(ext, 'mp4')
    
    def analyze_video(self, video_path: str, prompt: str = None, 
                     temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Analyze video using Nova Pro
        
        Args:
            video_path: Path to the video file
            prompt: Analysis prompt (optional, uses default financial analysis if not provided)
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Analysis result
        """
        try:
            print(f"Starting video analysis for: {os.path.basename(video_path)}")
            self.logger.info(f"Starting video analysis for: {video_path}")
            
            # Check file size (500MB limit for Nova Pro)
            file_size = os.path.getsize(video_path)
            print(f"Video Info: {os.path.basename(video_path)}, Size: {file_size / (1024*1024):.2f} MB")
            
            if file_size > 500 * 1024 * 1024:
                error_msg = f"Video file is too large ({file_size / (1024*1024):.2f} MB). Maximum supported size is 500 MB."
                print(f"Error: {error_msg}")
                return error_msg
            
            # Use default financial analysis prompt if none provided
            if prompt is None:
                prompt = VIDEO_ANALYSIS_PROMPT
            
            # Encode video
            print("Encoding video for analysis...")
            with open(video_path, "rb") as file:
                encoded_video = base64.b64encode(file.read()).decode('utf-8')
            
            video_format = self._get_video_format(video_path)
            print(f"Video encoded successfully ({len(encoded_video):,} characters, Format: {video_format})")
            
            # Prepare request body
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "video": {
                                    "format": video_format,
                                    "source": {"bytes": encoded_video}
                                }
                            },
                            {"text": prompt}
                        ]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": self.max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
            
            # Send request to Bedrock
            print("Sending request to AWS Bedrock Nova Pro...")
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            result = response_body['output']['message']['content'][0]['text']
            
            print("Video analysis completed successfully!")
            print("=" * 60)
            print("VIDEO ANALYSIS RESULT:")
            print("=" * 60)
            print(result)
            print("=" * 60)
            
            self.logger.info("Video analysis completed successfully")
            return result
            
        except Exception as e:
            print(f"Error in video analysis: {str(e)}")
            self.logger.error(f"Error in video analysis: {str(e)}")
            return f"Error in video analysis: {str(e)}"
    
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get basic information about a video file
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing video information
        """
        try:
            file_size = os.path.getsize(video_path)
            file_name = os.path.basename(video_path)
            video_format = self._get_video_format(video_path)
            
            return {
                'file_name': file_name,
                'file_size_mb': file_size / (1024*1024),
                'format': video_format,
                'supported': file_size <= 500 * 1024 * 1024,  # 500MB limit
                'file_path': video_path
            }
        except Exception as e:
            return {'error': str(e)}

if __name__ == "__main__":
    analyzer = VideoInference()
    path = "/Users/sarvesh/Desktop/freelance/Stock-Bot/stock-bot-deployment/data/video.mp4"
    result = analyzer.analyze_video(path)

    print(result)