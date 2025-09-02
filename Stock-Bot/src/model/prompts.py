"""
Custom prompts for Nova Pro multimodal analysis - Financial Analyst Focus
This file contains specialized prompts for financial analysis of Apple trading data
"""

# System prompt for financial analyst
SYSTEM_PROMPT = """You are an expert financial analyst specializing in stock market analysis, 
technical indicators, and market sentiment. You provide clear, actionable insights based on 
data analysis and visual content. Always include specific data points and recommendations when possible."""

# Apple-specific analysis prompts
APPLE_ANALYSIS_PROMPTS = {
    "trading_data": """Analyze this Apple (AAPL) trading data comprehensively:

1. **Price Action Analysis:**
   - Current trend direction and strength
   - Key support and resistance levels
   - Price momentum indicators

2. **Technical Indicators:**
   - Moving averages (20, 50, 200 day)
   - RSI, MACD, Bollinger Bands
   - Volume analysis and patterns

3. **Trading Signals:**
   - Buy/sell opportunities
   - Entry and exit points
   - Risk management levels

4. **Market Context:**
   - Sector performance comparison
   - Market sentiment indicators
   - News impact assessment

5. **Recommendations:**
   - Short-term trading strategy
   - Long-term investment outlook
   - Risk considerations

Provide specific data points and actionable insights.""",
    
    "earnings_analysis": """Analyze this Apple earnings data and provide:

1. **Financial Performance:**
   - Revenue and profit trends
   - Key performance metrics
   - Comparison with expectations

2. **Business Insights:**
   - Product segment performance
   - Geographic performance
   - Strategic initiatives

3. **Market Impact:**
   - Stock price implications
   - Sector performance
   - Investor sentiment

4. **Investment Outlook:**
   - Growth prospects
   - Risk factors
   - Investment recommendations""",
    
    "video_content": """Analyze this Apple-related video content and provide:

1. **Content Summary:**
   - Main topics and themes
   - Key messages conveyed
   - Visual elements and presentation

2. **Business Insights:**
   - Strategic announcements
   - Product information
   - Market positioning

3. **Investment Implications:**
   - Stock price impact
   - Market sentiment
   - Trading opportunities

4. **Risk Assessment:**
   - Potential challenges
   - Competitive factors
   - Market risks"""
}

# General analysis prompts for different content types
CONTENT_ANALYSIS_PROMPTS = {
    "image": """Analyze this image comprehensively and provide:

1. **Visual Content:**
   - What you see in the image
   - Key elements and objects
   - Visual composition and style

2. **Financial Context:**
   - Market-related information
   - Chart patterns and trends
   - Technical indicators visible

3. **Business Insights:**
   - Relevant financial data
   - Market implications
   - Investment considerations

4. **Recommendations:**
   - Trading opportunities
   - Risk factors
   - Next steps for analysis""",
    
    "video": """Analyze this video content comprehensively and provide:

1. **Content Summary:**
   - Main topics and themes
   - Key messages and points
   - Visual and audio elements

2. **Financial Context:**
   - Market implications
   - Investment relevance
   - Strategic significance

3. **Data Interpretation:**
   - Key information extracted
   - Trends and patterns
   - Comparative analysis

4. **Actionable Insights:**
   - Investment recommendations
   - Risk factors
   - Opportunities identified""",
    
    "data": """Analyze this financial data comprehensively and provide:

1. **Data Overview:**
   - Key metrics and indicators
   - Trends and patterns
   - Data quality assessment

2. **Financial Analysis:**
   - Performance evaluation
   - Comparative analysis
   - Risk assessment

3. **Market Implications:**
   - Investment opportunities
   - Risk factors
   - Strategic insights

4. **Recommendations:**
   - Actionable insights
   - Next steps
   - Areas for further analysis"""
}

# Helper functions for prompt generation
def get_system_prompt() -> str:
    """Get the financial analyst system prompt"""
    return SYSTEM_PROMPT

def get_apple_prompt(analysis_type: str) -> str:
    """Get Apple-specific analysis prompt"""
    return APPLE_ANALYSIS_PROMPTS.get(analysis_type, "")

def get_content_prompt(content_type: str) -> str:
    """Get general analysis prompt for content type"""
    return CONTENT_ANALYSIS_PROMPTS.get(content_type, "")

def get_comprehensive_analysis_prompt(content_type: str, stock_symbol: str = None) -> str:
    """Get a comprehensive analysis prompt for the given content and context"""
    
    if stock_symbol and stock_symbol.upper() == "AAPL":
        if content_type == "trading_data":
            return get_apple_prompt("trading_data")
        elif content_type == "earnings":
            return get_apple_prompt("earnings_analysis")
        elif content_type == "video":
            return get_apple_prompt("video_content")
    
    # Fall back to general prompts
    if content_type in ["image", "chart", "graph"]:
        return get_content_prompt("image")
    elif content_type in ["video", "presentation"]:
        return get_content_prompt("video")
    elif content_type in ["excel", "data", "spreadsheet"]:
        return get_content_prompt("data")
    
    # Default comprehensive prompt
    return f"""Please analyze this {content_type} comprehensively and provide:

1. **Content Analysis:** What is being presented or shown
2. **Key Insights:** Important findings and observations
3. **Financial Implications:** Relevance and impact on investments
4. **Recommendations:** Actionable next steps
5. **Risk Factors:** Potential concerns or challenges

Provide specific details and actionable insights."""
