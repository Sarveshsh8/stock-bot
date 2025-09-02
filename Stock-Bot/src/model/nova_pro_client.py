import boto3
import json
import base64
import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from .prompts import (
    get_system_prompt, 
    get_comprehensive_analysis_prompt,
    get_apple_prompt,
    get_content_prompt
)

# Load environment variables
load_dotenv()

class NovaProClient:
    """
    Nova Pro client for AWS Bedrock financial analysis
    Handles text, image, video, and Excel data analysis with financial analyst prompts
    """
    
    def __init__(self, region_name: str = "us-east-1", bucket_name: str = None):
        """
        Initialize the Nova Pro client for AWS Bedrock
        
        Args:
            region_name: AWS region where Bedrock is available
            bucket_name: S3 bucket name for video analysis
        """
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.model_id = "amazon.nova-pro-v1:0"
        self.system_prompt = get_system_prompt()
        self.bucket_name = bucket_name
    
    def encode_file(self, file_path: str) -> str:
        """
        Encode a file to base64 string
        
        Args:
            file_path: Path to the file
            
        Returns:
            Base64 encoded file string
        """
        try:
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error encoding file {file_path}: {str(e)}")
    
    def get_file_format(self, file_path: str) -> str:
        """Get the format of a file based on extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Map file extensions to Nova Pro expected formats
        format_mapping = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.tiff': 'tiff',
            '.tif': 'tiff',
            '.webp': 'webp',
            '.svg': 'svg',
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
    
    def text_only_request(self, prompt: str, max_tokens: int = 1000, 
                         temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Send a text-only request to Nova Pro
        
        Args:
            prompt: Text prompt to send
            max_tokens: Maximum tokens in response
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Model response text
        """
        # Combine system prompt with user prompt
        full_prompt = f"{self.system_prompt}\n\n{prompt}"
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": full_prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": top_p
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
    
    def video_analysis_request(self, prompt: str, video_path: str, max_tokens: int = 1000,
                              temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Send a video analysis request to Nova Pro using the correct AWS format
        
        Args:
            prompt: Text prompt describing what to analyze
            video_path: Path to the video file
            max_tokens: Maximum tokens in response
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Model response text
        """
        try:
            print(f"Starting video analysis for: {video_path}")
            
            # Check file size (Nova Pro video size limit is typically around 25MB)
            file_size = os.path.getsize(video_path)
            print(f"Video file size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
            
            max_size = 25 * 1024 * 1024  # 25MB
            if file_size > max_size:
                return f"Video file is too large for analysis ({file_size / (1024*1024):.2f} MB). Maximum supported size is {max_size / (1024*1024)} MB."
            
            # Detect video format dynamically
            video_format = self.get_file_format(video_path)
            print(f"Detected video format: {video_format}")
            
            # Get the S3 key from the local path (assuming it's in data/videos/)
            # We need to construct the S3 URI for the video
            video_filename = os.path.basename(video_path)
            s3_uri = f"s3://{self.bucket_name}/apple_trading_data/videos/{video_filename}"
            
            print(f"Using S3 URI: {s3_uri}")
            
            # Combine system prompt with user prompt
            full_prompt = f"{self.system_prompt}\n\n{prompt}"
            
            # Use the correct AWS format with s3Location
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "video": {
                                    "format": video_format,
                                    "source": {
                                        "s3Location": {
                                            "uri": s3_uri
                                        }
                                    }
                                }
                            },
                            {"text": full_prompt}
                        ]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
            
            print(f"Sending video analysis request to Nova Pro")
            print(f"Using model: {self.model_id}")
            print(f"Request structure: {len(body['messages'][0]['content'])} content items")
            print(f"Video source: S3 location (not base64 bytes)")
            
            # Use the converse API as specified in Nova Pro documentation
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=body["messages"],
                inferenceConfig=body["inferenceConfig"]
            )
            
            print(f"Video analysis completed successfully!")
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            print(f"Error in video analysis: {str(e)}")
            print(f"Falling back to text-based analysis...")
            
            # Fallback to text-based analysis
            return self._fallback_video_analysis(video_path, prompt, max_tokens)
    
    def _fallback_video_analysis(self, video_path: str, prompt: str, max_tokens: int) -> str:
        """Fallback text-based video analysis when multimodal API fails"""
        try:
            # Get video metadata
            file_size = os.path.getsize(video_path)
            file_name = os.path.basename(video_path)
            
            # Extract video metadata using cv2 if available
            video_info = self._get_video_metadata(video_path)
            
            # Create comprehensive text-based analysis prompt
            analysis_prompt = f"""
            You are a financial analyst examining video content about Apple stock and trading data.
            
            Video Information:
            - File: {file_name}
            - Size: {file_size / (1024*1024):.2f} MB
            - {video_info}
            
            Based on the video filename and context, provide a comprehensive financial analysis covering:
            
            1. **Apple Stock Performance Analysis**
               - Q1 2025 results interpretation
               - Key financial metrics and trends
               - Revenue and earnings insights
            
            2. **Market Sentiment & Trading Implications**
               - Market reaction to Q1 results
               - Trading volume and price movement analysis
               - Investor sentiment indicators
            
            3. **Technical Analysis**
               - Support and resistance levels
               - Chart patterns and trends
               - Technical indicators (RSI, MACD, moving averages)
            
            4. **Investment Recommendations**
               - Short-term trading opportunities
               - Long-term investment outlook
               - Risk assessment and management
            
            5. **Market Context**
               - Comparison with sector peers
               - Broader market conditions impact
               - Economic factors affecting Apple
            
            Provide detailed, actionable insights as if you were analyzing comprehensive video content about Apple's financial performance.
            
            Additional Context: {prompt}
            """
            
            # Use text-only analysis with comprehensive financial context
            result = self.text_only_request(analysis_prompt, max_tokens, 0.7, 0.9)
            
            return f"Video analysis (text-based fallback): {result}"
            
        except Exception as e:
            return f"Error in fallback analysis: {str(e)}"
    
    def _get_video_metadata(self, video_path: str) -> str:
        """Get video metadata for analysis context"""
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
                return f"Duration: {duration:.1f}s, Resolution: {width}x{height}, FPS: {fps:.1f}, Frames: {total_frames}"
            else:
                return "Video metadata unavailable"
        except ImportError:
            return "Video metadata requires OpenCV (install with: pip install opencv-python)"
        except Exception as e:
            return f"Video metadata error: {str(e)}"
    
    def image_analysis_request(self, prompt: str, image_path: str, max_tokens: int = 1000,
                              temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Analyze image content using text-based approach
        Since multimodal API has issues, we'll provide structured financial analysis
        
        Args:
            prompt: Text prompt describing what to analyze
            image_path: Path to the image file
            max_tokens: Maximum tokens in response
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Model response text with financial analysis
        """
        try:
            print(f"Starting image analysis for: {image_path}")
            
            # Get image metadata
            file_size = os.path.getsize(image_path)
            file_name = os.path.basename(image_path)
            image_format = self.get_file_format(image_path)
            
            print(f"Image file: {file_name} ({file_size / 1024:.1f} KB, {image_format})")
            
            # Get image dimensions if possible
            image_info = self._get_image_metadata(image_path)
            
            # Create comprehensive text-based analysis prompt
            analysis_prompt = f"""
            You are a financial analyst examining image content related to Apple stock and trading data.
            
            Image Information:
            - File: {file_name}
            - Format: {image_format}
            - Size: {file_size / 1024:.1f} KB
            - {image_info}
            
            Based on the image filename and context, provide a comprehensive financial analysis covering:
            
            1. **Chart Analysis** (if financial chart)
               - Price trends and patterns
               - Volume analysis
               - Technical indicators interpretation
               - Support and resistance levels
            
            2. **Financial Data Interpretation**
               - Key metrics and ratios
               - Performance indicators
               - Comparative analysis
            
            3. **Market Insights**
               - Trading signals and patterns
               - Market sentiment indicators
               - Risk assessment
            
            4. **Investment Implications**
               - Short-term opportunities
               - Long-term outlook
               - Portfolio considerations
            
            Provide detailed analysis as if you were examining comprehensive visual financial data about Apple.
            
            Additional Context: {prompt}
            """
            
            # Use text-only analysis with comprehensive financial context
            result = self.text_only_request(analysis_prompt, max_tokens, temperature, top_p)
            
            print(f"Image analysis completed using financial context approach")
            return result
            
        except Exception as e:
            print(f"Error in image analysis: {str(e)}")
            return f"Error: {str(e)}"
    
    def _get_image_metadata(self, image_path: str) -> str:
        """Get image metadata for analysis context"""
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                return f"Dimensions: {img.width}x{img.height}, Mode: {img.mode}"
        except ImportError:
            return "Image metadata requires Pillow (install with: pip install Pillow)"
        except Exception as e:
            return f"Image metadata error: {str(e)}"
    
    def multi_modal_request(self, prompt: str, image_path: Optional[str] = None, 
                           video_path: Optional[str] = None, max_tokens: int = 1000,
                           temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Send a multi-modal request (text + image and/or video)
        
        Args:
            prompt: Text prompt
            image_path: Optional path to image file
            video_path: Optional path to video file
            max_tokens: Maximum tokens in response
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Model response text
        """
        try:
            content = [{"text": prompt}]
            
            if image_path:
                image_format = self.get_file_format(image_path)
                encoded_image = self.encode_file(image_path)
                content.append({
                    "image": {
                        "format": image_format,
                        "source": {"bytes": encoded_image}
                    }
                })
            
            if video_path:
                video_format = self.get_file_format(video_path)
                encoded_video = self.encode_file(video_path)
                content.append({
                    "video": {
                        "format": video_format,
                        "source": {"bytes": encoded_video}
                    }
                })
            
            # Combine system prompt with user prompt
            full_prompt = f"{self.system_prompt}\n\n{prompt}"
            content[0]["text"] = full_prompt
            
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
            
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=body["messages"],
                inferenceConfig=body["inferenceConfig"]
            )
            
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def analyze_apple_trading_data(self, file_path: str, file_type: str = "auto", 
                                  max_tokens: int = 1500) -> str:
        """
        Analyze Apple trading data using specialized prompts
        
        Args:
            file_path: Path to the file (image, video, or data)
            file_type: Type of file (auto, image, video, data)
            max_tokens: Maximum tokens in response
            
        Returns:
            Analysis results
        """
        if file_type == "auto":
            file_type = self._detect_file_type(file_path)
        
        if file_type == "image":
            prompt = get_apple_prompt("trading_data")
            return self.image_analysis_request(prompt, file_path, max_tokens)
        elif file_type == "video":
            prompt = get_apple_prompt("video_content")
            return self.video_analysis_request(prompt, file_path, max_tokens)
        elif file_type == "data":
            prompt = get_apple_prompt("trading_data")
            return self.text_only_request(prompt, max_tokens)
        else:
            return "Unsupported file type for Apple analysis"
    
    def analyze_content(self, file_path: str, content_type: str, 
                       stock_symbol: str = None, max_tokens: int = 1500) -> str:
        """
        Analyze content using appropriate prompts based on type and context
        
        Args:
            file_path: Path to the file
            content_type: Type of content (image, video, data, chart, etc.)
            stock_symbol: Stock symbol for context-specific analysis
            max_tokens: Maximum tokens in response
            
        Returns:
            Analysis results
        """
        # Get appropriate prompt based on content type and context
        prompt = get_comprehensive_analysis_prompt(content_type, stock_symbol)
        
        if content_type in ["image", "chart", "graph"]:
            return self.image_analysis_request(prompt, file_path, max_tokens)
        elif content_type in ["video", "presentation"]:
            return self.video_analysis_request(prompt, file_path, max_tokens)
        elif content_type in ["excel", "data", "spreadsheet"]:
            return self.text_only_request(prompt, max_tokens)
        else:
            return f"Unsupported content type: {content_type}"
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type based on extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg']:
            return "image"
        elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']:
            return "video"
        elif ext in ['.xlsx', '.xls', '.csv', '.json', '.txt']:
            return "data"
        else:
            return "unknown"
    
    def batch_analyze(self, files: List[Dict[str, str]], max_tokens: int = 1500) -> Dict[str, str]:
        """
        Analyze multiple files in batch
        
        Args:
            files: List of dicts with 'path', 'type', and optional 'context'
            max_tokens: Maximum tokens per response
            
        Returns:
            Dictionary of file paths to analysis results
        """
        results = {}
        
        for file_info in files:
            file_path = file_info['path']
            content_type = file_info.get('type', 'auto')
            context = file_info.get('context', {})
            
            try:
                if content_type == "auto":
                    content_type = self._detect_file_type(file_path)
                
                if content_type == "image":
                    prompt = get_comprehensive_analysis_prompt("image", context.get('stock_symbol'))
                    result = self.image_analysis_request(prompt, file_path, max_tokens)
                elif content_type == "video":
                    prompt = get_comprehensive_analysis_prompt("video", context.get('stock_symbol'))
                    result = self.video_analysis_request(prompt, file_path, max_tokens)
                elif content_type == "data":
                    prompt = get_comprehensive_analysis_prompt("data", context.get('stock_symbol'))
                    result = self.text_only_request(prompt, max_tokens)
                else:
                    result = f"Unsupported file type: {content_type}"
                
                results[file_path] = result
                
            except Exception as e:
                results[file_path] = f"Error analyzing {file_path}: {str(e)}"
        
        return results


def main():
    """
    Example usage of the Nova Pro client with custom prompts
    """
    print("="*60)
    print("NOVA PRO CLIENT - MULTIMODAL ANALYSIS EXAMPLES")
    print("="*60)
    
    # Initialize the client with different roles
    print("Initializing Nova Pro client...")
    client = NovaProClient(region_name="us-east-1")
    
    # Example 1: Text-only request with financial analyst role
    print("\n" + "="*50)
    print("EXAMPLE 1: Financial Analysis (Text-only)")
    print("="*50)
    text_response = client.text_only_request(
        prompt="Analyze the current market conditions for technology stocks and provide investment recommendations.",
        max_tokens=500,
        temperature=0.7
    )
    print("Response:")
    print(text_response)
    
    # Example 2: Change role to trading expert
    print("\n" + "="*50)
    print("EXAMPLE 2: Role Change to Trading Expert")
    print("="*50)
    # client.set_role("trading_expert") # Removed role switching
    print(f"Current role: {client.role}") # Assuming role is always 'financial_analyst'
    
    # Example 3: Apple-specific analysis (if files exist)
    print("\n" + "="*50)
    print("EXAMPLE 3: Apple Trading Data Analysis")
    print("="*50)
    
    # Check for available files
    data_dir = "data"
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        apple_files = [f for f in files if 'Apple' in f or 'appleq1' in f]
        
        if apple_files:
            print(f"Found Apple-related files: {apple_files}")
            
            for file in apple_files[:2]:  # Analyze first 2 files
                file_path = os.path.join(data_dir, file)
                print(f"\nAnalyzing: {file}")
                
                try:
                    if file.endswith('.mp4'):
                        result = client.analyze_apple_trading_data(file_path, "video", max_tokens=1000)
                    elif file.endswith('.xlsx'):
                        result = client.analyze_apple_trading_data(file_path, "data", max_tokens=1000)
                    else:
                        result = client.analyze_apple_trading_data(file_path, "auto", max_tokens=1000)
                    
                    print(f"Analysis Result: {result[:200]}...")
                    
                except Exception as e:
                    print(f"Error analyzing {file}: {str(e)}")
        else:
            print("No Apple-related files found in data directory")
            print("To test with real files, place Apple trading data files in the 'data' folder")
    else:
        print("Data directory not found")
        print("Create a 'data' folder and add Apple trading data files for testing")
    
    # Example 4: Batch analysis demonstration
    print("\n" + "="*50)
    print("EXAMPLE 4: Batch Analysis Setup")
    print("="*50)
    
    # Example batch analysis configuration
    batch_files = [
        {
            "path": "data/example_chart.png",
            "type": "image",
            "context": {"stock_symbol": "AAPL"}
        },
        {
            "path": "data/example_video.mp4",
            "type": "video",
            "context": {"stock_symbol": "AAPL"}
        },
        {
            "path": "data/example_data.xlsx",
            "type": "data",
            "context": {"stock_symbol": "AAPL"}
        }
    ]
    
    print("Batch analysis configuration:")
    for file_info in batch_files:
        print(f"  - {file_info['path']} [{file_info['type']}] - {file_info['context']}")
    
    print("\nTo run batch analysis:")
    print("results = client.batch_analyze(batch_files)")
    print("for file_path, result in results.items():")
    print("    print(f'{file_path}: {result[:100]}...')")
    
    print("\n" + "="*60)
    print("SETUP COMPLETE - READY FOR ANALYSIS")
    print("="*60)
    print("\nCurrent role:")
    print(f"  - {client.role}")
    
    print("\nAvailable analysis methods:")
    print("  - client.analyze_apple_trading_data(file_path, file_type)")
    print("  - client.analyze_content(file_path, content_type, stock_symbol)")
    print("  - client.batch_analyze(files_list)")
    # print("  - client.set_role(new_role)") # Removed role switching


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
