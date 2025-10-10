import os
from typing import Dict, List, Optional
from serpapi import GoogleSearch


class StockGoogleSearch:
    """
    This module integrates with Google Search using SERP API.
    
    How it works:
    1. Takes a stock ticker symbol and query
    2. Performs a Google search using SERP API
    3. Returns relevant search results like news, company info, etc.
    
    SERP API provides programmatic access to Google Search results,
    which helps us get real-time information about stocks.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Search integration.
        
        Parameters:
        - api_key: SERP API key (if not provided, will use environment variable)
        """
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        if not self.api_key:
            print("Warning: SERPAPI_KEY not found. Google search will not work.")
    
    def search_stock_info(self, ticker: str, query: Optional[str] = None) -> Dict:
        """
        Search for information about a stock.
        
        Parameters:
        - ticker: Stock ticker symbol (e.g., 'AAPL')
        - query: Optional specific query (if None, searches for general stock info)
        
        Returns:
        - Dictionary containing search results
        
        How it works:
        1. Constructs a search query combining the ticker and user's question
        2. Calls the Google Search API
        3. Extracts relevant information from the results
        4. Returns formatted data that the chatbot can use
        """
        if not self.api_key:
            return {
                'error': 'SERP API key not configured',
                'results': []
            }
        
        # Construct search query
        if query:
            search_query = f"{ticker} stock {query}"
        else:
            search_query = f"{ticker} stock price news information"
        
        try:
            # Perform Google search
            params = {
                "q": search_query,
                "api_key": self.api_key,
                "num": 5  # Number of results to return
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Extract relevant information
            formatted_results = self._format_results(results, ticker)
            return formatted_results
            
        except Exception as e:
            return {
                'error': str(e),
                'results': []
            }
    
    def _format_results(self, raw_results: Dict, ticker: str) -> Dict:
        """
        Format the raw SERP API results into a clean structure.
        
        Parameters:
        - raw_results: Raw results from SERP API
        - ticker: Stock ticker symbol
        
        Returns:
        - Formatted dictionary with relevant information
        """
        formatted = {
            'ticker': ticker,
            'results': [],
            'knowledge_graph': None,
            'answer_box': None
        }
        
        # Extract organic search results
        if 'organic_results' in raw_results:
            for result in raw_results['organic_results'][:5]:
                formatted['results'].append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', '')
                })
        
        # Extract knowledge graph (company info)
        if 'knowledge_graph' in raw_results:
            kg = raw_results['knowledge_graph']
            formatted['knowledge_graph'] = {
                'title': kg.get('title', ''),
                'type': kg.get('type', ''),
                'description': kg.get('description', ''),
                'source': kg.get('source', {})
            }
        
        # Extract answer box (quick facts)
        if 'answer_box' in raw_results:
            ab = raw_results['answer_box']
            formatted['answer_box'] = {
                'answer': ab.get('answer', ''),
                'title': ab.get('title', ''),
                'snippet': ab.get('snippet', '')
            }
        
        return formatted
    
    def create_search_summary(self, search_results: Dict) -> str:
        """
        Create a human-readable summary from search results.
        
        Parameters:
        - search_results: Formatted search results dictionary
        
        Returns:
        - String summary that can be used by the chatbot
        
        This converts the search results into natural language that
        the chatbot can easily understand and use to answer questions.
        """
        if 'error' in search_results:
            return f"Error searching for information: {search_results['error']}"
        
        summary_parts = []
        ticker = search_results.get('ticker', 'Unknown')
        
        summary_parts.append(f"Google Search Results for {ticker}:")
        summary_parts.append("")
        
        # Add knowledge graph info
        if search_results.get('knowledge_graph'):
            kg = search_results['knowledge_graph']
            summary_parts.append("Company Information:")
            if kg.get('title'):
                summary_parts.append(f"- Name: {kg['title']}")
            if kg.get('type'):
                summary_parts.append(f"- Type: {kg['type']}")
            if kg.get('description'):
                summary_parts.append(f"- Description: {kg['description']}")
            summary_parts.append("")
        
        # Add answer box info
        if search_results.get('answer_box'):
            ab = search_results['answer_box']
            if ab.get('answer'):
                summary_parts.append(f"Quick Answer: {ab['answer']}")
                summary_parts.append("")
        
        # Add top search results
        if search_results.get('results'):
            summary_parts.append("Top Search Results:")
            for i, result in enumerate(search_results['results'][:3], 1):
                summary_parts.append(f"{i}. {result.get('title', 'No title')}")
                if result.get('snippet'):
                    summary_parts.append(f"   {result['snippet']}")
                summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def search_multiple_stocks(self, tickers: List[str], query: str) -> Dict[str, Dict]:
        """
        Search for information about multiple stocks.
        
        Parameters:
        - tickers: List of stock ticker symbols
        - query: Search query to apply to all tickers
        
        Returns:
        - Dictionary mapping ticker to search results
        """
        results = {}
        for ticker in tickers:
            results[ticker] = self.search_stock_info(ticker, query)
        return results

