"""
End-to-End Test for Stock Bot
Tests: AWS Nova Pro + Open Source Embeddings + RAG Workflow
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from config_aws import setup_aws_credentials, verify_aws_credentials
from src.chatbot.nova_text_analyzer import NovaTextAnalyzer
from src.vector_store.faiss_store import FAISSVectorStore
from src.chatbot.rag_chatbot import StockRAGChatbot
from src.serp_integration.google_search import StockGoogleSearch


def test_1_aws_config():
    """Test 1: AWS Configuration"""
    print("\n" + "="*60)
    print("TEST 1: AWS Configuration")
    print("="*60)
    
    try:
        setup_aws_credentials()
        if verify_aws_credentials():
            print("✓ AWS credentials configured")
            return True
        else:
            print("✗ AWS credentials not found")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_2_nova_connection():
    """Test 2: AWS Nova Pro Connection"""
    print("\n" + "="*60)
    print("TEST 2: AWS Bedrock Nova Pro Connection")
    print("="*60)
    
    try:
        setup_aws_credentials()
        nova = NovaTextAnalyzer()
        print("Nova analyzer initialized")
        
        if nova.test_connection():
            print("✓ Successfully connected to AWS Bedrock Nova Pro")
            return True
        else:
            print("✗ Failed to connect to Nova Pro")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_embedding_model():
    """Test 3: Open Source Embedding Model"""
    print("\n" + "="*60)
    print("TEST 3: Open Source Embedding Model")
    print("="*60)
    
    try:
        print("Loading sentence-transformers model (may download on first run)...")
        vs = FAISSVectorStore(model_name='all-MiniLM-L6-v2')
        print("✓ Embedding model loaded successfully")
        
        # Test embedding creation
        print("\nTesting embedding creation...")
        test_texts = [
            "Apple stock opened at $150 and closed at $155",
            "Microsoft stock traded with high volume"
        ]
        test_metadata = [
            {"ticker": "AAPL"},
            {"ticker": "MSFT"}
        ]
        
        vs.create_index(test_texts, test_metadata)
        print(f"✓ Created index with {vs.get_stats()['total_vectors']} vectors")
        
        # Test search
        print("\nTesting search...")
        results = vs.search("What is Apple's price?", k=1)
        if results:
            print(f"✓ Search working - found: {results[0][1]['ticker']}")
            return True
        else:
            print("✗ Search returned no results")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_nova_generation():
    """Test 4: Nova Pro Text Generation"""
    print("\n" + "="*60)
    print("TEST 4: Nova Pro Text Generation")
    print("="*60)
    
    try:
        setup_aws_credentials()
        nova = NovaTextAnalyzer()
        
        print("Generating response...")
        response = nova.generate_response(
            "What is a stock market? Answer in one sentence.",
            temperature=0.5
        )
        
        print(f"\nNova Response: {response[:150]}...")
        print("✓ Text generation working")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_complete_rag():
    """Test 5: Complete RAG Workflow"""
    print("\n" + "="*60)
    print("TEST 5: Complete RAG Workflow")
    print("="*60)
    
    try:
        setup_aws_credentials()
        
        # Create vector store
        print("Creating vector store with sample data...")
        vs = FAISSVectorStore(model_name='all-MiniLM-L6-v2')
        
        sample_texts = [
            """Stock: AAPL
Date: 20200102
Trading Summary:
- Opening Price: $295.05
- Closing Price: $300.35
- High Price: $301.00
- Low Price: $294.50
- Total Volume: 135,000,000 shares""",
            
            """Stock: MSFT
Date: 20200102
Trading Summary:
- Opening Price: $160.00
- Closing Price: $162.50
- High Price: $163.00
- Low Price: $159.50
- Total Volume: 40,000,000 shares"""
        ]
        
        sample_metadata = [
            {"ticker": "AAPL", "date": "20200102"},
            {"ticker": "MSFT", "date": "20200102"}
        ]
        
        vs.create_index(sample_texts, sample_metadata)
        print(f"✓ Vector store created with {len(sample_texts)} stocks")
        
        # Create chatbot
        print("\nInitializing RAG chatbot...")
        google_search = StockGoogleSearch()
        chatbot = StockRAGChatbot(vs, google_search)
        print("✓ Chatbot initialized")
        
        # Test query
        print("\nTesting query: 'What was AAPL closing price?'")
        response = chatbot.chat("What was AAPL closing price on 20200102?")
        
        print("\n" + "-"*60)
        print("Response Preview:")
        print(response[:300] + "..." if len(response) > 300 else response)
        print("-"*60)
        
        print("\n✓ Complete RAG workflow successful!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all end-to-end tests"""
    print("="*60)
    print("STOCK BOT - END-TO-END TESTING")
    print("AWS Nova Pro + Open Source Embeddings")
    print("="*60)
    
    tests = [
        ("AWS Configuration", test_1_aws_config),
        ("Nova Pro Connection", test_2_nova_connection),
        ("Open Source Embeddings", test_3_embedding_model),
        ("Nova Text Generation", test_4_nova_generation),
        ("Complete RAG Workflow", test_5_complete_rag)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status:12} | {name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready to use.")
        print("\nRun the app:")
        print("  streamlit run app.py")
    else:
        print("\n⚠️  Some tests failed. Please check errors above.")


if __name__ == "__main__":
    main()

