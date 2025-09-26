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

# Wheel Strategy prompts
WHEEL_STRATEGY_PROMPTS = {
    "analysis": """You are an expert options trader specializing in the Wheel Strategy. Analyze the provided intraday stock data and provide a comprehensive wheel strategy analysis.

**WHEEL STRATEGY ANALYSIS:**

**Stock Data Summary:**
- Analyze the price movements, volatility, and volume patterns
- Identify key support and resistance levels
- Calculate average daily range and volatility metrics

**Wheel Strategy Suitability:**
- Assess if this stock is suitable for wheel strategy based on:
  * Liquidity (volume and trades)
  * Price stability and volatility
  * Options availability (infer from stock characteristics)
  * Premium collection potential

**Entry Strategy:**
- Recommend optimal cash-secured put strike prices
- Suggest expiration dates based on volatility
- Calculate potential premium income
- Identify best entry timing based on price action

**Risk Assessment:**
- Evaluate downside risk if assigned
- Assess stock's fundamental strength for holding
- Calculate maximum loss scenarios
- Identify stop-loss levels if needed

**Covered Call Strategy (if assigned):**
- Recommend strike prices for covered calls
- Suggest roll-up/roll-out strategies
- Calculate potential returns from premium collection

**Key Metrics:**
- Annualized return potential
- Win rate probability
- Maximum drawdown risk
- Break-even analysis

Provide specific, actionable recommendations with exact strike prices and timeframes where possible.""",

    "entry_signals": """Analyze this stock data for optimal Wheel Strategy entry points:

**ENTRY SIGNAL ANALYSIS:**

**Current Market Conditions:**
- Price trend analysis (bullish/bearish/sideways)
- Volume analysis and liquidity assessment
- Volatility levels and patterns

**Put Selling Opportunities:**
- Identify oversold conditions for put selling
- Recommend strike prices (typically 5-15% OTM)
- Suggest optimal expiration cycles (30-45 DTE recommended)
- Calculate implied volatility rank if possible

**Risk/Reward Setup:**
- Premium collection vs assignment risk
- Support level analysis
- Historical price behavior at current levels

**Timing Recommendations:**
- Best times to enter based on price action
- Market conditions favoring wheel strategy
- When to avoid entries

Provide specific entry recommendations with reasoning.""",

    "risk_management": """Analyze this stock data for Wheel Strategy risk management:

**RISK MANAGEMENT ANALYSIS:**

**Position Sizing:**
- Recommend appropriate position size based on volatility
- Calculate maximum capital at risk
- Diversification considerations

**Assignment Risk:**
- Probability of put assignment
- Stock quality assessment for holding
- Exit strategies if assigned

**Adjustment Strategies:**
- When to roll puts down and out
- How to handle early assignment
- Managing covered calls after assignment

**Stop Loss Criteria:**
- Technical levels for closing positions
- Fundamental changes requiring exit
- Maximum loss thresholds

**Portfolio Impact:**
- Correlation with other positions
- Overall portfolio risk assessment
- Capital allocation recommendations

Provide specific risk management rules and thresholds.""",

    "performance_tracking": """Analyze this wheel strategy performance data:

**PERFORMANCE ANALYSIS:**

**Return Metrics:**
- Total premium collected
- Annualized return calculation
- Risk-adjusted returns

**Win/Loss Analysis:**
- Successful cycles completed
- Assignment frequency
- Average holding periods

**Strategy Efficiency:**
- Time decay capture
- Volatility exploitation
- Capital utilization

**Improvement Areas:**
- Strike selection optimization
- Timing improvements
- Risk management enhancements

**Market Condition Performance:**
- Performance in different market environments
- Volatility regime analysis
- Seasonal patterns

Provide actionable insights for strategy optimization."""
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

def get_wheel_strategy_prompt(analysis_type: str = "analysis") -> str:
    """Get wheel strategy analysis prompt"""
    return WHEEL_STRATEGY_PROMPTS.get(analysis_type, WHEEL_STRATEGY_PROMPTS["analysis"])

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
    elif content_type == "wheel_strategy":
        return get_wheel_strategy_prompt(analysis_type)
    
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
