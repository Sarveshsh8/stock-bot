"""
Wheel Strategy Prompts
Specialized prompts for wheel strategy analysis using AI
"""

from typing import List

# System prompt for wheel strategy analyst
SYSTEM_PROMPT = (
    "You are an expert options trader specializing in the Wheel Strategy. You have extensive experience in:\n"
    "- Options trading and strategy implementation\n"
    "- Risk management and position sizing\n"
    "- Technical analysis and market timing\n"
    "- Premium collection optimization\n"
    "- Assignment management and covered call strategies\n\n"
    "Provide clear, actionable insights with specific recommendations including exact strike prices, timeframes, and risk management rules when possible."
)

# Wheel Strategy prompts
WHEEL_STRATEGY_PROMPTS = {
    "analysis": (
        "You are an expert options trader specializing in the Wheel Strategy. Analyze the provided intraday stock data and provide a comprehensive wheel strategy analysis.\n\n"
        "**WHEEL STRATEGY ANALYSIS:**\n\n"
        "**Stock Data Summary:**\n"
        "- Analyze the price movements, volatility, and volume patterns\n"
        "- Identify key support and resistance levels\n"
        "- Calculate average daily range and volatility metrics\n\n"
        "**Wheel Strategy Suitability:**\n"
        "- Assess if this stock is suitable for wheel strategy based on:\n"
        "  * Liquidity (volume and trades)\n"
        "  * Price stability and volatility\n"
        "  * Options availability (infer from stock characteristics)\n"
        "  * Premium collection potential\n\n"
        "**Entry Strategy:**\n"
        "- Recommend optimal cash-secured put strike prices\n"
        "- Suggest expiration dates based on volatility\n"
        "- Calculate potential premium income\n"
        "- Identify best entry timing based on price action\n\n"
        "**Risk Assessment:**\n"
        "- Evaluate downside risk if assigned\n"
        "- Assess stock's fundamental strength for holding\n"
        "- Calculate maximum loss scenarios\n"
        "- Identify stop-loss levels if needed\n\n"
        "**Covered Call Strategy (if assigned):**\n"
        "- Recommend strike prices for covered calls\n"
        "- Suggest roll-up/roll-out strategies\n"
        "- Calculate potential returns from premium collection\n\n"
        "**Key Metrics:**\n"
        "- Annualized return potential\n"
        "- Win rate probability\n"
        "- Maximum drawdown risk\n"
        "- Break-even analysis\n\n"
        "Provide specific, actionable recommendations with exact strike prices and timeframes where possible."
    ),
    "entry_signals": (
        "Analyze this stock data for optimal Wheel Strategy entry points:\n\n"
        "**ENTRY SIGNAL ANALYSIS:**\n\n"
        "**Current Market Conditions:**\n"
        "- Price trend analysis (bullish/bearish/sideways)\n"
        "- Volume analysis and liquidity assessment\n"
        "- Volatility levels and patterns\n\n"
        "**Put Selling Opportunities:**\n"
        "- Identify oversold conditions for put selling\n"
        "- Recommend strike prices (typically 5-15% OTM)\n"
        "- Suggest optimal expiration cycles (30-45 DTE recommended)\n"
        "- Calculate implied volatility rank if possible\n\n"
        "**Risk/Reward Setup:**\n"
        "- Premium collection vs assignment risk\n"
        "- Support level analysis\n"
        "- Historical price behavior at current levels\n\n"
        "**Timing Recommendations:**\n"
        "- Best times to enter based on price action\n"
        "- Market conditions favoring wheel strategy\n"
        "- When to avoid entries\n\n"
        "Provide specific entry recommendations with reasoning."
    ),
    "risk_management": (
        "Analyze this stock data for Wheel Strategy risk management:\n\n"
        "**RISK MANAGEMENT ANALYSIS:**\n\n"
        "**Position Sizing:**\n"
        "- Recommend appropriate position size based on volatility\n"
        "- Calculate maximum capital at risk\n"
        "- Diversification considerations\n\n"
        "**Assignment Risk:**\n"
        "- Probability of put assignment\n"
        "- Stock quality assessment for holding\n"
        "- Exit strategies if assigned\n\n"
        "**Adjustment Strategies:**\n"
        "- When to roll puts down and out\n"
        "- How to handle early assignment\n"
        "- Managing covered calls after assignment\n\n"
        "**Stop Loss Criteria:**\n"
        "- Technical levels for closing positions\n"
        "- Fundamental changes requiring exit\n"
        "- Maximum loss thresholds\n\n"
        "**Portfolio Impact:**\n"
        "- Correlation with other positions\n"
        "- Overall portfolio risk assessment\n"
        "- Capital allocation recommendations\n\n"
        "Provide specific risk management rules and thresholds."
    ),
    "performance_tracking": (
        "Analyze this wheel strategy performance data:\n\n"
        "**PERFORMANCE ANALYSIS:**\n\n"
        "**Return Metrics:**\n"
        "- Total premium collected\n"
        "- Annualized return calculation\n"
        "- Risk-adjusted returns\n\n"
        "**Win/Loss Analysis:**\n"
        "- Successful cycles completed\n"
        "- Assignment frequency\n"
        "- Average holding periods\n\n"
        "**Strategy Efficiency:**\n"
        "- Time decay capture\n"
        "- Volatility exploitation\n"
        "- Capital utilization\n\n"
        "**Improvement Areas:**\n"
        "- Strike selection optimization\n"
        "- Timing improvements\n"
        "- Risk management enhancements\n\n"
        "**Market Condition Performance:**\n"
        "- Performance in different market environments\n"
        "- Volatility regime analysis\n"
        "- Seasonal patterns\n\n"
        "Provide actionable insights for strategy optimization."
    ),
}


def get_system_prompt() -> str:
    """Get the wheel strategy analyst system prompt"""
    return SYSTEM_PROMPT


def get_wheel_strategy_prompt(analysis_type: str = "analysis") -> str:
    """Get wheel strategy analysis prompt by type"""
    return WHEEL_STRATEGY_PROMPTS.get(analysis_type, WHEEL_STRATEGY_PROMPTS["analysis"])


def get_all_prompt_types() -> List[str]:
    """Get list of all available wheel prompt types"""
    return list(WHEEL_STRATEGY_PROMPTS.keys())


