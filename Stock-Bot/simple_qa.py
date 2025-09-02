#!/usr/bin/env python3
"""
Simple Q&A script for financial data using pre-built FAISS index
"""

import os
import sys
import json
import pandas as pd
from typing import List, Dict, Any

class SimpleFinancialQA:
    """Simple Q&A system for financial data without FAISS"""
    
    def __init__(self, excel_path: str, json_path: str):
        """
        Initialize the Q&A system
        
        Args:
            excel_path: Path to Excel file with trading data
            json_path: Path to JSON file with analysis results
        """
        self.excel_path = excel_path
        self.json_path = json_path
        self.excel_data = None
        self.json_data = None
        self.load_data()
    
    def load_data(self):
        """Load Excel and JSON data"""
        try:
            # Load Excel data
            if os.path.exists(self.excel_path):
                print(f"Loading Excel data from: {self.excel_path}")
                self.excel_data = pd.read_excel(self.excel_path, sheet_name='Historical_Data', index_col=0)
                print(f"Excel data loaded: {self.excel_data.shape}")
            else:
                print(f"Excel file not found: {self.excel_path}")
            
            # Load JSON data
            if os.path.exists(self.json_path):
                print(f"Loading JSON analysis from: {self.json_path}")
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.json_data = json.load(f)
                print(f"JSON data loaded with keys: {list(self.json_data.keys())}")
            else:
                print(f"JSON file not found: {self.json_path}")
                
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def search_excel_data(self, query: str) -> List[str]:
        """Search Excel data for relevant information"""
        if self.excel_data is None:
            return ["Excel data not available"]
        
        results = []
        query_lower = query.lower()
        
        try:
            # Search in column names
            matching_columns = [col for col in self.excel_data.columns if query_lower in col.lower()]
            if matching_columns:
                results.append(f"Found matching columns: {', '.join(matching_columns)}")
            
            # Search for specific data patterns
            if 'price' in query_lower or 'close' in query_lower:
                current_price = self.excel_data['Close'].iloc[-1]
                price_change = self.excel_data['Close'].pct_change().iloc[-1] * 100
                results.append(f"Current closing price: ${current_price:.2f}")
                results.append(f"Latest price change: {price_change:+.2f}%")
            
            if 'volume' in query_lower:
                current_volume = self.excel_data['Volume'].iloc[-1]
                avg_volume = self.excel_data['Volume'].mean()
                results.append(f"Current volume: {current_volume:,.0f}")
                results.append(f"Average volume: {avg_volume:,.0f}")
            
            if 'technical' in query_lower or 'sma' in query_lower or 'rsi' in query_lower:
                if 'SMA_20' in self.excel_data.columns:
                    sma_20 = self.excel_data['SMA_20'].iloc[-1]
                    results.append(f"20-day SMA: ${sma_20:.2f}")
                if 'SMA_50' in self.excel_data.columns:
                    sma_50 = self.excel_data['SMA_50'].iloc[-1]
                    results.append(f"50-day SMA: ${sma_50:.2f}")
                if 'RSI' in self.excel_data.columns:
                    rsi = self.excel_data['RSI'].iloc[-1]
                    status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                    results.append(f"Current RSI: {rsi:.2f} ({status})")
            
            if 'summary' in query_lower or 'overview' in query_lower:
                total_days = len(self.excel_data)
                date_range = f"{self.excel_data.index[0]} to {self.excel_data.index[-1]}"
                price_range = f"${self.excel_data['Low'].min():.2f} - ${self.excel_data['High'].max():.2f}"
                results.append(f"Trading summary: {total_days} days from {date_range}")
                results.append(f"Price range: {price_range}")
            
            if not results:
                results.append("No specific information found in Excel data for your query.")
                
        except Exception as e:
            results.append(f"Error searching Excel data: {e}")
        
        return results
    
    def search_json_analysis(self, query: str) -> List[str]:
        """Search JSON analysis for relevant information"""
        if self.json_data is None:
            return ["JSON analysis not available"]
        
        results = []
        query_lower = query.lower()
        
        try:
            # Search in detailed results
            if 'detailed_results' in self.json_data:
                for file_key, file_data in self.json_data['detailed_results'].items():
                    if 'analysis' in file_data:
                        analysis = file_data['analysis'].lower()
                        if any(word in analysis for word in query_lower.split()):
                            results.append(f"Found relevant analysis in {file_key}")
                            # Extract relevant sentences
                            sentences = file_data['analysis'].split('.')
                            relevant_sentences = [s.strip() for s in sentences if any(word in s.lower() for word in query_lower.split())]
                            if relevant_sentences:
                                results.extend(relevant_sentences[:2])  # Limit to 2 sentences
            
            # Search in category summaries
            if 'category_summaries' in self.json_data:
                for category, summary_data in self.json_data['category_summaries'].items():
                    summary = summary_data.get('summary', '').lower()
                    findings = summary_data.get('key_findings', '').lower()
                    if any(word in summary or word in findings for word in query_lower.split()):
                        results.append(f"Found relevant {category} analysis:")
                        results.append(f"  Summary: {summary_data.get('summary', 'No summary')}")
                        results.append(f"  Key findings: {summary_data.get('key_findings', 'No findings')}")
            
            # Search in financial recommendations
            if 'financial_recommendations' in self.json_data and 'recommend' in query_lower:
                recommendations = self.json_data['financial_recommendations']
                results.append("Financial recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):  # Limit to 3
                    results.append(f"  {i}. {rec}")
            
            if not results:
                results.append("No specific analysis found for your query.")
                
        except Exception as e:
            results.append(f"Error searching JSON analysis: {e}")
        
        return results
    
    def answer_question(self, question: str) -> str:
        """Answer a question using available data"""
        if not question.strip():
            return "Please provide a question."
        
        print(f"\nQuestion: {question}")
        
        # Search both data sources
        excel_results = self.search_excel_data(question)
        json_results = self.search_json_analysis(question)
        
        # Combine results
        all_results = []
        if excel_results:
            all_results.append("Excel Trading Data:")
            all_results.extend([f"  • {result}" for result in excel_results])
        
        if json_results:
            all_results.append("\nAI Analysis Results:")
            all_results.extend([f"  • {result}" for result in json_results])
        
        if not all_results:
            return "I couldn't find relevant information to answer your question."
        
        return "\n".join(all_results)
    
    def interactive_qa(self):
        """Run interactive Q&A session"""
        print("=" * 60)
        print("SIMPLE FINANCIAL DATA Q&A SYSTEM")
        print("=" * 60)
        print("Ask questions about Apple trading data and analysis!")
        print("Type 'quit' to exit")
        print("Example questions:")
        print("  - What is the current Apple stock price?")
        print("  - Show me technical indicators")
        print("  - What are the financial recommendations?")
        print("  - Give me a trading summary")
        
        while True:
            try:
                question = input("\nYour question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if question:
                    answer = self.answer_question(question)
                    print(f"\nAnswer:\n{answer}")
                else:
                    print("Please enter a question.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main function"""
    # File paths
    excel_path = "data/Apple_Trading_Data_20250902_104928.xlsx"
    json_path = "financial_analysis_20250902_122854.json"
    
    # Check if files exist
    if not os.path.exists(excel_path):
        print(f"Excel file not found: {excel_path}")
        print("Please ensure the Excel file exists in the data directory.")
        return
    
    if not os.path.exists(json_path):
        print(f"JSON file not found: {json_path}")
        print("Please ensure the JSON analysis file exists.")
        return
    
    # Initialize Q&A system
    qa_system = SimpleFinancialQA(excel_path, json_path)
    
    # Run interactive Q&A
    qa_system.interactive_qa()

if __name__ == "__main__":
    main()
