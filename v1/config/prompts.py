# Stock Analysis Prompts

## Data Collection Prompts

DATA_COLLECTION_PROMPT = """
You are a financial data analyst. Analyze the following stock data for {symbol}:

Current Price: ${current_price}
Volume: {volume}
Market Cap: ${market_cap}
PE Ratio: {pe_ratio}
Dividend Yield: {dividend_yield}

Historical Data Points: {data_points_count}

Please provide:
1. Key insights about the current price movement
2. Volume analysis
3. Technical indicators summary
4. Risk assessment
5. Short-term price prediction (next 4 hours)
"""

## Multimodal Analysis Prompts

MULTIMODAL_ANALYSIS_PROMPT = """
You are an expert financial analyst using multimodal AI. Analyze the provided stock data, charts, and videos for {symbol}.

Data Summary:
- Current Price: ${current_price}
- 24h Change: {price_change}
- Volume: {volume}
- Market Cap: ${market_cap}

Chart Analysis:
- Trend direction and strength
- Support/resistance levels
- Key technical patterns
- Volume-price relationship

Video Analysis:
- Price movement patterns over time
- Volatility assessment
- Trading volume patterns
- Market sentiment indicators

Please provide:
1. Comprehensive technical analysis
2. Pattern recognition from visual data
3. Market sentiment analysis
4. Risk assessment with confidence levels
5. Trading recommendations with rationale
6. Key events that might have influenced price movement
"""

## FAISS Database Prompts

FAISS_INDEXING_PROMPT = """
Create a searchable knowledge base entry for stock analysis data.

Stock: {symbol}
Timestamp: {timestamp}
Data Type: {data_type}

Content:
{content}

Create embeddings for:
1. Technical analysis insights
2. Price movement patterns
3. Volume analysis
4. Market sentiment indicators
5. Risk factors
6. Trading recommendations

Ensure the embeddings capture:
- Numerical data relationships
- Temporal patterns
- Market context
- Risk indicators
"""

## Q&A System Prompts

QA_SYSTEM_PROMPT = """
You are an expert financial analyst assistant. Answer questions about stock data for {symbol} based on the provided context.

Context Information:
{context}

Question: {question}

Please provide:
1. Direct answer based on available data
2. Supporting evidence from the context
3. Confidence level in your answer
4. Additional insights if relevant
5. Data limitations if any

Answer format:
- Clear, concise response
- Data-driven insights
- Risk considerations
- Actionable recommendations
"""

## Video Analysis Prompts

VIDEO_ANALYSIS_PROMPT = """
Analyze the stock price movement video for {symbol} covering the period from {start_time} to {end_time}.

Video Summary:
- Duration: {duration}
- Frame count: {frame_count}
- Time intervals: {intervals}

Please analyze:
1. Price movement patterns
2. Volatility trends
3. Volume patterns
4. Key turning points
5. Support/resistance levels
6. Market sentiment changes
7. Trading opportunities
8. Risk assessment

Provide:
- Pattern recognition
- Trend analysis
- Technical indicators
- Market psychology insights
- Trading recommendations
- Risk warnings
"""

## Excel Report Prompts

EXCEL_REPORT_PROMPT = """
Generate a comprehensive Excel report for {symbol} stock analysis.

Data Summary:
- Analysis Period: {period}
- Data Points: {data_points}
- Current Price: ${current_price}

Required Sections:
1. Executive Summary
2. Technical Analysis
3. Fundamental Analysis
4. Risk Assessment
5. Trading Recommendations
6. Market Outlook
7. Key Metrics Dashboard

Format Requirements:
- Professional layout
- Clear data visualization
- Actionable insights
- Risk warnings
- Performance metrics
- Comparative analysis
"""

## Bedrock Model Prompts

BEDROCK_ANALYSIS_PROMPT = """
You are an advanced AI financial analyst using Amazon Bedrock. Analyze the following multimodal data for {symbol}:

Text Data: {text_data}
Image Data: {image_analysis}
Video Data: {video_analysis}
Numerical Data: {numerical_data}

Please provide:
1. Advanced pattern recognition
2. Multi-timeframe analysis
3. Sentiment analysis
4. Risk modeling
5. Predictive insights
6. Trading strategy recommendations
7. Market psychology analysis
8. Regulatory considerations

Use advanced AI capabilities to:
- Identify complex patterns
- Predict price movements
- Assess market sentiment
- Calculate risk metrics
- Generate trading signals
- Provide market context
"""
