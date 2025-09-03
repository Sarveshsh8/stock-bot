#!/usr/bin/env python3
"""
Prompts for Financial Data RAG System
All prompts are centralized here for easy editing and customization
"""

# System prompts for different components
SYSTEM_PROMPTS = {
    "financial_analyst": "You are a financial analyst expert specializing in stock market analysis and trading insights.",
    "data_processor": "You are a data processing specialist focused on financial data analysis and interpretation.",
    "qa_assistant": "You are a financial Q&A assistant providing comprehensive insights based on retrieved data."
}

# Nova Pro prompts for different analysis types
NOVA_PRO_PROMPTS = {
    "general_analysis": """
    You are a financial analyst expert. Based on the following retrieved context, provide a comprehensive and intelligent answer to the user's question.

    USER QUESTION: {query}

    RETRIEVED CONTEXT:
    {context}

    INSTRUCTIONS:
    1. Analyze the retrieved context carefully
    2. Provide a comprehensive, well-structured answer
    3. Include specific data points and insights from the context
    4. Give actionable financial insights when possible
    5. Use professional financial analysis language
    6. Cite the sources of your information

    Please provide your comprehensive financial analysis:
    """,
    
    "stock_price_analysis": """
    You are a stock market analyst. Analyze the following context to provide detailed insights about stock prices.

    USER QUESTION: {query}

    RETRIEVED CONTEXT:
    {context}

    INSTRUCTIONS:
    1. Focus on current stock price and historical trends
    2. Analyze price movements and volatility
    3. Provide technical analysis insights
    4. Give price target recommendations if possible
    5. Include risk assessment
    6. Use professional financial terminology

    Please provide your comprehensive stock price analysis:
    """,
    
    "technical_indicators": """
    You are a technical analysis expert. Analyze the following context to provide insights about technical indicators.

    USER QUESTION: {query}

    RETRIEVED CONTEXT:
    {context}

    INSTRUCTIONS:
    1. Focus on technical indicators (SMA, RSI, MACD, etc.)
    2. Interpret indicator values and signals
    3. Provide trading recommendations based on indicators
    4. Analyze trend strength and direction
    5. Include risk management advice
    6. Use technical analysis terminology

    Please provide your comprehensive technical analysis:
    """,
    
    "market_sentiment": """
    You are a market sentiment analyst. Analyze the following context to provide insights about market sentiment.

    USER QUESTION: {query}

    RETRIEVED CONTEXT:
    {context}

    INSTRUCTIONS:
    1. Analyze overall market sentiment
    2. Identify bullish/bearish signals
    3. Consider volume and price action
    4. Provide sentiment-based insights
    5. Include market psychology factors
    6. Give actionable trading advice

    Please provide your comprehensive market sentiment analysis:
    """,
    
    "financial_recommendations": """
    You are a financial advisor. Analyze the following context to provide investment recommendations.

    USER QUESTION: {query}

    RETRIEVED CONTEXT:
    {context}

    INSTRUCTIONS:
    1. Provide clear investment recommendations
    2. Include risk assessment
    3. Give time horizon suggestions
    4. Consider diversification strategies
    5. Include exit strategy advice
    6. Use professional financial language

    Please provide your comprehensive financial recommendations:
    """,
    
    "trading_summary": """
    You are a trading strategist. Analyze the following context to provide a comprehensive trading summary.

    USER QUESTION: {query}

    RETRIEVED CONTEXT:
    {context}

    INSTRUCTIONS:
    1. Provide a comprehensive trading overview
    2. Include key price levels and support/resistance
    3. Analyze volume patterns
    4. Give entry and exit points
    5. Include risk management strategies
    6. Summarize key trading opportunities

    Please provide your comprehensive trading summary:
    """
}

# Context formatting templates
CONTEXT_TEMPLATES = {
    "source_format": "[{source_upper}, Relevance: {score:.3f}]\n{content}",
    "context_header": "RETRIEVED CONTEXT:\n{separator}",
    "source_list": "{index}. {source_upper} (Relevance: {score:.3f})"
}

