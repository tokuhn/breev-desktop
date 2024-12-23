import sounddevice as sd
import numpy as np
import wave
import threading
from pydub import AudioSegment
import os
import sys
import stat


# Global variables for recording
recording_active = False
device_info = None
audio_data = []
temp_wav_name = "temp_recording.wav"


def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "ffmpeg", "ffmpeg")
    else:
        return "/opt/homebrew/bin/ffmpeg"


def create_file_path(filename):
    # Get the user's home directory
    home_dir = os.path.expanduser("~")

    # Create the path to the Documents/Breev directory
    documents_dir = os.path.join(home_dir, "Documents/Breev")

    # Create the directory if it doesn't exist
    os.makedirs(documents_dir, exist_ok=True)

    # Create the full path to the file
    file_path = os.path.join(documents_dir, filename)

    return file_path


def initialize_device(device_name):
    global device_info
    device_info = next(
        (device for device in sd.query_devices() if device_name in device["name"]), None
    )
    if not device_info:
        raise ValueError(f'Gerät "{device_name}" nicht gefunden. Bitte überprüfen Sie Ihre Audioeinstellungen.')


def record_audio():
    global recording_active
    with sd.InputStream(
        samplerate=device_info["default_samplerate"],
        channels=device_info["max_input_channels"],
        dtype="int16",
        device=device_info["index"],
        callback=audio_callback,
    ):
        while recording_active:
            pass  # Keep the stream active


def audio_callback(indata, frames, time, status):
    global audio_data
    if status:
        pass
    audio_data.append(indata.copy())


def start_recording():
    global recording_active, audio_data
    if recording_active:
        return
    audio_data = []  # Reset buffer
    recording_active = True
    threading.Thread(target=record_audio, daemon=True).start()


def stop_recording(output_filename):
    global recording_active
    if not recording_active:
        return
    recording_active = False
    save_audio(output_filename)


def save_audio(filename):
    global audio_data
    combined_data = np.concatenate(audio_data, axis=0)  # Combine all audio

    # Save as temporary WAV file
    temp_wav = create_file_path(temp_wav_name)

    with wave.open(temp_wav, "wb") as wf:
        wf.setnchannels(device_info["max_input_channels"])
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(device_info["default_samplerate"])
        wf.writeframes(combined_data.tobytes())

    # Get ffmpeg path
    AudioSegment.converter = get_ffmpeg_path()

    # Load WAV into pydub
    audio = AudioSegment.from_wav(temp_wav)

    if audio.channels > 2:
        # Downmix to stereo (combine all channels)
        mono_segments = audio.split_to_mono()  # Split into individual channels
        mixed = mono_segments[0]  # Start with the first channel
        for segment in mono_segments[1:]:
            mixed = mixed.overlay(segment)  # Overlay each additional channel

        # Convert to stereo
        audio = mixed.set_channels(2)

    elif audio.channels == 1:
        # Convert mono to stereo
        audio = audio.set_channels(2)

    # Export as MP3
    audio.export(create_file_path(filename), format="mp3")

    # Remove temporary WAV file
    os.remove(temp_wav)
