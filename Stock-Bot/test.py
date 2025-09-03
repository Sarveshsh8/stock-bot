import boto3
import os
import base64
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def process_video_with_nova_arn(
    video_path: str, 
    profile_arn: str, 
    prompt: str = "Analyze this video content",
    aws_profile: Optional[str] = None
) -> str:
    """
    Process video using AWS Bedrock Nova Pro with ARN profile
    
    Args:
        video_path: Path to the video file
        profile_arn: ARN of the model access policy
        prompt: Text prompt for video analysis
        aws_profile: Optional AWS profile name (instead of hardcoded keys)
    
    Returns:
        Analysis result or error message
    """
    
    try:
        # Initialize Bedrock client - use profile or credentials from .env
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            bedrock = session.client(
                service_name='bedrock-runtime',
                region_name='us-east-1'
            )
        else:
            # Use credentials from .env file
            bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        
        # Video file validation
        if not os.path.exists(video_path):
            return f"Error: Video file not found: {video_path}"
        
        file_size = os.path.getsize(video_path)
        video_name = os.path.basename(video_path)
        
        print(f"Processing video: {video_name}")
        print(f"File size: {file_size / (1024*1024):.2f} MB")
        print(f"Using profile ARN: {profile_arn}")
        
        # Check file size limit (25MB for Nova Pro)
        if file_size > 25 * 1024 * 1024:
            return f"Error: Video too large: {file_size / (1024*1024):.2f} MB (max 25MB)"
        
        # Read and encode video file
        print("Encoding video to base64...")
        with open(video_path, 'rb') as video_file:
            video_bytes = video_file.read()
            video_b64 = base64.b64encode(video_bytes).decode('utf-8')
        
        print(f"Video bytes length: {len(video_bytes)}")
        print(f"Base64 string length: {len(video_b64)}")
        print(f"Base64 starts with: {video_b64[:50]}...")
        
        # Determine video format from file extension
        file_ext = os.path.splitext(video_path)[1].lower()
        format_map = {
            '.mp4': 'mp4',
            '.mov': 'mov',
            '.avi': 'avi',
            '.webm': 'webm'
        }
        video_format = format_map.get(file_ext, 'mp4')
        
        print(f"Detected video format: {video_format}")
        print(f"File extension: {file_ext}")
        
        # Prepare the message content
        messages = [
        {
            "role": "user",
            "content": [
                {
                    "video": {
                        "format": video_format,  # Use the detected format
                        "source": {
                            "bytes": video_b64
                        }
                    }
                },
                {"text": prompt}
            ]
        }
    ]
        # Inference configuration
        inference_config = {
            "maxTokens": 1000,
            "temperature": 0.7,
            "topP": 0.9
        }
        
        print("Sending request to Bedrock Nova Pro...")
        
        # Try using invoke_model instead of converse for better video handling
        try:
            print("Trying invoke_model method...")
            response = bedrock.invoke_model(
                modelId="amazon.nova-pro-v1:0",
                body=json.dumps({
                    "messages": messages,
                    "inferenceConfig": inference_config
                }),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            result = response_body['output']['message']['content'][0]['text']
            
        except Exception as e:
            print(f"invoke_model failed: {str(e)}")
            print("Falling back to converse method...")
            
            # Fallback to converse method
            response = bedrock.converse(
                modelId="amazon.nova-pro-v1:0",
                messages=messages,
                inferenceConfig=inference_config
            )
            
            # Extract response text
            result = response['output']['message']['content'][0]['text']
        
        print("Analysis completed successfully")
        return result
        
    except FileNotFoundError:
        return f"Error: Video file not found: {video_path}"
    except Exception as e:
        return f"Error processing video: {str(e)}"

def process_image_with_nova_arn(
    image_path: str, 
    profile_arn: str, 
    prompt: str = "Analyze this image content",
    aws_profile: Optional[str] = None
) -> str:
    """
    Process image using AWS Bedrock Nova Pro with ARN profile
    
    Args:
        image_path: Path to the image file
        profile_arn: ARN of the model access policy
        prompt: Text prompt for image analysis
        aws_profile: Optional AWS profile name
    
    Returns:
        Analysis result or error message
    """
    
    try:
        # Initialize Bedrock client - use profile or credentials from .env
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            bedrock = session.client(
                service_name='bedrock-runtime',
                region_name='us-east-1'
            )
        else:
            # Use credentials from .env file
            bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        
        # Image file validation
        if not os.path.exists(image_path):
            return f"Error: Image file not found: {image_path}"
        
        file_size = os.path.getsize(image_path)
        image_name = os.path.basename(image_path)
        
        print(f"Processing image: {image_name}")
        print(f"File size: {file_size / 1024:.2f} KB")
        print(f"Using profile ARN: {profile_arn}")
        
        # Check file size limit (25MB for Nova Pro)
        if file_size > 25 * 1024 * 1024:
            return f"Error: Image too large: {file_size / (1024*1024):.2f} MB (max 25MB)"
        
        # Read and encode image file
        print("Encoding image to base64...")
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        print(f"Image bytes length: {len(image_bytes)}")
        print(f"Base64 string length: {len(image_b64)}")
        
        # Check if image is too small (likely corrupted or test file)
        if len(image_bytes) < 1000:  # Less than 1KB
            print(f"Warning: Image file is very small ({len(image_bytes)} bytes). This may cause MIME type issues.")
            print("Consider using a larger, standard image file.")
        
        # Determine image format from file extension and validate
        file_ext = os.path.splitext(image_path)[1].lower()
        format_map = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.tiff': 'tiff',
            '.tif': 'tiff',
            '.webp': 'webp'
        }
        image_format = format_map.get(file_ext, 'jpeg')
        
        print(f"Detected image format: {image_format}")
        print(f"File extension: {file_ext}")
        
        # Validate image format
        if image_format not in ['jpeg', 'png', 'gif', 'webp']:
            print(f"Warning: Format {image_format} may not be fully supported by Nova Pro")
        
        # Prepare the message content
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": image_format,
                            "source": {
                                "bytes": image_b64
                            }
                        }
                    },
                    {"text": prompt}
                ]
            }
        ]
        
        # Inference configuration
        inference_config = {
            "maxTokens": 1000,
            "temperature": 0.7,
            "topP": 0.9
        }
        
        print("Sending request to Bedrock Nova Pro...")
        
        # Try using converse method first (more reliable for images)
        try:
            print("Trying converse method for image analysis...")
            response = bedrock.converse(
                modelId="amazon.nova-pro-v1:0",
                messages=messages,
                inferenceConfig=inference_config
            )
            
            # Extract response text
            result = response['output']['message']['content'][0]['text']
            
        except Exception as e:
            print(f"converse method failed: {str(e)}")
            print("Falling back to invoke_model method...")
            
            # Fallback to invoke_model method
            try:
                print("Trying invoke_model method...")
                response = bedrock.invoke_model(
                    modelId="amazon.nova-pro-v1:0",
                    body=json.dumps({
                        "messages": messages,
                        "inferenceConfig": inference_config
                    }),
                    contentType="application/json"
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                result = response_body['output']['message']['content'][0]['text']
                
            except Exception as e2:
                print(f"invoke_model also failed: {str(e2)}")
                return f"Both API methods failed. Image may not be compatible with Nova Pro. Errors: {str(e)}, {str(e2)}"
        
        print("Image analysis completed successfully")
        return result
        
    except FileNotFoundError:
        return f"Error: Image file not found: {image_path}"
    except Exception as e:
        return f"Error processing image: {str(e)}"

def validate_arn_format(arn: str) -> bool:
    """Validate ARN format"""
    return arn.startswith("arn:aws:bedrock:") and ("inference-profile" in arn or "model-access-policy" in arn)

# Usage example
if __name__ == "__main__":
    # Configuration
    profile_arn = "arn:aws:bedrock:ap-southeast-2:295386645352:inference-profile/apac.amazon.nova-pro-v1:0"
    video_file = "data/videos/appleq1.mp4"
    
    # Validate ARN format
    if not validate_arn_format(profile_arn):
        print("Invalid ARN format")
        exit(1)
    
    # Process video
    if os.path.exists(video_file):
        result = process_video_with_nova_arn(
            video_file, 
            profile_arn,
            "Analyze this video and provide key insights about the content, actions, and any notable elements."
        )
        print(f"\nVideo Analysis Result:")
        print("-" * 50)
        print(result)
    else:
        print(f"Video file not found: {video_file}")
    
    # Test image processing
    print("\n" + "="*60)
    print("TESTING IMAGE PROCESSING")
    print("="*60)
    
    image_file = "data/images/test_red_square.png"
    
    if os.path.exists(image_file):
        image_result = process_image_with_nova_arn(
            image_file,
            profile_arn,
            "Analyze this image and describe what you see in detail."
        )
        print(f"\nImage Analysis Result:")
        print("-" * 50)
        print(image_result)
    else:
        print(f"Image file not found: {image_file}")
        
        # Try to find any available images
        import glob
        available_images = glob.glob("data/images/*") + glob.glob("data/*.png") + glob.glob("data/*.jpg")
        if available_images:
            print(f"Available images found: {available_images}")
            # Use the first available image
            first_image = available_images[0]
            print(f"Testing with: {first_image}")
            
            image_result = process_image_with_nova_arn(
                first_image,
                profile_arn,
                "Analyze this image and describe what you see in detail."
            )
            print(f"\nImage Analysis Result:")
            print("-" * 50)
            print(image_result)
        else:
            print("No image files found in data directory")
        