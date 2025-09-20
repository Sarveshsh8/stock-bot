#!/usr/bin/env python3
"""
Test script using config.yaml for Sample Questions Generator
"""

import os
import sys
import yaml
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.sample_questions_generator import SampleQuestionsGenerator

def test_with_config():
    """Test the sample questions generator using config.yaml"""
    print("🧪 Testing Sample Questions Generator with config.yaml...")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Load config from YAML file
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        print("✅ Config loaded from config.yaml")
    except Exception as e:
        print(f"❌ Error loading config.yaml: {e}")
        return
    
    # Show config being used
    bedrock_settings = config.get('bedrock_settings', {})
    print(f"📋 Using config:")
    print(f"   - Region: {bedrock_settings.get('region', 'us-east-1')}")
    print(f"   - Model ID: {bedrock_settings.get('model_id', 'default')}")
    print(f"   - Max Tokens: {bedrock_settings.get('max_tokens', 4000)}")
    
    try:
        generator = SampleQuestionsGenerator(config)
        print("✅ Sample Questions Generator initialized with config")
        
        # Test with sample data
        market_data = {
            'AAPL': None,
            'GOOGL': None,
            'TSLA': None,
            'SPY': None,
            'QQQ': None
        }
        
        youtube_analyses = [
            {
                'title': 'Apple Q2 2025 Earnings Analysis',
                'content': 'Apple reported strong earnings...'
            }
        ]
        
        print(f"\n📊 Testing with sample data:")
        print(f"   - Market symbols: {list(market_data.keys())}")
        print(f"   - YouTube videos: {len(youtube_analyses)}")
        
        # Generate sample questions
        print(f"\n🤖 Generating sample questions using LLM...")
        sample_questions = generator.generate_questions_from_content(
            market_data=market_data,
            youtube_analyses=youtube_analyses
        )
        
        if sample_questions:
            print(f"\n✅ Generated {len(sample_questions)} sample questions:")
            for i, question in enumerate(sample_questions[:10], 1):  # Show first 10
                print(f"{i:2d}. {question}")
            if len(sample_questions) > 10:
                print(f"    ... and {len(sample_questions) - 10} more questions")
            
            # Save to file
            print(f"\n💾 Saving questions to file...")
            filepath = generator.save_questions_to_file(sample_questions, "sample_questions_config.txt")
            
            if filepath:
                print(f"✅ Sample questions saved to: {filepath}")
                print(f"📁 File size: {os.path.getsize(filepath)} bytes")
            else:
                print("❌ Failed to save questions to file")
        else:
            print("❌ No sample questions generated")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_config()
