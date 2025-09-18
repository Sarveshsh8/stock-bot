"""
Simple RAG with One Tool
A minimal RAG server using FastMCP with just one search tool
"""

from mcp.server.fastmcp import FastMCP

# Simple knowledge base
documents = [
    "Apple Inc. is an American multinational technology company.",
    "Tesla is an electric vehicle and clean energy company.",
    "Microsoft develops computer software and cloud services.",
    "Google is a multinational technology company specializing in Internet-related services.",
    "Amazon is an e-commerce and cloud computing company."
]

# Simple keyword search
def search_docs(query: str, top_k: int = 3):
    """Simple keyword-based document search"""
    query_words = query.lower().split()
    results = []
    
    for i, doc in enumerate(documents):
        doc_lower = doc.lower()
        score = sum(1 for word in query_words if word in doc_lower)
        if score > 0:
            results.append({
                "document": doc,
                "score": score,
                "index": i
            })
    
    # Sort by score and return top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

# Create MCP server
app = FastMCP("Simple RAG")

@app.tool()
def search(query: str, top_k: int = 3) -> str:
    """Search for relevant documents based on a query"""
    results = search_docs(query, top_k)
    
    if not results:
        return f"No documents found for query: '{query}'"
    
    response = f"Found {len(results)} relevant documents for '{query}':\n\n"
    for i, result in enumerate(results, 1):
        response += f"{i}. {result['document']} (Score: {result['score']})\n"
    
    return response

if __name__ == "__main__":
    print(" Simple RAG Server")
    print(f" {len(documents)} documents loaded")
    print("One tool: search")
    print("Running on stdio")
    
    app.run_stdio()