# Output formatting templates
OUTPUT_TEMPLATES = {
    "nova_pro_header": """
    INTELLIGENT ANALYSIS BY NOVA PRO
    {separator}
    
    QUESTION: {query}
    
    {separator}
    
    {response}
    
    {separator}
    
    SOURCES USED:
    """,
    
    "fallback_header": """
    FINAL OUTPUT FOR: "{query}"
    {separator}
    
    RETRIEVED CONTEXT:
    {context_separator}
    {context}
    
    COMPREHENSIVE ANSWER:
    {context_separator}
    """,
    
    "source_summary": """
    Total sources analyzed: {count}
    Most relevant source score: {score:.3f}
    """
}

# Interactive session prompts
INTERACTIVE_PROMPTS = {
    "welcome": "Welcome to the Financial Data Chat System!",
    "example_queries": [
        "What is the current Apple stock price?",
        "Show me technical indicators",
        "What are the financial recommendations?",
        "Give me a trading summary",
        "What is the market sentiment?",
        "Analyze the market trends",
        "What are the key financial insights?"
    ],
    "quit_commands": ["quit", "exit", "q"],
    "input_prompt": "Your question: ",
    "processing_message": "Processing your question...",
    "error_message": "An error occurred. Please try again."
}

# Error messages
ERROR_MESSAGES = {
    "file_not_found": "Error: File not found: {file_path}",
    "loading_failed": "Failed to load {component}. Please check configuration.",
    "index_not_found": "Index file not found. Please run previous steps first.",
    "model_not_loaded": "Model not loaded. Please check initialization.",
    "context_not_found": "No relevant context found for your query.",
    "nova_pro_failed": "Nova Pro analysis failed. Using fallback mode."
}

# Success messages
SUCCESS_MESSAGES = {
    "system_ready": "Financial Data Chat System is ready!",
    "index_built": "FAISS index built successfully!",
    "models_loaded": "All models loaded successfully!",
    "context_retrieved": "Context retrieved successfully!",
    "analysis_complete": "Analysis completed successfully!"
}

# Configuration constants
CONFIG = {
    "default_top_k": 3,
    "max_context_length": 500,
    "max_tokens": 1500,
    "temperature": 0.7,
    "top_p": 0.9,
    "separator_length": 60
}

def get_prompt(prompt_type: str, **kwargs) -> str:
    """Get a formatted prompt with the given type and parameters"""
    if prompt_type in NOVA_PRO_PROMPTS:
        prompt = NOVA_PRO_PROMPTS[prompt_type]
        return prompt.format(**kwargs)
    else:
        return f"Prompt type '{prompt_type}' not found."

def get_system_prompt(role: str) -> str:
    """Get system prompt for a specific role"""
    return SYSTEM_PROMPTS.get(role, SYSTEM_PROMPTS["financial_analyst"])

def get_context_template(template_type: str, **kwargs) -> str:
    """Get formatted context template"""
    if template_type in CONTEXT_TEMPLATES:
        template = CONTEXT_TEMPLATES[template_type]
        return template.format(**kwargs)
    else:
        return f"Template type '{template_type}' not found."

def get_output_template(template_type: str, **kwargs) -> str:
    """Get formatted output template"""
    if template_type in OUTPUT_TEMPLATES:
        template = OUTPUT_TEMPLATES[template_type]
        return template.format(**kwargs)
    else:
        return f"Template type '{template_type}' not found."

def get_error_message(error_type: str, **kwargs) -> str:
    """Get formatted error message"""
    if error_type in ERROR_MESSAGES:
        message = ERROR_MESSAGES[error_type]
        return message.format(**kwargs)
    else:
        return f"Error type '{error_type}' not found."

def get_success_message(success_type: str) -> str:
    """Get success message"""
    return SUCCESS_MESSAGES.get(success_type, "Operation completed successfully!")
