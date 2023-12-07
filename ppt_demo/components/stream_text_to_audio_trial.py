# ### streaming buffer
# from pydub import AudioSegment
# from pydub.playback import play
# import requests
# from io import BytesIO

# BUFFER_SIZE = 10 * 1024  # Start playback after collecting 10 KB of audio

# def stream_text_to_audio(text, api_key, user_id):
#     text = text.replace("%", "percent")
#     url = "https://play.ht/api/v2/tts/stream"
#     headers = {
#         "accept": "audio/mpeg",
#         "Authorization": f"Bearer {api_key}",
#         "x-user-id": user_id,
#     }
#     payload = {"text": text, "voice": "Michael"}

#     response = requests.post(url, headers=headers, json=payload, stream=True)
#     buffered_data = b""

#     if response.status_code == 200:
#         for chunk in response.iter_content(chunk_size=1024):
#             buffered_data += chunk

#             if len(buffered_data) >= BUFFER_SIZE:
#                 audio_stream = BytesIO(buffered_data)
#                 song = AudioSegment.from_file(audio_stream, format="mp3")
#                 play(song)
#                 buffered_data = b""

#         # Play any remaining audio data
#         if buffered_data:
#             audio_stream = BytesIO(buffered_data)
#             song = AudioSegment.from_file(audio_stream, format="mp3")
#             play(song)
#     else:
#         print(f"Error: {response.status_code}, {response.text}")

# # stream_text_to_audio.py
import requests
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
import queue
import threading

audio_queue = queue.Queue()
stop_event = threading.Event()

def audio_player():
    while not stop_event.is_set():
        try:
            audio_segment = audio_queue.get(timeout=1)  # 1-second timeout
            play(audio_segment)
        except queue.Empty:
            continue

player_thread = threading.Thread(target=audio_player)
player_thread.start()


def stream_text_to_audio(text, api_key, user_id):  # Add user_id parameter
    text = text.replace("%", "percent")
    url = "https://play.ht/api/v2/tts/stream"
    headers = {
        "accept": "audio/mpeg",
        "Authorization": f"Bearer {api_key}",  # Add Authorization header
        "x-user-id": user_id,  # Add x-user-id header
    }
    payload = {"text": text, "voice": "Michael"}  # Use the voice ID you want to use
    response = requests.post(
        url, headers=headers, json=payload, stream=True
    )  # Set stream=True to stream the response
    if response.status_code == 200:
        audio_data = b""  # Initialize an empty bytes object to hold the audio data
        # for chunk in response.iter_content(chunk_size=1024):  # Iterate over the response chunks
        for chunk in response.iter_content(chunk_size=8192): #4096
            if chunk:  # If chunk is not empty
                audio_data += chunk  # Add the chunk to audio_data
        audio_stream = BytesIO(
            audio_data
        )  # Load the complete audio data into a BytesIO object
        # song = AudioSegment.from_file(audio_stream, format="mp3")
        # play(song)
        song = AudioSegment.from_file(audio_stream, format="mp3")
        audio_queue.put(song)
    else:
        print(f"Error: {response.status_code}, {response.text}")

        
# import requests
# import pygame
# from io import BytesIO

# def stream_text_to_audio(text, api_key, user_id):
#     text = text.replace("%", "percent")
#     url = "https://play.ht/api/v2/tts/stream"
#     headers = {
#         "accept": "audio/mpeg",
#         "Authorization": f"Bearer {api_key}",
#         "x-user-id": user_id,
#     }
#     payload = {"text": text, "voice": "Michael"}
#     response = requests.post(url, headers=headers, json=payload, stream=True)
    
#     if response.status_code == 200:
#         pygame.mixer.init()
#         pygame.mixer.music.set_volume(1.0)
        
#         # Convert streaming mp3 data into a BytesIO for Pygame
#         byte_io = BytesIO(response.content)
#         pygame.mixer.music.load(byte_io)
#         pygame.mixer.music.play()
        
#         # This loop keeps the program running until the stream has finished playing.
#         while pygame.mixer.music.get_busy():
#             pygame.time.Clock().tick(10)
#     else:
#         print(f"Error: {response.status_code}, {response.text}")

# # Test the function with your API Key and User ID
# # stream_text_to_audio("Hello, this is a test.", YOUR_API_KEY, YOUR_USER_ID)

# # import requests
# # import simpleaudio as sa
# # from io import BytesIO

# # def stream_text_to_audio(text, api_key, user_id):
# #     text = text.replace("%", "percent")
# #     url = "https://play.ht/api/v2/tts/stream"
# #     headers = {
# #         "accept": "audio/mpeg",
# #         "Authorization": f"Bearer {api_key}",
# #         "x-user-id": user_id,
# #     }
# #     payload = {"text": text, "voice": "Michael"}
# #     response = requests.post(url, headers=headers, json=payload, stream=True)
    
# #     audio_buffer = b""  # Initialize an empty buffer

