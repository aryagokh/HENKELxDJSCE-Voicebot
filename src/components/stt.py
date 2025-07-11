import assemblyai as aai
import wave
from src.components.config import get_secret
import time

try:
    aai.settings.api_key = get_secret("ASSEMBLYAI_API_KEY")
except Exception as e:
    print(e)
    raise 

def convert_speech_to_text(audio_file_path: str):
    retries, max_retries = 0, 5
    while (retries < max_retries):
        try:
            start_time = time.time()

            config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_file_path)
            if transcript.status == "error":
                raise RuntimeError(f"Transcription failed: {transcript.error}")
            
            end_time = time.time()

            return transcript.text, (end_time - start_time)

        except Exception as e:
            print(e)
            retries += 1
            time.sleep(5 * retries)

    return None, None
    

def get_wav_duration(audio_file_path):
    try:
        with wave.open(audio_file_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return duration
    except Exception as e:
        print(f"Error reading WAV file: {e}")
        return None
    


if __name__ == '__main__':
    audio_file_path = './data/audios/harvard.wav'

    audio_file_length = get_wav_duration(audio_file_path=audio_file_path)
    transcription , elapsed_time = convert_speech_to_text(audio_file_path=audio_file_path)

    print("Video Transcribed!!")
    print(f"Video Length: {audio_file_length:.2f} seconds.")
    print(f"Time Taken by AssemblyAI API: {elapsed_time:.2f} seconds.")
    print(f"Transcription:\n{transcription}")
