"""
Enhanced Q&A System for Financial Data Analysis
Clean, modular design with improved prompting strategies
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from pathlib import Path
from abc import ABC, abstractmethod

# Import FAISS and embedding components
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available. Install with: pip install faiss-cpu sentence-transformers")

class BaseQASystem(ABC):
    """Abstract base class for Q&A systems"""
    
    @abstractmethod
    def answer_question(self, question: str, context: List[str] = None) -> str:
        """Answer a question using available context"""
        pass
    
    @abstractmethod
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for relevant documents"""
        pass

class FinancialQASystem(BaseQASystem):
    """Enhanced Question-Answering system for financial data with improved prompting"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the enhanced Q&A system
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.index = None
        self.model = None
        self.documents = []
        self.metadata = []
        self._setup_logging()
        self._initialize_model()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        if not FAISS_AVAILABLE:
            self.logger.warning("FAISS not available. Q&A functionality will be limited.")
            return
        
        try:
            model_name = self.config.get('faiss_settings', {}).get('model_name', 'all-MiniLM-L6-v2')
            
            # Fix for PyTorch device issues on macOS MPS
            import torch
            import os
            
            # Force CPU usage to avoid MPS issues and segmentation faults
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
            os.environ['PYTORCH_DISABLE_MPS'] = '1'
            torch.set_num_threads(1)  # Limit threading to avoid conflicts
            
            # Explicitly disable MPS
            if hasattr(torch.backends, 'mps'):
                torch.backends.mps.is_available = lambda: False
            
            # Always use CPU for stability
            self.model = SentenceTransformer(model_name, device='cpu')
            
            # Ensure model is on CPU
            if hasattr(self.model, 'to'):
                self.model = self.model.to('cpu')
            
            self.logger.info(f"Initialized embedding model: {model_name} on CPU")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            self.model = None
    
    def add_documents(self, documents: List[str], metadata: List[Dict] = None):
        """
        Add documents to the knowledge base
        
        Args:
            documents: List of document texts
            metadata: List of metadata dictionaries for each document
        """
        if not self.model:
            self.logger.error("Model not initialized. Cannot add documents.")
            return
        
        if metadata is None:
            metadata = [{}] * len(documents)
        
        self.documents.extend(documents)
        self.metadata.extend(metadata)
        
        self.logger.info(f"Added {len(documents)} documents. Total: {len(self.documents)}")
    
    def add_financial_data(self, data: Dict[str, pd.DataFrame]):
        """
        Add financial data to the knowledge base
        
        Args:
            data: Dictionary mapping symbol to DataFrame
        """
        documents = []
        metadata = []
        
        for symbol, df in data.items():
            # Create summary text for each symbol
            summary = self._create_data_summary(symbol, df)
            documents.append(summary)
            metadata.append({
                'type': 'financial_data',
                'symbol': symbol,
                'data_points': len(df),
                'date_range': f"{df.index[0].date()} to {df.index[-1].date()}"
            })
        
        self.add_documents(documents, metadata)
    
    def _create_data_summary(self, symbol: str, df: pd.DataFrame) -> str:
        """Create a text summary of financial data"""
        summary = f"Financial data for {symbol}:\n"
        summary += f"Data points: {len(df)}\n"
        summary += f"Date range: {df.index[0].date()} to {df.index[-1].date()}\n"
        
        if 'Close' in df.columns:
            latest_close = df['Close'].iloc[-1]
            price_change = df['Close'].iloc[-1] - df['Close'].iloc[0]
            price_change_pct = (price_change / df['Close'].iloc[0]) * 100
            
            summary += f"Latest close price: ${latest_close:.2f}\n"
            summary += f"Total price change: ${price_change:.2f} ({price_change_pct:.2f}%)\n"
        
        if 'Volume' in df.columns:
            avg_volume = df['Volume'].mean()
            summary += f"Average volume: {avg_volume:,.0f}\n"
        
        # Add recent price action
        if len(df) >= 5:
            recent_5d = df['Close'].tail(5)
            summary += f"Recent 5-day prices: {', '.join([f'${p:.2f}' for p in recent_5d.values])}\n"
        
        return summary
    
    def build_index(self):
        """Build the FAISS index from documents"""
        if not self.model or not self.documents:
            self.logger.error("Cannot build index: model or documents not available")
            return
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(self.documents)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings.astype('float32'))
            
            self.logger.info(f"Built FAISS index with {len(self.documents)} documents")
            
        except Exception as e:
            self.logger.error(f"Failed to build index: {e}")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        if not self.index or not self.model:
            self.logger.error("Index or model not available")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    results.append({
                        'document': self.documents[idx],
                        'metadata': self.metadata[idx],
                        'score': float(score)
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def answer_question(self, question: str, context_documents: List[str] = None) -> str:
        """
        Answer a question using enhanced prompting strategies
        
        Args:
            question: User's question
            context_documents: Optional context documents to use
            
        Returns:
            Enhanced answer string
        """
        if context_documents is None:
            # Search for relevant documents
            search_results = self.search(question, k=5)
            context_documents = [result['document'] for result in search_results]
        
        if not context_documents:
            return self._get_no_context_response(question)
        
        # Analyze question type and create appropriate prompt
        question_type = self._analyze_question_type(question)
        context = self._format_context(context_documents, question_type)
        
        # Generate enhanced answer based on question type
        return self._generate_enhanced_answer(question, context, question_type)
    
    def _analyze_question_type(self, question: str) -> str:
        """Analyze the type of financial question being asked"""
        question_lower = question.lower()
        
        # Price and performance questions
        if any(word in question_lower for word in ['price', 'cost', 'value', 'worth', 'expensive', 'cheap']):
            return 'price_analysis'
        
        # Trend and movement questions
        if any(word in question_lower for word in ['trend', 'going up', 'going down', 'rising', 'falling', 'direction']):
            return 'trend_analysis'
        
        # Comparison questions
        if any(word in question_lower for word in ['compare', 'vs', 'versus', 'better', 'worse', 'difference']):
            return 'comparison'
        
        # Technical analysis questions
        if any(word in question_lower for word in ['technical', 'chart', 'indicator', 'support', 'resistance', 'rsi', 'macd']):
            return 'technical_analysis'
        
        # Fundamental analysis questions
        if any(word in question_lower for word in ['earnings', 'revenue', 'profit', 'fundamental', 'financials']):
            return 'fundamental_analysis'
        
        # Investment advice questions
        if any(word in question_lower for word in ['buy', 'sell', 'hold', 'invest', 'recommend', 'should i']):
            return 'investment_advice'
        
        # General information questions
        return 'general_info'
    
    def _format_context(self, context_documents: List[str], question_type: str) -> str:
        """Format context based on question type for better relevance"""
        if question_type == 'price_analysis':
            # Focus on price-related information
            price_context = []
            for doc in context_documents:
                if any(word in doc.lower() for word in ['price', 'close', 'open', 'high', 'low', '$']):
                    price_context.append(doc)
            return "\n\n".join(price_context[:3]) if price_context else "\n\n".join(context_documents[:3])
        
        elif question_type == 'trend_analysis':
            # Focus on trend-related information
            trend_context = []
            for doc in context_documents:
                if any(word in doc.lower() for word in ['trend', 'change', 'increase', 'decrease', '%', 'percent']):
                    trend_context.append(doc)
            return "\n\n".join(trend_context[:3]) if trend_context else "\n\n".join(context_documents[:3])
        
        elif question_type == 'technical_analysis':
            # Focus on technical indicators
            tech_context = []
            for doc in context_documents:
                if any(word in doc.lower() for word in ['technical', 'chart', 'indicator', 'moving average', 'volume']):
                    tech_context.append(doc)
            return "\n\n".join(tech_context[:3]) if tech_context else "\n\n".join(context_documents[:3])
        
        # Default: return top 3 most relevant documents
        return "\n\n".join(context_documents[:3])
    
    def _generate_enhanced_answer(self, question: str, context: str, question_type: str) -> str:
        """Generate enhanced answer using AI model with specialized prompts"""
        try:
            # Get specialized prompt for the question type
            prompt = self._get_ai_prompt(question, context, question_type)
            
            # Generate answer using AI model
            answer = self._generate_ai_answer(prompt)
            
            return answer
            
        except Exception as e:
            self.logger.error(f"Error generating AI answer: {e}")
            # Fallback to simple formatting if AI fails
            return self._generate_fallback_answer(question, context, question_type)
    
    def _get_ai_prompt(self, question: str, context: str, question_type: str) -> str:
        """Get simple AI prompt for direct Q&A"""
        
        prompt = f"""Based on the following context, answer the user's question directly and concisely.

