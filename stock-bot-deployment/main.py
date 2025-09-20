"""
Stock Bot - Main Application
Clean, modular financial analysis application
"""

# Fix PyTorch device issues before importing anything else
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['PYTORCH_DISABLE_MPS'] = '1'
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import streamlit as st
import sys
import yaml
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import asyncio
import tempfile
import threading
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Import voice functionality
try:
    from ai.voice.voice_handler import is_voice_available, convert_speech_to_text, create_test_audio_file
    import pyaudio
    import wave
    VOICE_AVAILABLE = is_voice_available()
except ImportError:
    VOICE_AVAILABLE = False

def record_audio_from_microphone():
    """Record audio from microphone and return the file path."""
    if not VOICE_AVAILABLE:
        return None
    
    try:
        # Audio configuration
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        # Get recording duration from session state or use default
        RECORD_SECONDS = st.session_state.get('recording_duration', 5)  # Default 5 seconds for faster processing
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        # Start recording
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
        
        frames = []
        total_chunks = int(RATE / CHUNK * RECORD_SECONDS)
        
        for i in range(total_chunks):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        
        # Stop recording
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save to file
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error recording audio: {e}")
        return None

def record_audio_with_manual_control():
    """Record audio with manual start/stop control."""
    if not VOICE_AVAILABLE:
        return None
    
    try:
        # Audio configuration
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        # Start recording
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
        
        frames = []
        recording = True
        
        # Record until manually stopped
        while recording and len(frames) < (RATE / CHUNK * 60):  # Max 60 seconds
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            # Check if recording should stop (this will be controlled by the UI)
            # For now, we'll use a reasonable duration
            if len(frames) >= (RATE / CHUNK * st.session_state.get('recording_duration', 10)):
                break
        
        # Stop recording
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save to file
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error recording audio: {e}")
        return None

# Page configuration
st.set_page_config(
    page_title="Stock Bot - Financial Analysis",
    page_icon="",
    layout="wide"
)

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        st.error(f"Failed to load config: {str(e)}")
        return None

def initialize_pipeline():
    """Initialize the unified pipeline"""
    try:
        from core.unified_pipeline import UnifiedFinancialPipeline
        config = load_config()
        if not config:
            return None, "Configuration not loaded"
        
        pipeline = UnifiedFinancialPipeline(config)
        return pipeline, "Pipeline initialized successfully"
    except Exception as e:
        return None, f"Pipeline initialization failed: {str(e)}"

