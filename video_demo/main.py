import openai
import time
import pyautogui
import os
import threading
import sys
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

sys.path.append("./components")
from speech_to_text import transcribe_stream
from stream_text_to_audio import stream_text_to_audio
from content_dictionary import content_dict

pause_event = threading.Event()  # This event will be used to pause/resume the timer thread

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

def record_elapsed_time(stop_event, pause_event):
    global elapsed_time
    current_start_time = time.time()
    while not stop_event.is_set():
        if pause_event.is_set():
            # If pause_event is set, just sleep for a bit without updating the elapsed_time
            time.sleep(0.1)
            continue

        current_elapsed = time.time() - current_start_time
        elapsed_time += current_elapsed
        current_start_time = time.time()
        time.sleep(0.1)

def get_answer_from_gpt_turbo(messages, audio_streamer):
    start_time = time.time()
    answer = ""
    resume_video_found = False  # Flag to check if "resume the video" is found
    
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

            if "resume the video" in chunk_content.lower():
                resume_video_found = True

            # If "resume the video" is not found, add the chunk content to the streamer's buffer
            if not resume_video_found:
                audio_streamer.add_to_buffer(chunk_content)

            print(chunk_content, end='', flush=True)

    if resume_video_found:
        # Only stream "Alright! I will resume the video."
        audio_streamer.add_to_buffer("Alright! I will resume the video.")

    return answer

elapsed_time = 0  # Global variable to store elapsed time

def get_content_for_time(elapsed_time_seconds, content_dict):
    for interval, content in content_dict.items():
        start_time_str, end_time_str = interval.split('-')
        start_time_minutes, start_time_seconds = map(int, start_time_str.split(':'))
        end_time_minutes, end_time_seconds = map(int, end_time_str.split(':'))

        start_time_total_seconds = start_time_minutes * 60 + start_time_seconds
        end_time_total_seconds = end_time_minutes * 60 + end_time_seconds
        
        if start_time_total_seconds <= elapsed_time_seconds < end_time_total_seconds:
            return content
    return "No specific content found for this time."  # This should be outside the loop

def chat_with_user():
    audio_streamer = ContinuousAudioStreamer()
    audio_streamer.start()

    sales_bot_statement = "You are a sales bot. You have to solve the doubts of the user with the help of the following information. Answer in short. In the end, always ask the user if their doubt is cleared. If the doubt is not cleared, ask them what doubt they have. If the doubt is cleared, reply only with 'Alright! I will resume the video'."
    
    # Initialize messages list with the sales bot statement
    messages = [
        {
            "role": "system", 
            "content": sales_bot_statement
        }
    ]
    
    stop_event = threading.Event()
    pause_event = threading.Event()
    pause_event.set()  # Initially pause the timer

    time_thread = threading.Thread(target=record_elapsed_time, args=(stop_event, pause_event))
    time_thread.daemon = True
    time_thread.start()
    
    pause_event.clear()  # Start the timer immediately

    new_query = True  # Flag to check if this is the user's first query

    while True:
        try:
            # print("Start speaking...")
            query = transcribe_stream()

            print("Transcription received...")

            if new_query:
                pyautogui.click()  # Click after the first query
                new_query = False

            # Stop the timer immediately after the user query
            pause_event.set()

            if query.lower() == "exit":
                break
            
            # Get the system content based on the elapsed time
            system_content = get_content_for_time(int(elapsed_time), content_dict)
            print(f"Elapsed Time: {elapsed_time}")
            print(f"System Content: {system_content}")

            # Append the newly fetched content to the system message
            messages[-1]['content'] = sales_bot_statement + " " + system_content
            print(f"System Content: {system_content}")

            
            messages.append({"role": "user", "content": query})
            answer = get_answer_from_gpt_turbo(messages, audio_streamer)

            if not "resume the video" in answer.lower():
                followup_question = "May I know if your doubt is cleared or not?"
                audio_streamer.add_to_buffer(followup_question)
                print(followup_question)
                answer+=followup_question
            messages.append({"role": "assistant", "content": answer})
            # print(answer)

            if "play video" in answer.lower():
                pause_event.clear()  # Restart the timer
                audio_streamer.stop()
                pyautogui.click()
                new_query = True
            elif "resume the video" in answer.lower():
                pause_event.clear()  # Restart the timer
                audio_streamer.stop()
                pyautogui.click()
                new_query = True

        except KeyboardInterrupt:
            print("\nGoodbye!")
            stop_event.set()
            if time_thread is not None and time_thread.is_alive():
                time_thread.join()
            break

if __name__ == "__main__":
    print("Chat with the assistant. Say 'exit' to end the conversation.")
    chat_with_user()

