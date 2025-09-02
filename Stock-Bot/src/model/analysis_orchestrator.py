"""
Analysis Orchestrator - Coordinates S3 reading, Nova Pro analysis, and output generation
Financial Analyst Focus - Simplified and streamlined
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..aws_code.read_from_s3 import read_file_from_s3, list_s3_files
from .nova_pro_client import NovaProClient
from .prompts import get_comprehensive_analysis_prompt, get_apple_prompt

class AnalysisOrchestrator:
    """
    Orchestrates the complete analysis workflow:
    1. Read files from S3
    2. Analyze with Nova Pro (Financial Analyst)
    3. Generate comprehensive output
    """
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """
        Initialize the orchestrator
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
        """
        self.bucket_name = bucket_name
        # Initialize Nova Pro client
        self.nova_client = NovaProClient(region_name=region, bucket_name=bucket_name)
        self.analysis_results = {}
        self.final_output = {}
    
    def read_files_from_s3(self, prefix: str = "apple_trading_data/") -> List[Dict[str, Any]]:
        """
        Read available files from S3 and categorize them
        
        Args:
            prefix: S3 prefix to search
            
        Returns:
            List of file information dictionaries
        """
        print(f"Reading files from S3 bucket: {self.bucket_name}")
        print(f"Searching prefix: {prefix}")
        
        # List files in S3
        s3_files = list_s3_files(self.bucket_name, prefix)
        
        if not s3_files:
            print("No files found in S3")
            return []
        
        categorized_files = []
        
        for s3_key in s3_files:
            file_info = self._categorize_file(s3_key)
            if file_info:
                categorized_files.append(file_info)
        
        print(f"Found {len(categorized_files)} analyzable files:")
        for file_info in categorized_files:
            print(f"  - {file_info['s3_key']} [{file_info['type']}] - {file_info['category']}")
        
        return categorized_files
    
    def _categorize_file(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Categorize a file based on its S3 key and type"""
        file_ext = os.path.splitext(s3_key)[1].lower()
        
        # Determine file type
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg']:
            file_type = "image"
        elif file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']:
            file_type = "video"
        elif file_ext in ['.xlsx', '.xls', '.csv']:
            file_type = "data"
        else:
            return None  # Skip unsupported file types
        
        # Determine category based on S3 key structure
        if "spreadsheets" in s3_key:
            category = "trading_data"
        elif "videos" in s3_key:
            category = "video_content"
        elif "images" in s3_key:
            category = "chart_analysis"
        else:
            category = "general"
        
        return {
            "s3_key": s3_key,
            "type": file_type,
            "category": category,
            "file_ext": file_ext,
            "timestamp": self._extract_timestamp(s3_key)
        }
    
    def _extract_timestamp(self, s3_key: str) -> str:
        """Extract timestamp from S3 key if available"""
        try:
            # Look for timestamp pattern in S3 key
            parts = s3_key.split('/')
            for part in parts:
                if len(part) >= 14 and part.replace('_', '').isdigit():
                    return part
        except:
            pass
        return "unknown"
    
    def analyze_files(self, files: List[Dict[str, Any]], max_tokens: int = 1500) -> Dict[str, Any]:
        """
        Analyze all files using Nova Pro (Financial Analyst)
        
        Args:
            files: List of file information from S3
            max_tokens: Maximum tokens per analysis
            
        Returns:
            Dictionary of analysis results
        """
        print(f"\nStarting financial analysis of {len(files)} files...")
        
        results = {}
        
        for file_info in files:
            print(f"\nAnalyzing: {file_info['s3_key']}")
            
            try:
                # Get appropriate prompt based on file type and category
                prompt = self._get_analysis_prompt(file_info)
                
                # Analyze based on file type
                if file_info['type'] == "image":
                    result = self._analyze_image_from_s3(file_info, prompt, max_tokens)
                elif file_info['type'] == "video":
                    result = self._analyze_video_from_s3(file_info, prompt, max_tokens)
                elif file_info['type'] == "data":
                    result = self._analyze_data_from_s3(file_info, prompt, max_tokens)
                else:
                    result = f"Unsupported file type: {file_info['type']}"
                
                results[file_info['s3_key']] = {
                    "file_info": file_info,
                    "analysis": result,
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"Financial analysis completed for {file_info['s3_key']}")
                
            except Exception as e:
                print(f"Error analyzing {file_info['s3_key']}: {str(e)}")
                results[file_info['s3_key']] = {
                    "file_info": file_info,
                    "analysis": f"Error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        self.analysis_results = results
        return results
    
    def _get_analysis_prompt(self, file_info: Dict[str, Any]) -> str:
        """Get appropriate financial analysis prompt based on file type and category"""
        if file_info['category'] == "trading_data":
            return get_apple_prompt("trading_data")
        elif file_info['category'] == "video_content":
            return get_apple_prompt("video_content")
        elif file_info['category'] == "chart_analysis":
            return get_comprehensive_analysis_prompt("image", "AAPL")
        else:
            return get_comprehensive_analysis_prompt(file_info['type'])
    
    def _analyze_image_from_s3(self, file_info: Dict[str, Any], prompt: str, max_tokens: int) -> str:
        """Analyze image file from S3 using Nova Pro"""
        try:
            # Read file from S3
            file_content = read_file_from_s3(self.bucket_name, file_info['s3_key'])
            
            if file_content and isinstance(file_content, dict) and 'image_file' in file_content:
                # Get the image file path for analysis
                image_path = file_content.get('local_path')
                if image_path and os.path.exists(image_path):
                    # Analyze the image using Nova Pro
                    analysis_result = self.nova_client.image_analysis_request(
                        prompt, 
                        image_path, 
                        max_tokens
                    )
                    return f"Financial analysis for {file_info['s3_key']}: {analysis_result}"
                else:
                    # If no local path, try to analyze the image content directly
                    return self.nova_client.image_analysis_request(
                        prompt,
                        file_info['s3_key'],  # Pass S3 key for direct analysis
                        max_tokens
                    )
            else:
                return "Unable to analyze image from S3 directly. Consider downloading for local analysis."
                
        except Exception as e:
            return f"Error analyzing image: {str(e)}"
    
    def _analyze_video_from_s3(self, file_info: Dict[str, Any], prompt: str, max_tokens: int) -> str:
        """Analyze video file from S3 using Nova Pro"""
        try:
            print(f"Starting video analysis for: {file_info['s3_key']}")
            
            # Read file from S3
            file_content = read_file_from_s3(self.bucket_name, file_info['s3_key'])
            print(f"File content received: {type(file_content)}")
            
            if file_content and isinstance(file_content, dict):
                print(f"File content keys: {list(file_content.keys())}")
                
                if 'video_file' in file_content:
                    # Get the video file path for analysis
                    video_path = file_content.get('local_path')
                    print(f"Local video path: {video_path}")
                    
                    if video_path and os.path.exists(video_path):
                        print(f"Video file exists locally, size: {os.path.getsize(video_path)} bytes")
                        
                        # Analyze the video using Nova Pro
                        analysis_result = self.nova_client.video_analysis_request(
                            prompt, 
                            video_path, 
                            max_tokens
                        )
                        return f"Financial analysis for {file_info['s3_key']}: {analysis_result}"
                    else:
                        print(f"No local path or file doesn't exist: {video_path}")
                        return "Video file not available locally for analysis"
                else:
                    print(f"Not a video file: {file_content}")
                    return "File is not recognized as a video file"
            else:
                print(f"Invalid file content: {file_content}")
                return "Unable to read video file from S3"
                
        except Exception as e:
            print(f"Error in video analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error analyzing video: {str(e)}"
    
    def _analyze_data_from_s3(self, file_info: Dict[str, Any], prompt: str, max_tokens: int) -> str:
        """Analyze data file from S3 using Nova Pro"""
        try:
            # Read file from S3
            file_content = read_file_from_s3(self.bucket_name, file_info['s3_key'])
            
            if file_content and isinstance(file_content, dict):
                # Analyze the data content
                return self.nova_client.text_only_request(prompt, max_tokens)
            else:
                return "Unable to read data file from S3"
                
        except Exception as e:
            return f"Error analyzing data: {str(e)}"
    
    def generate_final_output(self) -> Dict[str, Any]:
        """
        Generate comprehensive final output combining all financial analysis results
        
        Returns:
            Final comprehensive financial analysis output
        """
        if not self.analysis_results:
            return {"error": "No analysis results available"}
        
        print("\nGenerating comprehensive financial analysis output...")
        
        # Organize results by category
        categorized_results = {}
        for s3_key, result in self.analysis_results.items():
            category = result['file_info']['category']
            if category not in categorized_results:
                categorized_results[category] = []
            categorized_results[category].append(result)
        
        # Generate summary for each category
        category_summaries = {}
        for category, results in categorized_results.items():
            summary = self._generate_category_summary(category, results)
            category_summaries[category] = summary
        
        # Generate overall insights
        overall_insights = self._generate_overall_insights()
        
        # Compile final output
        final_output = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_files_analyzed": len(self.analysis_results),
                "categories_analyzed": list(categorized_results.keys()),
                "analysis_type": "Financial Analyst"
            },
            "category_summaries": category_summaries,
            "overall_insights": overall_insights,
            "detailed_results": self.analysis_results,
            "financial_recommendations": self._generate_financial_recommendations()
        }
        
        self.final_output = final_output
        return final_output
    
    def _generate_category_summary(self, category: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary for a specific category"""
        if category == "trading_data":
            return {
                "summary": f"Analyzed {len(results)} trading data files",
                "key_findings": "Financial metrics and performance indicators",
                "files": [r['file_info']['s3_key'] for r in results]
            }
        elif category == "video_content":
            return {
                "summary": f"Analyzed {len(results)} video content files",
                "key_findings": "Visual and audio content analysis",
                "files": [r['file_info']['s3_key'] for r in results]
            }
        elif category == "chart_analysis":
            return {
                "summary": f"Analyzed {len(results)} chart/image files",
                "key_findings": "Technical analysis and visual patterns",
                "files": [r['file_info']['s3_key'] for r in results]
            }
        else:
            return {
                "summary": f"Analyzed {len(results)} {category} files",
                "key_findings": "General financial content analysis",
                "files": [r['file_info']['s3_key'] for r in results]
            }
    
    def _generate_overall_insights(self) -> Dict[str, Any]:
        """Generate overall financial insights from all analyses"""
        total_files = len(self.analysis_results)
        successful_analyses = sum(1 for r in self.analysis_results.values() 
                                if not r['analysis'].startswith('Error'))
        
        return {
            "total_files": total_files,
            "successful_analyses": successful_analyses,
            "success_rate": f"{(successful_analyses/total_files)*100:.1f}%" if total_files > 0 else "0%",
            "analysis_coverage": "Comprehensive financial analysis of Apple trading data across multiple formats",
            "key_insights": "Combined financial analysis of trading data, video content, and visual charts"
        }
    
    def _generate_financial_recommendations(self) -> List[str]:
        """Generate actionable financial recommendations based on analysis"""
        recommendations = [
            "Review trading data analysis for investment decisions",
            "Consider video content insights for market sentiment",
            "Use chart analysis for technical trading signals",
            "Combine all analyses for comprehensive market understanding"
        ]
        
        if self.analysis_results:
            if any('trading_data' in r['file_info']['category'] for r in self.analysis_results.values()):
                recommendations.append("Focus on key financial metrics from trading data")
            
            if any('video_content' in r['file_info']['category'] for r in self.analysis_results.values()):
                recommendations.append("Leverage video content insights for strategic decisions")
        
        return recommendations
    
    def save_output(self, output_path: str = None):
        """Save the final output to a file"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"financial_analysis_{timestamp}.json"
        
        try:
            with open(output_path, 'w') as f:
                json.dump(self.final_output, f, indent=2, default=str)
            
            print(f"Financial analysis output saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error saving output: {str(e)}")
            return None
    
    def run_complete_analysis(self, prefix: str = "apple_trading_data/", 
                             max_tokens: int = 1500, save_output: bool = True) -> Dict[str, Any]:
        """
        Run the complete financial analysis workflow
        
        Args:
            prefix: S3 prefix to search
            max_tokens: Maximum tokens per analysis
            save_output: Whether to save output to file
            
        Returns:
            Final comprehensive financial analysis output
        """
        print("="*60)
        print("COMPREHENSIVE FINANCIAL ANALYSIS WORKFLOW")
        print("="*60)
        
        # Step 1: Read files from S3
        print("\nSTEP 1: Reading files from S3...")
        files = self.read_files_from_s3(prefix)
        
        if not files:
            print("No files to analyze. Exiting.")
            return {}
        
        # Step 2: Analyze all files
        print("\nSTEP 2: Analyzing files with Nova Pro (Financial Analyst)...")
        self.analyze_files(files, max_tokens)
        
        # Step 3: Generate final output
        print("\nSTEP 3: Generating comprehensive financial output...")
        final_output = self.generate_final_output()
        
        # Step 4: Save output if requested
        if save_output:
            print("\nSTEP 4: Saving financial analysis output...")
            self.save_output()
        
        print("\n" + "="*60)
        print("FINANCIAL ANALYSIS WORKFLOW COMPLETED")
        print("="*60)
        
        return final_output
