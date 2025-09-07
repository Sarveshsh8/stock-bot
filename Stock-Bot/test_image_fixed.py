import boto3
import os
import base64
import json
from typing import Optional
from dotenv import load_dotenv
from PIL import Image
import io

# Load environment variables from .env file
load_dotenv()

def process_image_with_nova_arn_fixed(
    image_path: str, 
    profile_arn: str, 
    prompt: str = "Analyze this image content",
    aws_profile: Optional[str] = None
) -> str:
    """
    Process image using AWS Bedrock Nova Pro with ARN profile - Fixed version
    Handles MIME type issues and image validation better
    
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
        
        # Validate and potentially fix image using PIL
        try:
            with Image.open(image_path) as img:
                print(f"Original image format: {img.format}")
                print(f"Original image mode: {img.mode}")
                print(f"Original image size: {img.size}")
                
                # Convert to RGB if necessary (Nova Pro works best with RGB)
                if img.mode != 'RGB':
                    print(f"Converting from {img.mode} to RGB")
                    img = img.convert('RGB')
                
                # Resize if too large (Nova Pro has limits)
                max_size = 2048
                if max(img.size) > max_size:
                    print(f"Resizing image from {img.size} to fit {max_size}px limit")
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Save to bytes buffer in PNG format for consistency
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                image_bytes = buffer.getvalue()
                
                print(f"Processed image bytes length: {len(image_bytes)}")
                print(f"Final image format: PNG")
                print(f"Final image size: {img.size}")
                
        except Exception as e:
            print(f"PIL processing failed: {str(e)}")
            # Fallback to original file
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
        
        # Encode to base64
        print("Encoding image to base64...")
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        print(f"Base64 string length: {len(image_b64)}")
        
        # Prepare the message content - use PNG format for consistency
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": "png",  # Always use PNG for consistency
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
        
        # Try using converse method first
        try:
            print("Trying converse method for image analysis...")
            response = bedrock.converse(
                modelId="amazon.nova-pro-v1:0",
                messages=messages,
                inferenceConfig=inference_config
            )
            
            # Extract response text
            result = response['output']['message']['content'][0]['text']
            print("Image analysis completed successfully with converse method")
            return result
            
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
                print("Image analysis completed successfully with invoke_model method")
                return result
                
            except Exception as e2:
                print(f"invoke_model also failed: {str(e2)}")
                return f"Both API methods failed. Image processing errors: {str(e)}, {str(e2)}"
        
    except FileNotFoundError:
        return f"Error: Image file not found: {image_path}"
    except Exception as e:
        return f"Error processing image: {str(e)}"

def validate_arn_format(arn: str) -> bool:
    """Validate ARN format"""
    return arn.startswith("arn:aws:bedrock:") and ("inference-profile" in arn or "model-access-policy" in arn)

# Test the fixed image processing
if __name__ == "__main__":
    # Configuration
    profile_arn = "arn:aws:bedrock:ap-southeast-2:295386645352:inference-profile/apac.amazon.nova-pro-v1:0"
    
    # Test with the new stock chart image
    image_file = "data/images/stock_chart.png"
    
    # Validate ARN format
    if not validate_arn_format(profile_arn):
        print("Invalid ARN format")
        exit(1)
    
    print("="*60)
    print("TESTING FIXED IMAGE PROCESSING")
    print("="*60)
    
    if os.path.exists(image_file):
        print(f"Testing with: {image_file}")
        image_result = process_image_with_nova_arn_fixed(
            image_file,
            profile_arn,
            "Analyze this financial chart image and describe what you see. Focus on trends, patterns, and any notable data points."
        )
        print(f"\nImage Analysis Result:")
        print("-" * 50)
        print(image_result)
    else:
        print(f"Image file not found: {image_file}")
        
        # Try with the fixed red square
        fallback_image = "data/images/test_red_square_fixed.png"
        if os.path.exists(fallback_image):
            print(f"Testing with fallback: {fallback_image}")
            image_result = process_image_with_nova_arn_fixed(
                fallback_image,
                profile_arn,
                "Describe this simple image."
            )
            print(f"\nImage Analysis Result:")
            print("-" * 50)
            print(image_result)
        else:
            print("No suitable test images found")
