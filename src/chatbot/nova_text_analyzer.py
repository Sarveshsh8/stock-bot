"""
Text Analysis Module using AWS Bedrock Nova Pro
Handles text generation and analysis for stock market queries
"""

import boto3
import json
import os
import logging
from typing import Dict, Any, Optional


class NovaTextAnalyzer:
    """Handles text analysis and generation using AWS Bedrock Nova Pro"""
    
    def __init__(self, 
                 region: str = "us-east-1",
                 model_id: str = "us.amazon.nova-pro-v1:0",
                 max_tokens: int = 2000):
        """
        Initialize the text analyzer with AWS Bedrock Nova Pro
        
        Parameters:
        - region: AWS region for Bedrock service
        - model_id: Nova Pro model identifier
        - max_tokens: Maximum tokens in response
        
        How it works:
        This module replaces OpenAI with AWS Bedrock Nova for text generation.
        Nova Pro is Amazon's advanced language model that can understand and
        generate natural language responses about stock market data.
        """
        self.region = region
        self.model_id = model_id
        self.max_tokens = max_tokens
        
        self._setup_logging()
        self._setup_bedrock_client()
    
    def _setup_logging(self):
        """Setup logging for debugging and monitoring."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_bedrock_client(self):
        """
        Setup AWS Bedrock client.
        
        This connects to AWS Bedrock service using credentials from:
        1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        2. AWS credentials file (~/.aws/credentials)
        3. IAM role (if running on AWS)
        """
        try:
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region
            )
            self.logger.info(f"Bedrock client initialized for region: {self.region}")
        except Exception as e:
            self.logger.error(f"Error setting up Bedrock client: {str(e)}")
            raise
    
    def generate_response(self, 
                         prompt: str,
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7,
                         top_p: float = 0.9) -> str:
        """
        Generate text response using Nova Pro.
        
        Parameters:
        - prompt: User's question or prompt
        - system_prompt: System instructions for the model
        - temperature: Response creativity (0.0 = focused, 1.0 = creative)
        - top_p: Response diversity (0.0 to 1.0)
        
        Returns:
        - Generated text response
        
        How it works:
        1. Takes the user's question and context
        2. Formats it for Nova Pro model
        3. Sends request to AWS Bedrock
        4. Returns the generated response
        """
        try:
            self.logger.info("Generating response with Nova Pro")
            
            # Prepare messages
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({
                    "role": "user",
                    "content": [{"text": f"System Instructions: {system_prompt}\n\nUser Query: {prompt}"}]
                })
            else:
                messages.append({
                    "role": "user",
                    "content": [{"text": prompt}]
                })
            
            # Prepare request body for Nova Pro
            body = {
                "messages": messages,
                "inferenceConfig": {
                    "maxTokens": self.max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
            
            # Send request to Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            result = response_body['output']['message']['content'][0]['text']
            
            self.logger.info("Response generated successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise
    
    def analyze_stock_context(self,
                             query: str,
                             retrieved_context: str,
                             search_results: str,
                             temperature: float = 0.2,
                             system_prompt_override: Optional[str] = None,
                             preface_instructions: Optional[str] = None) -> str:
        """
        Analyze stock market query with retrieved context.
        
        Parameters:
        - query: User's question about stocks
        - retrieved_context: Stock data from FAISS vector store
        - search_results: Real-time data from Google search
        - temperature: Response creativity
        
        Returns:
        - Comprehensive analysis and answer
        
        How it works:
        This is the main function used by the chatbot to generate answers.
        It combines:
        1. Historical stock data (from CSV files)
        2. Real-time search results (from Google)
        3. User's question
        
        Then uses Nova Pro to generate a helpful, accurate answer.
        """
        try:
            # Create comprehensive prompt
            system_prompt = system_prompt_override or (
                """You are a helpful stock market assistant with expertise in financial analysis.
You have access to historical stock trading data and real-time search results.
Provide accurate, comprehensive answers based on the provided context.
Always cite your sources when using specific data points.
If information is not available, clearly state so."""
            )
            
            preface = (preface_instructions + "\n\n") if preface_instructions else ""

            user_prompt = f"""{preface}Question: {query}

Historical Stock Data:
{retrieved_context}

Real-time Search Results:
{search_results}

Please analyze the above information and provide a comprehensive answer that:
1. Directly addresses the user's question
2. Uses specific data points from the historical data
3. Incorporates relevant real-time information
4. Provides actionable insights when appropriate
5. Cites sources for specific claims

Answer:"""
            
            # Generate response
            return self.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature
            )
            
        except Exception as e:
            self.logger.error(f"Error in stock analysis: {str(e)}")
            return f"Error analyzing stock data: {str(e)}"
    
    def summarize_stock_data(self, stock_data: str) -> str:
        """
        Create a concise summary of stock data.
        
        Parameters:
        - stock_data: Raw stock data text
        
        Returns:
        - Concise summary
        
        Useful for condensing large amounts of stock data into
        key insights and highlights.
        """
        try:
            prompt = f"""Summarize the following stock market data into key insights:

{stock_data}

Provide:
1. Key statistics (prices, volume, trends)
2. Notable patterns or anomalies
3. Important takeaways for investors

Summary:"""
            
            return self.generate_response(prompt, temperature=0.5)
            
        except Exception as e:
            self.logger.error(f"Error summarizing data: {str(e)}")
            return f"Error: {str(e)}"
    
    def compare_stocks(self, stock1_data: str, stock2_data: str) -> str:
        """
        Compare two stocks based on their data.
        
        Parameters:
        - stock1_data: First stock's data
        - stock2_data: Second stock's data
        
        Returns:
        - Comparative analysis
        
        Useful for side-by-side stock comparisons.
        """
        try:
            prompt = f"""Compare these two stocks and provide insights:

Stock 1:
{stock1_data}

Stock 2:
{stock2_data}

Provide:
1. Key differences in performance
2. Volume and trading activity comparison
3. Price movement patterns
4. Investment implications

Comparison:"""
            
            return self.generate_response(prompt, temperature=0.6)
            
        except Exception as e:
            self.logger.error(f"Error comparing stocks: {str(e)}")
            return f"Error: {str(e)}"
    
    def explain_technical_terms(self, term: str, context: str = "") -> str:
        """
        Explain financial and technical terms.
        
        Parameters:
        - term: Technical term to explain
        - context: Additional context
        
        Returns:
        - Clear explanation
        
        Helps users understand financial jargon.
        """
        try:
            prompt = f"""Explain the following financial term in simple language:

Term: {term}
Context: {context}

Provide:
1. Simple definition
2. How it's used in stock trading
3. Example in context
4. Why it matters to investors

Explanation:"""
            
            return self.generate_response(prompt, temperature=0.5)
            
        except Exception as e:
            self.logger.error(f"Error explaining term: {str(e)}")
            return f"Error: {str(e)}"
    
    def test_connection(self) -> bool:
        """
        Test connection to AWS Bedrock.
        
        Returns:
        - True if connection successful, False otherwise
        
        Useful for verifying AWS credentials and Bedrock access.
        """
        try:
            test_prompt = "Hello, this is a test message. Please respond with 'Connection successful.'"
            response = self.generate_response(test_prompt, temperature=0.1)
            self.logger.info("Connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

