"""
Image Analysis Module
Handles image analysis using AWS Bedrock Nova Pro
"""

import boto3
import base64
import os
from typing import Optional, Dict, Any
import logging
from PIL import Image

class ImageAnalyzer:
    """Handles image analysis using AWS Bedrock Nova Pro"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the image analyzer
        
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
    
    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            with open(image_path, "rb") as file:
                return base64.b64encode(file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error encoding image {image_path}: {str(e)}")
    
    def get_image_format(self, image_path: str) -> str:
        """Get the format of an image based on extension"""
        ext = os.path.splitext(image_path)[1].lower()
        
        format_mapping = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.tiff': 'tiff',
            '.tif': 'tiff',
            '.webp': 'webp',
            '.svg': 'svg'
        }
        
        return format_mapping.get(ext, ext.lstrip('.'))
    
    def get_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """Get image metadata"""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'size_bytes': os.path.getsize(image_path)
                }
        except Exception as e:
            self.logger.error(f"Error getting image metadata: {str(e)}")
            return {}
    
    def analyze_image(self, image_path: str, prompt: str, 
                     temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Analyze image using Nova Pro
        
        Args:
            image_path: Path to the image file
            prompt: Analysis prompt
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Analysis result
        """
        try:
            self.logger.info(f"Starting image analysis for: {image_path}")
            
            # Get image metadata
            metadata = self.get_image_metadata(image_path)
            self.logger.info(f"Image metadata: {metadata}")
            
            # Encode image
            encoded_image = self.encode_image(image_path)
            image_format = self.get_image_format(image_path)
            
            # Prepare request body
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "image": {
                                    "format": image_format,
                                    "source": {"bytes": encoded_image}
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
            self.logger.info("Image analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in image analysis: {str(e)}")
            return f"Error analyzing image: {str(e)}"
    
    def analyze_financial_chart(self, image_path: str, stock_symbol: str = None) -> str:
        """
        Analyze financial chart image
        
        Args:
            image_path: Path to chart image
            stock_symbol: Stock symbol for context
            
        Returns:
            Chart analysis result
        """
        prompt = f"""Analyze this financial chart comprehensively:

1. **Chart Analysis:**
   - Chart type and timeframe
   - Price trends and patterns
   - Volume analysis
   - Technical indicators visible

2. **Technical Analysis:**
   - Support and resistance levels
   - Moving averages
   - Chart patterns (head & shoulders, triangles, etc.)
   - Momentum indicators

3. **Trading Signals:**
   - Buy/sell opportunities
   - Entry and exit points
   - Risk management levels

4. **Market Context:**
   - Current market conditions
   - Sector performance
   - News impact

5. **Recommendations:**
   - Short-term trading strategy
   - Long-term outlook
   - Risk considerations

{f'Focus on {stock_symbol} if visible in the chart.' if stock_symbol else ''}

Provide specific data points and actionable insights."""

        return self.analyze_image(image_path, prompt)
    
    def analyze_general_image(self, image_path: str, context: str = "") -> str:
        """
        Analyze general image content
        
        Args:
            image_path: Path to image
            context: Additional context for analysis
            
        Returns:
            Image analysis result
        """
        prompt = f"""Analyze this image comprehensively:

1. **Visual Content:**
   - What you see in the image
   - Key elements and objects
   - Visual composition and style

2. **Context Analysis:**
   - Business or financial relevance
   - Market implications
   - Strategic significance

3. **Key Insights:**
   - Important findings
   - Trends or patterns
   - Comparative analysis

4. **Recommendations:**
   - Actionable insights
   - Next steps
   - Areas for further analysis

{context if context else ''}

Provide detailed analysis with specific observations."""
