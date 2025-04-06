import sounddevice as sd
import numpy as np
import queue
import soundfile as sf
import threading
import io

def record_until_silence_bytes(samplerate=44100, channels=1, threshold=0.01, silence_duration=1.0):
    """
    Records audio from the default microphone until a period of silence is detected
    and returns the recorded audio as a bytes object in WAV format.
    
    Parameters:
        samplerate (int): The sample rate in Hertz.
        channels (int): Number of audio channels.
        threshold (float): Amplitude threshold below which audio is considered silent.
        silence_duration (float): Duration (in seconds) of continuous silence to stop recording.
    
    Returns:
        bytes: A bytes object representing the recorded audio in WAV format.
    """
    # Calculate the number of frames corresponding to the silence duration.
    silence_frames = int(silence_duration * samplerate)
    
    # Queue to receive audio blocks from the callback.
    audio_queue = queue.Queue()
    recorded_frames = []
    silence_counter = 0
    recorded_bytes = None

    def audio_callback(indata, frames, time, status):
        if status:
            print(status)
        audio_queue.put(indata.copy())

    def record_loop():
        nonlocal silence_counter, recorded_bytes
        print("Recording... Speak into the microphone.")
        with sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback):
            while True:
                # Get a block of recorded audio.
                data = audio_queue.get()
                recorded_frames.append(data)
                
                # Calculate the maximum absolute amplitude in the block.
                max_amplitude = np.max(np.abs(data))
                
                # Update the silence counter if the block is below the threshold.
                if max_amplitude < threshold:
                    silence_counter += len(data)
                else:
                    silence_counter = 0  # Reset if sound is detected
                
                # Break the loop if silence persists long enough.
                if silence_counter >= silence_frames:
                    print("Silence detected. Stopping recording.")
                    break
        
        # Concatenate all recorded frames into a single array.
        audio_data = np.concatenate(recorded_frames, axis=0)
        
        # Write the recorded audio to a BytesIO buffer in WAV format.
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, samplerate, format='WAV')
        recorded_bytes = buffer.getvalue()

    # Create and start the recording thread.
    record_thread = threading.Thread(target=record_loop)
    record_thread.start()
    record_thread.join()

    return recorded_bytes

# Example usage:
if __name__ == "__main__":
    audio_bytes = record_until_silence_bytes()
    # Optionally, write the bytes to a file to verify the recording.
    with open('output.wav', 'wb') as f:
        f.write(audio_bytes)
    print("Recording complete and saved to output.wav")
