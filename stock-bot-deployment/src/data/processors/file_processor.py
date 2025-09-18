"""
File Processor
Handles processing of uploaded files (documents, images, videos)
"""

import os
import base64
import mimetypes
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
import pandas as pd

# Document processing imports
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

class FileProcessor:
    """Processes uploaded files for analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the file processor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.supported_formats = {
            'documents': ['.pdf', '.txt', '.doc', '.docx', '.xlsx', '.csv', '.xls', '.rtf', '.odt'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
        }
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def validate_file(self, file_path: str) -> Tuple[bool, str, str]:
        """
        Validate uploaded file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, file_type, error_message)
        """
        if not os.path.exists(file_path):
            return False, "", "File does not exist"
        
        file_ext = Path(file_path).suffix.lower()
        
        # Check file type
        for file_type, extensions in self.supported_formats.items():
            if file_ext in extensions:
                return True, file_type, ""
        
        return False, "", f"Unsupported file format: {file_ext}"
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process document files
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dictionary containing processed document data
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                return self._process_pdf(file_path)
            elif file_ext in ['.txt', '.rtf']:
                return self._process_text(file_path)
            elif file_ext in ['.docx']:
                return self._process_docx(file_path)
            elif file_ext in ['.xlsx', '.csv', '.xls']:
                return self._process_spreadsheet(file_path)
            else:
                return self._process_generic_document(file_path)
                
        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {str(e)}")
            return {'error': str(e), 'content': '', 'metadata': {}}
    
    def process_image(self, file_path: str) -> Dict[str, Any]:
        """
        Process image files
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary containing processed image data
        """
        try:
            # Encode image to base64
            with open(file_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Get file metadata
            file_size = os.path.getsize(file_path)
            file_name = Path(file_path).name
            
            return {
                'content': image_data,
                'metadata': {
                    'file_name': file_name,
                    'file_size': file_size,
                    'file_type': 'image',
                    'format': Path(file_path).suffix.lower()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing image {file_path}: {str(e)}")
            return {'error': str(e), 'content': '', 'metadata': {}}
    
    def process_video(self, file_path: str) -> Dict[str, Any]:
        """
        Process video files
        
        Args:
            file_path: Path to video file
            
        Returns:
            Dictionary containing processed video data
        """
        try:
            # Encode video to base64
            with open(file_path, 'rb') as video_file:
                video_data = base64.b64encode(video_file.read()).decode('utf-8')
            
            # Get file metadata
            file_size = os.path.getsize(file_path)
            file_name = Path(file_path).name
            
            return {
                'content': video_data,
                'metadata': {
                    'file_name': file_name,
                    'file_size': file_size,
                    'file_type': 'video',
                    'format': Path(file_path).suffix.lower()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing video {file_path}: {str(e)}")
            return {'error': str(e), 'content': '', 'metadata': {}}
    
    def process_audio(self, file_path: str) -> Dict[str, Any]:
        """
        Process audio files
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary containing processed audio data
        """
        try:
            # Encode audio to base64
            with open(file_path, 'rb') as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
            
            # Get file metadata
            file_size = os.path.getsize(file_path)
            file_name = Path(file_path).name
            
            return {
                'content': audio_data,
                'metadata': {
                    'file_name': file_name,
                    'file_size': file_size,
                    'file_type': 'audio',
                    'format': Path(file_path).suffix.lower()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing audio {file_path}: {str(e)}")
            return {'error': str(e), 'content': '', 'metadata': {}}
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF files"""
        if not PDF_AVAILABLE:
            return {
                'content': f"PDF file: {Path(file_path).name} (PDF processing not available - install PyPDF2)",
                'metadata': {
                    'file_name': Path(file_path).name,
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'document',
                    'format': '.pdf',
                    'error': 'PDF processing library not available'
                }
            }
        
        try:
            content = ""
            page_count = 0
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num in range(page_count):
                    page = pdf_reader.pages[page_num]
                    content += page.extract_text() + "\n"
            
            return {
                'content': content.strip(),
                'metadata': {
                    'file_name': Path(file_path).name,
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'document',
                    'format': '.pdf',
                    'page_count': page_count,
                    'word_count': len(content.split()) if content else 0
                }
            }
        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return {
                'content': f"Error processing PDF: {str(e)}",
                'metadata': {
                    'file_name': Path(file_path).name,
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'document',
                    'format': '.pdf',
                    'error': str(e)
                }
            }
    
    def _process_docx(self, file_path: str) -> Dict[str, Any]:
        """Process Word document files"""
        if not DOCX_AVAILABLE:
            return {
                'content': f"Word document: {Path(file_path).name} (Word processing not available - install python-docx)",
                'metadata': {
                    'file_name': Path(file_path).name,
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'document',
                    'format': '.docx',
                    'error': 'Word processing library not available'
                }
            }
        
        try:
            doc = Document(file_path)
            content = ""
            paragraph_count = 0
            
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
                paragraph_count += 1
            
            return {
                'content': content.strip(),
                'metadata': {
                    'file_name': Path(file_path).name,
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'document',
                    'format': '.docx',
                    'paragraph_count': paragraph_count,
                    'word_count': len(content.split()) if content else 0
                }
            }
        except Exception as e:
            self.logger.error(f"Error processing Word document {file_path}: {str(e)}")
            return {
                'content': f"Error processing Word document: {str(e)}",
                'metadata': {
                    'file_name': Path(file_path).name,
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'document',
                    'format': '.docx',
                    'error': str(e)
                }
            }
    
    def _process_text(self, file_path: str) -> Dict[str, Any]:
        """Process text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return {
                'content': content,
                'metadata': {
                    'file_name': Path(file_path).name,
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'document',
                    'format': Path(file_path).suffix.lower(),
                    'word_count': len(content.split()) if content else 0
                }
            }
        except Exception as e:
            return {'error': str(e), 'content': '', 'metadata': {}}
    
    def _process_spreadsheet(self, file_path: str) -> Dict[str, Any]:
        """Process spreadsheet files"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_ext == '.csv':
                df = pd.read_csv(file_path)
            else:
                return {'error': 'Unsupported spreadsheet format', 'content': '', 'metadata': {}}
            
            # Convert to text representation
            content = df.to_string()
            
            return {
                'content': content,
                'metadata': {
                    'file_name': Path(file_path).name,
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'document',
                    'format': file_ext,
                    'rows': len(df),
                    'columns': len(df.columns)
                }
            }
        except Exception as e:
            return {'error': str(e), 'content': '', 'metadata': {}}
    
    def _process_generic_document(self, file_path: str) -> Dict[str, Any]:
        """Process generic document files"""
        return {
            'content': f"Document file: {Path(file_path).name}",
            'metadata': {
                'file_name': Path(file_path).name,
                'file_size': os.path.getsize(file_path),
                'file_type': 'document',
                'format': Path(file_path).suffix.lower()
            }
        }
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported file formats"""
        return self.supported_formats
