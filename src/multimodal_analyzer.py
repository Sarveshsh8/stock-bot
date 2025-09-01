#!/usr/bin/env python3
"""
Multimodal Analyzer Module

Performs multimodal analysis using Nova Pro
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MultimodalAnalyzer:
    def __init__(self):
        self.output_dir = "data/analysis"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def analyze_images(self, image_paths: List[str], data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Analyze images using Nova Pro"""
        print("🤖 Analyzing images...")
        
        try:
            from nova_pro_client import NovaProClient
            
            nova = NovaProClient(region_name='us-east-1')
            analysis_results = {}
            
            for i, image_path in enumerate(image_paths):
                prompt = f"""
                Analyze this stock chart for {symbol}:
                - Current price: ${data.get('current_price', 'N/A')}
                - Time period: Last 7 days
                - Chart type: {'Price and Volume' if i == 0 else 'Technical Analysis'}
                
                Provide:
                1. Chart pattern analysis
                2. Key support/resistance levels
                3. Trend direction
                4. Trading signals
                5. Risk assessment
                """
                
                result = nova.image_analysis_request(
                    prompt=prompt,
                    image_path=image_path,
                    max_tokens=1000
                )
                
                analysis_results[f'image_analysis_{i+1}'] = result
            
            print("✅ Image analysis completed")
            return analysis_results
            
        except Exception as e:
            print(f"❌ Error in image analysis: {e}")
            return {}
    
    def analyze_video(self, video_path: str, symbol: str) -> str:
        """Analyze video using Nova Pro"""
        print("🤖 Analyzing video...")
        
        if not video_path:
            return ""
        
        try:
            from nova_pro_client import NovaProClient
            
            nova = NovaProClient(region_name='us-east-1')
            
            video_prompt = f"""
            Analyze this stock analysis video for {symbol}:
            - Video contains multiple charts
            - Focus on overall market sentiment
            - Identify key patterns across timeframes
            - Provide trading recommendations
            """
            
            result = nova.video_analysis_request(
                prompt=video_prompt,
                video_path=video_path,
                max_tokens=1000
            )
            
            print("✅ Video analysis completed")
            return result
            
        except Exception as e:
            print(f"❌ Error in video analysis: {e}")
            return ""
    
    def analyze_all(self, image_paths: List[str], video_path: str, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Perform complete multimodal analysis"""
        print("🤖 Performing multimodal analysis...")
        
        results = {}
        
        # Analyze images
        image_results = self.analyze_images(image_paths, data, symbol)
        results.update(image_results)
        
        # Analyze video
        if video_path:
            video_result = self.analyze_video(video_path, symbol)
            results['video_analysis'] = video_result
        
        print("✅ Multimodal analysis completed")
        return results
