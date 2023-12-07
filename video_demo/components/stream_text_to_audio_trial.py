### streaming buffer
from pydub import AudioSegment
from pydub.playback import play
import requests
from io import BytesIO

BUFFER_SIZE = 10 * 1024  # Start playback after collecting 10 KB of audio

def stream_text_to_audio(text, api_key, user_id):
    text = text.replace("%", "percent")
    url = "https://play.ht/api/v2/tts/stream"
    headers = {
        "accept": "audio/mpeg",
        "Authorization": f"Bearer {api_key}",
        "x-user-id": user_id,
    }
    payload = {"text": text, "voice": "Michael"}

    response = requests.post(url, headers=headers, json=payload, stream=True)
    buffered_data = b""

    if response.status_code == 200:
        for chunk in response.iter_content(chunk_size=1024):
            buffered_data += chunk

            if len(buffered_data) >= BUFFER_SIZE:
                audio_stream = BytesIO(buffered_data)
                song = AudioSegment.from_file(audio_stream, format="mp3")
                play(song)
                buffered_data = b""

        # Play any remaining audio data
        if buffered_data:
            audio_stream = BytesIO(buffered_data)
            song = AudioSegment.from_file(audio_stream, format="mp3")
            play(song)
    else:
        print(f"Error: {response.status_code}, {response.text}")

# # # stream_text_to_audio.py--  demo 10 gpt direct streaming, taking pauses
# import requests
# from pydub import AudioSegment
# from pydub.playback import play
# from io import BytesIO
# import queue
# import threading

# audio_queue = queue.Queue()
# stop_event = threading.Event()

# def audio_player():
#     while not stop_event.is_set():
#         try:
#             audio_segment = audio_queue.get(timeout=1)  # 1-second timeout
#             play(audio_segment)
#         except queue.Empty:
#             continue

# player_thread = threading.Thread(target=audio_player)
# player_thread.start()


# def stream_text_to_audio(text, api_key, user_id):  # Add user_id parameter
#     text = text.replace("%", "percent")
#     url = "https://play.ht/api/v2/tts/stream"
#     headers = {
#         "accept": "audio/mpeg",
#         "Authorization": f"Bearer {api_key}",  # Add Authorization header
#         "x-user-id": user_id,  # Add x-user-id header
#     }
#     payload = {"text": text, "voice": "Michael"}  # Use the voice ID you want to use
#     response = requests.post(
#         url, headers=headers, json=payload, stream=True
#     )  # Set stream=True to stream the response
#     if response.status_code == 200:
#         audio_data = b""  # Initialize an empty bytes object to hold the audio data
#         # for chunk in response.iter_content(chunk_size=1024):  # Iterate over the response chunks
#         for chunk in response.iter_content(chunk_size=8192): #4096
#             if chunk:  # If chunk is not empty
#                 audio_data += chunk  # Add the chunk to audio_data
#         audio_stream = BytesIO(
#             audio_data
#         )  # Load the complete audio data into a BytesIO object
#         # song = AudioSegment.from_file(audio_stream, format="mp3")
#         # play(song)
#         song = AudioSegment.from_file(audio_stream, format="mp3")
#         audio_queue.put(song)
#     else:
#         print(f"Error: {response.status_code}, {response.text}")

        
