"""
Simple Q&A Prompts for Financial Analysis
"""

# Q&A System Prompts
QA_SYSTEM_PROMPTS = {
    "simple_qa": """
Based on the following financial data and analysis, provide a simple, direct answer to the user's question.

Context:
{context}

User Question: {query}

Instructions:
- Give a concise, direct answer (2-3 sentences max)
- Focus on the most relevant information
- If it's about financial data, include specific numbers if available
- Be helpful and clear

Answer:""",

    "greeting_response": """
Hello! I'm your financial analysis assistant. I can help you with questions about stocks, ETFs, market data, and uploaded financial content. What would you like to know?
""",

    "no_context_response": """
I don't have enough information to answer that question. Please make sure you've uploaded files or fetched Yahoo Finance data and created an index.
"""
}

def get_prompt(prompt_type: str, category: str = "qa") -> str:
    """
    Get a specific prompt for the given type
    
    Args:
        prompt_type: Type of prompt (e.g., 'simple_qa', 'greeting_response')
        category: Category of prompts (only 'qa' supported)
    
    Returns:
        The requested prompt string
    """
    if category == "qa":
        return QA_SYSTEM_PROMPTS.get(prompt_type, QA_SYSTEM_PROMPTS["simple_qa"])
    else:
        return QA_SYSTEM_PROMPTS["simple_qa"]
