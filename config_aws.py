"""
AWS Configuration Helper
Sets up AWS credentials and Bedrock configuration
"""

import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=False)

# AWS Configuration
AWS_CONFIG = {
    'access_key_id': os.getenv('AWS_ACCESS_KEY_ID', 'AKIAUJRTKQNULWFWRMNV'),
    'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY', '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'),
    'region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
}

# Bedrock Configuration
BEDROCK_CONFIG = {
    'region': AWS_CONFIG['region'],
    'model_id': os.getenv('BEDROCK_MODEL_ID', 'us.amazon.nova-pro-v1:0'),
    'max_tokens': int(os.getenv('BEDROCK_MAX_TOKENS', '2000')),
    'temperature': float(os.getenv('BEDROCK_TEMPERATURE', '0.7')),
    'top_p': float(os.getenv('BEDROCK_TOP_P', '0.9'))
}

def setup_aws_credentials():
    """
    Setup AWS credentials in environment.
    
    This ensures AWS credentials are available for boto3.
    Call this at the start of your application.
    """
    os.environ['AWS_ACCESS_KEY_ID'] = AWS_CONFIG['access_key_id']
    os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_CONFIG['secret_access_key']
    os.environ['AWS_DEFAULT_REGION'] = AWS_CONFIG['region']
    
    print(f"AWS credentials configured for region: {AWS_CONFIG['region']}")

def get_bedrock_config(region=None, model_id=None):
    """
    Get Bedrock configuration dictionary.
    
    Parameters:
    - region: AWS region (optional, uses default if not provided)
    - model_id: Bedrock model ID (optional, uses default if not provided)
    
    Returns:
    - Dictionary with Bedrock settings
    """
    config = BEDROCK_CONFIG.copy()
    if region:
        config['region'] = region
    if model_id:
        config['model_id'] = model_id
    
    # Return in expected format for NovaTextAnalyzer
    return {
        'bedrock_settings': {
            'region': config['region'],
            'nova_pro_arn': config['model_id'],
            'max_tokens': config['max_tokens'],
            'temperature': config['temperature'],
            'top_p': config['top_p']
        }
    }

def verify_aws_credentials():
    """
    Verify AWS credentials are configured.
    
    Returns:
    - True if credentials found, False otherwise
    """
    has_key = bool(AWS_CONFIG['access_key_id'])
    has_secret = bool(AWS_CONFIG['secret_access_key'])
    
    if has_key and has_secret:
        print("AWS credentials found")
        return True
    else:
        print("WARNING: AWS credentials not found")
        return False


if __name__ == "__main__":
    print("AWS Configuration Test")
    print("=" * 50)
    
    if verify_aws_credentials():
        print(f"Access Key: {AWS_CONFIG['access_key_id'][:10]}...")
        print(f"Region: {AWS_CONFIG['region']}")
        print(f"Bedrock Model: {BEDROCK_CONFIG['model_id']}")
        print("\nConfiguration valid!")
    else:
        print("Please set AWS credentials in .env file")

