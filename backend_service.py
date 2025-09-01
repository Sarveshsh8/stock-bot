#!/usr/bin/env python3
"""
Backend Data Collection Service

Runs continuously in the background to collect data and build/maintain FAISS database
"""

import time
import schedule
import threading
from datetime import datetime, timedelta
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import (
    DataCollector,
    ChartGenerator,
    ExcelReporter,
    VideoCreator,
    MultimodalAnalyzer,
    FAISSBuilder,
    QASystem
)

class BackendService:
    def __init__(self, symbols: list = ["AAPL"]):
        self.symbols = symbols
        self.faiss_db_path = "data/faiss/stock_analysis_db.faiss"
        self.metadata_path = "data/faiss/stock_analysis_metadata.pkl"
        self.last_update = {}
        
        # Create directories
        os.makedirs("data/faiss", exist_ok=True)
        os.makedirs("data/charts", exist_ok=True)
        os.makedirs("data/excel", exist_ok=True)
        os.makedirs("data/videos", exist_ok=True)
        
        # Initialize components
        self.data_collectors = {symbol: DataCollector(symbol) for symbol in symbols}
        self.chart_generator = ChartGenerator()
        self.excel_reporter = ExcelReporter()
        self.video_creator = VideoCreator()
        self.multimodal_analyzer = MultimodalAnalyzer()
        self.faiss_builder = FAISSBuilder()
        
        # Load existing database or create new one
        self.qa_system = self._load_or_create_database()
    
    def _load_or_create_database(self):
        """Load existing FAISS database or create new one"""
        try:
            if os.path.exists(self.faiss_db_path) and os.path.exists(self.metadata_path):
                print("📚 Loading existing FAISS database...")
                return QASystem(self.faiss_db_path)
            else:
                print("🆕 Creating new FAISS database...")
                return None
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return None
    
    def collect_and_analyze(self, symbol: str):
        """Collect data and perform analysis for a symbol"""
        try:
            print(f"📊 Processing {symbol}...")
            
            # Collect current 5-minute data
            collector = self.data_collectors[symbol]
            current_data = collector.collect_current_data()
            
            # Collect historical data
            data = collector.get_historical_data(days=4)  # Collect 4 days of data
            
            if not data:
                print(f"❌ No data collected for {symbol}")
                return
            
            # Add current data to historical data
            if current_data:
                data['current_5min'] = current_data
                data['current_price'] = current_data.get('close', 'N/A')
            
            # Create Excel report
            excel_path = self.excel_reporter.create_report(data, symbol)
            
            # Generate charts
            image_paths = self.chart_generator.create_all_charts(data, symbol)
            
            # Create video
            video_path = self.video_creator.create_video(image_paths, symbol)
            
            # Multimodal analysis
            multimodal_results = self.multimodal_analyzer.analyze_all(image_paths, video_path, data, symbol)
            
            # Update FAISS database
            self._update_database(data, excel_path, multimodal_results, symbol)
            
            self.last_update[symbol] = datetime.now()
            print(f"✅ {symbol} processed successfully")
            
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
    
    def _update_database(self, data: dict, excel_path: str, multimodal_results: dict, symbol: str):
        """Update the FAISS database with new data"""
        try:
            # Create documents for new data
            new_documents = self.faiss_builder.create_documents(data, excel_path, multimodal_results, symbol)
            
            if new_documents:
                # Merge with existing database or create new one
                if self.qa_system and os.path.exists(self.faiss_db_path):
                    # Merge with existing database
                    new_index_path = self.faiss_builder.merge_with_existing(new_documents, self.faiss_db_path, symbol)
                else:
                    # Create new database
                    new_index_path = self.faiss_builder.build_index(new_documents, symbol)
                
                if new_index_path:
                    # Update Q&A system
                    self.qa_system = QASystem(new_index_path)
                    
                    # Copy to main database location
                    import shutil
                    shutil.copy(new_index_path, self.faiss_db_path)
                    
                    # Find the correct metadata path
                    metadata_path = new_index_path.replace('.faiss', '_metadata.pkl')
                    if not os.path.exists(metadata_path):
                        # Try with timestamp pattern
                        base_name = new_index_path.replace('.faiss', '')
                        if '_index_' in base_name:
                            symbol = base_name.split('_index_')[0]
                            timestamp = base_name.split('_index_')[1]
                            metadata_path = f"{symbol}_metadata_{timestamp}.pkl"
                    
                    shutil.copy(metadata_path, self.metadata_path)
                    
                    print(f"💾 Database updated for {symbol}")
            
        except Exception as e:
            print(f"❌ Error updating database: {e}")
    
    def run_continuous_collection(self):
        """Run continuous data collection"""
        print("🔄 Starting continuous data collection service...")
        print(f"📊 Monitoring symbols: {', '.join(self.symbols)}")
        
        # Initial collection and analysis
        for symbol in self.symbols:
            self.collect_and_analyze(symbol)
        
        # Schedule regular updates
        schedule.every(5).minutes.do(self._update_all_symbols)  # Update every 5 minutes
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n⏹️ Stopping backend service...")
    
    def _update_all_symbols(self):
        """Update all symbols"""
        print(f"\n🔄 Scheduled update at {datetime.now().strftime('%H:%M:%S')}")
        for symbol in self.symbols:
            self.collect_and_analyze(symbol)
    
    def get_qa_system(self):
        """Get the Q&A system"""
        return self.qa_system

def main():
    """Main function for backend service"""
    print("🚀 Stock Analysis Backend Service")
    print("=" * 50)
    
    # You can add more symbols here
    symbols = ["AAPL"]  # Only Apple
    
    service = BackendService(symbols)
    service.run_continuous_collection()

if __name__ == "__main__":
    main()