# #     if response.status_code == 200:
# #         for chunk in response.iter_content(chunk_size=8192):  
# #             audio_buffer += chunk  # Append chunk to the buffer

# #             while len(audio_buffer) >= 4:
# #                 # Extract the maximum number of bytes that is a multiple of 4
# #                 play_size = len(audio_buffer) - (len(audio_buffer) % 4)
                
# #                 # Play this portion
# #                 play_obj = sa.play_buffer(audio_buffer[:play_size], 2, 2, 44100)
# #                 play_obj.wait_done()
                
# #                 # Remove the played portion from the buffer
# #                 audio_buffer = audio_buffer[play_size:]

# #     else:
# #         print(f"Error: {response.status_code}, {response.text}")

# # # import requests
# # # import simpleaudio as sa
# # # from io import BytesIO

# # # def stream_text_to_audio(text, api_key, user_id):
# # #     text = text.replace("%", "percent")
# # #     url = "https://play.ht/api/v2/tts/stream"
# # #     headers = {
# # #         "accept": "audio/mpeg",
# # #         "Authorization": f"Bearer {api_key}",  # Add Authorization header
# # #         "x-user-id": user_id,  # Add x-user-id header
# # #     }
# # #     payload = {"text": text, "voice": "Michael"}
# # #     response = requests.post(url, headers=headers, json=payload, stream=True)
    
# # #     if response.status_code == 200:
# # #         # Instead of collecting the entire audio and then playing, we'll play in chunks
# # #         for chunk in response.iter_content(chunk_size=8192):  # Adjust the chunk size as needed
# # #             if chunk:
# # #                 # Play the audio chunk immediately
# # #                 play_obj = sa.play_buffer(chunk, 2, 2, 44100)  # 2 channels, 2 bytes per sample, 44100 sample rate
# # #                 play_obj.wait_done()  # Block until audio playback is done
# # #     else:
# # #         print(f"Error: {response.status_code}, {response.text}")

# # # # from pydub import AudioSegment
# # # # from pydub.playback import play
# # # # import requests
# # # # from io import BytesIO

# # # # BUFFER_SIZE = 10 * 1024  # Start playback after collecting 10 KB of audio

# # # # def stream_text_to_audio(text, api_key, user_id):
# # # #     text = text.replace("%", "percent")
# # # #     url = "https://play.ht/api/v2/tts/stream"
# # # #     headers = {
# # # #         "accept": "audio/mpeg",
# # # #         "Authorization": f"Bearer {api_key}",
# # # #         "x-user-id": user_id,
# # # #     }
# # # #     payload = {"text": text, "voice": "Michael"}

# # # #     response = requests.post(url, headers=headers, json=payload, stream=True)
# # # #     buffered_data = b""

# # # #     if response.status_code == 200:
# # # #         for chunk in response.iter_content(chunk_size=1024):
# # # #             buffered_data += chunk

# # # #             if len(buffered_data) >= BUFFER_SIZE:
# # # #                 audio_stream = BytesIO(buffered_data)
# # # #                 song = AudioSegment.from_file(audio_stream, format="mp3")
# # # #                 play(song)
# # # #                 buffered_data = b""

# # # #         # Play any remaining audio data
# # # #         if buffered_data:
# # # #             audio_stream = BytesIO(buffered_data)
# # # #             song = AudioSegment.from_file(audio_stream, format="mp3")
# # # #             play(song)
# # # #     else:
# # # #         print(f"Error: {response.status_code}, {response.text}")

# # # # # # stream_text_to_speech.py
# # # # # import requests
# # # # # from pydub import AudioSegment
# # # # # from pydub.playback import play
# # # # # from io import BytesIO

# # # # # def stream_text_to_audio(text, api_key, user_id):  # Add user_id parameter
# # # # #     text = text.replace("%", "percent")
# # # # #     url = "https://play.ht/api/v2/tts/stream"
# # # # #     headers = {
# # # # #         "accept": "audio/mpeg",
# # # # #         "Authorization": f"Bearer {api_key}",  # Add Authorization header
# # # # #         "x-user-id": user_id,  # Add x-user-id header
# # # # #     }
# # # # #     payload = {"text": text, "voice": "Michael"}  # Use the voice ID you want to use
# # # # #     response = requests.post(
# # # # #         url, headers=headers, json=payload, stream=True
# # # # #     )  # Set stream=True to stream the response
# # # # #     if response.status_code == 200:
# # # # #         audio_data = b""  # Initialize an empty bytes object to hold the audio data
# # # # #         # for chunk in response.iter_content(chunk_size=1024):  # Iterate over the response chunks
# # # # #         for chunk in response.iter_content(chunk_size=8192): #4096
# # # # #             if chunk:  # If chunk is not empty
# # # # #                 audio_data += chunk  # Add the chunk to audio_data
# # # # #         audio_stream = BytesIO(
# # # # #             audio_data
# # # # #         )  # Load the complete audio data into a BytesIO object
# # # # #         song = AudioSegment.from_file(audio_stream, format="mp3")
# # # # #         play(song)
# # # # #     else:
# # # # #         print(f"Error: {response.status_code}, {response.text}")
# # # # # ###############################################################################################




