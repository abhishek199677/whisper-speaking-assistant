import io
import os
import whisper
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr

key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=key)
model = whisper.load_model("base")  # preparing my model
recognizer = sr.Recognizer()

STATUS_COMPLETED = "completed"

THREAD_ID = os.getenv("THREAD_ID")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

ASSISTANT_VOICE = "onyx"  # alloy | onyx | nova | shimmer
ASSISTANT_VOICE_MODEL = "tts-1"  # tts-1 | tts-1-hd


def run_thread(thread_id, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )
    return run.id


def create_message(prompt, thread_id):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=prompt,
    )
    return message


def retrieve_run_instances(thread_id, run_id):
    run_list = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )
    return run_list.status


def retrieve_message_list(thread_id):
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )
    return messages.data


def speak(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice=ASSISTANT_VOICE,
        input=text,
    )
    byte_stream = io.BytesIO(response.content)
    audio = AudioSegment.from_file(byte_stream, format="mp3")
    play(audio)


# Start - Transcribe Voice To Text
def transcribe_voice_to_text():
    audio_file = open("speech.wav", "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en"
    )
    return transcript.text
# END


while True:
    text = input("Hey Customer, how can I help you?\n")

    if text == "lets talk":
        # START - create a speech recognition instance that listens to the microphone
        with sr.Microphone() as source:
            print("Listening ... ")
            source.pause_threshold = 0.5
            audio = recognizer.listen(source, timeout=None)

            with open("speech.wav", "wb") as f:
                f.write(audio.get_wav_data())

        text = transcribe_voice_to_text()
        print(f"You Said - {text}\n")
        # END

    message = create_message(text, THREAD_ID)
    run_id = run_thread(THREAD_ID, ASSISTANT_ID)
    print(f"Your new run id is - {run_id}")

    status = None
    while status != STATUS_COMPLETED:
        status = retrieve_run_instances(THREAD_ID, run_id)
        print(f"{status}\r", end="")
        status = status

    messages = retrieve_message_list(THREAD_ID)

    # The top message at index 0 will always be from index after the run job is completed.
    response = messages[0].content[0].text.value
    role = messages[0].role

    print(f"{'Assistant' if role == 'assistant' else 'User'} : {response}\n")
    speak(messages[0].content[0].text.value)
