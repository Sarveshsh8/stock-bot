import json
import pandas as pd
import numpy as np
import os
import sys
from typing import List, Dict, Any, Optional
import faiss
from sentence_transformers import SentenceTransformer
import pickle

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class FinancialDataIndexer:
    """Build FAISS index from Excel trading data and JSON analysis for Q&A operations"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the indexer
        
        Args:
            model_name: Sentence transformer model for embeddings
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.document_metadata = []
        
    def load_sentence_transformer(self):
        """Load the sentence transformer model"""
        try:
            print(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to default model...")
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Default model loaded successfully")
            except Exception as e2:
                print(f"Failed to load any model: {e2}")
                return False
        return True
    
    def read_excel_data(self, excel_path: str, sheet_name: str = 'Historical_Data') -> pd.DataFrame:
        """Read Excel file and return DataFrame"""
        try:
            print(f"Reading Excel file: {excel_path}")
            print(f"Sheet name: {sheet_name}")
            
            # Read the Excel file
            df = pd.read_excel(excel_path, sheet_name=sheet_name, index_col=0)
            
            print(f"Excel data loaded successfully")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print(f"Date range: {df.index[0]} to {df.index[-1]}")
            
            return df
            
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return None
    
    def read_json_analysis(self, json_path: str) -> Dict[str, Any]:
        """Read JSON analysis file and return data"""
        try:
            print(f"Reading JSON analysis file: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"JSON analysis loaded successfully")
            print(f"Keys: {list(data.keys())}")
            
            return data
            
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return None
    
    def prepare_excel_text_chunks(self, df: pd.DataFrame, chunk_size: int = 1000) -> List[str]:
        """Convert Excel data to text chunks for indexing"""
        chunks = []
        
        try:
            print("Preparing Excel data chunks...")
            
            # Create summary statistics
            summary_stats = f"""
            Apple Trading Data Summary:
            - Date Range: {df.index[0]} to {df.index[-1]}
            - Total Trading Days: {len(df)}
            - Current Price: ${df['Close'].iloc[-1]:.2f}
            - Price Range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}
            - Average Volume: {df['Volume'].mean():,.0f}
            - Total Volume: {df['Volume'].sum():,.0f}
            """
            chunks.append(summary_stats)
            
            # Create technical analysis chunks
            if 'SMA_20' in df.columns and 'SMA_50' in df.columns:
                tech_analysis = f"""
                Technical Analysis Summary:
                - 20-day SMA: ${df['SMA_20'].iloc[-1]:.2f}
                - 50-day SMA: ${df['SMA_50'].iloc[-1]:.2f}
                - Current Price vs 20-day SMA: {'Above' if df['Close'].iloc[-1] > df['SMA_20'].iloc[-1] else 'Below'}
                - Current Price vs 50-day SMA: {'Above' if df['Close'].iloc[-1] > df['SMA_50'].iloc[-1] else 'Below'}
                """
                chunks.append(tech_analysis)
            
            if 'RSI' in df.columns:
                rsi_analysis = f"""
                RSI Analysis:
                - Current RSI: {df['RSI'].iloc[-1]:.2f}
                - RSI Status: {'Overbought' if df['RSI'].iloc[-1] > 70 else 'Oversold' if df['RSI'].iloc[-1] < 30 else 'Neutral'}
                - RSI Range: {df['RSI'].min():.2f} to {df['RSI'].max():.2f}
                """
                chunks.append(rsi_analysis)
            
            # Create recent data chunks (last 10 days)
            recent_data = df.tail(10)
            recent_chunk = f"""
            Recent Trading Data (Last 10 Days):
            {recent_data[['Open', 'High', 'Low', 'Close', 'Volume']].to_string()}
            """
            chunks.append(recent_chunk)
            
            # Create price movement analysis
            price_changes = df['Close'].pct_change().dropna()
            price_analysis = f"""
            Price Movement Analysis:
            - Average Daily Return: {price_changes.mean()*100:.2f}%
            - Volatility (Std Dev): {price_changes.std()*100:.2f}%
            - Best Day: {price_changes.max()*100:.2f}%
            - Worst Day: {price_changes.min()*100:.2f}%
            - Positive Days: {(price_changes > 0).sum()} out of {len(price_changes)}
            """
            chunks.append(price_analysis)
            
            print(f"Created {len(chunks)} Excel data chunks")
            return chunks
            
        except Exception as e:
            print(f"Error preparing Excel chunks: {e}")
            return []
    
    def prepare_json_analysis_chunks(self, json_data: Dict[str, Any]) -> List[str]:
        """Convert JSON analysis to text chunks for indexing"""
        chunks = []
        
        try:
            print("Preparing JSON analysis chunks...")
            
            # Extract detailed results
            if 'detailed_results' in json_data:
                for file_key, file_data in json_data['detailed_results'].items():
                    if 'analysis' in file_data:
                        analysis_text = file_data['analysis']
                        chunk = f"""
                        Analysis for {file_key}:
                        {analysis_text}
                        """
                        chunks.append(chunk)
            
            # Extract category summaries
            if 'category_summaries' in json_data:
                for category, summary_data in json_data['category_summaries'].items():
                    summary_chunk = f"""
                        {category.upper()} Analysis Summary:
                        Summary: {summary_data.get('summary', 'No summary available')}
                        Key Findings: {summary_data.get('key_findings', 'No key findings available')}
                        """
                    chunks.append(summary_chunk)
            
            # Extract financial recommendations
            if 'financial_recommendations' in json_data:
                recommendations = json_data['financial_recommendations']
                rec_chunk = f"""
                Financial Recommendations:
                {chr(10).join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])}
                """
                chunks.append(rec_chunk)
            
            # Extract overall insights
            if 'overall_insights' in json_data:
                insights = json_data['overall_insights']
                insights_chunk = f"""
                Overall Analysis Insights:
                - Total Files Analyzed: {insights.get('total_files', 'Unknown')}
                - Success Rate: {insights.get('success_rate', 'Unknown')}
                - Analysis Coverage: {insights.get('analysis_coverage', 'Unknown')}
                """
                chunks.append(insights_chunk)
            
            print(f"Created {len(chunks)} JSON analysis chunks")
            return chunks
            
        except Exception as e:
            print(f"Error preparing JSON chunks: {e}")
            return []
    
    def build_faiss_index(self, excel_path: str, json_path: str, 
                          sheet_name: str = 'Historical_Data') -> bool:
        """Build FAISS index from Excel and JSON data"""
        try:
            print("Building FAISS index...")
            
            # Load sentence transformer
            if not self.load_sentence_transformer():
                return False
            
            # Read data sources
            excel_df = self.read_excel_data(excel_path, sheet_name)
            json_data = self.read_json_analysis(json_path)
            
            if excel_df is None or json_data is None:
                print("Failed to load data sources")
                return False
            
            # Prepare text chunks
            excel_chunks = self.prepare_excel_text_chunks(excel_df)
            json_chunks = self.prepare_json_analysis_chunks(json_data)
            
            all_chunks = excel_chunks + json_chunks
            
            if not all_chunks:
                print("No text chunks created")
                return False
            
            print(f"Total chunks to index: {len(all_chunks)}")
            
            # Create embeddings
            print("Creating embeddings...")
            embeddings = self.model.encode(all_chunks, show_progress_bar=True)
            
            # Initialize FAISS index
            dimension = embeddings.shape[1]
            print(f"Embedding dimension: {dimension}")
            
            # Use IndexFlatIP for inner product similarity
            self.index = faiss.IndexFlatIP(dimension)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add vectors to index
            self.index.add(embeddings.astype('float32'))
            
            # Store documents and metadata
            self.documents = all_chunks
            self.document_metadata = [
                {
                    'source': 'excel' if i < len(excel_chunks) else 'json_analysis',
                    'chunk_index': i,
                    'content_preview': chunk[:200] + '...' if len(chunk) > 200 else chunk
                }
                for i, chunk in enumerate(all_chunks)
            ]
            
            print(f"FAISS index built successfully with {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            print(f"Error building FAISS index: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the index for relevant documents"""
        try:
            if self.index is None or self.model is None:
                print("Index or model not initialized")
                return []
            
            # Encode query
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            # Prepare results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):
                    result = {
                        'rank': i + 1,
                        'score': float(score),
                        'content': self.documents[idx],
                        'metadata': self.document_metadata[idx] if idx < len(self.document_metadata) else {}
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error searching index: {e}")
            return []
    
    def answer_question(self, question: str, top_k: int = 3) -> str:
        """Answer a question using the indexed data"""
        try:
            print(f"Question: {question}")
            
            # Search for relevant documents
            results = self.search(question, top_k)
            
            if not results:
                return "I couldn't find relevant information to answer your question."
            
            # Prepare answer
            answer_parts = []
            answer_parts.append(f"Based on the available data, here's what I found:")
            
            for i, result in enumerate(results):
                score = result['score']
                content = result['content'].strip()
                source = result['metadata'].get('source', 'unknown')
                
                answer_parts.append(f"\n{i+1}. [Relevance: {score:.3f}, Source: {source}]")
                answer_parts.append(content[:500] + "..." if len(content) > 500 else content)
            
            # Add summary
            answer_parts.append(f"\n\nI found {len(results)} relevant pieces of information. The most relevant source has a similarity score of {results[0]['score']:.3f}.")
            
            return "\n".join(answer_parts)
            
        except Exception as e:
            print(f"Error answering question: {e}")
            return f"Sorry, I encountered an error while processing your question: {str(e)}"
    
    def save_index(self, index_path: str, docs_path: str):
        """Save the FAISS index and documents"""
        try:
            print(f"Saving FAISS index to: {index_path}")
            faiss.write_index(self.index, index_path)
            
            print(f"Saving documents to: {docs_path}")
            with open(docs_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadata': self.document_metadata
                }, f)
            
            print("Index and documents saved successfully")
            
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def load_index(self, index_path: str, docs_path: str) -> bool:
        """Load a saved FAISS index and documents"""
        try:
            print(f"Loading FAISS index from: {index_path}")
            self.index = faiss.read_index(index_path)
            
            print(f"Loading documents from: {docs_path}")
            with open(docs_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.document_metadata = data['metadata']
            
            print("Index and documents loaded successfully")
            return True
            
        except Exception as e:
            print(f"Error loading index: {e}")
            return False

def main():
    """Main function to build index and demonstrate Q&A"""
    
    # File paths
    excel_path = "data/Apple_Trading_Data_20250902_104928.xlsx"
    json_path = "financial_analysis_20250902_122854.json"
    
    # Initialize indexer
    indexer = FinancialDataIndexer()
    
    # Build index
    print("=" * 60)
    print("BUILDING FAISS INDEX FOR FINANCIAL Q&A")
    print("=" * 60)
    
    if indexer.build_faiss_index(excel_path, json_path):
        print("\nIndex built successfully!")
        
        # Save index for future use
        indexer.save_index("financial_data.index", "financial_documents.pkl")
        
        # Interactive Q&A
        print("\n" + "=" * 60)
        print("INTERACTIVE FINANCIAL Q&A")
        print("=" * 60)
        print("Ask questions about Apple trading data and analysis!")
        print("Type 'quit' to exit")
        
        while True:
            try:
                question = input("\nYour question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if question:
                    answer = indexer.answer_question(question)
                    print(f"\nAnswer:\n{answer}")
                else:
                    print("Please enter a question.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    else:
        print("Failed to build index")

if __name__ == "__main__":
    main()
