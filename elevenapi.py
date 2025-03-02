from dotenv import load_dotenv
import os
from elevenlabs.client import ElevenLabs
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import play
import aiohttp
import base64
import requests

class elevenlabs_calls:

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("ELEVENLABS_API_KEY_uofa")
        self.client = ElevenLabs(api_key=self.api_key)
        self.async_client = AsyncElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.output_format = "mp3_44100_128"
        self.model_id="eleven_flash_v2_5" # eleven_multilingual_v2, eleven_flash_v2_5
        self.voice_id="9BWtsMINqrJLrRacOk9x"

        self.req_url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/with-timestamps"
    
        self.req_headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

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
    

    async def async_text_to_speech_audio(self, text):
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


    async def text_to_speech_timestamps(self, text, output_file_path):
        """
        Async tts with per character timestamps for subtitles

        Returns:
            Audio object of output format mp3_44100_128
        """
        payload = {
            "text": text,
            "model_id": self.model_id,
        }

        output_filename = output_file_path + ".mp3"

        async with aiohttp.ClientSession() as session:
            async with session.post(self.req_url, json=payload, headers=self.req_headers) as response:
                if response.status == 200:
                    # Parse JSON response
                    response_json = await response.json()
                    
                    # Extract base64 audio data
                    audio_base64 = response_json.get("audio_base64")
                    if not audio_base64:
                        print("Error: No audio data found in response.")
                        return

                    # Decode and save the audio file
                    audio_bytes = base64.b64decode(audio_base64)
                    with open(output_filename, "wb") as f: # change output file name to be unique to build db
                        f.write(audio_bytes)
                    print(f"Audio saved at {output_file_path}")

                    # Extract character timings
                    word_timing_map = self.extract_character_timings(text, response_json)
                    
                    
                    # print("Characters:", response_json.get("alignment", {}).get("characters"), len(response_json.get("alignment", {}).get("characters")))
                    # start_times = response_json.get("alignment", {}).get("character_start_times_seconds")
                    # print("Start times:", start_times, len(start_times))
                    # print("Character Timings:", word_timing_map)

                else:
                    error_message = await response.text()
                    print(f"Error: {response.status}, {error_message}")


        return (output_filename, word_timing_map)


    def extract_character_timings(self, text, response_json):
        """
        Maps characters and words to their start and end timestamps.
        
        Returns:
            Dict: {"Word":(start_time, end_time)}
        
        """

        alignment = response_json.get("alignment", {})

        characters = alignment.get("characters", []) # List of all character in the word
        start_times = alignment.get("character_start_times_seconds", [])
        end_times = alignment.get("character_end_times_seconds", [])

        # Word timing map
        words = text.split()  # Split text into words
        word_timing_map = {}
        index = 0  # Keep track of character index in the alignment

        print("Words", words)

        for word in words:
            # Find the first character of the word in the characters list (ignoring spaces)
            while index < len(characters) and characters[index] == ' ':
                index += 1  # Skip spaces

            if index < len(characters):  # Ensure index is within range
                word_start = start_times[index]
                index += len(word)-1  # Move index to the last letter of the word
                word_end = end_times[index]
                index += 1 # And now past the word

                word_timing_map[word] = (word_start, word_end)  # Store time of first character
            
            
        return word_timing_map
    
    def get_models(self):
        """Get list of models"""
        url = "https://api.elevenlabs.io/v1/models"
        response = requests.get(url, headers=self.req_headers)

        print(response.json())

        
    def get_voice_list(self):
        """
        Get list of voices and their ids
        """

        url = "https://api.elevenlabs.io/v1/voices"
        response = requests.get(url, headers=self.req_headers)

        print(response.json())



if __name__ == "__main__":
    elevenlabs_object = elevenlabs_calls()

    elevenlabs_object.get_voice_list()