# # # # # # # # ##########################################3
# # # # # # # # stream_text_to_speech.py
# # # # # # # import requests
# # # # # # # import sounddevice as sd
# # # # # # # import numpy as np
# # # # # # # from pydub import AudioSegment
# # # # # # # from io import BytesIO

# # # # # # # def stream_text_to_audio(text, api_key, user_id):
# # # # # # #     url = "https://play.ht/api/v2/tts/stream"
# # # # # # #     headers = {
# # # # # # #         "accept": "audio/mpeg",
# # # # # # #         "Authorization": f"Bearer {api_key}",
# # # # # # #         "x-user-id": user_id,
# # # # # # #     }
# # # # # # #     payload = {"text": text, "voice": "Michael"}
# # # # # # #     response = requests.post(url, headers=headers, json=payload, stream=True)

# # # # # # #     if response.status_code == 200:
# # # # # # #         audio_data = b""
# # # # # # #         for chunk in response.iter_content(chunk_size=1024):
# # # # # # #             if chunk:
# # # # # # #                 audio_data += chunk
# # # # # # #                 audio_stream = BytesIO(audio_data)
# # # # # # #                 song = AudioSegment.from_file(audio_stream, format="mp3")
# # # # # # #                 samples = np.array(song.get_array_of_samples())
# # # # # # #                 sd.play(samples, song.frame_rate)
# # # # # # #                 sd.wait()  # Wait for the audio to finish before playing the next chunk
# # # # # # #     else:
# # # # # # #         print(f"Error: {response.status_code}, {response.text}")
# # # # # # # ########################################3

# # # # # # # # stream_text_to_speech.py
# # # # # # # import requests
# # # # # # # import sounddevice as sd
# # # # # # # import numpy as np
# # # # # # # from pydub import AudioSegment
# # # # # # # from io import BytesIO

# # # # # # # def stream_text_to_audio(text, api_key, user_id):
# # # # # # #     url = "https://play.ht/api/v2/tts/stream"
# # # # # # #     headers = {
# # # # # # #         "accept": "audio/mpeg",
# # # # # # #         "Authorization": f"Bearer {api_key}",
# # # # # # #         "x-user-id": user_id,
# # # # # # #     }
# # # # # # #     payload = {"text": text, "voice": "Michael"}
# # # # # # #     response = requests.post(url, headers=headers, json=payload, stream=True)

# # # # # # #     if response.status_code == 200:
# # # # # # #         for chunk in response.iter_content(chunk_size=1024):
# # # # # # #             if chunk:
# # # # # # #                 audio_stream = BytesIO(chunk)
# # # # # # #                 song = AudioSegment.from_file(audio_stream, format="mp3")
# # # # # # #                 samples = np.array(song.get_array_of_samples())
# # # # # # #                 sd.play(samples, song.frame_rate)
# # # # # # #                 sd.wait()  # Wait for the audio to finish before playing the next chunk
# # # # # # #     else:
# # # # # # #         print(f"Error: {response.status_code}, {response.text}")
# # # # # # # ####################################################

# # # # # # # # stream_text_to_speech.py
# # # # # # # import requests
# # # # # # # import sounddevice as sd
# # # # # # # import numpy as np
# # # # # # # from pydub import AudioSegment
# # # # # # # from io import BytesIO

# # # # # # # def stream_text_to_audio(text, api_key, user_id):
# # # # # # #     url = "https://play.ht/api/v2/tts/stream"
# # # # # # #     headers = {
# # # # # # #         "accept": "audio/mpeg",
# # # # # # #         "Authorization": f"Bearer {api_key}",
# # # # # # #         "x-user-id": user_id,
# # # # # # #     }
# # # # # # #     payload = {"text": text, "voice": "Michael"}
# # # # # # #     response = requests.post(url, headers=headers, json=payload, stream=True)

# # # # # # #     if response.status_code == 200:
# # # # # # #         audio_data = b""
# # # # # # #         for chunk in response.iter_content(chunk_size=1024):
# # # # # # #             audio_data += chunk
        
# # # # # # #         # Only once we've accumulated all the chunks do we attempt to play them.
# # # # # # #         audio_stream = BytesIO(audio_data)
# # # # # # #         song = AudioSegment.from_file(audio_stream, format="mp3")
# # # # # # #         samples = np.array(song.get_array_of_samples())
# # # # # # #         sd.play(samples, song.frame_rate)
# # # # # # #         sd.wait()  # Wait for the audio to finish before returning
# # # # # # #     else:
# # # # # # #         print(f"Error: {response.status_code}, {response.text}")
