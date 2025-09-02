#!/usr/bin/env python3
"""
Simple test script to verify FAISS and sentence transformers setup
"""

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing imports...")
    
    try:
        import pandas as pd
        print("✓ pandas imported successfully")
    except ImportError as e:
        print(f"✗ pandas import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ numpy imported successfully")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    try:
        import faiss
        print("✓ faiss imported successfully")
        print(f"  FAISS version: {faiss.__version__}")
    except ImportError as e:
        print(f"✗ faiss import failed: {e}")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✓ sentence_transformers imported successfully")
    except ImportError as e:
        print(f"✗ sentence_transformers import failed: {e}")
        return False
    
    try:
        import torch
        print("✓ torch imported successfully")
        print(f"  PyTorch version: {torch.__version__}")
    except ImportError as e:
        print(f"✗ torch import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of imported packages"""
    print("\nTesting basic functionality...")
    
    try:
        # Test pandas
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        print("✓ pandas DataFrame creation works")
        
        # Test numpy
        arr = np.array([1, 2, 3, 4, 5])
        print("✓ numpy array creation works")
        
        # Test FAISS
        dimension = 128
        index = faiss.IndexFlatL2(dimension)
        print("✓ FAISS index creation works")
        
        # Test sentence transformers (just loading, not downloading)
        print("Testing sentence transformer model loading...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ Sentence transformer model loaded successfully")
        
        # Test embedding creation
        text = "Hello, this is a test sentence."
        embedding = model.encode([text])
        print(f"✓ Embedding creation works (shape: {embedding.shape})")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("FAISS AND SENTENCE TRANSFORMERS SETUP TEST")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed. Please install missing packages.")
        print("Run: pip install -r requirements.txt")
        return
    
    # Test basic functionality
    if not test_basic_functionality():
        print("\n❌ Basic functionality test failed.")
        return
    
    print("\n✅ All tests passed! Your setup is ready for FAISS indexing.")
    print("\nYou can now run: python3 build_faiss_qa.py")

if __name__ == "__main__":
    main()
