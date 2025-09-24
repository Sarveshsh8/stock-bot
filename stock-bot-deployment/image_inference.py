#!/usr/bin/env python3
"""
Standalone Image Inference Module
Analyzes images using AWS Bedrock Nova Pro with financial analysis focus
"""

import boto3
import base64
import os
import json
import io
import sys
from typing import Dict, Any, Optional
import logging
from PIL import Image
from dotenv import load_dotenv

# Image Analysis Prompt - Edit this to customize analysis
IMAGE_ANALYSIS_PROMPT = """Analyze this image from a financial perspective. Please provide:

1. **Content Description:** What do you see in this image?
2. **Financial Context:** How does this relate to stocks, markets, or investments?
3. **Data Analysis:** If there are charts, graphs, or financial data, interpret them
4. **Market Implications:** What does this information suggest about market conditions?
5. **Investment Insights:** What actionable insights can be derived for investors?
6. **Risk Assessment:** What risks or opportunities are highlighted?

Please be specific and provide actionable financial analysis."""




class ImageInference:
    """Standalone image analysis using AWS Bedrock Nova Pro"""
    
    def __init__(self, region: str = "us-east-1", model_id: str = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"):
        """
        Initialize the image inference module
        
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
    
    def analyze_image(self, image_path: str, prompt: str = None, 
                     temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Analyze image using Nova Pro
        
        Args:
            image_path: Path to the image file
            prompt: Analysis prompt (optional, uses default financial analysis if not provided)
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Analysis result
        """
        try:
            self.logger.info(f"Starting image analysis for: {image_path}")
            
            # Use default financial analysis prompt if none provided
            if prompt is None:
                prompt = IMAGE_ANALYSIS_PROMPT
            
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
            return f"Error in image analysis: {str(e)}"
    


if __name__ == "__main__":
    analyzer = ImageInference()
    path = "/Users/sarvesh/Desktop/freelance/Stock-Bot/stock-bot-deployment/data/sample.jpg"
    result = analyzer.analyze_image(path)

    print(result)
