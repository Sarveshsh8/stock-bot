"""
Unified Financial Analysis Pipeline
Clean, modular orchestration of all components
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import boto3
from pathlib import Path

from ai.faiss.faiss_manager import FAISSManager
from ai.bedrock.video.video_analyzer import VideoAnalyzer
from ai.bedrock.image.image_analyzer import ImageAnalyzer
from ai.sample_questions_generator import SampleQuestionsGenerator
from qa.qa_system import FinancialQASystem
from data.processors.file_processor import FileProcessor

# Optional imports - will be handled gracefully if not available
try:
    from data.downloaders.youtube_downloader import YouTubeDownloader
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    YouTubeDownloader = None

try:
    from storage.s3.s3_manager import S3Manager
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    S3Manager = None

class UnifiedFinancialPipeline:
    """
    Unified pipeline for financial data analysis
    Orchestrates all components in a clean, modular way
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the unified pipeline
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self._setup_logging()
        self._initialize_components()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_components(self):
        """Initialize all pipeline components"""
        try:
            # Initialize FAISS manager
            self.faiss_manager = FAISSManager(self.config)
            self.logger.info(" FAISS Manager initialized")
            
            # Initialize analyzers
            self.video_analyzer = VideoAnalyzer(self.config)
            self.image_analyzer = ImageAnalyzer(self.config)
            self.logger.info(" Nova Pro analyzers initialized")
            
            # Initialize QA system
            self.qa_system = FinancialQASystem(self.config)
            self.logger.info(" Enhanced QA system initialized")
            
            # Initialize sample questions generator
            self.sample_questions_generator = SampleQuestionsGenerator(self.config)
            self.logger.info(" Sample questions generator initialized")
            
            # Initialize file processor
            self.file_processor = FileProcessor(self.config)
            self.logger.info(" File processor initialized")
            
            # Initialize YouTube downloader (optional)
            if YOUTUBE_AVAILABLE:
                self.youtube_downloader = YouTubeDownloader(self.config)
                self.logger.info(" YouTube downloader initialized")
            else:
                self.youtube_downloader = None
                self.logger.warning(" YouTube downloader not available")
            
            # Initialize S3 manager (optional)
            if S3_AVAILABLE:
                self.s3_manager = S3Manager(self.config)
                self.logger.info(" S3 manager initialized")
            else:
                self.s3_manager = None
                self.logger.warning(" S3 manager not available")
            
            self.logger.info(" Unified pipeline initialized successfully")
            
        except Exception as e:
            self.logger.error(f" Failed to initialize pipeline components: {e}")
            raise
    
    def fetch_market_data(self, symbols: List[str], period_months: int = 6) -> Dict[str, pd.DataFrame]:
        """
        Fetch market data from Yahoo Finance
        
        Args:
            symbols: List of stock/ETF symbols
            period_months: Number of months of data to fetch
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        try:
            self.logger.info(f" Fetching market data for {len(symbols)} symbols")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_months * 30)
            
            data = {}
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(start=start_date, end=end_date)
                    if not df.empty:
                        data[symbol] = df
                        self.logger.info(f" Fetched {len(df)} days of data for {symbol}")
                    else:
                        self.logger.warning(f" No data found for {symbol}")
                except Exception as e:
                    self.logger.error(f" Error fetching {symbol}: {e}")
            
            self.logger.info(f" Successfully fetched data for {len(data)} symbols")
            return data
            
        except Exception as e:
            self.logger.error(f" Market data fetch failed: {e}")
            return {}
    
    def process_media_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process media files (images/videos) with Nova Pro
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of processed file data with analysis
        """
        try:
            self.logger.info(f" Processing {len(file_paths)} media files")
            
            processed_files = []
            
            for file_path in file_paths:
                try:
                    file_ext = Path(file_path).suffix.lower()
                    
                    # Validate file first
                    is_valid, file_type, error_msg = self.file_processor.validate_file(file_path)
                    if not is_valid:
                        self.logger.warning(f" {error_msg}: {Path(file_path).name}")
                        continue
                    
                    if file_type == 'documents':
                        # Process documents (PDF, Word, Excel, etc.)
                        result = self.file_processor.process_document(file_path)
                        if 'error' not in result:
                            processed_files.append({
                                'content': result['content'],
                                'metadata': {
                                    'file_path': file_path,
                                    'file_type': 'document',
                                    'source': 'file_processor',
                                    'processed_at': datetime.now().isoformat(),
                                    **result['metadata']
                                }
                            })
                            self.logger.info(f" Processed document: {Path(file_path).name}")
                        else:
                            self.logger.error(f" Document processing failed: {result['error']}")
                    
                    elif file_type == 'videos':
                        # Process video
                        analysis = self.video_analyzer.analyze_video(
                            file_path, 
                            self._get_video_prompt()
                        )
                        processed_files.append({
                            'content': analysis,
                            'metadata': {
                                'file_path': file_path,
                                'file_type': 'video',
                                'source': 'nova_pro_analysis',
                                'processed_at': datetime.now().isoformat()
                            }
                        })
                        self.logger.info(f" Processed video: {Path(file_path).name}")
                    
                    elif file_type == 'images':
                        # Process image
                        analysis = self.image_analyzer.analyze_image(
                            file_path,
                            self._get_image_prompt()
                        )
                        processed_files.append({
                            'content': analysis,
                            'metadata': {
                                'file_path': file_path,
                                'file_type': 'image',
                                'source': 'nova_pro_analysis',
                                'processed_at': datetime.now().isoformat()
                            }
                        })
                        self.logger.info(f" Processed image: {Path(file_path).name}")
                    
                    elif file_type == 'audio':
                        # Process audio (basic processing for now)
                        result = self.file_processor.process_audio(file_path)
                        if 'error' not in result:
                            processed_files.append({
                                'content': f"Audio file: {Path(file_path).name}",
                                'metadata': {
                                    'file_path': file_path,
                                    'file_type': 'audio',
                                    'source': 'file_processor',
                                    'processed_at': datetime.now().isoformat(),
                                    **result['metadata']
                                }
                            })
                            self.logger.info(f" Processed audio: {Path(file_path).name}")
                        else:
                            self.logger.error(f" Audio processing failed: {result['error']}")
                    
                    else:
                        self.logger.warning(f" Unsupported file type: {file_ext}")
                
                except Exception as e:
                    self.logger.error(f" Error processing {file_path}: {e}")
            
            self.logger.info(f" Successfully processed {len(processed_files)} media files")
            return processed_files
            
        except Exception as e:
            self.logger.error(f" Media processing failed: {e}")
            return []
    
    def download_and_analyze_youtube(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Download and analyze YouTube video
        
        Args:
            url: YouTube video URL
            
        Returns:
            Analysis data or None if failed
        """
        if not YOUTUBE_AVAILABLE or not self.youtube_downloader:
            self.logger.error(" YouTube downloader not available")
            return None
            
        try:
            self.logger.info(f" Processing YouTube URL: {url}")
            
            # Validate URL
            if not self.youtube_downloader.validate_url(url):
                self.logger.error(" Invalid YouTube URL")
                return None
            
            # Get video info
            video_info = self.youtube_downloader.get_video_info(url)
            if not video_info:
                self.logger.error(" Could not retrieve video information")
                return None
            
            # Download video
            success, file_path, metadata = self.youtube_downloader.download_video(url)
            if not success:
                self.logger.error(" Failed to download video")
                return None
            
            # Analyze video
            analysis = self.video_analyzer.analyze_video(
                file_path,
                self._get_video_prompt()
            )
            
            # Clean up downloaded file
            try:
                os.unlink(file_path)
                os.rmdir(os.path.dirname(file_path))
            except:
                pass
            
            result = {
                'content': analysis,
                'metadata': {
                    'file_name': f"youtube_{metadata.get('title', 'video')}",
                    'file_type': 'youtube_video',
                    'source': 'youtube_download',
                    'youtube_metadata': metadata,
                    'processed_at': datetime.now().isoformat()
                }
            }
            
            self.logger.info(f" Successfully processed YouTube video: {metadata.get('title', 'Unknown')}")
            return result
            
        except Exception as e:
            self.logger.error(f" YouTube processing failed: {e}")
            return None
    
    def create_unified_index(self, 
                           market_data: Dict[str, pd.DataFrame] = None,
                           processed_files: List[Dict[str, Any]] = None,
                           youtube_analyses: List[Dict[str, Any]] = None) -> bool:
        """
        Create unified FAISS index from all data sources
        
        Args:
            market_data: Yahoo Finance data
            processed_files: Processed media files
            youtube_analyses: YouTube video analyses
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(" Creating unified FAISS index from all data sources")
            
            # Create single unified index with all data sources
            success = self.faiss_manager.create_unified_index(
                yahoo_data=market_data,
                uploaded_files=processed_files,
                youtube_analyses=youtube_analyses
            )
            
            if success:
                # Update QA system with unified FAISS data
                self.qa_system.documents = self.faiss_manager.documents
                self.qa_system.metadata = self.faiss_manager.document_metadata
                self.qa_system.index = self.faiss_manager.index
                
                # Log summary of what was added
                total_docs = len(self.faiss_manager.documents)
                yahoo_count = len(market_data) if market_data else 0
                files_count = len(processed_files) if processed_files else 0
                youtube_count = len(youtube_analyses) if youtube_analyses else 0
                
                self.logger.info(f" Unified index created successfully with {total_docs} total documents:")
                self.logger.info(f"  - Yahoo Finance data: {yahoo_count} symbols")
                self.logger.info(f"  - Uploaded files: {files_count} files")
                self.logger.info(f"  - YouTube videos: {youtube_count} videos")
                
                # Generate and save sample questions using LLM
                self.logger.info(" Generating sample questions from knowledge base using LLM...")
                try:
                    sample_questions = self.sample_questions_generator.generate_questions_from_content(
                        market_data=market_data,
                        processed_files=processed_files,
                        youtube_analyses=youtube_analyses
                    )
                    
                    if sample_questions:
                        filepath = self.sample_questions_generator.save_questions_to_file(sample_questions)
                        if filepath:
                            self.logger.info(f" Sample questions saved to: {filepath}")
                        else:
                            self.logger.warning(" Failed to save sample questions")
                    else:
                        self.logger.warning(" No sample questions generated")
                        
                except Exception as e:
                    self.logger.error(f" Error generating sample questions: {e}")
                
                return True
            else:
                self.logger.error(" Failed to create unified index")
                return False
            
        except Exception as e:
            self.logger.error(f" Index creation failed: {e}")
            return False
    
    def answer_question(self, question: str) -> str:
        """
        Answer a question using AI-powered analysis with retrieved context
        
        Args:
            question: User's question
            
        Returns:
            AI-generated answer based on retrieved context
        """
        try:
            self.logger.info(f" Processing question: {question[:50]}...")
            
            # Search for relevant documents using FAISS
            search_results = self.faiss_manager.search(question, k=10)  # Increased k for better retrieval
            
            if not search_results:
                self.logger.warning("No relevant context found for question")
                return self.qa_system._get_no_context_response(question)
            
            # Log search results for debugging
            self.logger.info(f"Found {len(search_results)} relevant documents")
            for i, result in enumerate(search_results[:3]):  # Log top 3 results
                self.logger.info(f"Result {i+1}: Score={result.get('score', 'N/A'):.3f}, Content preview: {result['content'][:100]}...")
            
            # Extract context from search results
            context_documents = [result['content'] for result in search_results]
            
            # Generate AI-powered answer using the enhanced QA system
            answer = self.qa_system.answer_question(question, context_documents)
            
            self.logger.info(" AI-powered question answered successfully")
            return answer
            
        except Exception as e:
            self.logger.error(f" Question answering failed: {e}")
            return f"Error processing your question: {str(e)}"
    
    def save_to_s3(self, bucket_name: str = None) -> bool:
        """
        Save FAISS index to S3 using local index files
        
        Args:
            bucket_name: S3 bucket name (uses config default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not S3_AVAILABLE or not self.s3_manager or not self.s3_manager.is_available():
            self.logger.error(" S3 manager not available")
            return False
            
        try:
            if bucket_name is None:
                bucket_name = self.config.get('s3_settings', {}).get('bucket_name', 'stock-bot-v3-index')
            
            self.logger.info(f" Saving index to S3 bucket: {bucket_name}")
            
            # Get the latest local index files
            import glob
            local_dir = self.faiss_manager.local_directory
            prefix = self.faiss_manager.filename_prefix
            
            # Find the most recent index file
            pattern = os.path.join(local_dir, f"{prefix}_*.faiss")
            index_files = glob.glob(pattern)
            
            if not index_files:
                self.logger.error("No local index files found to upload")
                return False
            
            # Get the most recent file
            latest_index = max(index_files, key=os.path.getmtime)
            latest_docs = latest_index.replace('.faiss', '_docs.pkl')
            
            if not os.path.exists(latest_docs):
                self.logger.error(f"Corresponding docs file not found: {latest_docs}")
                return False
            
            # Extract timestamp from filename
            filename = os.path.basename(latest_index)
            timestamp = filename.replace(f"{prefix}_", "").replace(".faiss", "")
            
            # Upload to S3
            s3_index_key = f"indexes/{timestamp}/faiss_index.index"
            s3_docs_key = f"indexes/{timestamp}/faiss_docs.pkl"
            
            index_success = self.s3_manager.upload_file(
                latest_index,
                bucket_name,
                s3_index_key
            )
            
            docs_success = self.s3_manager.upload_file(
                latest_docs,
                bucket_name,
                s3_docs_key
            )
            
            if index_success and docs_success:
                self.logger.info(f" Index saved to S3: s3://{bucket_name}/indexes/{timestamp}/")
                return True
            else:
                self.logger.error(" Failed to upload files to S3")
                return False
                
        except Exception as e:
            self.logger.error(f" S3 save failed: {e}")
            return False
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get comprehensive pipeline status
        
        Returns:
            Status dictionary
        """
        return {
            'faiss_manager': self.faiss_manager.get_index_info(),
            'qa_system': self.qa_system.get_index_stats(),
            'components_initialized': {
                'video_analyzer': self.video_analyzer is not None,
                'image_analyzer': self.image_analyzer is not None,
                'youtube_downloader': self.youtube_downloader is not None,
                's3_manager': self.s3_manager is not None
            },
            'pipeline_ready': all([
                self.faiss_manager is not None,
                self.qa_system is not None,
                self.video_analyzer is not None,
                self.image_analyzer is not None
            ])
        }
    
    def _get_video_prompt(self) -> str:
        """Get video analysis prompt"""
        from ai.prompts.financial_prompts import get_video_prompt
        return get_video_prompt("simple_analysis")
    
    def _get_image_prompt(self) -> str:
        """Get image analysis prompt"""
        from ai.prompts.financial_prompts import get_image_prompt
        return get_image_prompt("simple_analysis")
