"""
Test the simple RAG
"""

from simple_rag import search_docs, documents

def test_search():
    """Test the search functionality"""
    print(" Testing Simple RAG")    
    # Test queries
    queries = [
        "Apple technology",
        "electric vehicle", 
        "cloud computing",
        "Microsoft software"
    ]
    
    for query in queries:
        print(f"\n Query: '{query}'")
        results = search_docs(query, top_k=2)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['document']} (Score: {result['score']})")
        else:
            print("  No results found")
    
    print(f"\n Total documents: {len(documents)}")
    print(" Test completed!")

if __name__ == "__main__":
    test_search()
