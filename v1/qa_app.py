#!/usr/bin/env python3
"""
Stock Analysis Q&A System - Streamlit App

Simple Q&A interface for the stock analysis database
"""

import streamlit as st
import os
import glob
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import QASystem

def main():
    st.set_page_config(
        page_title="Stock Analysis Q&A",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Stock Analysis Q&A System")
    st.markdown("---")
    
    # Check if database exists
    faiss_db_path = "data/faiss/stock_analysis_db.faiss"
    metadata_path = "data/faiss/stock_analysis_metadata.pkl"
    
    if not os.path.exists(faiss_db_path) or not os.path.exists(metadata_path):
        st.error("❌ Database not found!")
        st.info("Please run the backend service first to collect data and build the database.")
        st.code("python3 backend_service.py")
        return
    
    try:
        # Load Q&A system
        qa_system = QASystem(faiss_db_path)
        
        # Main Q&A interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("❓ Ask Questions")
            
            # Question input
            question = st.text_input(
                "Enter your question about stock analysis:",
                placeholder="e.g., What is the current price of AAPL?"
            )
            
            if st.button("Ask Question", type="primary"):
                if question:
                    with st.spinner("Searching database..."):
                        answer = qa_system.answer_question(question)
                        
                        st.write("**Answer:**")
                        st.write(answer)
                        
                        # Show confidence/score
                        st.info("💡 This answer is based on the latest analysis data in our database.")
                else:
                    st.warning("Please enter a question.")
        
        with col2:
            st.subheader("📊 Quick Questions")
            
            quick_questions = [
                "What is the current price?",
                "What is the trading volume?",
                "What is the trend analysis?",
                "What technical analysis is available?",
                "What are the support levels?",
                "What are the resistance levels?",
                "What is the market sentiment?",
                "What trading signals are available?"
            ]
            
            for q in quick_questions:
                if st.button(q, key=q):
                    with st.spinner("Searching..."):
                        answer = qa_system.answer_question(q)
                        st.write(f"**Q:** {q}")
                        st.write(f"**A:** {answer}")
        
        # Database info
        st.markdown("---")
        st.subheader("📚 Database Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Database Status", "✅ Active")
        
        with col2:
            # Get file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(faiss_db_path))
            st.metric("Last Updated", mod_time.strftime("%H:%M:%S"))
        
        with col3:
            file_size = os.path.getsize(faiss_db_path) / 1024  # KB
            st.metric("Database Size", f"{file_size:.1f} KB")
        
        # Available topics
        st.subheader("📖 Available Topics")
        topics = qa_system.get_available_topics()
        if topics:
            for topic in topics:
                st.write(f"• {topic}")
        else:
            st.write("No topics available.")
        
        # Sample questions
        st.subheader("💡 Sample Questions You Can Ask")
        st.write("""
        - What is the current price of [STOCK]?
        - What is the trading volume?
        - What is the trend analysis?
        - What technical indicators are available?
        - What are the support and resistance levels?
        - What is the market sentiment?
        - What trading signals are recommended?
        - What is the risk assessment?
        - What is the price prediction?
        - What are the key patterns identified?
        """)
        
    except Exception as e:
        st.error(f"Error loading Q&A system: {str(e)}")
        st.info("Please ensure the backend service is running and database is properly built.")

if __name__ == "__main__":
    main()
