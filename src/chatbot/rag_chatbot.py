import os
from typing import TypedDict, Annotated, Sequence, Optional, List, Dict
import re
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
    ticker: Optional[str]
    history_context: str


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
        
    # Common company-name to ticker mapping for better intent detection
    COMPANY_TO_TICKER = {
        "TESLA": "TSLA",
        "APPLE": "AAPL",
        "ALPHABET": "GOOGL",
        "GOOGLE": "GOOGL",
        "MICROSOFT": "MSFT",
        "AMAZON": "AMZN",
        "META": "META",
        "FACEBOOK": "META",
        "NVIDIA": "NVDA",
        "NETFLIX": "NFLX",
        "ADOBE": "ADBE",
        "INTEL": "INTC",
        "AMD": "AMD",
        "IBM": "IBM",
    }

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
        history_context = state.get('history_context', '')
        print(f"Retrieving data for query: {query}")

        # Detect ticker early (use company name or history if needed)
        inferred_ticker = self._detect_ticker(query, history_context) or state.get('ticker')
        if inferred_ticker:
            # Remember ticker for later nodes
            state['ticker'] = inferred_ticker
            # Bias retrieval toward the ticker string as well
            augmented_query = f"{query} {inferred_ticker}"
        else:
            augmented_query = query
        
        # Search vector store for relevant documents
        results = self.vector_store.search(augmented_query, k=3)
        
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
        
        history_text = state.get('history_context') or ''
        ticker = self._detect_ticker(query, history_text) or state.get('ticker')
        
        search_summary = ""
        if ticker:
            search_results = self.google_search.search_stock_info(ticker, query)
            search_summary = self.google_search.create_search_summary(search_results)
            state['ticker'] = ticker
        else:
            search_summary = "No specific stock ticker identified for Google search."
            state['ticker'] = None
        
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
        history_context = state.get('history_context', '')
        ticker = state.get('ticker')
        
        print("Generating final answer with Nova Pro...")
        
        # Use Nova Pro to generate response
        try:
            # Decide between structured fact response (first queries) and analytical follow-up
            explicit_ticker_in_query = bool(self._detect_ticker(query, ""))
            # Bullet/structured mode only when explicitly requested
            wants_structured = any(k in query.lower() for k in ["structured", "show bullets", "bullet", "table"])
            # Default to analytical unless explicitly asking for structured
            follow_up = True if not wants_structured else False

            if follow_up:
                # Analytical follow-up: multi-paragraph narrative, richer company overview
                analysis_instructions = (
                    f"Provide a clear analysis of {ticker or 'the stock'} in plain text (no markdown, no italics, no bullets). "
                    "Organize the response into four labeled sections, each as 1 short paragraph separated by a blank line: "
                    "Summary: a direct answer to the question. "
                    "Price & Levels: cite open/high/low/close with dates and infer likely support/resistance. "
                    "Volume & Volatility: discuss intraday range vs average and notable volume context. "
                    "Company Overview: 4-7 sentences on business model, major segments/products, revenue drivers, competition, and strategy. "
                    "Avoid boilerplate like 'based on the context'. Keep it professional and precise."
                )
                guided_query = (
                    f"{analysis_instructions}\n\n"
                    f"Question: {query}"
                )
            else:
                # Structured facts for initial or explicit-ticker questions
                format_instructions = (
                    "Return ONLY the following bullet list, nothing else. Use plain text (no italics, no bold, no underscores, no markdown).\n"
                    "- Ticker: <ticker or N/A>\n"
                    "- Company: <company name or N/A>\n"
                    "- Company Info: <one short sentence describing what the company does>\n"
                    "- As Of: <date (YYYYMMDD) or N/A>\n"
                    "- Open: <open or N/A>\n"
                    "- High: <high or N/A>\n"
                    "- Low: <low or N/A>\n"
                    "- Close: <close or N/A>\n"
                    "- Volume: <volume or N/A>\n"
                    "- Sources: Retrieved Stock Data; Search"
                )
                guided_query = (
                    f"User asked about {ticker or 'a stock'}. Provide a concise, non-technical response grounded in the given data and search.\n"
                    f"{format_instructions}\n\n"
                    f"Original user query: {query}"
                )

            response = self.nova.analyze_stock_context(
                query=guided_query,
                retrieved_context=(
                    ("Recent Conversation (last messages):\n" + history_context + "\n\n") if history_context else ""
                ) + ("Retrieved Stock Data:\n" + context if context else "Retrieved Stock Data: None"),
                search_results=search,
                temperature=0.1
            )
            # Sanitize any stray markdown characters and excessive whitespace
            sanitized = self._sanitize_output(response)
            state['final_answer'] = sanitized
            state['messages'] = state.get('messages', []) + [
                HumanMessage(content=query),
                AIMessage(content=sanitized)
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
    
    def chat(self, user_query: str, conversation_messages: Optional[List[Dict[str, str]]] = None) -> str:
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
        # Lightweight intent handling: greetings/casual chat -> friendly prompt, skip heavy RAG
        casual_phrases = [
            "hi", "hello", "hey", "yo", "sup", "good morning", "good evening", "good afternoon",
            "how are you", "what's up", "howdy"
        ]
        uq_lower = user_query.strip().lower()
        if any(phrase in uq_lower for phrase in casual_phrases) and not any(k in uq_lower for k in ["stock", "price", "company", "ticker"]):
            return "Hi! How can I assist you with stocks today?"

        # Initialize state
        initial_state = {
            'messages': [],
            'user_query': user_query,
            'retrieved_context': '',
            'search_results': '',
            'final_answer': '',
            'ticker': None,
            'history_context': self._format_history(conversation_messages) if conversation_messages else ''
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state['final_answer']

    def _format_history(self, messages: Optional[List[Dict[str, str]]], max_chars: int = 1500) -> str:
        """
        Format recent conversation messages into a compact string for grounding follow-ups.
        Only include the last portion up to max_chars to keep prompts small.
        """
        if not messages:
            return ''
        # Use last 20 messages max
        trimmed = messages[-20:]
        lines: List[str] = []
        for m in trimmed:
            role = m.get('role', 'user')
            content = (m.get('content') or '').strip()
            if not content:
                continue
            lines.append(f"{role.capitalize()}: {content}")
        blob = "\n".join(lines)
        if len(blob) > max_chars:
            return blob[-max_chars:]
        return blob

    def _extract_ticker_from_history_text(self, text: str) -> Optional[str]:
        """
        Heuristic: find last occurrence of $TICKER or uppercase 1-5 letters in recent conversation.
        Filters common words to reduce false positives.
        """
        if not text:
            return None
        # Prefer $TICKER pattern
        dollar_matches = re.findall(r"\$([A-Z]{1,5})\b", text)
        if dollar_matches:
            return dollar_matches[-1]
        # Fallback: standalone uppercase tokens 1-5 chars
        tokens = re.findall(r"\b([A-Z]{1,5})\b", text)
        # Exclude common words
        stop = {"THE","AND","FOR","WITH","FROM","THIS","THAT","WHAT","WAS","WERE","WHEN","WILL","HAVE","HAD","HAS","YOUR","USER","ASSISTANT","DATA","VOLUME"}
        candidates = [t for t in tokens if t not in stop]
        return candidates[-1] if candidates else None

    def _detect_ticker(self, query: str, history_text: str = "") -> Optional[str]:
        """
        Detect ticker from current query using $TICKER, explicit ticker, or company name.
        If not found, fallback to history.
        """
        if not query:
            return self._extract_ticker_from_history_text(history_text)

        # $TICKER pattern
        m = re.findall(r"\$([A-Za-z]{1,5})\b", query)
        if m:
            return m[-1].upper()

        # Explicit uppercase tokens (filter out generic words to avoid 'WHAT' false positive)
        tokens = re.findall(r"\b([A-Z]{1,5})\b", query)
        if tokens:
            stop = {
                "WHAT","WHATS","WHATS?","WHATSUP","OPEN","OPENING","CLOSE","CLOSED","PRICE","PRICES",
                "VOLUME","TOTAL","TRADING","TRADE","TRADES","STOCK","DATA","LATEST","REALTIME","REAL-TIME",
                "THE","AND","FOR","WITH","FROM","THIS","THAT","WHAT'S","IS","WAS","ARE","OF","ON","AT"
            }
            filtered = [t for t in tokens if t not in stop]
            if filtered:
                return filtered[-1]

        # Company-name mapping
        up = query.upper()
        for name, tkr in self.COMPANY_TO_TICKER.items():
            if name in up:
                return tkr

        # Fallback to history
        return self._extract_ticker_from_history_text(history_text)
    
    def _sanitize_output(self, text: str) -> str:
        """
        Remove markdown italics/bold markers and fix accidental concatenations from formatting.
        Keeps content as plain text.
        """
        if not text:
            return text
        # Remove *, _, **, __ while preserving numbers/letters
        cleaned = re.sub(r"\*\*?", "", text)
        # Replace underscores with spaces to prevent glued words
        cleaned = re.sub(r"_+", " ", cleaned)
        # Collapse multiple spaces/newlines
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\s*\n\s*", "\n", cleaned)
        # Ensure each bullet starts on new line with '- '
        cleaned = re.sub(r"(?:^|\n)[\-\*]\s*", "\n- ", cleaned)
        # Normalize spacing around punctuation
        cleaned = re.sub(r"\s+,", ",", cleaned)
        cleaned = re.sub(r"\s+\.", ".", cleaned)
        cleaned = cleaned.strip()
        return cleaned
    
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

