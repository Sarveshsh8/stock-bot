"""
Video Analysis Module
Handles video analysis using AWS Bedrock Nova Pro
"""

import boto3
import base64
import os
import json
from typing import Dict, Any
import logging

class VideoAnalyzer:
    """Handles video analysis using AWS Bedrock Nova Pro"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the video analyzer
        
        Args:
            config: Configuration dictionary containing Bedrock settings
        """
        self.config = config
        self.region = config['bedrock_settings']['region']
        self.model_id = config['bedrock_settings']['nova_pro_arn']
        self.max_tokens = config['bedrock_settings']['max_tokens']
        
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
                region_name=self.region
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
    
    def analyze_video(self, video_path: str, prompt: str, 
                     temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Analyze video using Nova Pro
        
        Args:
            video_path: Path to the video file
            prompt: Analysis prompt
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Analysis result
        """
        try:
            self.logger.info(f"Starting video analysis for: {video_path}")
            
            # Check file size (25MB limit for Nova Pro)
            file_size = os.path.getsize(video_path)
            if file_size > 25 * 1024 * 1024:
                return f"Video file is too large ({file_size / (1024*1024):.2f} MB). Maximum supported size is 25 MB."
            
            # Encode video
            with open(video_path, "rb") as file:
                encoded_video = base64.b64encode(file.read()).decode('utf-8')
            
            video_format = self._get_video_format(video_path)
            
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
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            result = response_body['output']['message']['content'][0]['text']
            self.logger.info("Video analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in video analysis: {str(e)}")
            return self._fallback_video_analysis(video_path, prompt)
    
    def _fallback_video_analysis(self, video_path: str, prompt: str) -> str:
        """Fallback text-based video analysis when multimodal API fails"""
        try:
            file_name = os.path.basename(video_path)
            file_size = os.path.getsize(video_path) / (1024*1024)
            
            analysis_prompt = f"""You are a financial analyst examining video content about stock market and trading data.

Video Information:
- File: {file_name}
- Size: {file_size:.2f} MB

Based on the video filename and context, provide a comprehensive financial analysis covering:

1. **Content Analysis:** Main topics and themes
2. **Financial Context:** Market implications and investment relevance
3. **Data Interpretation:** Key information and trends
4. **Investment Implications:** Trading opportunities and risk factors
5. **Recommendations:** Actionable insights and next steps

Additional Context: {prompt}"""

            # Use text-only analysis
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": analysis_prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": self.max_tokens,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            result = response_body['output']['message']['content'][0]['text']
            return f"Video analysis (text-based fallback): {result}"
            
        except Exception as e:
            return f"Error in fallback analysis: {str(e)}"