Context:
{context}

Question: {question}

Instructions:
- Answer the question directly based on the context provided
- Be concise and to the point
- If the context doesn't contain enough information to answer, say so
- Don't add extra analysis or recommendations
- Just provide a straightforward answer

Answer:"""
        
        return prompt
    
    def _generate_ai_answer(self, prompt: str) -> str:
        """Generate answer using AI model (Bedrock Nova Pro)"""
        try:
            import boto3
            import os
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv()
            
            # Get Bedrock client with explicit credentials
            bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.config['bedrock_settings']['region'],
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            # Prepare request
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 2000,  # Increased for detailed analysis
                    "temperature": 0.1,  # More focused and direct responses
                    "topP": 0.8
                }
            }
            
            # Call Bedrock
            response = bedrock_runtime.invoke_model(
                modelId=self.config['bedrock_settings']['nova_pro_arn'],
                body=json.dumps(body),
                contentType="application/json"
            )
            
            # Extract answer
            response_body = json.loads(response['body'].read())
            answer = response_body['output']['message']['content'][0]['text']
            return answer
            
        except Exception as e:
            self.logger.error(f"AI answer generation failed: {e}")
            raise
    
    def _generate_fallback_answer(self, question: str, context: str, question_type: str) -> str:
        """Generate simple fallback answer if AI fails"""
        return f"""Based on the available data:

