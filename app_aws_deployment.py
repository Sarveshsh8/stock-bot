import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
import sys

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.data_processor.stock_data_loader import StockDataLoader
from src.vector_store.faiss_store import FAISSVectorStore
from src.serp_integration.google_search import StockGoogleSearch
from src.chatbot.rag_chatbot import StockRAGChatbot
from config_aws import setup_aws_credentials
from s3_faiss_manager import S3FAISSManager
from src.auth.dynamodb_auth import DynamoDBAuthService
from src.chat_history.dynamodb_history import DynamoDBChatHistory

# Load environment variables
load_dotenv()

# Setup AWS credentials
setup_aws_credentials()

# Page configuration
st.set_page_config(
    page_title="Stock Bot - AWS Deployment",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
)

# Initialize session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'index_created' not in st.session_state:
    st.session_state.index_created = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'auth' not in st.session_state:
    st.session_state.auth = DynamoDBAuthService()
if 'history' not in st.session_state:
    st.session_state.history = DynamoDBChatHistory()
if 'session_id' not in st.session_state:
    st.session_state.session_id = None


@st.cache_resource
def initialize_system():
    """Initialize system - reads FAISS index from S3 directly to temp location."""
    try:
        import tempfile
        import shutil
        
        embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # S3 Configuration (force S3-only, no local fallback)
        s3_uri = os.getenv("S3_INDEX_URI", "").strip()
        s3_bucket = None
        s3_key = None
        if s3_uri.startswith("s3://"):
            # Parse s3://bucket/key
            rest = s3_uri[5:]
            if "/" in rest:
                s3_bucket, s3_key = rest.split("/", 1)
            else:
                s3_bucket = rest
                s3_key = os.getenv("S3_INDEX_KEY", "faiss_index.tar.gz")
        else:
            # Fallback to separate bucket/key envs
            s3_bucket = os.getenv("S3_BUCKET_NAME")
            s3_key = os.getenv("S3_INDEX_KEY", "faiss_index.tar.gz")
        
        vector_store = FAISSVectorStore(model_name=embedding_model)

        if not s3_bucket or not s3_key:
            st.error("S3 index configuration missing. Set S3_INDEX_URI or S3_BUCKET_NAME and S3_INDEX_KEY in .env")
            return None

        # Download from S3 to temporary directory (in memory)
        with st.spinner("Loading index from S3..."):
            temp_dir = tempfile.mkdtemp(prefix="faiss_")
            try:
                # Two modes:
                # 1) Tar mode (single archive, e.g., faiss_index.tar.gz)
                # 2) Folder mode (prefix containing individual files: faiss_index.bin, documents.pkl, metadata.pkl, model_name.pkl, dimension.pkl)

                folder_mode = s3_key.endswith("/") or s3_key == "" or s3_key is None or not s3_key.endswith((".tar.gz", ".tgz", ".tar"))

                if folder_mode:
                    import boto3 as _boto3
                    s3 = _boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
                    required_files = [
                        "faiss_index.bin",
                        "documents.pkl",
                        "metadata.pkl",
                        "model_name.pkl",
                        "dimension.pkl",
                    ]
                    prefix = s3_key or ""
                    if prefix and not prefix.endswith("/"):
                        prefix += "/"
                    # Download each file
                    for fname in required_files:
                        key = f"{prefix}{fname}"
                        s3.download_file(s3_bucket, key, str(Path(temp_dir) / fname))

                    # Load the index folder
                    vector_store.load(temp_dir)
                    stats = vector_store.get_stats()
                    st.sidebar.success(
                        f"✓ Loaded index: s3://{s3_bucket}/{prefix} | {stats.get('total_documents', 0)} docs"
                    )
                else:
                    # Tar mode via helper
                    s3_manager = S3FAISSManager(s3_bucket, index_key=s3_key)
                    if not s3_manager.index_exists():
                        st.error(f"Index not found at s3://{s3_bucket}/{s3_key}")
                        return None
                    downloaded_path = s3_manager.download_index(temp_dir)
                    if not downloaded_path or not Path(downloaded_path).exists():
                        st.error("Failed to download index from S3")
                        return None
                    vector_store.load(downloaded_path)
                    stats = vector_store.get_stats()
                    st.sidebar.success(
                        f"✓ Loaded index: s3://{s3_bucket}/{s3_key} | {stats.get('total_documents', 0)} docs"
                    )
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Initialize chatbot
        google_search = StockGoogleSearch()
        region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")
        
        chatbot = StockRAGChatbot(vector_store, google_search, region=region, model_id=model_id)
        
        return chatbot
    
    except Exception as e:
        st.error(f"Initialization error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


def main():
    """Main Streamlit application - Simple chat interface."""
    
    # Simple title
    st.title("Stock Bot")
    
    # Minimal sidebar (no login here; unified flow in main)
    with st.sidebar:
        st.header("Stock Bot")
        st.caption("Powered by AWS Nova Pro")
        # Show resolved S3 path
        _s3uri = os.getenv("S3_INDEX_URI", "").strip()
        if _s3uri.startswith("s3://"):
            st.caption(f"Index: {_s3uri}")
        else:
            st.caption(f"Index: s3://{os.getenv('S3_BUCKET_NAME','')}/{os.getenv('S3_INDEX_KEY','faiss_index.tar.gz')}")
        if st.session_state.user_email:
            st.caption(f"Signed in as {st.session_state.user_email}")
            if st.button("Logout"):
                st.session_state.user_email = None
                st.session_state.messages = []
                st.session_state.session_id = None
                st.rerun()

        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize system
    if st.session_state.chatbot is None:
        with st.spinner("Initializing..."):
            st.session_state.chatbot = initialize_system()
        
        if st.session_state.chatbot:
            st.session_state.index_created = True
        else:
            st.error("Failed to initialize. Check configuration.")
            st.stop()
    
    # Unified login page in main content when not logged in
    if st.session_state.user_email is None:
        st.title("Login")
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        with tab1:
            email = st.text_input("Email", key="login_email_main")
            password = st.text_input("Password", type="password", key="login_pw_main")
            if st.button("Login", key="btn_login_main"):
                if not email or not password:
                    st.error("Please enter email and password.")
                else:
                    try:
                        if st.session_state.auth.login(email, password):
                            st.session_state.user_email = email
                            # Create a new session id on each successful login
                            import uuid
                            st.session_state.session_id = uuid.uuid4().hex
                            msgs = st.session_state.history.get_last_messages(email, session_id=st.session_state.session_id)
                            st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in msgs]
                            st.success("Logged in. Loading chat...")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    except Exception as e:
                        st.error(f"Auth error: {e}")
        with tab2:
            email_su = st.text_input("Email", key="signup_email_main")
            password_su = st.text_input("Password", type="password", key="signup_pw_main")
            if st.button("Create Account", key="btn_signup_main"):
                if not email_su or not password_su:
                    st.error("Please enter email and password.")
                else:
                    try:
                        if st.session_state.auth.signup(email_su, password_su):
                            st.success("Account created. Please login.")
                        else:
                            st.warning("User already exists.")
                    except Exception as e:
                        st.error(f"Signup error: {e}")
        return

    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # User input
    if prompt := st.chat_input("Ask about stocks..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                
                try:
                    # Pass recent conversation so follow-ups are grounded
                    response = st.session_state.chatbot.chat(
                        prompt,
                        conversation_messages=st.session_state.messages,
                    )
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    # Persist to DynamoDB
                    try:
                        st.session_state.history.add_message(st.session_state.user_email, "user", prompt, session_id=st.session_state.session_id)
                        st.session_state.history.add_message(st.session_state.user_email, "assistant", response, session_id=st.session_state.session_id)
                    except Exception:
                        pass
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()

