#!/usr/bin/env python3
"""
Test script for Wheel Strategy Analysis
Demonstrates the functionality of the standalone wheel strategy analyzer
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_wheel_strategy():
    """Test the wheel strategy analysis functionality"""
    try:
        # Import the analyzer
        from ai.wheel_analyzer import WheelStrategyAnalyzer
        
        print("=" * 60)
        print("WHEEL STRATEGY ANALYSIS TEST")
        print("=" * 60)
        
        # Initialize analyzer
        print("\n1. Initializing Wheel Strategy Analyzer...")
        analyzer = WheelStrategyAnalyzer()
        
        # Get data info
        print("\n2. Getting available data information...")
        data_info = analyzer.get_available_data_info()
        
        if 'error' in data_info:
            print(f"Error getting data info: {data_info['error']}")
            return
        
        print(f"Available dates: {data_info.get('total_dates', 0)}")
        print(f"Latest date: {data_info.get('latest_date', 'N/A')}")
        
        if 'latest_date_info' in data_info:
            print(f"Total tickers: {data_info['latest_date_info'].get('total_tickers', 0)}")
            print("Sample tickers:")
            for letter, tickers in data_info['latest_date_info'].get('sample_tickers', {}).items():
                if tickers:
                    print(f"  {letter}: {', '.join(tickers[:3])}")
        
        # Test single ticker analysis
        print("\n3. Testing single ticker analysis...")
        test_ticker = "AAPL"  # Use Apple as test case
        
        print(f"Analyzing {test_ticker}...")
        result = analyzer.analyze_ticker(test_ticker, analysis_type="analysis")
        
        if 'error' in result:
            print(f"Error analyzing {test_ticker}: {result['error']}")
        else:
            print(f"✓ Successfully analyzed {test_ticker}")
            print(f"Current Price: ${result['data_summary']['current_price']:.2f}")
            print(f"Data Points: {result['data_summary']['total_bars']}")
            
            if 'technical_analysis' in result:
                tech = result['technical_analysis']
                suitability = tech.get('wheel_recommendations', {}).get('suitability_score', 'Unknown')
                print(f"Suitability Score: {suitability}")
                
                if 'wheel_recommendations' in tech and 'put_strikes' in tech['wheel_recommendations']:
                    strikes = tech['wheel_recommendations']['put_strikes']
                    print(f"Suggested Put Strikes:")
                    print(f"  5% OTM: ${strikes.get('5_percent_otm', 0):.2f}")
                    print(f"  10% OTM: ${strikes.get('10_percent_otm', 0):.2f}")
                    print(f"  15% OTM: ${strikes.get('15_percent_otm', 0):.2f}")
            
            # Show first 200 characters of AI analysis
            if 'ai_analysis' in result:
                ai_text = result['ai_analysis']
                print(f"\nAI Analysis Preview:")
                print(f"{ai_text[:200]}...")
        
        # Test finding top candidates (limit to 3 for quick test)
        print("\n4. Testing top candidates finder...")
        candidates = analyzer.get_top_wheel_candidates(limit=3, min_volume=5000)
        
        if candidates:
            print(f"✓ Found {len(candidates)} top candidates:")
            for i, candidate in enumerate(candidates):
                print(f"  {i+1}. {candidate['ticker']} - {candidate['suitability_score']} - ${candidate['current_price']:.2f}")
        else:
            print("No candidates found")
        
        # Test comparison (using a small set)
        print("\n5. Testing ticker comparison...")
        compare_tickers = ["AAPL", "MSFT"]  # Small set for quick test
        
        comparison = analyzer.compare_tickers(compare_tickers)
        
        if 'error' in comparison:
            print(f"Error in comparison: {comparison['error']}")
        else:
            print(f"✓ Successfully compared {len(compare_tickers)} tickers")
            if 'comparison_data' in comparison:
                for data in comparison['comparison_data']:
                    print(f"  {data['ticker']}: ${data['current_price']:.2f} - {data['suitability_score']}")
        
        print("\n" + "=" * 60)
        print("WHEEL STRATEGY TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nTo use the full interface:")
        print("1. Run: streamlit run wheel_app.py")
        print("2. Use the web interface for detailed analysis")
        print("3. Choose from various analysis options")
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure all dependencies are installed and the data folder exists")
    except Exception as e:
        print(f"Error during test: {e}")
        logger.exception("Full error details:")

if __name__ == "__main__":
    test_wheel_strategy()
