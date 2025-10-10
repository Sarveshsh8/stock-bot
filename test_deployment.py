"""
End-to-End Deployment Test
Tests the complete deployment workflow with S3
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from s3_faiss_manager import S3FAISSManager
from config_aws import setup_aws_credentials

def test_s3_connection():
    """Test S3 connection and bucket access."""
    print("=" * 60)
    print("TEST 1: S3 Connection")
    print("=" * 60)
    
    load_dotenv()
    setup_aws_credentials()
    
    bucket_name = os.getenv("S3_BUCKET_NAME", "stock-bot-algoseek")
    
    try:
        manager = S3FAISSManager(bucket_name)
        print(f"✓ S3 Manager initialized for bucket: {bucket_name}")
        
        # Check if index exists
        if manager.index_exists():
            print("✓ FAISS index found in S3")
            info = manager.get_index_info()
            print(f"  Size: {info['size_mb']:.2f} MB")
            print(f"  Last Modified: {info['last_modified']}")
        else:
            print("⚠ FAISS index NOT found in S3 (will be uploaded)")
        
        return True
    except Exception as e:
        print(f"✗ S3 Connection failed: {e}")
        return False


def test_upload_index():
    """Test uploading FAISS index to S3."""
    print("\n" + "=" * 60)
    print("TEST 2: Upload FAISS Index to S3")
    print("=" * 60)
    
    index_path = Path(__file__).parent / "faiss_index_all"
    
    if not index_path.exists():
        print("⚠ No local FAISS index found")
        print("  Run the app first to create the index")
        return False
    
    load_dotenv()
    bucket_name = os.getenv("S3_BUCKET_NAME", "stock-bot-algoseek")
    
    try:
        manager = S3FAISSManager(bucket_name)
        print(f"Uploading index from: {index_path}")
        
        s3_url = manager.upload_index(str(index_path))
        print(f"✓ Successfully uploaded to: {s3_url}")
        
        # Verify
        info = manager.get_index_info()
        print(f"  Verified - Size: {info['size_mb']:.2f} MB")
        
        return True
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        return False


def test_download_index():
    """Test downloading FAISS index from S3."""
    print("\n" + "=" * 60)
    print("TEST 3: Download FAISS Index from S3")
    print("=" * 60)
    
    load_dotenv()
    bucket_name = os.getenv("S3_BUCKET_NAME", "stock-bot-algoseek")
    
    try:
        manager = S3FAISSManager(bucket_name)
        
        # Download to temp location
        temp_path = Path(__file__).parent / "test_download"
        temp_path.mkdir(exist_ok=True)
        
        print(f"Downloading index to: {temp_path}")
        downloaded_path = manager.download_index(str(temp_path))
        
        if downloaded_path and Path(downloaded_path).exists():
            print(f"✓ Successfully downloaded to: {downloaded_path}")
            
            # Check files
            files = list(Path(downloaded_path).glob("*"))
            print(f"  Files found: {len(files)}")
            for f in files:
                print(f"    - {f.name}")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_path)
            print("  Cleaned up test download")
            
            return True
        else:
            print("✗ Download failed")
            return False
            
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return False


def test_vector_store_with_s3():
    """Test vector store loading from S3."""
    print("\n" + "=" * 60)
    print("TEST 4: Vector Store with S3 Index")
    print("=" * 60)
    
    from src.vector_store.faiss_store import FAISSVectorStore
    
    load_dotenv()
    bucket_name = os.getenv("S3_BUCKET_NAME", "stock-bot-algoseek")
    
    try:
        # Download index
        s3_manager = S3FAISSManager(bucket_name)
        temp_path = Path(__file__).parent / "temp_index"
        temp_path.mkdir(exist_ok=True)
        
        print("Downloading index for testing...")
        index_path = s3_manager.download_index(str(temp_path))
        
        if not index_path:
            print("✗ Could not download index")
            return False
        
        # Load into vector store
        print("Loading into FAISS vector store...")
        vector_store = FAISSVectorStore()
        vector_store.load(index_path)
        
        stats = vector_store.get_stats()
        print(f"✓ Vector store loaded successfully")
        print(f"  Documents: {stats.get('total_documents', stats.get('num_documents', 0))}")
        print(f"  Vectors: {stats.get('total_vectors', stats.get('num_vectors', 0))}")
        print(f"  Embedding model: {stats.get('model_name', stats.get('embedding_model', 'unknown'))}")
        print(f"  Dimension: {stats.get('dimension', stats.get('index_dimension', 0))}")
        
        # Test search
        print("\nTesting search...")
        results = vector_store.search("What are tech stocks?", k=3)
        print(f"✓ Search returned {len(results)} results")
        
        if results:
            print(f"  Top result: {results[0][1].get('ticker', 'N/A')}")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_path)
        
        return True
        
    except Exception as e:
        print(f"✗ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bedrock_nova():
    """Test AWS Bedrock Nova Pro connection."""
    print("\n" + "=" * 60)
    print("TEST 5: AWS Bedrock Nova Pro")
    print("=" * 60)
    
    from src.chatbot.nova_text_analyzer import NovaTextAnalyzer
    
    load_dotenv()
    setup_aws_credentials()
    
    try:
        region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")
        
        # Initialize directly with parameters
        analyzer = NovaTextAnalyzer(region=region, model_id=model_id)
        
        print(f"Region: {region}")
        print(f"Model: {model_id}")
        
        # Test generation
        print("\nTesting text generation...")
        response = analyzer.generate_response(
            "What is a stock? Answer in one sentence."
        )
        
        print(f"✓ Nova Pro response:")
        print(f"  {response[:200]}..." if len(response) > 200 else f"  {response}")
        
        return True
        
    except Exception as e:
        print(f"✗ Bedrock test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_docker_build():
    """Test Docker build."""
    print("\n" + "=" * 60)
    print("TEST 6: Docker Build")
    print("=" * 60)
    
    import subprocess
    
    try:
        print("Building Docker image...")
        result = subprocess.run(
            ["docker", "build", "-t", "stock-bot-test", "."],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✓ Docker image built successfully")
            return True
        else:
            print(f"✗ Docker build failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Docker build timed out (> 5 minutes)")
        return False
    except FileNotFoundError:
        print("⚠ Docker not installed - skipping this test")
        return None
    except Exception as e:
        print(f"✗ Docker build test failed: {e}")
        return False


def main():
    """Run all deployment tests."""
    print("\n" + "=" * 60)
    print("STOCK BOT - END-TO-END DEPLOYMENT TEST")
    print("=" * 60)
    print(f"S3 Bucket: stock-bot-algoseek")
    print(f"Region: us-east-1")
    print()
    
    results = {}
    
    # Run tests
    results["S3 Connection"] = test_s3_connection()
    
    # Check if we have local index to upload
    index_path = Path(__file__).parent / "faiss_index_all"
    if index_path.exists():
        results["Upload Index"] = test_upload_index()
    else:
        print("\n⚠ Skipping upload test - no local index found")
        results["Upload Index"] = None
    
    results["Download Index"] = test_download_index()
    results["Vector Store"] = test_vector_store_with_s3()
    results["Bedrock Nova"] = test_bedrock_nova()
    results["Docker Build"] = test_docker_build()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⚠ SKIP"
        print(f"{test_name:.<40} {status}")
    
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Ready for deployment!")
        print("\nNext steps:")
        print("1. Run: ./deploy_ec2_public.sh")
        print("2. Wait 5-10 minutes for deployment")
        print("3. Get your shareable URL: http://YOUR_IP:8501")
        return True
    else:
        print("\n⚠ Some tests failed - check errors above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

