import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

class Settings:
    """Centralized settings configuration"""
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'your_access_key_here')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'your_secret_key_here')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Stock Configuration
    STOCK_SYMBOL = os.getenv('STOCK_SYMBOL', 'AAPL')
    DATA_COLLECTION_INTERVAL = int(os.getenv('DATA_COLLECTION_INTERVAL', 300))  # 5 minutes
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 1))
    
    # File Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    IMAGES_DIR = os.path.join(DATA_DIR, 'images')
    VIDEOS_DIR = os.path.join(DATA_DIR, 'videos')
    EXCEL_DIR = os.path.join(DATA_DIR, 'excel')
    FAISS_DIR = os.path.join(DATA_DIR, 'faiss')
    LOGS_DIR = os.path.join(DATA_DIR, 'logs')
    
    # Bedrock Model Configuration
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    NOVA_PRO_MODEL_ID = os.getenv('NOVA_PRO_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v1:0')
    
    # Analysis Configuration
    ANALYSIS_WINDOW_HOURS = int(os.getenv('ANALYSIS_WINDOW_HOURS', 24))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 4000))
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
    
    # FAISS Configuration
    FAISS_DIMENSION = int(os.getenv('FAISS_DIMENSION', 1536))  # Default for OpenAI embeddings
    FAISS_INDEX_TYPE = os.getenv('FAISS_INDEX_TYPE', 'Flat')
    
    @classmethod
    def create_directories(cls):
        """Create all necessary directories"""
        directories = [
            cls.DATA_DIR,
            cls.IMAGES_DIR,
            cls.VIDEOS_DIR,
            cls.EXCEL_DIR,
            cls.FAISS_DIR,
            cls.LOGS_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
        return directories

# Global settings instance
settings = Settings()
