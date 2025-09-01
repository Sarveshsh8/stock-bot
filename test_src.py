#!/usr/bin/env python3
"""
Test Script - New src Structure

Demonstrates the clean src import structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all classes from src
from src import (
    DataCollector,
    ChartGenerator,
    ExcelReporter,
    VideoCreator,
    MultimodalAnalyzer,
    FAISSBuilder,
    QASystem
)

def test_src_structure():
    """Test the new src structure"""
    print("🚀 Testing New src Structure")
    print("=" * 50)
    
    symbol = "AAPL"
    
    try:
        # Test data collection
        print("📊 Testing DataCollector...")
        collector = DataCollector(symbol)
        data = collector.get_historical_data(days=1)
        print(f"✅ Data collected: {len(data['hist_5min'])} 5-min points")
        
        # Test chart generation
        print("\n📈 Testing ChartGenerator...")
        chart_gen = ChartGenerator()
        charts = chart_gen.create_all_charts(data, symbol)
        print(f"✅ Charts created: {len(charts)}")
        
        # Test Excel reporting
        print("\n📊 Testing ExcelReporter...")
        excel_rep = ExcelReporter()
        excel_path = excel_rep.create_report(data, symbol)
        print(f"✅ Excel created: {excel_path}")
        
        # Test video creation
        print("\n🎬 Testing VideoCreator...")
        video_cre = VideoCreator()
        video_path = video_cre.create_video(charts, symbol)
        print(f"✅ Video created: {video_path}")
        
        # Test multimodal analysis
        print("\n🤖 Testing MultimodalAnalyzer...")
        multimodal = MultimodalAnalyzer()
        analysis = multimodal.analyze_all(charts, video_path, data, symbol)
        print(f"✅ Analysis completed: {len(analysis)} results")
        
        # Test FAISS building
        print("\n🔍 Testing FAISSBuilder...")
        faiss_build = FAISSBuilder()
        index_path = faiss_build.create_index(data, excel_path, analysis, symbol)
        print(f"✅ FAISS index created: {index_path}")
        
        # Test Q&A system
        print("\n❓ Testing QASystem...")
        qa = QASystem(index_path)
        answer = qa.answer_question("What is the current price?")
        print(f"✅ Q&A working: {answer[:100]}...")
        
        print("\n" + "=" * 50)
        print("🎉 All modules working perfectly!")
        print("✅ New src structure is clean and functional")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_src_structure()