{context}

This information relates to your question: {question}

*Note: AI analysis is temporarily unavailable. This is the relevant context found.*"""
    
    def _generate_price_analysis_answer(self, question: str, context: str) -> str:
        """Generate price-focused analysis"""
        return f"""**Price Analysis for: {question}**

Based on the available financial data:

{context}

**Key Price Insights:**
- Current price levels and recent movements
- Price volatility and range analysis
- Support and resistance levels (if available)

*Note: This analysis is based on available data. For real-time pricing and comprehensive analysis, please consult current market data.*"""
    
    def _generate_trend_analysis_answer(self, question: str, context: str) -> str:
        """Generate trend-focused analysis"""
        return f"""**Trend Analysis for: {question}**

Based on the available data:

{context}

**Trend Insights:**
- Direction and strength of current trends
- Momentum indicators and patterns
- Historical trend context

*Note: Past performance does not guarantee future results. Consider multiple factors when analyzing trends.*"""
    
    def _generate_comparison_answer(self, question: str, context: str) -> str:
        """Generate comparison-focused analysis"""
        return f"""**Comparison Analysis for: {question}**

Based on the available data:

{context}

**Comparison Insights:**
- Relative performance metrics
- Key differences and similarities
- Risk and return characteristics

*Note: Comparisons should consider multiple factors including risk tolerance and investment objectives.*"""
    
    def _generate_technical_analysis_answer(self, question: str, context: str) -> str:
        """Generate technical analysis-focused answer"""
        return f"""**Technical Analysis for: {question}**

Based on the available data:

{context}

**Technical Insights:**
- Chart patterns and indicators
- Volume analysis and momentum
- Key technical levels

*Note: Technical analysis should be combined with fundamental analysis for comprehensive investment decisions.*"""
    
    def _generate_fundamental_analysis_answer(self, question: str, context: str) -> str:
        """Generate fundamental analysis-focused answer"""
        return f"""**Fundamental Analysis for: {question}**

Based on the available data:

{context}

**Fundamental Insights:**
- Financial performance metrics
- Business fundamentals and outlook
- Valuation considerations

*Note: Fundamental analysis provides insight into the underlying business value and long-term prospects.*"""
    
    def _generate_investment_advice_answer(self, question: str, context: str) -> str:
        """Generate investment advice-focused answer with appropriate disclaimers"""
        return f"""**Investment Analysis for: {question}**

Based on the available data:

{context}

**Investment Considerations:**
- Risk and return profile
- Market conditions and outlook
- Portfolio fit and diversification

**Important Disclaimer:** This analysis is for informational purposes only and should not be considered as financial advice. Always consult with a qualified financial advisor before making investment decisions. Past performance does not guarantee future results."""
    
    def _generate_general_answer(self, question: str, context: str) -> str:
        """Generate general information answer"""
        return f"""**Answer to: {question}**

Based on the available financial data:

{context}

**Summary:** The information above provides relevant context for your question. For more specific analysis or real-time data, please ensure you have the most current information available."""
    
    def _get_no_context_response(self, question: str) -> str:
        """Generate appropriate response when no context is available"""
        return f"""I don't have enough information to provide a comprehensive answer to your question about "{question}".

**To get better answers, please:**
1. Upload relevant financial documents, charts, or videos
2. Fetch current market data using the Yahoo Finance integration
3. Create an index of your data sources
4. Ensure your question relates to the data you've provided

**Available data types I can analyze:**
- Stock and ETF price data
- Financial charts and images
- Earnings reports and financial documents
- Market analysis videos
- YouTube financial content"""
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index"""
        return {
            'total_documents': len(self.documents),
            'index_built': self.index is not None,
            'model_available': self.model is not None,
            'faiss_available': FAISS_AVAILABLE
        }

# Backward compatibility alias
QASystem = FinancialQASystem
