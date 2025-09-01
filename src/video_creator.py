#!/usr/bin/env python3
"""
Video Creator Module

Creates videos from chart images
"""

import cv2
import os
from datetime import datetime
from typing import List

class VideoCreator:
    def __init__(self):
        self.output_dir = "data/videos"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_video(self, image_paths: List[str], symbol: str) -> str:
        """Create video from images"""
        print("🎬 Creating video...")
        
        if not image_paths:
            print("❌ No images to create video from")
            return ""
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_path = os.path.join(self.output_dir, f"{symbol}_analysis_video_{timestamp}.mp4")
            
            # Read first image to get dimensions
            img = cv2.imread(image_paths[0])
            height, width, layers = img.shape
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_path, fourcc, 1.0, (width, height))
            
            # Add each image for 3 seconds
            for image_path in image_paths:
                img = cv2.imread(image_path)
                for _ in range(90):  # 3 seconds at 30 fps
                    out.write(img)
            
            out.release()
            
            print(f"✅ Video saved: {video_path}")
            return video_path
            
        except Exception as e:
            print(f"❌ Error creating video: {e}")
            return ""
