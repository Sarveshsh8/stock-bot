"""
Image Analysis Module
Handles image analysis using AWS Bedrock Nova Pro
"""

import boto3
import base64
import os
import json
import io
from typing import Dict, Any
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
    
    def _process_and_encode_image(self, image_path: str) -> str:
        """
        Process image with PIL and encode to base64 for better Nova Pro compatibility
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded processed image string
        """
        try:
            with Image.open(image_path) as img:
                self.logger.info(f"Processing image: {img.format}, {img.mode}, {img.size}")
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                max_size = 2048
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Save to bytes buffer in PNG format
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                image_bytes = buffer.getvalue()
                
                return base64.b64encode(image_bytes).decode('utf-8')
                
        except Exception as e:
            self.logger.warning(f"PIL processing failed: {str(e)}, using original file")
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            return base64.b64encode(image_bytes).decode('utf-8')
    
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
            
            # Process and encode image
            processed_image_b64 = self._process_and_encode_image(image_path)
            
            # Prepare request body
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "image": {
                                    "format": "png",
                                    "source": {"bytes": processed_image_b64}
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
            self.logger.info("Image analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in image analysis: {str(e)}")
            return self._fallback_image_analysis(image_path, prompt)
    
    def _fallback_image_analysis(self, image_path: str, prompt: str) -> str:
        """Fallback text-based image analysis when multimodal API fails"""
        try:
            file_name = os.path.basename(image_path)
            file_size = os.path.getsize(image_path) / 1024
            
            analysis_prompt = f"""You are a financial analyst examining image content about stock market and trading data.

Image Information:
- File: {file_name}
- Size: {file_size:.2f} KB

Based on the image filename and context, provide a comprehensive financial analysis covering:

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
            return f"Image analysis (text-based fallback): {result}"
            
        except Exception as e:
            return f"Error in fallback analysis: {str(e)}"