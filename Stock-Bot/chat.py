#!/usr/bin/env python3
"""
Financial Data Chat System - Complete FAISS Q&A Pipeline
"""

import os
import sys
import subprocess
import time
from typing import List, Dict, Any

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.QA_Agent.data_loader import DataLoader
from src.QA_Agent.index_builder import FAISSIndexBuilder
from src.QA_Agent.query_engine import FAISSQueryEngine
from src.QA_Agent.output_generator import FinalOutputGenerator

class FinancialDataChat:
    """Complete financial data chat system with FAISS indexing"""
    
    def __init__(self):
        self.data_loader = None
        self.index_builder = None
        self.query_engine = None
        self.output_generator = None
        self.is_initialized = False
        
    def check_prerequisites(self) -> bool:
        """Check if required files exist"""
        print("Checking prerequisites...")
        
        required_files = [
            "data/Apple_Trading_Data_20250902_104928.xlsx",
            "financial_analysis_20250902_122854.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print("❌ Missing required files:")
            for file_path in missing_files:
                print(f"  - {file_path}")
            print("\nPlease ensure all required files are present before running the chat system.")
            return False
        
        print("✅ All required files found!")
        return True
    
    def initialize_system(self) -> bool:
        """Initialize the complete chat system"""
        try:
            print("Initializing Financial Data Chat System...")
            
            # Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Check if index already exists
            if os.path.exists("financial_data.index") and os.path.exists("financial_documents.pkl"):
                print("✅ FAISS index already exists. Loading existing system...")
                self.is_initialized = True
                return True
            
            print("Building FAISS index for the first time...")
            
            # Step 1: Load data
            print("\nStep 1: Loading Excel and JSON data...")
            self.data_loader = DataLoader()
            
            excel_path = "data/Apple_Trading_Data_20250902_104928.xlsx"
            json_path = "financial_analysis_20250902_122854.json"
            
            excel_success = self.data_loader.load_excel_data(excel_path)
            json_success = self.data_loader.load_json_data(json_path)
            
            if not excel_success or not json_success:
                print("❌ Failed to load data files")
                return False
            
            # Save extracted values
            extracted_values = self.data_loader.get_extracted_values()
            import pickle
            with open('step1_extracted_values.pkl', 'wb') as f:
                pickle.dump(extracted_values, f)
            
            print("✅ Step 1 completed: Data loaded and extracted")
            
            # Step 2: Build FAISS index
            print("\nStep 2: Building FAISS index...")
            self.index_builder = FAISSIndexBuilder()
            
            if not self.index_builder.load_step1_data():
                print("❌ Failed to load Step 1 data")
                return False
            
            if not self.index_builder.build_index():
                print("❌ Failed to build FAISS index")
                return False
            
            # Save index
            self.index_builder.save_index("financial_data.index", "financial_documents.pkl")
            print("✅ Step 2 completed: FAISS index built")
            
            self.is_initialized = True
            print("\n🎉 Financial Data Chat System initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing system: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def chat_session(self):
        """Run interactive chat session"""
        if not self.is_initialized:
            print("❌ System not initialized. Please run initialize_system() first.")
            return
        
        print("\n" + "=" * 60)
        print("FINANCIAL DATA CHAT SYSTEM")
        print("=" * 60)
        print("Ask questions about Apple trading data and analysis!")
        print("Type 'quit' to exit")
        print("\nExample questions:")
        print("  - What is the current Apple stock price?")
        print("  - Show me technical indicators")
        print("  - What are the financial recommendations?")
        print("  - Give me a trading summary")
        print("  - What is the market sentiment?")
        print("  - Analyze the market trends")
        print("  - What are the key financial insights?")
        
        # Initialize output generator for chat
        self.output_generator = FinalOutputGenerator()
        if not self.output_generator.load_index_and_model("financial_data.index", "financial_documents.pkl"):
            print("❌ Failed to load index and model for chat")
            return
        
        print("\n✅ Chat system ready with Nova Pro integration!")
        print("Your questions will be analyzed using:")
        print("  - FAISS vector search for context retrieval")
        print("  - Nova Pro AI model for intelligent analysis")
        print("  - Comprehensive financial insights generation")
        print("\nAsk your questions...")
        
        while True:
            try:
                question = input("\nYour question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye! Thanks for using the Financial Data Chat System!")
                    break
                
                if question:
                    print(f"\nProcessing: '{question}'")
                    print("-" * 50)
                    
                    # Generate comprehensive answer
                    answer = self.output_generator.process_query(question)
                    print(f"\n{answer}")
                    
                else:
                    print("Please enter a question.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye! Thanks for using the Financial Data Chat System!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def run_individual_steps(self):
        """Run individual steps manually"""
        print("\n" + "=" * 60)
        print("INDIVIDUAL STEP EXECUTION")
        print("=" * 60)
        print("Choose a step to run:")
        print("1. Load data and extract values")
        print("2. Build FAISS index")
        print("3. Query index for context")
        print("4. Generate final output")
        print("5. Return to main menu")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-5): ").strip()
                
                if choice == "1":
                    print("\nRunning Step 1: Load data...")
                    subprocess.run([sys.executable, "src/QA_Agent/data_loader.py"])
                    
                elif choice == "2":
                    print("\nRunning Step 2: Build index...")
                    subprocess.run([sys.executable, "src/QA_Agent/index_builder.py"])
                    
                elif choice == "3":
                    print("\nRunning Step 3: Query index...")
                    subprocess.run([sys.executable, "src/QA_Agent/query_engine.py"])
                    
                elif choice == "4":
                    print("\nRunning Step 4: Generate output...")
                    subprocess.run([sys.executable, "src/QA_Agent/output_generator.py"])
                    
                elif choice == "5":
                    print("Returning to main menu...")
                    break
                    
                else:
                    print("Invalid choice. Please enter 1-5.")
                    
            except KeyboardInterrupt:
                print("\nReturning to main menu...")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main function"""
    
    print("=" * 60)
    print("FINANCIAL DATA CHAT SYSTEM")
    print("=" * 60)
    print("Complete FAISS-based Q&A system with Nova Pro AI integration")
    print("for intelligent Apple trading data analysis")
    print("=" * 60)
    
    # Initialize chat system
    chat_system = FinancialDataChat()
    
    if not chat_system.initialize_system():
        print("\n❌ Failed to initialize chat system. Please check prerequisites.")
        return
    
    # Main menu
    while True:
        print("\n" + "=" * 60)
        print("MAIN MENU")
        print("=" * 60)
        print("1. Start Chat Session")
        print("2. Run Individual Steps")
        print("3. Exit")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                print("\nStarting chat session...")
                chat_system.chat_session()
                
            elif choice == "2":
                chat_system.run_individual_steps()
                
            elif choice == "3":
                print("\nGoodbye! Thanks for using the Financial Data Chat System!")
                break
                
            else:
                print("Invalid choice. Please enter 1-3.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye! Thanks for using the Financial Data Chat System!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
