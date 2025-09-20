"""
Sample Questions Generator
Generates relevant sample questions based on knowledge base content using LLM
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import boto3
import json

class SampleQuestionsGenerator:
    """Generate sample questions from knowledge base using LLM"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the sample questions generator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize Bedrock client
        try:
            bedrock_settings = self.config.get('bedrock_settings', {})
            region = bedrock_settings.get('region', self.config.get('aws_region', 'us-east-1'))
            
            # Load environment variables for credentials
            from dotenv import load_dotenv
            load_dotenv()
            
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.bedrock_available = True
            self.logger.info(f"Bedrock client initialized for region: {region}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Bedrock client: {e}")
            self.bedrock_available = False
    
    def generate_questions_from_content(self, 
                                      market_data: Dict[str, Any] = None,
                                      processed_files: List[Dict[str, Any]] = None,
                                      youtube_analyses: List[Dict[str, Any]] = None) -> List[str]:
        """
        Generate sample questions using LLM based on available content
        
        Args:
            market_data: Yahoo Finance data
            processed_files: Processed media files
            youtube_analyses: YouTube video analyses
            
        Returns:
            List of sample questions
        """
        if not self.bedrock_available:
            self.logger.error("Bedrock not available, using fallback questions")
            return self._generate_fallback_questions(market_data, youtube_analyses)
        
        try:
            # Prepare raw content for LLM (no summary)
            raw_content = self._prepare_raw_content(
                market_data, processed_files, youtube_analyses
            )
            
            # Print the raw content being passed to AI
            print("\n" + "="*80)
            print("RAW CONTENT BEING PASSED TO AI:")
            print("="*80)
            print(raw_content)
            print("="*80)
            print("END OF RAW CONTENT")
            print("="*80 + "\n")
            
            # Generate questions using LLM
            questions = self._generate_with_llm(raw_content)
            
            if questions:
                self.logger.info(f"Generated {len(questions)} sample questions using LLM")
                return questions
            else:
                self.logger.warning("LLM failed to generate questions, using fallback")
                return self._generate_fallback_questions(market_data, youtube_analyses)
                
        except Exception as e:
            self.logger.error(f"Error generating questions with LLM: {e}")
            return self._generate_fallback_questions(market_data, youtube_analyses)
    
    def _prepare_content_summary(self, 
                                market_data: Dict[str, Any] = None,
                                processed_files: List[Dict[str, Any]] = None,
                                youtube_analyses: List[Dict[str, Any]] = None) -> str:
        """Prepare a detailed summary of actual available content for LLM"""
        summary_parts = []
        
        # Add detailed market data summary
        if market_data:
            summary_parts.append("=== STOCK MARKET DATA ===")
            for symbol, data in list(market_data.items())[:5]:  # Limit to first 5 symbols
                if hasattr(data, 'columns') and hasattr(data, 'index'):
                    # This is a DataFrame
                    date_range = f"{data.index[0].date()} to {data.index[-1].date()}"
                    columns = list(data.columns)
                    summary_parts.append(f"• {symbol}: {len(data)} days of data ({date_range})")
                    summary_parts.append(f"  Columns: {', '.join(columns)}")
                    summary_parts.append(f"  Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
                else:
                    summary_parts.append(f"• {symbol}: {type(data).__name__} data")
            
            if len(market_data) > 5:
                summary_parts.append(f"... and {len(market_data) - 5} more symbols")
        
        # Add detailed YouTube analyses summary
        if youtube_analyses:
            summary_parts.append("\n=== YOUTUBE VIDEO ANALYSES ===")
            for analysis in youtube_analyses[:3]:
                title = analysis.get('title', 'Unknown')
                summary = analysis.get('summary', 'No summary available')
                summary_parts.append(f"• Video: {title}")
                summary_parts.append(f"  Summary: {summary[:200]}...")
        
        # Add detailed processed files summary
        if processed_files:
            summary_parts.append("\n=== PROCESSED FILES ===")
            for file_info in processed_files[:3]:
                file_name = file_info.get('file_name', 'Unknown')
                file_type = file_info.get('type', 'unknown')
                content = file_info.get('content', 'No content available')
                summary_parts.append(f"• File: {file_name} ({file_type})")
                summary_parts.append(f"  Content preview: {content[:200]}...")
        
        return "\n".join(summary_parts)
    
    def _prepare_raw_content(self, 
                            market_data: Dict[str, Any] = None,
                            processed_files: List[Dict[str, Any]] = None,
                            youtube_analyses: List[Dict[str, Any]] = None) -> str:
        """Prepare raw content data for LLM (no summary)"""
        content_parts = []
        
        # Add raw market data (limited size)
        if market_data:
            content_parts.append("=== STOCK MARKET DATA ===")
            for symbol, data in list(market_data.items())[:2]:  # Limit to first 2 symbols
                content_parts.append(f"\n--- {symbol} DATA ---")
                if hasattr(data, 'columns') and hasattr(data, 'index'):
                    # This is a DataFrame - show actual data (limited)
                    content_parts.append(f"Date range: {data.index[0].date()} to {data.index[-1].date()}")
                    content_parts.append(f"Columns: {', '.join(data.columns)}")
                    content_parts.append("Recent data (last 3 rows):")
                    content_parts.append(str(data.tail(3)))  # Show last 3 rows only
                else:
                    # This is raw text data (limited)
                    content_parts.append(str(data)[:500])  # Show first 500 chars only
        
        # Add raw YouTube analyses (limited size)
        if youtube_analyses:
            content_parts.append("\n=== YOUTUBE VIDEO ANALYSES ===")
            for analysis in youtube_analyses[:1]:  # Limit to first 1 video
                title = analysis.get('title', 'Unknown')
                summary = analysis.get('summary', 'No summary available')
                content_parts.append(f"\n--- Video: {title} ---")
                content_parts.append(summary[:1000])  # Show first 1000 chars only
        
        # Add raw processed files (limited size)
        if processed_files:
            content_parts.append("\n=== PROCESSED FILES ===")
            for file_info in processed_files[:1]:  # Limit to first 1 file
                file_name = file_info.get('file_name', 'Unknown')
                content = file_info.get('content', 'No content available')
                content_parts.append(f"\n--- File: {file_name} ---")
                content_parts.append(content[:1000])  # Show first 1000 chars only
        
        return "\n".join(content_parts)
    
    def _generate_with_llm(self, raw_content: str) -> List[str]:
        """Generate questions using LLM"""
        try:
            prompt = f"""
You are a financial AI assistant. Based on the EXACT raw data available in the knowledge base below, generate 15-20 relevant sample questions that users can ask about this specific data.

IMPORTANT: Only generate questions about data that is ACTUALLY available in the raw content below. Do not assume data exists that is not explicitly shown.

Raw Knowledge Base Data:
{raw_content}

Generate questions that are:
1. Based ONLY on the actual raw data shown above
2. Simple questions that can be answered with the data available


Example format:
["What is the current price of AAPL?", "How has the technology sector performed?", ...]
"""

            # Use Nova Pro for question generation
            bedrock_settings = self.config.get('bedrock_settings', {})
            model_id = bedrock_settings.get('nova_pro_arn', 'arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0')
            
            max_tokens = bedrock_settings.get('max_tokens', 2000)
            
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"text": prompt}
                            ]
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": max_tokens,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                }),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['output']['message']['content'][0]['text']
            
            # Print the AI response for debugging
            print(f"\n🤖 AI Response: {content[:500]}...")
            
            # Try to parse JSON response with better error handling
            try:
                questions = json.loads(content)
            except json.JSONDecodeError as json_err:
                self.logger.error(f"JSON parsing error: {json_err}")
                self.logger.error(f"Raw AI response: {content}")
                
                # Try to extract questions from text if JSON fails
                questions = self._extract_questions_from_text(content)
            
            if isinstance(questions, list) and len(questions) > 0:
                return questions[:20]  # Limit to 20 questions
            else:
                self.logger.warning("No valid questions found in AI response")
                return []
                
        except Exception as e:
            self.logger.error(f"Error in LLM question generation: {e}")
            return []
    
    def _extract_questions_from_text(self, text: str) -> List[str]:
        """Extract questions from text when JSON parsing fails"""
        import re
        
        # Try to find questions in various formats
        questions = []
        
        # Look for numbered questions (1. What is...)
        numbered_pattern = r'\d+\.\s*([^?\n]*\?)'
        numbered_matches = re.findall(numbered_pattern, text)
        questions.extend([q.strip() for q in numbered_matches])
        
        # Look for bullet point questions (- What is...)
        bullet_pattern = r'[-*]\s*([^?\n]*\?)'
        bullet_matches = re.findall(bullet_pattern, text)
        questions.extend([q.strip() for q in bullet_matches])
        
        # Look for questions in quotes
        quote_pattern = r'"([^"]*\?)"'
        quote_matches = re.findall(quote_pattern, text)
        questions.extend([q.strip() for q in quote_matches])
        
        # Look for any line ending with ?
        question_pattern = r'([^?\n]*\?)'
        question_matches = re.findall(question_pattern, text)
        questions.extend([q.strip() for q in question_matches if len(q.strip()) > 10])
        
        # Remove duplicates and clean up
        unique_questions = list(dict.fromkeys(questions))  # Preserve order, remove duplicates
        clean_questions = [q for q in unique_questions if len(q) > 10 and q.endswith('?')]
        
        self.logger.info(f"Extracted {len(clean_questions)} questions from text")
        return clean_questions[:20]  # Limit to 20 questions
    
    def _generate_fallback_questions(self, 
                                   market_data: Dict[str, Any] = None,
                                   youtube_analyses: List[Dict[str, Any]] = None) -> List[str]:
        """Generate fallback questions when LLM is not available"""
        questions = []
        
        # Generate questions based on available symbols
        if market_data:
            symbols = list(market_data.keys())[:5]
            for symbol in symbols:
                questions.extend([
                    f"What is the current stock price of {symbol}?",
                    f"What is the trend for {symbol}?",
                    f"How has {symbol} performed recently?",
                    f"What are the key financial metrics for {symbol}?"
                ])
        
        # Generate questions based on YouTube analyses
        if youtube_analyses:
            for analysis in youtube_analyses[:2]:
                title = analysis.get('title', 'this video')
                questions.extend([
                    f"What are the key insights from {title}?",
                    f"What financial analysis is provided in {title}?"
                ])
        
        # Add general financial questions
        questions.extend([
            "What are the top performing stocks?",
            "How do different ETFs compare?",
            "What is the market sentiment?",
            "What are the latest earnings reports?",
            "What are the key market trends?",
            "How is the technology sector performing?",
            "What are the best investment opportunities?",
            "What are the risks in the current market?",
            "How do different sectors compare?",
            "What are the dividend yields?"
        ])
        
        # Remove duplicates and limit to 20
        unique_questions = list(dict.fromkeys(questions))
        return unique_questions[:20]
    
    def save_questions_to_file(self, questions: List[str], filename: str = "sample_questions.txt") -> str:
        """
        Save sample questions to a text file
        
        Args:
            questions: List of sample questions
            filename: Name of the file to save
            
        Returns:
            Path to the saved file
        """
        try:
            filepath = os.path.join(os.getcwd(), filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("SAMPLE QUESTIONS FOR STOCK BOT\n")
                f.write("=" * 50 + "\n\n")
                f.write("Based on your knowledge base, here are sample questions you can ask:\n\n")
                
                for i, question in enumerate(questions, 1):
                    f.write(f"{i:2d}. {question}\n")
                
                f.write(f"\nTotal: {len(questions)} sample questions\n")
                f.write("\nGenerated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
                f.write("Generated using: AI-powered question generation\n")
            
            self.logger.info(f"Sample questions saved to: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving sample questions: {str(e)}")
            return ""
