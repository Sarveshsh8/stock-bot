"""
Unified Financial Analysis Pipeline
Combines Yahoo Finance data fetching, file processing, S3 storage, and FAISS indexing
"""

import yaml
import os
import sys
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.fetchers.yahoo_finance_fetcher import YahooFinanceFetcher
from src.data.processors.file_processor import FileProcessor
from src.storage.s3.s3_manager import S3Manager
from src.ai.faiss.faiss_manager import FAISSManager

class UnifiedPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize the unified pipeline
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.yahoo_fetcher = YahooFinanceFetcher(self.config)
        self.file_processor = FileProcessor(self.config)
        self.s3_manager = S3Manager(self.config)
        self.faiss_manager = FAISSManager(self.config)
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing configuration file: {e}")
            raise
    
    def run_full_pipeline(self, uploaded_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run the complete pipeline
        
        Args:
            uploaded_files: List of file paths to process (optional)
            
        Returns:
            Dictionary containing pipeline results
        """
        self.logger.info("Starting unified financial analysis pipeline")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'yahoo_data': {},
            'uploaded_files': [],
            's3_uploads': [],
            'faiss_index': {},
            'status': 'success'
        }
        
        try:
            # Step 1: Fetch Yahoo Finance data
            self.logger.info("Step 1: Fetching Yahoo Finance data")
            yahoo_data = self.yahoo_fetcher.fetch_data(
                period_months=self.config['data_settings']['default_period_months']
            )
            results['yahoo_data'] = {
                'symbols': list(yahoo_data.keys()),
                'total_symbols': len(yahoo_data)
            }
            
            # Step 2: Upload Yahoo Finance data to S3
            self.logger.info("Step 2: Uploading Yahoo Finance data to S3")
            s3_yahoo_files = self.s3_manager.upload_yahoo_finance_data(yahoo_data)
            results['s3_uploads'].extend(s3_yahoo_files)
            
            # Step 3: Process uploaded files (if any)
            if uploaded_files:
                self.logger.info("Step 3: Processing uploaded files")
                processed_files = []
                
                for file_path in uploaded_files:
                    # Validate file
                    is_valid, file_type, error = self.file_processor.validate_file(file_path)
                    if not is_valid:
                        self.logger.warning(f"Skipping invalid file {file_path}: {error}")
                        continue
                    
                    # Process file based on type
                    if file_type == 'documents':
                        processed_data = self.file_processor.process_document(file_path)
                    elif file_type == 'images':
                        processed_data = self.file_processor.process_image(file_path)
                    elif file_type == 'videos':
                        processed_data = self.file_processor.process_video(file_path)
                    elif file_type == 'audio':
                        processed_data = self.file_processor.process_audio(file_path)
                    else:
                        self.logger.warning(f"Unknown file type: {file_type}")
                        continue
                    
                    if 'error' not in processed_data:
                        processed_files.append(processed_data)
                        
                        # Upload to S3
                        filename = os.path.basename(file_path)
                        s3_key = self.s3_manager.upload_processed_file(
                            processed_data, filename, file_type
                        )
                        results['s3_uploads'].append(s3_key)
                
                results['uploaded_files'] = processed_files
            
            # Step 4: Create FAISS index
            self.logger.info("Step 4: Creating FAISS index")
            
            # Create index from Yahoo Finance data
            faiss_success = self.faiss_manager.create_index_from_yahoo_data(yahoo_data)
            
            # Add uploaded files to index if any
            if uploaded_files and results['uploaded_files']:
                faiss_success = self.faiss_manager.create_index_from_files(results['uploaded_files'])
            
            if faiss_success:
                # Save index locally
                index_path = f"indices/financial_index_{datetime.now().strftime('%Y%m%d_%H%M%S')}.faiss"
                docs_path = f"indices/financial_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                
                os.makedirs('indices', exist_ok=True)
                self.faiss_manager.save_index(index_path, docs_path)
                
                # Upload index to S3
                with open(index_path, 'rb') as f:
                    index_data = f.read()
                with open(docs_path, 'rb') as f:
                    docs_data = f.read()
                
                index_s3_key, docs_s3_key = self.s3_manager.upload_faiss_index(index_data, docs_data)
                results['s3_uploads'].extend([index_s3_key, docs_s3_key])
                
                results['faiss_index'] = {
                    'status': 'created',
                    'local_index': index_path,
                    'local_docs': docs_path,
                    's3_index': index_s3_key,
                    's3_docs': docs_s3_key,
                    'info': self.faiss_manager.get_index_info()
                }
            else:
                results['faiss_index'] = {'status': 'failed'}
                results['status'] = 'partial_success'
            
            self.logger.info("Pipeline completed successfully")
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def query_system(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the FAISS index
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of search results
        """
        if self.faiss_manager.index is None:
            self.logger.warning("No FAISS index available. Run pipeline first.")
            return []
        
        return self.faiss_manager.search(query, k)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'config_loaded': bool(self.config),
            'yahoo_symbols': self.yahoo_fetcher.get_symbol_info(),
            's3_status': self.s3_manager.get_bucket_info(),
            'faiss_status': self.faiss_manager.get_index_info(),
            'supported_file_formats': self.file_processor.get_supported_formats()
        }

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Financial Analysis Pipeline')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--files', nargs='*', help='Files to process')
    parser.add_argument('--query', help='Query the system')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = UnifiedPipeline(args.config)
    
    if args.status:
        # Show system status
        status = pipeline.get_system_status()
        print("System Status:")
        print(f"  Config loaded: {status['config_loaded']}")
        print(f"  Yahoo symbols: {status['yahoo_symbols']['total_count']}")
        print(f"  S3 status: {status['s3_status']['status']}")
        print(f"  FAISS status: {status['faiss_status']['status']}")
        return
    
    if args.query:
        # Query the system
        results = pipeline.query_system(args.query)
        print(f"Query: {args.query}")
        print(f"Results: {len(results)}")
        for i, result in enumerate(results):
            print(f"\nResult {i+1} (Score: {result['score']:.3f}):")
            print(f"Content: {result['content'][:200]}...")
            print(f"Metadata: {result['metadata']}")
        return
    
    # Run full pipeline
    results = pipeline.run_full_pipeline(args.files)
    
    print("Pipeline Results:")
    print(f"  Status: {results['status']}")
    print(f"  Yahoo symbols processed: {results['yahoo_data']['total_symbols']}")
    print(f"  Files uploaded: {len(results['uploaded_files'])}")
    print(f"  S3 uploads: {len(results['s3_uploads'])}")
    print(f"  FAISS index: {results['faiss_index']['status']}")
    
    if results['status'] == 'failed':
        print(f"  Error: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
