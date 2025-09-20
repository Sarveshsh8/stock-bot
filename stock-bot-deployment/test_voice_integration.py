"""
Test script for voice integration
"""

import asyncio
import os
import tempfile
import wave
import pyaudio
from dotenv import load_dotenv

load_dotenv()

# Test the voice recording function
def test_audio_recording():
    """Test audio recording functionality."""
    print("🎤 Testing audio recording...")
    
    try:
        # Audio configuration
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        RECORD_SECONDS = 3  # Short test recording
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        print("Recording for 3 seconds...")
        
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
        
        print(f"✅ Audio recorded successfully: {temp_file.name}")
        
        # Check file size
        file_size = os.path.getsize(temp_file.name)
        print(f"📁 File size: {file_size} bytes")
        
        # Clean up
        os.unlink(temp_file.name)
        print("🧹 Cleaned up test file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error recording audio: {e}")
        return False

async def test_voice_conversion():
    """Test voice conversion functionality."""
    print("\n🔄 Testing voice conversion...")
    
    try:
        from src.ai.voice.voice_handler import convert_speech_to_text, create_test_audio_file
        
        # Create test audio
        audio_path = create_test_audio_file()
        print(f"📁 Created test audio: {audio_path}")
        
        # Convert to text
        result = await convert_speech_to_text(audio_path)
        print(f"📝 Conversion result: {result}")
        
        # Clean up
        os.unlink(audio_path)
        print("🧹 Cleaned up test file")
        
        return result is not None
        
    except Exception as e:
        print(f"❌ Error in voice conversion: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Voice Integration")
    print("=" * 40)
    
    # Test 1: Audio recording
    recording_ok = test_audio_recording()
    
    # Test 2: Voice conversion
    conversion_ok = asyncio.run(test_voice_conversion())
    
    print("\n📊 Test Results:")
    print(f"Audio Recording: {'✅ PASS' if recording_ok else '❌ FAIL'}")
    print(f"Voice Conversion: {'✅ PASS' if conversion_ok else '❌ FAIL'}")
    
    if recording_ok and conversion_ok:
        print("\n🎉 All tests passed! Voice integration is ready.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
