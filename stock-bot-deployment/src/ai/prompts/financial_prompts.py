"""
Financial Analysis Prompts
Specialized prompts for financial analysis using AWS Bedrock Nova Pro
"""

# System prompt for financial analyst
SYSTEM_PROMPT = """You are an expert financial analyst specializing in stock market analysis, 
technical indicators, and market sentiment. You provide clear, actionable insights based on 
data analysis and visual content. Always include specific data points and recommendations when possible."""

# Image analysis prompts
IMAGE_PROMPTS = {
    "simple_analysis": """Analyze this financial image:

**DATA:**
- Extract revenue, profit, earnings numbers
- Note growth rates and percentages
- Identify company names and stock symbols

**SUMMARY:**
- Key financial information
- Investment insights

Keep it simple and focused and provide a detailed analysis of this image."""
}

# Video analysis prompts
VIDEO_PROMPTS = {
    "simple_analysis": """Analyze this financial video:

**DATA:**
- Extract revenue, profit, earnings numbers
- Note growth rates and percentages
- Identify company names and stock symbols

**SUMMARY:**
- Key financial information
- Investment insights

Keep it simple and focused and provide a detailed analysis of this video."""
}

# Text analysis prompts
TEXT_PROMPTS = {
    "simple_analysis": """Analyze this financial data:

**DATA:**
- Extract revenue, profit, earnings numbers
- Note growth rates and percentages
- Identify company names and stock symbols

**SUMMARY:**
- Key financial information
- Investment insights

Keep it simple and focused and provide a detailed analysis of this text."""
}

# Stock-specific prompts (simplified)
STOCK_PROMPTS = {}

# Helper functions
def get_system_prompt() -> str:
    """Get the financial analyst system prompt"""
    return SYSTEM_PROMPT

def get_image_prompt(prompt_type: str = "simple_analysis") -> str:
    """Get image analysis prompt"""
    return IMAGE_PROMPTS.get(prompt_type, IMAGE_PROMPTS["simple_analysis"])

def get_video_prompt(prompt_type: str = "simple_analysis") -> str:
    """Get video analysis prompt"""
    return VIDEO_PROMPTS.get(prompt_type, VIDEO_PROMPTS["simple_analysis"])

def get_text_prompt(prompt_type: str = "simple_analysis") -> str:
    """Get text analysis prompt"""
    return TEXT_PROMPTS.get(prompt_type, TEXT_PROMPTS["simple_analysis"])

def get_stock_prompt(stock_symbol: str, analysis_type: str) -> str:
    """Get stock-specific analysis prompt"""
    stock_symbol = stock_symbol.upper()
    if stock_symbol in STOCK_PROMPTS:
        return STOCK_PROMPTS[stock_symbol].get(analysis_type, "")
    return ""

def get_comprehensive_prompt(content_type: str, stock_symbol: str = None, 
                           analysis_type: str = "general") -> str:
    """Get simple analysis prompt based on content type"""
    
    # Use simple prompts for all content types
    if content_type in ["image", "chart", "graph"]:
        return get_image_prompt("simple_analysis")
    elif content_type in ["video", "presentation"]:
        return get_video_prompt("simple_analysis")
    elif content_type in ["text", "data", "excel", "spreadsheet"]:
        return get_text_prompt("simple_analysis")
    
    # Default simple prompt
    return """Analyze this content:

**DATA:**
- Extract revenue, profit, earnings numbers
- Note growth rates and percentages
- Identify company names and stock symbols

**SUMMARY:**
- Key financial information
- Investment insights

Keep it simple and focused."""
