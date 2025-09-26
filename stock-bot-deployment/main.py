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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([" Upload Files", " Market Data", " YouTube", " Q&A", " Wheel Strategy"])
    
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
    
    with tab5:
        st.subheader(" Wheel Strategy Analysis")
        st.markdown("**Analyze stocks for wheel options strategy using AI-powered prompt engineering**")
        
        # Initialize wheel strategy analyzer
        if 'wheel_analyzer' not in st.session_state:
            try:
                from ai.wheel_strategy_analyzer import WheelStrategyAnalyzer
                st.session_state.wheel_analyzer = WheelStrategyAnalyzer()
                st.session_state.wheel_data_info = st.session_state.wheel_analyzer.get_available_data_info()
            except Exception as e:
                st.error(f"Error initializing wheel strategy analyzer: {str(e)}")
                st.session_state.wheel_analyzer = None
        
        if st.session_state.wheel_analyzer:
            # Data info section
            with st.expander(" Data Information", expanded=True):
                if st.session_state.wheel_data_info and 'error' not in st.session_state.wheel_data_info:
                    info = st.session_state.wheel_data_info
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Available Dates", info.get('total_dates', 0))
                    with col2:
                        st.metric("Latest Date", info.get('latest_date', 'N/A'))
                    with col3:
                        if 'latest_date_info' in info:
                            st.metric("Total Tickers", info['latest_date_info'].get('total_tickers', 0))
                    
                    if 'latest_date_info' in info and 'sample_tickers' in info['latest_date_info']:
                        st.markdown("**Sample Tickers by Letter:**")
                        sample_text = ""
                        for letter, tickers in info['latest_date_info']['sample_tickers'].items():
                            if tickers:
                                sample_text += f"**{letter}:** {', '.join(tickers[:3])}{'...' if len(tickers) > 3 else ''}  \n"
                        st.markdown(sample_text)
                else:
                    st.error("No wheel strategy data available")
            
            # Analysis options
            st.markdown("### Analysis Options")
            
            analysis_option = st.selectbox(
                "Choose Analysis Type:",
                ["Single Ticker Analysis", "Compare Multiple Tickers", "Find Top Candidates", "Custom Analysis"]
            )
            
            if analysis_option == "Single Ticker Analysis":
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    ticker = st.text_input("Enter Ticker Symbol:", placeholder="e.g., AAPL, MSFT, TSLA").upper()
                
                with col2:
                    analysis_type = st.selectbox(
                        "Analysis Type:",
                        ["analysis", "entry_signals", "risk_management", "performance_tracking"],
                        format_func=lambda x: {
                            "analysis": "General Analysis",
                            "entry_signals": "Entry Signals",
                            "risk_management": "Risk Management", 
                            "performance_tracking": "Performance Tracking"
                        }[x]
                    )
                
                if st.button(" Analyze Ticker") and ticker:
                    with st.spinner(f"Analyzing {ticker} for wheel strategy..."):
                        try:
                            result = st.session_state.wheel_analyzer.analyze_ticker(ticker, analysis_type=analysis_type)
                            
                            if 'error' in result:
                                st.error(f"Error: {result['error']}")
                            else:
                                # Display results
                                st.success(f"Analysis completed for {ticker}")
                                
                                # Basic info
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Current Price", f"${result['data_summary']['current_price']:.2f}")
                                with col2:
                                    st.metric("Data Points", result['data_summary']['total_bars'])
                                with col3:
                                    suitability = result.get('technical_analysis', {}).get('wheel_recommendations', {}).get('suitability_score', 'Unknown')
                                    st.metric("Suitability", suitability)
                                
                                # Technical analysis summary
                                if 'technical_analysis' in result:
                                    tech = result['technical_analysis']
                                    
                                    st.markdown("**Quick Stats:**")
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        if 'liquidity' in tech:
                                            st.markdown(f"**Liquidity Score:** {tech['liquidity'].get('liquidity_score', 'N/A')}")
                                            st.markdown(f"**Avg Volume:** {tech['liquidity'].get('avg_volume', 0):,.0f}")
                                        
                                        if 'wheel_recommendations' in tech and 'put_strikes' in tech['wheel_recommendations']:
                                            strikes = tech['wheel_recommendations']['put_strikes']
                                            st.markdown(f"**10% OTM Put:** ${strikes.get('10_percent_otm', 0):.2f}")
                                    
                                    with col2:
                                        if 'volatility' in tech:
                                            st.markdown(f"**Volatility Rank:** {tech['volatility'].get('volatility_rank', 'N/A')}")
                                            st.markdown(f"**Ann. Volatility:** {tech['volatility'].get('annualized_volatility', 0):.1%}")
                                        
                                        if 'wheel_recommendations' in tech and 'estimated_premium_pct' in tech['wheel_recommendations']:
                                            premium = tech['wheel_recommendations']['estimated_premium_pct']
                                            st.markdown(f"**Est. Premium (10% OTM):** {premium.get('10_percent_otm', 0):.1%}")
                                
                                # AI Analysis
                                st.markdown("### AI Analysis")
                                if 'ai_analysis' in result:
                                    st.markdown(f"""
                                    <div style="
                                        background-color: #f0f2f6;
                                        padding: 20px;
                                        border-radius: 10px;
                                        border-left: 5px solid #007bff;
                                        color: #262730;
                                        font-size: 14px;
                                        line-height: 1.6;
                                    ">
                                        {result['ai_analysis'].replace(chr(10), '<br>')}
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                        except Exception as e:
                            st.error(f"Analysis error: {str(e)}")
            
            elif analysis_option == "Compare Multiple Tickers":
                st.markdown("**Compare multiple tickers for wheel strategy suitability**")
                
                # Input for multiple tickers
                tickers_input = st.text_input(
                    "Enter Ticker Symbols (comma-separated):",
                    placeholder="e.g., AAPL, MSFT, TSLA, SPY"
                )
                
                if st.button(" Compare Tickers") and tickers_input:
                    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
                    
                    if len(tickers) > 5:
                        st.warning("Limiting comparison to first 5 tickers for performance")
                        tickers = tickers[:5]
                    
                    with st.spinner(f"Comparing {len(tickers)} tickers..."):
                        try:
                            comparison = st.session_state.wheel_analyzer.compare_tickers(tickers)
                            
                            if 'error' in comparison:
                                st.error(f"Error: {comparison['error']}")
                            else:
                                st.success("Comparison completed!")
                                
                                # Display comparison table
                                if 'comparison_data' in comparison and comparison['comparison_data']:
                                    df = pd.DataFrame(comparison['comparison_data'])
                                    
                                    # Format the dataframe for display
                                    display_df = df.copy()
                                    display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
                                    display_df['avg_volume'] = display_df['avg_volume'].apply(lambda x: f"{x:,.0f}")
                                    display_df['volatility'] = display_df['volatility'].apply(lambda x: f"{x:.1%}")
                                    display_df['put_10_otm'] = display_df['put_10_otm'].apply(lambda x: f"${x:.2f}")
                                    display_df['estimated_premium_10_otm'] = display_df['estimated_premium_10_otm'].apply(lambda x: f"{x:.1%}")
                                    
                                    # Rename columns for display
                                    display_df.columns = [
                                        'Ticker', 'Current Price', 'Suitability', 'Liquidity', 
                                        'Volatility', 'Avg Volume', '10% OTM Put', 'Est. Premium'
                                    ]
                                    
                                    st.markdown("**Comparison Table:**")
                                    st.dataframe(display_df, use_container_width=True)
                                
                                # AI Comparison Analysis
                                if 'ai_comparison' in comparison:
                                    st.markdown("### AI Comparison Analysis")
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
                                        {comparison['ai_comparison'].replace(chr(10), '<br>')}
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                        except Exception as e:
                            st.error(f"Comparison error: {str(e)}")
            
            elif analysis_option == "Find Top Candidates":
                st.markdown("**Find the best wheel strategy candidates from available data**")
                
                col1, col2 = st.columns(2)
                with col1:
                    limit = st.number_input("Number of candidates:", min_value=5, max_value=20, value=10)
                with col2:
                    min_volume = st.number_input("Minimum avg volume:", min_value=1000, max_value=100000, value=10000, step=1000)
                
                if st.button(" Find Top Candidates"):
                    with st.spinner("Analyzing candidates..."):
                        try:
                            candidates = st.session_state.wheel_analyzer.get_top_wheel_candidates(
                                limit=limit, min_volume=min_volume
                            )
                            
                            if candidates:
                                st.success(f"Found {len(candidates)} candidates")
                                
                                # Create dataframe for display
                                df = pd.DataFrame(candidates)
                                
                                # Format for display
                                display_df = df.copy()
                                display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
                                display_df['avg_volume'] = display_df['avg_volume'].apply(lambda x: f"{x:,.0f}")
                                display_df['annualized_volatility'] = display_df['annualized_volatility'].apply(lambda x: f"{x:.1%}")
                                
                                # Select columns for display
                                display_cols = ['ticker', 'current_price', 'suitability_score', 'liquidity_score', 
                                              'volatility_rank', 'avg_volume', 'annualized_volatility']
                                display_df = display_df[display_cols]
                                
                                # Rename columns
                                display_df.columns = ['Ticker', 'Price', 'Suitability', 'Liquidity', 
                                                    'Vol Rank', 'Avg Volume', 'Ann. Volatility']
                                
                                st.dataframe(display_df, use_container_width=True)
                                
                                # Show top 3 with more details
                                st.markdown("### Top 3 Candidates Details")
                                for i, candidate in enumerate(candidates[:3]):
                                    with st.expander(f"{i+1}. {candidate['ticker']} - {candidate['suitability_score']}"):
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown(f"**Current Price:** ${candidate['current_price']:.2f}")
                                            st.markdown(f"**Suitability:** {candidate['suitability_score']}")
                                            st.markdown(f"**Liquidity:** {candidate['liquidity_score']}")
                                        
                                        with col2:
                                            st.markdown(f"**Volatility:** {candidate['volatility_rank']}")
                                            st.markdown(f"**Avg Volume:** {candidate['avg_volume']:,.0f}")
                                            st.markdown(f"**Ann. Vol:** {candidate['annualized_volatility']:.1%}")
                                        
                                        # Put strike recommendations
                                        strikes = candidate['put_strikes']
                                        st.markdown("**Suggested Put Strikes:**")
                                        st.markdown(f"• 5% OTM: ${strikes['5_percent_otm']:.2f}")
                                        st.markdown(f"• 10% OTM: ${strikes['10_percent_otm']:.2f}")
                                        st.markdown(f"• 15% OTM: ${strikes['15_percent_otm']:.2f}")
                            else:
                                st.warning("No candidates found matching the criteria")
                                
                        except Exception as e:
                            st.error(f"Error finding candidates: {str(e)}")
            
            elif analysis_option == "Custom Analysis":
                st.markdown("**Enter a custom ticker for detailed wheel strategy analysis**")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    custom_ticker = st.text_input("Enter any ticker symbol:", placeholder="e.g., NVDA").upper()
                with col2:
                    if st.button(" Quick Analysis") and custom_ticker:
                        with st.spinner(f"Quick analysis for {custom_ticker}..."):
                            try:
                                # Get just the technical analysis without full AI processing for speed
                                df = st.session_state.wheel_analyzer.processor.load_ticker_data(custom_ticker, None)
                                if df is not None:
                                    df_with_indicators = st.session_state.wheel_analyzer.processor.calculate_technical_indicators(df)
                                    analysis = st.session_state.wheel_analyzer.processor.analyze_wheel_suitability(df_with_indicators, custom_ticker)
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Current Price", f"${analysis['price_stats']['current_price']:.2f}")
                                    with col2:
                                        st.metric("Suitability", analysis['wheel_recommendations']['suitability_score'])
                                    with col3:
                                        st.metric("Liquidity", analysis['liquidity']['liquidity_score'])
                                    
                                    # Quick recommendations
                                    strikes = analysis['wheel_recommendations']['put_strikes']
                                    st.markdown("**Quick Put Strike Suggestions:**")
                                    st.markdown(f"• Conservative (5% OTM): ${strikes['5_percent_otm']:.2f}")
                                    st.markdown(f"• Moderate (10% OTM): ${strikes['10_percent_otm']:.2f}")
                                    st.markdown(f"• Aggressive (15% OTM): ${strikes['15_percent_otm']:.2f}")
                                else:
                                    st.error(f"No data found for {custom_ticker}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                # Full custom analysis
                if custom_ticker:
                    st.markdown("---")
                    if st.button(f" Full AI Analysis for {custom_ticker}"):
                        with st.spinner("Performing full AI analysis..."):
                            try:
                                result = st.session_state.wheel_analyzer.analyze_ticker(custom_ticker)
                                
                                if 'error' in result:
                                    st.error(f"Error: {result['error']}")
                                else:
                                    st.success("Full analysis completed!")
                                    
                                    # Show AI analysis
                                    if 'ai_analysis' in result:
                                        st.markdown("### AI Analysis")
                                        st.markdown(f"""
                                        <div style="
                                            background-color: #f0f2f6;
                                            padding: 20px;
                                            border-radius: 10px;
                                            border-left: 5px solid #6c757d;
                                            color: #262730;
                                            font-size: 14px;
                                            line-height: 1.6;
                                        ">
                                            {result['ai_analysis'].replace(chr(10), '<br>')}
                                        </div>
                                        """, unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        else:
            st.error("Wheel Strategy Analyzer not available. Please check the configuration.")
    
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
