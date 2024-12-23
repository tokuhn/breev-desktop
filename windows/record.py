import pyaudiowpatch as pyaudio
import numpy as np
import wave
import threading
import time
import os, sys
from pydub import AudioSegment


# Constant variables
CHUNK_SIZE = 512

# Global variables
audio_interface = None
default_speakers = None
default_microphone = None
recording_active = False
loopback_audio_data = []
mic_audio_data = []
loopback_stream = None
mic_stream = None
loopback_temp_wav = "loopback_temp.wav"
mic_temp_wav = "mic_temp.wav"


def get_ffmpeg_path():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "ffmpeg", "ffmpeg.exe")
    else:
        return "ffmpeg.exe"

def initialize_device():
    global audio_interface, default_speakers, default_microphone

    audio_interface = pyaudio.PyAudio()
    
    wasapi_info = audio_interface.get_host_api_info_by_type(pyaudio.paWASAPI)

    # Get default WASAPI speakers (loopback device)
    default_speakers = audio_interface.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if not default_speakers["isLoopbackDevice"]:
        # Try to find the loopback device
        for loopback in audio_interface.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break

    # Find the default microphone (input device)
    default_microphone = audio_interface.get_device_info_by_index(wasapi_info["defaultInputDevice"])

def loopback_callback(in_data, frame_count, time_info, status):
    global loopback_audio_data, recording_active
    if recording_active:
        data_array = np.frombuffer(in_data, dtype=np.int16)
        loopback_audio_data.append(data_array)
    return (in_data, pyaudio.paContinue)

def mic_callback(in_data, frame_count, time_info, status):
    global mic_audio_data, recording_active
    if recording_active:
        data_array = np.frombuffer(in_data, dtype=np.int16)
        mic_audio_data.append(data_array)
    return (in_data, pyaudio.paContinue)

def record_loop():
    while recording_active:
        time.sleep(0.1)

def create_file_path(filename):
    # Create a Breev directory in the user's Documents folder
    home_dir = os.path.expanduser("~")
    documents_dir = os.path.join(home_dir, "Documents", "Breev")
    os.makedirs(documents_dir, exist_ok=True)
    return os.path.join(documents_dir, filename)

def start_recording():
    global recording_active, loopback_stream, mic_stream, loopback_audio_data, mic_audio_data
  
    if recording_active:
        return
 
    loopback_audio_data = []
    mic_audio_data = []
    recording_active = True   

    # Open loopback stream
    loopback_stream = audio_interface.open(
        format=pyaudio.paInt16,
        channels=default_speakers["maxInputChannels"],
        rate=int(default_speakers["defaultSampleRate"]),
        frames_per_buffer=CHUNK_SIZE,
        input=True,
        input_device_index=default_speakers["index"],
        stream_callback=loopback_callback,
        start=True
    )
    
    # Open microphone stream
    mic_stream = audio_interface.open(
        format=pyaudio.paInt16,
        channels=default_microphone["maxInputChannels"],
        rate=int(default_microphone["defaultSampleRate"]),
        frames_per_buffer=CHUNK_SIZE,
        input=True,
        input_device_index=default_microphone["index"],
        stream_callback=mic_callback,
        start=True
    )

    # Start a thread to keep the recording active
    threading.Thread(target=record_loop, daemon=True).start()

def stop_recording(output_filename):
    global recording_active, loopback_stream, mic_stream

    if not recording_active:
        return

    # Signal to stop
    recording_active = False
    # Wait a moment to ensure final callbacks complete
    time.sleep(0.2)

    # Close streams
    if loopback_stream is not None:
        loopback_stream.stop_stream()
        loopback_stream.close()
    
    if mic_stream is not None:
        mic_stream.stop_stream()
        mic_stream.close()

    # Save the recorded audio data
    save_audio(output_filename)

def save_audio(filename):
    # Combine loopback audio data
    loopback_combined = np.concatenate(loopback_audio_data, axis=0) if loopback_audio_data else np.array([], dtype=np.int16)

    # Combine mic audio data
    mic_combined = np.concatenate(mic_audio_data, axis=0) if mic_audio_data else np.array([], dtype=np.int16)

    # Save loopback as temp WAV
    loopback_path = create_file_path(loopback_temp_wav)
    with wave.open(loopback_path, "wb") as wf:
        wf.setnchannels(default_speakers["maxInputChannels"])
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(int(default_speakers["defaultSampleRate"]))
        wf.writeframes(loopback_combined.tobytes())

    # Save mic as temp WAV
    mic_path = create_file_path(mic_temp_wav)
    with wave.open(mic_path, "wb") as wf:
        wf.setnchannels(default_microphone["maxInputChannels"])
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(int(default_microphone["defaultSampleRate"]))
        wf.writeframes(mic_combined.tobytes())

    AudioSegment.converter = get_ffmpeg_path()

    # Overlay the two audio files
    loopback_audio = AudioSegment.from_wav(loopback_path)
    mic_audio = AudioSegment.from_wav(mic_path)
    combined_audio = loopback_audio.overlay(mic_audio)
    combined_audio.set_channels(2)

    # Export combined audio to MP3
    final_path = create_file_path(filename)
    combined_audio.export(final_path, format="mp3")

    # Clean up temporary files
    if os.path.exists(loopback_path):
        os.remove(loopback_path)
    if os.path.exists(mic_path):
        os.remove(mic_path)