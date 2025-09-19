import os
import librosa
import soundfile as sf

def convert_audio_for_nova_sonic(input_file, output_file=None):
    """
    Convert audio file to LPCM format that Nova Sonic expects:
    - 16kHz sample rate
    - 16-bit depth
    - Mono channel
    - WAV format
    """
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return None
    
    if output_file is None:
        # Create output filename
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_nova_sonic.wav"
    
    try:
        print(f"Converting {input_file} to Nova Sonic format...")
        
        # Load the audio file with librosa
        # sr=None keeps original sample rate, we'll resample later
        audio_data, original_sr = librosa.load(input_file, sr=None, mono=False)
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = librosa.to_mono(audio_data)
        
        # Resample to 16kHz
        audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=16000)
        
        # Save as WAV with 16-bit depth
        sf.write(output_file, audio_data, 16000, subtype='PCM_16')
        
        # Get file info
        file_size = os.path.getsize(output_file)
        duration = len(audio_data) / 16000.0  # Convert to seconds
        
        print(f"Conversion successful!")
        print(f"Output file: {output_file}")
        print(f"File size: {file_size / 1024:.2f} KB")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Sample rate: 16000 Hz")
        print(f"Channels: 1 (mono)")
        print(f"Bit depth: 16-bit")
        
        return output_file
        
    except Exception as e:
        print(f"Error converting audio: {e}")
        return None

if __name__ == "__main__":
    # Convert the original MP3 file
    input_file = "data/audio_test.mp3"
    output_file = convert_audio_for_nova_sonic(input_file)
    
    if output_file:
        print(f"\nConverted file ready: {output_file}")
        print("You can now use this file with Nova Sonic.")
    else:
        print("Conversion failed.")
