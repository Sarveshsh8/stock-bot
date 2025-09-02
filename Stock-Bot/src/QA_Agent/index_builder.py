#!/usr/bin/env python3
"""
Index Builder: Build FAISS index from loaded data
"""

import json
import pandas as pd
import numpy as np
import os
import sys
import pickle
from typing import List, Dict, Any
import faiss
from sentence_transformers import SentenceTransformer

class FAISSIndexBuilder:
    """Build FAISS index from Excel and JSON data"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.document_metadata = []
        self.excel_data = None
        self.json_data = None
        
    def load_step1_data(self) -> bool:
        """Load data from Step 1"""
        try:
            print("Loading data from Step 1...")
            
            # Load extracted values
            if not os.path.exists('step1_extracted_values.pkl'):
                print("Error: step1_extracted_values.pkl not found. Please run Step 1 first.")
                return False
            
            with open('step1_extracted_values.pkl', 'rb') as f:
                extracted_values = pickle.load(f)
            
            print("Step 1 data loaded successfully!")
            
            # Load original data files
            excel_path = "data/Apple_Trading_Data_20250902_104928.xlsx"
            json_path = "financial_analysis_20250902_122854.json"
            
            # Load Excel data
            self.excel_data = pd.read_excel(excel_path, sheet_name='Historical_Data', index_col=0)
            print(f"Excel data loaded: {self.excel_data.shape}")
            
            # Load JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
            print(f"JSON data loaded with keys: {list(self.json_data.keys())}")
            
            return True
            
        except Exception as e:
            print(f"Error loading Step 1 data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_sentence_transformer(self) -> bool:
        """Load the sentence transformer model"""
        try:
            print(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print("Model loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to default model...")
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Default model loaded successfully")
                return True
            except Exception as e2:
                print(f"Failed to load any model: {e2}")
                return False
    
    def create_excel_chunks(self) -> List[str]:
        """Create text chunks from Excel data"""
        chunks = []
        
        try:
            print("Creating Excel data chunks...")
            
            # Summary statistics
            summary = f"""
            Apple Trading Data Summary:
            - Date Range: {self.excel_data.index[0]} to {self.excel_data.index[-1]}
            - Total Trading Days: {len(self.excel_data)}
            - Current Price: ${self.excel_data['Close'].iloc[-1]:.2f}
            - Price Range: ${self.excel_data['Low'].min():.2f} - ${self.excel_data['High'].max():.2f}
            - Average Volume: {self.excel_data['Volume'].mean():,.0f}
            """
            chunks.append(summary)
            
            # Technical indicators
            if 'SMA_20' in self.excel_data.columns:
                tech_analysis = f"""
                Technical Analysis:
                - 20-day SMA: ${self.excel_data['SMA_20'].iloc[-1]:.2f}
                - 50-day SMA: ${self.excel_data['SMA_50'].iloc[-1]:.2f}
                - Current Price vs 20-day SMA: {'Above' if self.excel_data['Close'].iloc[-1] > self.excel_data['SMA_20'].iloc[-1] else 'Below'}
                - Current Price vs 50-day SMA: {'Above' if self.excel_data['Close'].iloc[-1] > self.excel_data['SMA_50'].iloc[-1] else 'Below'}
                """
                chunks.append(tech_analysis)
            
            if 'RSI' in self.excel_data.columns:
                rsi_info = f"""
                RSI Analysis:
                - Current RSI: {self.excel_data['RSI'].iloc[-1]:.2f}
                - RSI Status: {'Overbought' if self.excel_data['RSI'].iloc[-1] > 70 else 'Oversold' if self.excel_data['RSI'].iloc[-1] < 30 else 'Neutral'}
                - RSI Range: {self.excel_data['RSI'].min():.2f} to {self.excel_data['RSI'].max():.2f}
                """
                chunks.append(rsi_info)
            
            # Recent data (last 5 days)
            recent_data = self.excel_data.tail(5)
            recent_chunk = f"""
            Recent Trading Data (Last 5 Days):
            {recent_data[['Open', 'High', 'Low', 'Close', 'Volume']].to_string()}
            """
            chunks.append(recent_chunk)
            
            # Price movement analysis
            price_changes = self.excel_data['Close'].pct_change().dropna()
            price_analysis = f"""
            Price Movement Analysis:
            - Average Daily Return: {price_changes.mean()*100:.2f}%
            - Volatility: {price_changes.std()*100:.2f}%
            - Best Day: {price_changes.max()*100:.2f}%
            - Worst Day: {price_changes.min()*100:.2f}%
            """
            chunks.append(price_analysis)
            
            print(f"Created {len(chunks)} Excel chunks")
            return chunks
            
        except Exception as e:
            print(f"Error creating Excel chunks: {e}")
            return []
    
    def create_json_chunks(self) -> List[str]:
        """Create text chunks from JSON analysis"""
        chunks = []
        
        try:
            print("Creating JSON analysis chunks...")
            
            # Detailed results
            if 'detailed_results' in self.json_data:
                for file_key, file_data in self.json_data['detailed_results'].items():
                    if 'analysis' in file_data:
                        chunk = f"""
                        Analysis for {file_key}:
                        {file_data['analysis']}
                        """
                        chunks.append(chunk)
            
            # Category summaries
            if 'category_summaries' in self.json_data:
                for category, summary_data in self.json_data['category_summaries'].items():
                    chunk = f"""
                    {category.upper()} Analysis:
                    Summary: {summary_data.get('summary', 'No summary')}
                    Key Findings: {summary_data.get('key_findings', 'No findings')}
                    """
                    chunks.append(chunk)
            
            # Financial recommendations
            if 'financial_recommendations' in self.json_data:
                recommendations = self.json_data['financial_recommendations']
                chunk = f"""
                Financial Recommendations:
                {chr(10).join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])}
                """
                chunks.append(chunk)
            
            # Overall insights
            if 'overall_insights' in self.json_data:
                insights = self.json_data['overall_insights']
                chunk = f"""
                Overall Insights:
                - Total Files: {insights.get('total_files', 'Unknown')}
                - Success Rate: {insights.get('success_rate', 'Unknown')}
                - Coverage: {insights.get('analysis_coverage', 'Unknown')}
                """
                chunks.append(chunk)
            
            print(f"Created {len(chunks)} JSON chunks")
            return chunks
            
        except Exception as e:
            print(f"Error creating JSON chunks: {e}")
            return []
    
    def build_index(self) -> bool:
        """Build the FAISS index"""
        try:
            print("Building FAISS index...")
            
            # Load model
            if not self.load_sentence_transformer():
                return False
            
            # Create chunks
            excel_chunks = self.create_excel_chunks()
            json_chunks = self.create_json_chunks()
            
            all_chunks = excel_chunks + json_chunks
            
            if not all_chunks:
                print("No chunks created")
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
            print(f"Error building index: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
    
    def print_index_info(self):
        """Print information about the built index"""
        print("\n" + "=" * 60)
        print("FAISS INDEX INFORMATION")
        print("=" * 60)
        print(f"Total vectors: {self.index.ntotal}")
        print(f"Dimension: {self.index.d}")
        print(f"Total documents: {len(self.documents)}")
        print(f"Excel chunks: {len([d for d in self.document_metadata if d['source'] == 'excel'])}")
        print(f"JSON chunks: {len([d for d in self.document_metadata if d['source'] == 'json_analysis'])}")
        print("=" * 60)

def main():
    """Main function to build FAISS index"""
    
    print("=" * 60)
    print("STEP 2: BUILDING FAISS INDEX")
    print("=" * 60)
    
    # Initialize builder
    builder = FAISSIndexBuilder()
    
    # Load Step 1 data
    if not builder.load_step1_data():
        print("Failed to load Step 1 data. Please run Step 1 first.")
        return
    
    # Build index
    if builder.build_index():
        print("\n✅ FAISS index built successfully!")
        
        # Print index information
        builder.print_index_info()
        
        # Save index
        builder.save_index("financial_data.index", "financial_documents.pkl")
        
        print("\nIndex saved successfully!")
        print("Ready for Step 3: Loading index and querying")
        
    else:
        print("\n❌ Failed to build FAISS index")

if __name__ == "__main__":
    main()
