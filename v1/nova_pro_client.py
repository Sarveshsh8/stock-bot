import boto3
import json
import base64
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NovaProClient:
    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize the Nova Pro client for AWS Bedrock
        
        Args:
            region_name: AWS region where Bedrock is available
        """
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.model_id = "amazon.nova-pro-v1:0"
    
    def encode_image(self, image_path: str) -> str:
        """
        Encode an image file to base64 string
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def encode_video(self, video_path: str) -> str:
        """
        Encode a video file to base64 string
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Base64 encoded video string
        """
        with open(video_path, "rb") as video_file:
            return base64.b64encode(video_file.read()).decode('utf-8')
    
    def text_only_request(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Send a text-only request to Nova Pro
        
        Args:
            prompt: Text prompt to send
            max_tokens: Maximum tokens in response
            
        Returns:
            Model response text
        """
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        try:
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=body["messages"],
                inferenceConfig=body["inferenceConfig"]
            )
            
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def image_analysis_request(self, prompt: str, image_path: str, max_tokens: int = 1000) -> str:
        """
        Send an image analysis request to Nova Pro
        
        Args:
            prompt: Text prompt describing what to analyze
            image_path: Path to the image file
            max_tokens: Maximum tokens in response
            
        Returns:
            Model response text
        """
        # Determine image format from file extension
        image_format = image_path.lower().split('.')[-1]
        if image_format == 'jpg':
            image_format = 'jpeg'
        
        encoded_image = self.encode_image(image_path)
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        },
                        {
                            "image": {
                                "format": image_format,
                                "source": {
                                    "bytes": encoded_image
                                }
                            }
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        try:
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=body["messages"],
                inferenceConfig=body["inferenceConfig"]
            )
            
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def video_analysis_request(self, prompt: str, video_path: str, max_tokens: int = 1000) -> str:
        """
        Send a video analysis request to Nova Pro
        
        Args:
            prompt: Text prompt describing what to analyze
            video_path: Path to the video file (MP4)
            max_tokens: Maximum tokens in response
            
        Returns:
            Model response text
        """
        encoded_video = self.encode_video(video_path)
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        },
                        {
                            "video": {
                                "format": "mp4",
                                "source": {
                                    "bytes": encoded_video
                                }
                            }
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        try:
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=body["messages"],
                inferenceConfig=body["inferenceConfig"]
            )
            
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def multi_modal_request(self, prompt: str, image_path: Optional[str] = None, 
                           video_path: Optional[str] = None, max_tokens: int = 1000) -> str:
        """
        Send a multi-modal request (text + image and/or video)
        
        Args:
            prompt: Text prompt
            image_path: Optional path to image file
            video_path: Optional path to video file
            max_tokens: Maximum tokens in response
            
        Returns:
            Model response text
        """
        content = [{"text": prompt}]
        
        if image_path:
            image_format = image_path.lower().split('.')[-1]
            if image_format == 'jpg':
                image_format = 'jpeg'
            
            encoded_image = self.encode_image(image_path)
            content.append({
                "image": {
                    "format": image_format,
                    "source": {
                        "bytes": encoded_image
                    }
                }
            })
        
        if video_path:
            encoded_video = self.encode_video(video_path)
            content.append({
                "video": {
                    "format": "mp4",
                    "source": {
                        "bytes": encoded_video
                    }
                }
            })
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        try:
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=body["messages"],
                inferenceConfig=body["inferenceConfig"]
            )
            
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            return f"Error: {str(e)}"


def main():
    """
    Example usage of the Nova Pro client
    """
    # Initialize the client
    client = NovaProClient(region_name="us-east-1")
    
    # Example 1: Text-only request
    print("=== Text-only Example ===")
    text_response = client.text_only_request(
        prompt="Explain quantum computing in simple terms.",
        max_tokens=500
    )
    print(text_response)
    print("\n" + "="*50 + "\n")
    
    # Example 2: Image analysis (uncomment and provide actual image path)
    # print("=== Image Analysis Example ===")
    # image_response = client.image_analysis_request(
    #     prompt="Describe what you see in this image in detail.",
    #     image_path="path/to/your/image.jpg",
    #     max_tokens=500
    # )
    # print(image_response)
    # print("\n" + "="*50 + "\n")
    
    # Example 3: Video analysis (uncomment and provide actual video path)
    # print("=== Video Analysis Example ===")
    # video_response = client.video_analysis_request(
    #     prompt="Analyze the content of this video and summarize what happens.",
    #     video_path="path/to/your/video.mp4",
    #     max_tokens=500
    # )
    # print(video_response)
    # print("\n" + "="*50 + "\n")
    
    # Example 4: Multi-modal request (uncomment and provide actual file paths)
    # print("=== Multi-modal Example ===")
    # multimodal_response = client.multi_modal_request(
    #     prompt="Compare and contrast the content in this image and video.",
    #     image_path="path/to/your/image.jpg",
    #     video_path="path/to/your/video.mp4",
    #     max_tokens=750
    # )
    # print(multimodal_response)


# Configuration helper function
def setup_aws_credentials():
    """
    Helper function to remind about AWS credential setup
    """
    print("""
    Before running this script, ensure you have AWS credentials configured:
    
    Option 1 - AWS CLI:
    aws configure
    
    Option 2 - Environment variables:
    export AWS_ACCESS_KEY_ID=your_access_key
    export AWS_SECRET_ACCESS_KEY=your_secret_key
    export AWS_DEFAULT_REGION=us-east-1
    
    Option 3 - IAM Role (if running on EC2/Lambda)
    
    Required IAM permissions:
    - bedrock:InvokeModel
    - bedrock:InvokeModelWithResponseStream (if using streaming)
    """)


if __name__ == "__main__":
    # Uncomment the line below if you need credential setup guidance
    # setup_aws_credentials()
    
    main()
