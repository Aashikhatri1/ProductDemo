## Final as on 28-10-23 6:30 PM
import openai
import time
import pyautogui as pg
import os
import threading
import sys
import queue
from dotenv import load_dotenv
import sounddevice as sd
import soundfile as sf
import asyncio

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


sys.path.append("./components")
from speech_to_text import transcribe_stream
from stream_text_to_audio import stream_text_to_audio
from content_dictionary import content_dict

transcription_queue = queue.Queue()

pause_event = threading.Event()
resume_event = threading.Event()
gpt_audio_playing_event = threading.Event() 


class ContinuousAudioStreamer:
    def __init__(self):
        self.buffer = ""
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def add_to_buffer(self, text):
        with self.lock:
            self.buffer += text

    def stream_audio_from_buffer(self):
        while not self.stop_event.is_set():
            with self.lock:
                text_to_stream = self.buffer
                self.buffer = ""

            if text_to_stream:
                stream_text_to_audio(text_to_stream, os.environ.get("PLAYHT_API_KEY"), os.environ.get("PLAYHT_USER_ID"))

            time.sleep(0.1)
            # time.sleep(0.5)  # Sleep for a bit to prevent busy-waiting

    def start(self):
        self.thread = threading.Thread(target=self.stream_audio_from_buffer)
        self.thread.daemon = True  # Set this thread as a daemon thread
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join()

# Modified play_audio_and_slide_thread to wait for resume_event after being paused
def play_audio_and_slide_thread():
    global pause_event, resume_event

    while True:
        # Check if the pause event is set
        if pause_event.is_set():
            # Wait for the resume event to be set before continuing
            resume_event.wait()
            resume_event.clear()
            pause_event.clear()
            continue  # Go back to the start of the loop instead of proceeding to play_next_audio_and_slide()

        play_next_audio_and_slide()
        time.sleep(1.0)

def play_audio(filename):
    data, rate = sf.read(filename)
    sd.play(data, rate)

    while sd.get_stream().active:
        if pause_event.is_set():
            sd.stop()
            resume_event.wait()
            sd.play(data, rate)
            pause_event.clear()
            resume_event.clear()
        time.sleep(0.1)

    sd.wait()


# This thread will be responsible for continuous transcription
def continuous_transcription_thread():
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    global pause_event

    while True:
        query = transcribe_stream()
        print(f"User Query: {query}")

        if query.lower() == "exit":
            break

        transcription_queue.put(query)  # Add the transcribed text to the queue
        pause_event.set()  # Signal that a transcription was received

def get_answer_from_gpt_turbo(messages, audio_streamer):
    start_time = time.time()
    answer = ""
    resume_video_found = False
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=messages,
        stream=True,
        temperature=0
    )

    for chunk in response:
        chunk_time = time.time() - start_time

        if 'content' in chunk['choices'][0]['delta']:
            chunk_content = chunk['choices'][0]['delta']['content']
            answer += chunk_content

            # if "resume the explanation" in chunk_content.lower():
            #     resume_video_found = True
            #     resume_event.set()

            if "resume the explanation" in chunk_content.lower():
                resume_video_found = True
                play_audio('assets/audio_files/Alright.wav')
                pause_event.clear()  # Clear the pause_event
                resume_event.set()  # Set the resume_event

            if "resume the explanation" in answer.lower():
                resume_video_found = True
                play_audio('assets/audio_files/Alright.wav')
                pause_event.clear()  # Clear the pause_event
                resume_event.set()  # Set the resume_event

            # # If "resume the video" is not found, add the chunk content to the streamer's buffer
            if not resume_video_found:
                audio_streamer.add_to_buffer(chunk_content)

            print(chunk_content, end='', flush=True)

    # if resume_video_found:
    #     # Only stream "Alright! I will resume the video."
    #     audio_streamer.add_to_buffer("Alright! I will resume the explanation.")
    #     resume_event.set()

    return answer

no_of_slide = 1

def get_content_for_slide(no_of_slide, content_dict):
    return content_dict.get(str(no_of_slide), "No specific content found for this slide.")

def play_next_audio_and_slide():
    global no_of_slide

    audio_file = f"assets/audio_files/{no_of_slide}.wav"
    if os.path.exists(audio_file):
        play_audio(audio_file)
        pg.press('down')
        no_of_slide += 1
    else:
        print("No more slides and audio files!")

# Stop all threads gracefully
def stop_all_threads():
    global audio_streamer, transcription_thread, audio_slide_thread
    audio_streamer.stop()
    if transcription_thread.is_alive():
        transcription_thread.join()
    if audio_slide_thread.is_alive():
        audio_slide_thread.join()

def chat_with_user():
    global audio_streamer, transcription_thread, audio_slide_thread

    audio_streamer = ContinuousAudioStreamer()
    audio_streamer.start()

    sales_bot_statement = ("You are a sales bot. You have to solve the doubts of the user with the help of the following information. "
                           "Answer in short. In the end, always ask the user if their doubt is cleared. "
                           "If the doubt is not cleared, ask them what doubt they have. "
                           "If the doubt is cleared, reply only with 'Alright! I will resume the explanation'.")

    # Initialize messages list with the sales bot statement
    messages = [{"role": "system", "content": sales_bot_statement}]

    audio_slide_thread = threading.Thread(target=play_audio_and_slide_thread)
    audio_slide_thread.daemon = True
    audio_slide_thread.start()

    transcription_thread = threading.Thread(target=continuous_transcription_thread)
    transcription_thread.daemon = True
    transcription_thread.start()

    try:
        while True:
            pause_event.wait()  # Wait until a transcription is received

            query = transcription_queue.get()  # Retrieve the transcribed text from the queue
            # query = input('Query: ')

            system_content = get_content_for_slide(no_of_slide, content_dict)
            
            messages[-1]['content'] = sales_bot_statement + " " + system_content
            messages.append({"role": "user", "content": query})

            answer = get_answer_from_gpt_turbo(messages, audio_streamer)
            messages.append({"role": "assistant", "content": answer})

    except KeyboardInterrupt:
        print("\nGoodbye!")
        stop_all_threads() 

    audio_slide_thread.join()
    transcription_thread.join()

if __name__ == "__main__":
    print("Chat with the assistant. Say 'exit' to end the conversation.")
    chat_with_user()