def main():
    """Main application interface"""
    st.title(" Stock Bot - Financial Analysis")
    st.markdown("**Unified Financial Data Analysis Platform**")
    
    # Initialize session state
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None
    if 'initialization_status' not in st.session_state:
        st.session_state.initialization_status = None
    
    # Initialize pipeline
    if st.session_state.pipeline is None:
        with st.spinner("Initializing pipeline..."):
            pipeline, status = initialize_pipeline()
            st.session_state.pipeline = pipeline
            st.session_state.initialization_status = status
    
    # Show initialization status
    if st.session_state.initialization_status:
        if "successfully" in st.session_state.initialization_status:
            st.success(f" {st.session_state.initialization_status}")
        else:
            st.error(f" {st.session_state.initialization_status}")
            st.stop()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([" Upload Files", " Market Data", " YouTube", " Q&A"])
    
    with tab1:
        st.subheader(" File Upload & Analysis")
        
        # Show supported file types
        with st.expander(" Supported File Types"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("** Documents**")
                st.markdown("• PDF (.pdf)")
                st.markdown("• Word (.docx, .doc)")
                st.markdown("• Text (.txt, .rtf)")
                st.markdown("• Excel (.xlsx, .xls)")
                st.markdown("• CSV (.csv)")
            with col2:
                st.markdown("** Images**")
                st.markdown("• JPG/JPEG")
                st.markdown("• PNG")
                st.markdown("• GIF")
                st.markdown("• BMP, TIFF")
                st.markdown("• WebP")
            with col3:
                st.markdown("** Videos**")
                st.markdown("• MP4")
                st.markdown("• AVI, MOV")
                st.markdown("• WMV, FLV")
                st.markdown("• WebM, MKV")
            with col4:
                st.markdown("** Audio**")
                st.markdown("• MP3")
                st.markdown("• WAV, FLAC")
                st.markdown("• AAC, OGG")
                st.markdown("• M4A")
        
        uploaded_files = st.file_uploader(
            "Upload financial documents, charts, or videos:",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt', 'rtf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'],
            help="Maximum file size: 500 MB per file"
        )
        
        if uploaded_files:
            if st.button(" Process Files"):
                if st.session_state.pipeline:
                    with st.spinner("Processing files..."):
                        try:
                            # Save files temporarily
                            file_paths = []
                            for uploaded_file in uploaded_files:
                                file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                                with open(f"temp_{uploaded_file.name}", "wb") as f:
                                    f.write(uploaded_file.getvalue())
                                file_paths.append(f"temp_{uploaded_file.name}")
                            
                            # Process files
                            processed_files = st.session_state.pipeline.process_media_files(file_paths)
                            
                            # Clean up temp files
                            for file_path in file_paths:
                                try:
                                    os.unlink(file_path)
                                except:
                                    pass
                            
                            if processed_files:
                                st.success(f" Successfully processed {len(processed_files)} files")
                                st.session_state.processed_files = processed_files
                                
                                # Display results
                                for i, file_data in enumerate(processed_files):
                                    with st.expander(f" {file_data['metadata'].get('file_path', f'File {i+1}')}"):
                                        st.markdown("**Analysis:**")
                                        st.markdown(f"""
                                        <div style="
                                            background-color: #f0f2f6;
                                            padding: 15px;
                                            border-radius: 5px;
                                            border-left: 3px solid #1f77b4;
                                            color: #262730;
                                            font-size: 14px;
                                            line-height: 1.6;
                                        ">
                                            {file_data['content'].replace(chr(10), '<br>')}
                                        </div>
                                        """, unsafe_allow_html=True)
                            else:
                                st.error(" Failed to process files")
                        except Exception as e:
                            st.error(f" Error processing files: {str(e)}")
                else:
                    st.error("Pipeline not initialized")
    
    with tab2:
        st.subheader(" Market Data")
        
        config = load_config()
        if config:
            etf_symbols = [etf['symbol'] for etf in config.get('etfs', [])]
            stock_symbols = [stock['symbol'] for stock in config.get('stocks', [])]
            all_symbols = etf_symbols + stock_symbols
            
            if all_symbols:
                st.write(f"**Available Symbols:** {', '.join(all_symbols)}")
                
                if st.button(" Fetch Market Data"):
                    if st.session_state.pipeline:
                        with st.spinner("Fetching market data..."):
                            try:
                                market_data = st.session_state.pipeline.fetch_market_data(all_symbols, 3)
                                if market_data:
                                    st.session_state.market_data = market_data
                                    st.success(f" Fetched data for {len(market_data)} symbols")
                                    
                                    # Display summary
                                    for symbol, df in market_data.items():
                                        latest_price = df['Close'].iloc[-1]
                                        price_change = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100)
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric(f"{symbol} Price", f"${latest_price:.2f}")
                                        with col2:
                                            st.metric(f"{symbol} Change", f"{price_change:.2f}%")
                                        with col3:
                                            st.metric(f"{symbol} Records", len(df))
                                else:
                                    st.error(" Failed to fetch market data")
                            except Exception as e:
                                st.error(f" Error fetching market data: {str(e)}")
                    else:
                        st.error("Pipeline not initialized")
            else:
                st.warning("No symbols configured in config.yaml")
    
    with tab3:
        st.subheader(" YouTube Video Analysis")
        
        st.info(" **Large Video Support**: Videos up to 500 MB can be downloaded and analyzed")
        
        youtube_url = st.text_input(
            "Enter YouTube URL:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste a YouTube video URL to download and analyze (supports videos up to 500 MB)"
        )
        
        if youtube_url:
            if st.button(" Download & Analyze"):
                if st.session_state.pipeline:
                    with st.spinner("Processing YouTube video..."):
                        try:
                            analysis = st.session_state.pipeline.download_and_analyze_youtube(youtube_url)
                            
                            if analysis:
                                if 'youtube_analyses' not in st.session_state:
                                    st.session_state.youtube_analyses = []
                                st.session_state.youtube_analyses.append(analysis)
                                st.success(" YouTube video analyzed successfully")
                                
                                # Display analysis
                                st.subheader(" Analysis Results")
                                st.markdown("**Video Analysis:**")
                                st.markdown(f"""
                                <div style="
                                    background-color: #f0f2f6;
                                    padding: 20px;
                                    border-radius: 10px;
                                    border-left: 5px solid #1f77b4;
                                    color: #262730;
                                    font-size: 14px;
                                    line-height: 1.6;
                                ">
                                    {analysis['content'].replace(chr(10), '<br>')}
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.error(" Failed to analyze YouTube video")
                        except Exception as e:
                            st.error(f" Error analyzing YouTube video: {str(e)}")
                else:
                    st.error("Pipeline not initialized")
    
    with tab4:
        st.subheader(" Question & Answer")
        
        # Index management buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(" Create Knowledge Index"):
                if st.session_state.pipeline:
                    with st.spinner("Creating unified index..."):
                        try:
                            success = st.session_state.pipeline.create_unified_index(
                                market_data=getattr(st.session_state, 'market_data', {}),
                                processed_files=getattr(st.session_state, 'processed_files', []),
                                youtube_analyses=getattr(st.session_state, 'youtube_analyses', [])
                            )
                            
                            if success:
                                st.session_state.index_created = True
                                st.success(" Knowledge index created successfully")
                            else:
                                st.error(" Failed to create index")
                        except Exception as e:
                            st.error(f" Error creating index: {str(e)}")
                else:
                    st.error("Pipeline not initialized")
        
        with col2:
            if st.button(" Clear Old Indices"):
                if st.session_state.pipeline:
                    with st.spinner("Clearing old indices..."):
                        try:
                            success = st.session_state.pipeline.faiss_manager.clear_old_indices()
                            if success:
                                st.success(" Old indices cleared - fresh indexing will be performed")
                                st.session_state.index_created = False
                            else:
                                st.error(" Failed to clear old indices")
                        except Exception as e:
                            st.error(f" Error clearing indices: {str(e)}")
                else:
                    st.error("Pipeline not initialized")
        
        # Q&A interface
        if getattr(st.session_state, 'index_created', False):
            st.markdown("---")
            st.subheader(" Ask Questions")
            
            # Voice input option
            if VOICE_AVAILABLE:
                # Initialize voice transcription state
                if 'voice_transcription' not in st.session_state:
                    st.session_state.voice_transcription = ""
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Use the voice transcription as default value if available
                    default_query = st.session_state.voice_transcription if st.session_state.voice_transcription else ""
                    query = st.text_input(
                        "Ask me anything about your financial data:",
                        placeholder="What's the trend for AAPL? How does SPY compare to QQQ?",
                        key="query_input",
                        value=default_query
                    )
                with col2:
                    st.markdown("**Voice Input**")
                    st.markdown("*Speak clearly - I'll detect when you stop*")
                    st.markdown("*Smart recording: stops after 4s of silence*")
                    
                    if st.button("🎤 Record Voice", help="Record your question using voice"):
                        st.session_state.voice_recording = True
                
                # Voice recording interface
                if getattr(st.session_state, 'voice_recording', False):
                    st.info("🎤 Recording audio... Speak now! (I'll detect when you stop)")
                    
                    # Show recording status
                    status_text = st.empty()
                    status_text.info("🎤 Listening for your voice...")
                    
                    # Cancel button only
                    if st.button("❌ Cancel Recording"):
                        st.session_state.voice_recording = False
                        status_text.empty()
                    
                    # Process voice immediately when recording starts (smart detection)
                    with st.spinner("Processing voice input..."):
                        try:
                            # Use real-time voice processing directly (no file needed)
                            print(f"Processing voice input using real-time approach...")
                            transcribed_text = asyncio.run(convert_speech_to_text("dummy_path"))
                            print(f"Transcription result: {transcribed_text}")
                            
                            if transcribed_text and "Voice input received" not in transcribed_text:
                                st.session_state.voice_transcription = transcribed_text
                                st.success(f"🎤 Voice transcribed: '{transcribed_text}'")
                                st.session_state.voice_recording = False
                                st.rerun()  # Rerun to update the text input with transcribed text
                            elif transcribed_text and "Voice input received" in transcribed_text:
                                st.warning("🎤 Voice input detected but transcription pending. Please speak clearly into your microphone and try again.")
                                st.info("💡 **Tip**: Speak clearly and avoid background noise.")
                                st.session_state.voice_transcription = ""
                                st.session_state.voice_recording = False
                            else:
                                st.error("❌ Could not transcribe voice input")
                                st.session_state.voice_recording = False
                            
                        except Exception as e:
                            st.error(f"❌ Voice processing error: {str(e)}")
                            st.session_state.voice_recording = False
            else:
                query = st.text_input(
                    "Ask me anything about your financial data:",
                    placeholder="What's the trend for AAPL? How does SPY compare to QQQ?"
                )
                if not VOICE_AVAILABLE:
                    st.info("💡 Voice input not available. Install AWS SDK v2 for voice functionality.")
            
            if st.button(" Get Answer") and query:
                if st.session_state.pipeline:
                    with st.spinner("Generating answer..."):
                        try:
                            answer = st.session_state.pipeline.answer_question(query)
                            
                            st.markdown("**Answer:**")
                            st.markdown(f"""
                            <div style="
                                background-color: #f0f2f6;
                                padding: 20px;
                                border-radius: 10px;
                                border-left: 5px solid #28a745;
                                color: #262730;
                                font-size: 14px;
                                line-height: 1.6;
                            ">
                                {answer.replace(chr(10), '<br>')}
                            </div>
                            """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f" Error generating answer: {str(e)}")
                else:
                    st.error("Pipeline not initialized")
        else:
            st.info(" Create a knowledge index first to enable Q&A functionality")
    
    # Status sidebar
    with st.sidebar:
        st.subheader(" System Status")
        
        if st.session_state.pipeline:
            try:
                status = st.session_state.pipeline.get_pipeline_status()
                
                st.metric("Files Processed", len(getattr(st.session_state, 'processed_files', [])))
                st.metric("YouTube Videos", len(getattr(st.session_state, 'youtube_analyses', [])))
                st.metric("Market Symbols", len(getattr(st.session_state, 'market_data', {})))
                st.metric("Index Created", "" if getattr(st.session_state, 'index_created', False) else "")
                st.metric("Voice Input", "🎤 Available" if VOICE_AVAILABLE else "❌ Not Available")
                
                if st.button(" Refresh Status"):
                    st.rerun()
            except Exception as e:
                st.error(f"Status error: {str(e)}")
        else:
            st.warning("Pipeline not initialized")

if __name__ == "__main__":
    main()
