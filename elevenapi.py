from dotenv import load_dotenv
import os
from elevenlabs.client import ElevenLabs
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import play


class elevenlabs:

    def __init__(self):
        load_dotenv()
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.async_client = AsyncElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.output_format = "mp3_44100_128"
        self.model_id="eleven_multilingual_v2"
        self.voice_id="JBFqnCBsd6RMkjVDRZzb"

    def text_to_speech_audio(self, text):
        """
        Returns:
            Audio object of output format mp3_44100_128
        """

        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format=self.output_format,
        )

        return audio
    

    async def text_to_speech_audio(self, text):
        """
        Async compatible tts generation 

        Returns:
            Audio object of output format mp3_44100_128
        """

        audio = self.async_client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format=self.output_format,
        )

        return audio