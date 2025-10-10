import os
from typing import TypedDict, Annotated, Sequence
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
import operator
from src.chatbot.nova_text_analyzer import NovaTextAnalyzer


class AgentState(TypedDict):
    """
    State that will be passed between nodes in the graph.
    
    This is like a shared memory that all parts of the chatbot can read and write to.
    As the chatbot processes a query, it updates this state with new information.
    """
    messages: Annotated[Sequence[HumanMessage | AIMessage | SystemMessage], operator.add]
    user_query: str
    retrieved_context: str
    search_results: str
    final_answer: str


class StockRAGChatbot:
    """
    RAG Chatbot using AWS Bedrock Nova Pro instead of OpenAI.
    
    How it works:
    1. User asks a question about stocks
    2. The chatbot retrieves relevant data from the FAISS vector store (RAG - Retrieval)
    3. Optionally searches Google for real-time information (Google Search)
    4. Uses AWS Bedrock Nova Pro to generate an answer (Generation)
    
    LangGraph helps us create a workflow where different steps happen in sequence:
    Query -> Retrieve Data -> Search Google -> Generate Answer with Nova
    
    RAG (Retrieval Augmented Generation) means:
    - Retrieval: Find relevant information from our database
    - Augmented: Add extra context to help answer better
    - Generation: Generate the final answer using AWS Nova Pro
    """
    
    def __init__(self, vector_store, google_search, 
                 region: str = "us-east-1",
                 model_id: str = "us.amazon.nova-pro-v1:0",
                 max_tokens: int = 2000):
        """
        Initialize the RAG chatbot with Nova Pro.
        
        Parameters:
        - vector_store: FAISSVectorStore instance for retrieving stock data
        - google_search: StockGoogleSearch instance for web search
        - region: AWS region for Bedrock
        - model_id: Nova Pro model identifier
        - max_tokens: Maximum tokens in response
        """
        self.vector_store = vector_store
        self.google_search = google_search
        self.nova = NovaTextAnalyzer(region=region, model_id=model_id, max_tokens=max_tokens)
        self.graph = self._create_graph()
        
    def _create_graph(self):
        """
        Create the LangGraph workflow.
        
        This defines the flow of how the chatbot processes queries:
        1. Start -> 2. Retrieve -> 3. Search -> 4. Generate -> 5. End
        
        Each step is a "node" in the graph, and arrows between them
        show the order of execution.
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes (steps in the workflow)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("generate", self._generate_node)
        
        # Define the flow
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "search")
        workflow.add_edge("search", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    def _retrieve_node(self, state: AgentState) -> AgentState:
        """
        Retrieve relevant stock data from the vector store.
        
        This node:
        1. Takes the user's query
        2. Searches the FAISS vector store for similar stock data
        3. Adds the retrieved information to the state
        
        Think of this as looking up information in a book's index
        to find the relevant pages.
        """
        query = state['user_query']
        print(f"Retrieving data for query: {query}")
        
        # Search vector store for relevant documents
        results = self.vector_store.search(query, k=3)
        
        # Format retrieved context
        context_parts = []
        for i, (doc, metadata, score) in enumerate(results, 1):
            context_parts.append(f"Stock Data {i}:")
            context_parts.append(doc)
            context_parts.append("")
        
        retrieved_context = "\n".join(context_parts) if context_parts else "No relevant stock data found."
        
        state['retrieved_context'] = retrieved_context
        return state
    
    def _search_node(self, state: AgentState) -> AgentState:
        """
        Search Google for additional information.
        
        This node:
        1. Extracts stock tickers from the query
        2. Performs Google search for real-time information
        3. Adds search results to the state
        
        This helps get current news, prices, and other real-time data.
        """
        query = state['user_query']
        print(f"Searching Google for: {query}")
        
        # Try to extract ticker from query (simple approach)
        words = query.upper().split()
        potential_tickers = [word for word in words if word.isalpha() and len(word) <= 5]
        
        search_summary = ""
        if potential_tickers:
            # Search for the first potential ticker
            ticker = potential_tickers[0]
            search_results = self.google_search.search_stock_info(ticker, query)
            search_summary = self.google_search.create_search_summary(search_results)
        else:
            search_summary = "No specific stock ticker identified for Google search."
        
        state['search_results'] = search_summary
        return state
    
    def _generate_node(self, state: AgentState) -> AgentState:
        """
        Generate the final answer using AWS Bedrock Nova Pro.
        
        This node:
        1. Takes the user's query
        2. Combines retrieved stock data and Google search results
        3. Uses Nova Pro to generate a helpful answer
        4. Returns the final answer
        
        This is where Nova Pro AI puts everything together to answer the user's question.
        """
        query = state['user_query']
        context = state['retrieved_context']
        search = state['search_results']
        
        print("Generating final answer with Nova Pro...")
        
        # Use Nova Pro to generate response
        try:
            response = self.nova.analyze_stock_context(
                query=query,
                retrieved_context=context,
                search_results=search,
                temperature=0.7
            )
            
            state['final_answer'] = response
            state['messages'] = state.get('messages', []) + [
                HumanMessage(content=query),
                AIMessage(content=response)
            ]
            
        except Exception as e:
            error_msg = f"Error generating response with Nova Pro: {str(e)}"
            print(error_msg)
            state['final_answer'] = error_msg
            state['messages'] = state.get('messages', []) + [
                HumanMessage(content=query),
                AIMessage(content=error_msg)
            ]
        
        return state
    
    def chat(self, user_query: str) -> str:
        """
        Main chat interface.
        
        Parameters:
        - user_query: The user's question
        
        Returns:
        - The chatbot's answer
        
        This is the main function you call to interact with the chatbot.
        It runs the entire workflow (retrieve -> search -> generate with Nova) and
        returns the final answer.
        """
        # Initialize state
        initial_state = {
            'messages': [],
            'user_query': user_query,
            'retrieved_context': '',
            'search_results': '',
            'final_answer': ''
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state['final_answer']
    
    def get_conversation_history(self, state: AgentState) -> list:
        """
        Get the conversation history.
        
        Parameters:
        - state: Current agent state
        
        Returns:
        - List of messages in the conversation
        """
        return state.get('messages', [])
    
    def test_nova_connection(self) -> bool:
        """
        Test connection to AWS Bedrock Nova.
        
        Returns:
        - True if connection successful, False otherwise
        
        Use this to verify AWS credentials are configured correctly.
        """
        return self.nova.test_connection()

