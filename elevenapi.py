from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os

load_dotenv()

class elevenlabs:

    def __init__(self):
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.output_format = "mp3_44100_128"
        self.model_id="eleven_multilingual_v2",
        self.voice_id="JBFqnCBsd6RMkjVDRZzb",


    def text_to_speech_audio(self, text):
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format=self.output_format,
        )

        return audio