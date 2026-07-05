import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import os

# Load the Whisper model
print("Loading Whisper model...")
whisper_model = whisper.load_model("base")
print("Whisper model loaded successfully.")

def record_audio(duration=5, sample_rate=16000):
    """
    Record audio from the microphone.

    Args:
        duration (int): Recording duration in seconds.
        sample_rate (int): Audio sample rate.

    Returns:
        tuple: Recorded audio and sample rate.
    """
    print(f"\nRecording for {duration} seconds...")
    print("Speak now...")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )

    # Wait until recording is complete
    sd.wait()
    print("Recording completed.")

    return audio, sample_rate


def save_audio(audio, sample_rate):
    """
    Save the recorded audio to a temporary WAV file.

    Args:
        audio: Recorded audio data.
        sample_rate (int): Audio sample rate.

    Returns:
        str: Path to the temporary audio file.
    """
    temp_file = tempfile.mktemp(suffix=".wav")
    wav.write(temp_file, sample_rate, audio)
    return temp_file


def transcribe_audio(audio_file):
    """
    Convert speech to text using Whisper.

    Args:
        audio_file (str): Path to the audio file.

    Returns:
        str: Transcribed text.
    """
    print("Converting speech to text...")

    result = whisper_model.transcribe(audio_file)
    text = result["text"].strip()

    print(f"You said: {text}")

    return text


def get_voice_query(duration=25):
    """
    Complete voice input pipeline.

    Steps:
    1. Record audio
    2. Save the audio as a temporary file
    3. Convert speech to text
    4. Delete the temporary file
    5. Return the transcribed text
    """
    audio, sample_rate = record_audio(duration)
    temp_file = save_audio(audio, sample_rate)

    text = transcribe_audio(temp_file)

    # Delete the temporary file
    os.remove(temp_file)

    return text


# Test the voice input pipeline
if __name__ == "__main__":
    print("Voice Input Test")
    print("=" * 40)

    text = get_voice_query(duration=25)

    print(f"\nTranscribed text: {text}")