"""
Test complete voice workflow
"""

import asyncio
import os
import tempfile
import wave
import pyaudio
from dotenv import load_dotenv

load_dotenv()

def create_real_audio_test():
    """Create a real audio test file with actual speech simulation."""
    print("🎤 Creating test audio file...")
    
    try:
        # Audio configuration
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        RECORD_SECONDS = 2  # Short test
        
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
        
        print("Recording for 2 seconds... Speak now!")
        
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
        
        print(f"✅ Audio recorded: {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        print(f"❌ Error recording audio: {e}")
        return None

async def test_complete_voice_workflow():
    """Test the complete voice workflow."""
    print("🚀 Testing Complete Voice Workflow")
    print("=" * 50)
    
    # Test 1: Create real audio
    audio_file = create_real_audio_test()
    if not audio_file:
        print("❌ Failed to create audio file")
        return
    
    # Test 2: Convert to text
    print("\n🔄 Testing voice-to-text conversion...")
    try:
        from src.ai.voice.voice_handler import convert_speech_to_text
        
        result = await convert_speech_to_text(audio_file)
        print(f"📝 Transcription result: '{result}'")
        
        if result and result != "Voice input received (transcription pending)":
            print("✅ Voice transcription successful!")
        else:
            print("⚠️ Voice transcription returned fallback message")
            
    except Exception as e:
        print(f"❌ Error in voice conversion: {e}")
    
    # Test 3: Clean up
    try:
        os.unlink(audio_file)
        print("🧹 Cleaned up test file")
    except:
        pass
    
    print("\n✅ Voice workflow test completed!")

if __name__ == "__main__":
    asyncio.run(test_complete_voice_workflow())
