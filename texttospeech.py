from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')


if not api_key:
    raise ValueError("API key not found in environment variables. Make sure your .env file is in the correct location and properly formatted.")

client = OpenAI(api_key=api_key)


response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input="Hola a todos IntiDev ganaremos esta hackathon",
)

response.stream_to_file("output3.mp3")