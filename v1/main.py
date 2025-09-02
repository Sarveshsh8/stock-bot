#!/usr/bin/env python3
"""
Stock Analysis System - Streamlit App

Main application for Q&A and data collection
"""

import streamlit as st
import os
import glob
from datetime import datetime
from dotenv import load_dotenv

# Import modules
from src import (
    DataCollector,
    ChartGenerator,
    ExcelReporter,
    VideoCreator,
    MultimodalAnalyzer,
    FAISSBuilder,
    QASystem
)

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(
        page_title="Stock Analysis System",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Stock Analysis System")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Data Collection", "Analysis Pipeline", "Q&A System", "Settings"]
    )
    
    if page == "Data Collection":
        show_data_collection()
    elif page == "Analysis Pipeline":
        show_analysis_pipeline()
    elif page == "Q&A System":
        show_qa_system()
    elif page == "Settings":
        show_settings()

def show_data_collection():
    st.header("📊 Data Collection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Real-time Data Collection")
        symbol = st.text_input("Stock Symbol", value="AAPL").upper()
        
        if st.button("Start Continuous Collection"):
            with st.spinner("Starting data collection..."):
                collector = DataCollector(symbol)
                st.success(f"Started collecting data for {symbol} every 5 minutes")
                st.info("Data will be saved to data/{symbol}_data/")
        
        if st.button("Collect Historical Data"):
            with st.spinner("Collecting historical data..."):
                collector = DataCollector(symbol)
                data = collector.get_historical_data(days=3)
                if data:
                    st.success(f"Collected {len(data['hist_5min'])} 5-min data points")
                    st.json(data.get('info', {}))
    
    with col2:
        st.subheader("Today's Summary")
        if st.button("Get Today's Summary"):
            collector = DataCollector("AAPL")  # Default for demo
            summary = collector.get_today_summary()
            if summary:
                st.json(summary)
            else:
                st.info("No data collected today yet")

def show_analysis_pipeline():
    st.header("🔄 Analysis Pipeline")
    
    symbol = st.text_input("Stock Symbol for Analysis", value="AAPL").upper()
    
    if st.button("Run Complete Analysis"):
        with st.spinner("Running complete analysis pipeline..."):
            try:
                # Step 1: Collect data
                collector = DataCollector(symbol)
                data = collector.get_historical_data(days=3)
                
                if not data:
                    st.error("Failed to collect data")
                    return
                
                # Step 2: Create Excel
                excel_reporter = ExcelReporter()
                excel_path = excel_reporter.create_report(data, symbol)
                
                # Step 3: Create charts
                chart_generator = ChartGenerator()
                image_paths = chart_generator.create_all_charts(data, symbol)
                
                # Step 4: Create video
                video_creator = VideoCreator()
                video_path = video_creator.create_video(image_paths, symbol)
                
                # Step 5: Multimodal analysis
                multimodal_analyzer = MultimodalAnalyzer()
                multimodal_results = multimodal_analyzer.analyze_all(image_paths, video_path, data, symbol)
                
                # Step 6: Build FAISS index
                faiss_builder = FAISSBuilder()
                index_path = faiss_builder.create_index(data, excel_path, multimodal_results, symbol)
                
                st.success("✅ Analysis completed successfully!")
                
                # Display results
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Generated Files")
                    st.write(f"📊 Excel: {excel_path}")
                    st.write(f"📈 Images: {len(image_paths)}")
                    st.write(f"🎬 Video: {video_path}")
                    st.write(f"🔍 FAISS Index: {index_path}")
                
                with col2:
                    st.subheader("Analysis Results")
                    for key, result in multimodal_results.items():
                        if isinstance(result, str):
                            st.text_area(f"{key}", result, height=100)
                
            except Exception as e:
                st.error(f"Error in analysis: {str(e)}")

def show_qa_system():
    st.header("❓ Q&A System")
    
    # Find latest FAISS index
    faiss_files = glob.glob("data/faiss/*.faiss")
    
    if not faiss_files:
        st.warning("No FAISS index found. Please run analysis first.")
        return
    
    # Get latest index
    latest_index = max(faiss_files, key=os.path.getctime)
    
    try:
        qa_system = QASystem(latest_index)
        
        st.subheader("Ask Questions")
        question = st.text_input("Enter your question:")
        
        if st.button("Ask"):
            if question:
                with st.spinner("Searching..."):
                    answer = qa_system.answer_question(question)
                    st.write("**Answer:**")
                    st.write(answer)
        
        # Show available topics
        st.subheader("Available Topics")
        topics = qa_system.get_available_topics()
        for topic in topics:
            st.write(f"• {topic}")
        
        # Sample questions
        st.subheader("Sample Questions")
        sample_questions = [
            "What is the current price?",
            "What is the trading volume?",
            "What is the trend analysis?",
            "What technical analysis is available?"
        ]
        
        for q in sample_questions:
            if st.button(q):
                answer = qa_system.answer_question(q)
                st.write(f"**Q:** {q}")
                st.write(f"**A:** {answer}")
    
    except Exception as e:
        st.error(f"Error loading Q&A system: {str(e)}")

def show_settings():
    st.header("⚙️ Settings")
    
    st.subheader("AWS Configuration")
    aws_region = st.text_input("AWS Region", value="us-east-1")
    aws_access_key = st.text_input("AWS Access Key ID", type="password")
    aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
    
    if st.button("Save Settings"):
        # Save to .env file
        with open(".env", "w") as f:
            f.write(f"AWS_ACCESS_KEY_ID={aws_access_key}\n")
            f.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_key}\n")
            f.write(f"AWS_DEFAULT_REGION={aws_region}\n")
        
        st.success("Settings saved!")
    
    st.subheader("System Status")
    st.write(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check data directories
    data_dirs = ["data", "data/charts", "data/excel", "data/videos", "data/faiss", "data/analysis"]
    for dir_path in data_dirs:
        if os.path.exists(dir_path):
            st.write(f"✅ {dir_path}")
        else:
            st.write(f"❌ {dir_path}")

if __name__ == "__main__":
    main()
