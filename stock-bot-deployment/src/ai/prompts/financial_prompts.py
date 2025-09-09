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
    "financial_chart": """Analyze this financial chart comprehensively:

1. **Chart Analysis:**
   - Chart type and timeframe
   - Price trends and patterns
   - Volume analysis
   - Technical indicators visible

2. **Technical Analysis:**
   - Support and resistance levels
   - Moving averages
   - Chart patterns (head & shoulders, triangles, etc.)
   - Momentum indicators

3. **Trading Signals:**
   - Buy/sell opportunities
   - Entry and exit points
   - Risk management levels

4. **Market Context:**
   - Current market conditions
   - Sector performance
   - News impact

5. **Recommendations:**
   - Short-term trading strategy
   - Long-term outlook
   - Risk considerations

Provide specific data points and actionable insights.""",

    "earnings_chart": """Analyze this earnings or financial data chart:

1. **Data Interpretation:**
   - Key metrics and indicators
   - Trends and patterns
   - Performance comparison

2. **Financial Analysis:**
   - Revenue and profit trends
   - Growth rates
   - Profitability metrics

3. **Business Insights:**
   - Operational performance
   - Strategic initiatives
   - Market positioning

4. **Investment Implications:**
   - Stock price impact
   - Valuation considerations
   - Risk assessment

5. **Recommendations:**
   - Investment outlook
   - Key factors to watch
   - Actionable insights""",

    "general_financial": """Analyze this financial image comprehensively:

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
   - Next steps for analysis

Provide detailed analysis with specific observations."""
}

# Video analysis prompts
VIDEO_PROMPTS = {
    "earnings_call": """Analyze this earnings call video comprehensively:

1. **Content Summary:**
   - Main topics and themes discussed
   - Key messages from management
   - Visual elements and presentation style

2. **Financial Performance:**
   - Revenue and profit trends
   - Key performance metrics
   - Comparison with expectations

3. **Business Insights:**
   - Strategic initiatives
   - Market positioning
   - Growth prospects

4. **Market Impact:**
   - Stock price implications
   - Investor sentiment
   - Sector performance

5. **Investment Outlook:**
   - Growth prospects
   - Risk factors
   - Investment recommendations

Provide detailed analysis with specific insights and recommendations.""",

    "market_analysis": """Analyze this market analysis video comprehensively:

1. **Market Overview:**
   - Current market conditions
   - Key trends and patterns
   - Sector performance

2. **Technical Analysis:**
   - Chart patterns and indicators
   - Support and resistance levels
   - Trading signals

3. **Fundamental Analysis:**
   - Economic indicators
   - Company performance
   - Industry trends

4. **Trading Opportunities:**
   - Buy/sell signals
   - Entry and exit points
   - Risk management

5. **Market Outlook:**
   - Short-term predictions
   - Long-term trends
   - Risk factors

Provide actionable insights and specific recommendations.""",

    "general_financial": """Analyze this financial video content comprehensively:

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
   - Opportunities identified

Provide detailed analysis with specific recommendations."""
}

# Text analysis prompts
TEXT_PROMPTS = {
    "financial_data": """Analyze this financial data comprehensively:

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
   - Areas for further analysis""",

    "market_analysis": """Analyze this market data and provide:

1. **Market Conditions:**
   - Current trends and patterns
   - Key indicators
   - Market sentiment

2. **Technical Analysis:**
   - Chart patterns
   - Support/resistance levels
   - Trading signals

3. **Fundamental Analysis:**
   - Economic factors
   - Company performance
   - Industry trends

4. **Investment Strategy:**
   - Opportunities identified
   - Risk management
   - Portfolio considerations

5. **Outlook:**
   - Short-term predictions
   - Long-term trends
   - Key factors to watch""",

    "earnings_analysis": """Analyze this earnings data and provide:

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
   - Investment recommendations"""
}

# Stock-specific prompts
STOCK_PROMPTS = {
    "AAPL": {
        "trading_analysis": """Analyze this Apple (AAPL) trading data comprehensively:

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
   - Product segment performance (iPhone, Services, Mac, iPad, Wearables)
   - Geographic performance
   - Strategic initiatives

3. **Market Impact:**
   - Stock price implications
   - Sector performance
   - Investor sentiment

4. **Investment Outlook:**
   - Growth prospects
   - Risk factors
   - Investment recommendations"""
    }
}

# Helper functions
def get_system_prompt() -> str:
    """Get the financial analyst system prompt"""
    return SYSTEM_PROMPT

def get_image_prompt(prompt_type: str = "general_financial") -> str:
    """Get image analysis prompt"""
    return IMAGE_PROMPTS.get(prompt_type, IMAGE_PROMPTS["general_financial"])

def get_video_prompt(prompt_type: str = "general_financial") -> str:
    """Get video analysis prompt"""
    return VIDEO_PROMPTS.get(prompt_type, VIDEO_PROMPTS["general_financial"])

def get_text_prompt(prompt_type: str = "financial_data") -> str:
    """Get text analysis prompt"""
    return TEXT_PROMPTS.get(prompt_type, TEXT_PROMPTS["financial_data"])

def get_stock_prompt(stock_symbol: str, analysis_type: str) -> str:
    """Get stock-specific analysis prompt"""
    stock_symbol = stock_symbol.upper()
    if stock_symbol in STOCK_PROMPTS:
        return STOCK_PROMPTS[stock_symbol].get(analysis_type, "")
    return ""

def get_comprehensive_prompt(content_type: str, stock_symbol: str = None, 
                           analysis_type: str = "general") -> str:
    """Get comprehensive analysis prompt based on content type and context"""
    
    # Check for stock-specific prompts first
    if stock_symbol:
        stock_prompt = get_stock_prompt(stock_symbol, analysis_type)
        if stock_prompt:
            return stock_prompt
    
    # Fall back to general prompts based on content type
    if content_type in ["image", "chart", "graph"]:
        if analysis_type == "earnings":
            return get_image_prompt("earnings_chart")
        elif analysis_type == "trading":
            return get_image_prompt("financial_chart")
        else:
            return get_image_prompt("general_financial")
    
    elif content_type in ["video", "presentation"]:
        if analysis_type == "earnings":
            return get_video_prompt("earnings_call")
        elif analysis_type == "market":
            return get_video_prompt("market_analysis")
        else:
            return get_video_prompt("general_financial")
    
    elif content_type in ["text", "data", "excel", "spreadsheet"]:
        if analysis_type == "earnings":
            return get_text_prompt("earnings_analysis")
        elif analysis_type == "market":
            return get_text_prompt("market_analysis")
        else:
            return get_text_prompt("financial_data")
    
    # Default comprehensive prompt
    return f"""Please analyze this {content_type} comprehensively and provide:

1. **Content Analysis:** What is being presented or shown
2. **Key Insights:** Important findings and observations
3. **Financial Implications:** Relevance and impact on investments
4. **Recommendations:** Actionable next steps
5. **Risk Factors:** Potential concerns or challenges

Provide specific details and actionable insights."""
