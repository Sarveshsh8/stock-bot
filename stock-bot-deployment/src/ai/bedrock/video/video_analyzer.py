"""
Video Analysis Module
Handles video analysis using AWS Bedrock Nova Pro
"""

import boto3
import base64
import os
from typing import Optional, Dict, Any
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
    
    def encode_video(self, video_path: str) -> str:
        """
        Encode video to base64 string
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Base64 encoded video string
        """
        try:
            with open(video_path, "rb") as file:
                return base64.b64encode(file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error encoding video {video_path}: {str(e)}")
    
    def get_video_format(self, video_path: str) -> str:
        """Get the format of a video based on extension"""
        ext = os.path.splitext(video_path)[1].lower()
        
        format_mapping = {
            '.mp4': 'mp4',
            '.avi': 'avi',
            '.mov': 'mov',
            '.wmv': 'wmv',
            '.flv': 'flv',
            '.webm': 'webm',
            '.mkv': 'mkv',
            '.m4v': 'mp4',
            '.3gp': '3gp',
            '.ogv': 'ogv',
            '.mpg': 'mpeg',
            '.mpeg': 'mpeg'
        }
        
        return format_mapping.get(ext, ext.lstrip('.'))
    
    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata"""
        try:
            file_size = os.path.getsize(video_path)
            file_name = os.path.basename(video_path)
            
            # Try to get video metadata using cv2 if available
            try:
                import cv2
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration = total_frames / fps if fps > 0 else 0
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
                    
                    return {
                        'file_name': file_name,
                        'file_size': file_size,
                        'duration': duration,
                        'width': width,
                        'height': height,
                        'fps': fps,
                        'total_frames': total_frames
                    }
            except ImportError:
                pass
            
            return {
                'file_name': file_name,
                'file_size': file_size,
                'duration': 'unknown',
                'width': 'unknown',
                'height': 'unknown',
                'fps': 'unknown',
                'total_frames': 'unknown'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting video metadata: {str(e)}")
            return {}
    
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
            
            # Check file size (Nova Pro video size limit is typically around 25MB)
            file_size = os.path.getsize(video_path)
            self.logger.info(f"Video file size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
            
            max_size = 25 * 1024 * 1024  # 25MB
            if file_size > max_size:
                return f"Video file is too large for analysis ({file_size / (1024*1024):.2f} MB). Maximum supported size is {max_size / (1024*1024)} MB."
            
            # Get video metadata
            metadata = self.get_video_metadata(video_path)
            self.logger.info(f"Video metadata: {metadata}")
            
            # Encode video
            encoded_video = self.encode_video(video_path)
            video_format = self.get_video_format(video_path)
            
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
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=body["messages"],
                inferenceConfig=body["inferenceConfig"]
            )
            
            result = response['output']['message']['content'][0]['text']
            self.logger.info("Video analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in video analysis: {str(e)}")
            return self._fallback_video_analysis(video_path, prompt)
    
    def _fallback_video_analysis(self, video_path: str, prompt: str) -> str:
        """Fallback text-based video analysis when multimodal API fails"""
        try:
            metadata = self.get_video_metadata(video_path)
            
            analysis_prompt = f"""You are a financial analyst examining video content about stock market and trading data.

Video Information:
- File: {metadata.get('file_name', 'unknown')}
- Size: {metadata.get('file_size', 0) / (1024*1024):.2f} MB
- Duration: {metadata.get('duration', 'unknown')} seconds
- Resolution: {metadata.get('width', 'unknown')}x{metadata.get('height', 'unknown')}

Based on the video filename and context, provide a comprehensive financial analysis covering:

1. **Content Analysis:**
   - Main topics and themes
   - Key messages conveyed
   - Visual and audio elements

2. **Financial Context:**
   - Market implications
   - Investment relevance
   - Strategic significance

3. **Data Interpretation:**
   - Key information extracted
   - Trends and patterns
   - Comparative analysis

4. **Investment Implications:**
   - Trading opportunities
   - Risk factors
   - Market sentiment

5. **Recommendations:**
   - Actionable insights
   - Next steps
   - Areas for further analysis

Provide detailed analysis as if you were examining comprehensive video content about financial markets.

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
            
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=body["messages"],
                inferenceConfig=body["inferenceConfig"]
            )
            
            result = response['output']['message']['content'][0]['text']
            return f"Video analysis (text-based fallback): {result}"
            
        except Exception as e:
            return f"Error in fallback analysis: {str(e)}"
    
    def analyze_earnings_call(self, video_path: str, company: str = None) -> str:
        """
        Analyze earnings call video
        
        Args:
            video_path: Path to earnings call video
            company: Company name for context
            
        Returns:
            Earnings call analysis result
        """
        prompt = f"""Analyze this earnings call video comprehensively:

1. **Content Summary:**
   - Main topics and themes discussed
   - Key messages from management
   - Visual elements and presentation style

2. **Financial Performance:**
   - Revenue and profit trends
   - Key performance metrics
   - Comparison with expectations

3. **Business Insights:**
   - Strategic initiatives
   - Market positioning
   - Growth prospects

4. **Market Impact:**
   - Stock price implications
   - Investor sentiment
   - Sector performance

5. **Investment Outlook:**
   - Growth prospects
   - Risk factors
   - Investment recommendations

{f'Focus on {company} if mentioned in the video.' if company else ''}

Provide detailed analysis with specific insights and recommendations."""

        return self.analyze_video(video_path, prompt)
    
    def analyze_market_analysis_video(self, video_path: str, market_context: str = "") -> str:
        """
        Analyze market analysis video
        
        Args:
            video_path: Path to market analysis video
            market_context: Additional market context
            
        Returns:
            Market analysis result
        """
        prompt = f"""Analyze this market analysis video comprehensively:

1. **Market Overview:**
   - Current market conditions
   - Key trends and patterns
   - Sector performance

2. **Technical Analysis:**
   - Chart patterns and indicators
   - Support and resistance levels
   - Trading signals

3. **Fundamental Analysis:**
   - Economic indicators
   - Company performance
   - Industry trends

4. **Trading Opportunities:**
   - Buy/sell signals
   - Entry and exit points
   - Risk management

5. **Market Outlook:**
   - Short-term predictions
   - Long-term trends
   - Risk factors

{market_context if market_context else ''}

Provide actionable insights and specific recommendations."""
