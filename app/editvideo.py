import asyncio
from elevenapi import elevenlabs_calls
import uuid
import os
import subprocess
import ffmpeg
import tempfile
import time

class VideoGenerator():

    def __init__(self, api_key):
        self.creator = elevenlabs_calls(api_key)

    def add_subtitles_to_video(self, video_file, output_video_file, audio_and_timings):
        """
        FFMPEG
        Use a base video and audio file, stitch them together and add hard coded subtitles to the final video.
        """
        audio_file = os.path.normpath(tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name)
        srt_file = f'temp/{str(uuid.uuid4())}.srt'


        try:
            with open(audio_file, "wb") as f:
                f.write(audio_and_timings[0])


            with open(srt_file, "w", encoding="utf-8") as f:
                f.write(self.create_srt_from_dict_timed(audio_and_timings[1]))
            
            print(srt_file)

            # command = [
            #     'ffmpeg',
            #     '-y',
            #     '-i', video_file,  # Input video file
            #     '-i', audio_path_for_ffmpeg, # Input audio file
            #     '-vf', f"subtitles='{srt_path_for_ffmpeg}':charenc=UTF-8",  # Apply subtitles filter
            #     '-map', '0:v:0',
            #     '-map', '1:a:0',
            #     '-c:a', 'copy',  # Copy the audio without re-encoding
            #     '-c:v', 'libx264',  # Encode video in H.264 format
            #     '-b:a', '192k',
            #     output_video_file  # Output video file with subtitles
            # ]
            # subprocess.run(command, check=True)
            audio_duration = ffmpeg.probe(audio_file, v='error', select_streams='a:0', show_entries='format=duration')
            audio_duration = float(audio_duration['format']['duration'])

            input_video = ffmpeg.input(video_file, stream_loop=-1).video.filter("subtitles", f"{srt_file}")
            input_audio = ffmpeg.input(audio_file)
            print(audio_duration)

            ffmpeg.concat(input_video, input_audio, v=1, a=1).output(output_video_file, vcodec='libx264', audio_bitrate='192k', t=audio_duration).run()

        finally:
            os.remove(audio_file)
            os.remove(srt_file)

        return output_video_file

    def create_srt_from_dict(self, word_dict, output_filename):
        """
        Generates an SRT file from a dictionary where keys are words and values are tuples 
        representing (start_time, end_time) in seconds.
        
        :param word_dict: Dictionary in the format {word: (start_time, end_time)}.
        :param output_filename: Name of the output SRT file.
        """
        output_filename = 'temp/' + output_filename + '_subtitles.srt'
        with open(output_filename, 'w', encoding='UTF-8') as file:
            counter = 1
            for word_triple in word_dict:
                word = word_triple[0]
                start = word_triple[1]
                end = word_triple[2]

                print(f"{word}: {start}--->{end}")

                # Convert start and end time to the SRT format (HH:MM:SS,MMM)
                start_time = self.format_time(start)
                end_time = self.format_time(end)

                # Write each entry in SRT format
                file.write(f"{counter}\n")
                file.write(f"{start_time} --> {end_time}\n")
                file.write(f"{word}\n\n")
                counter += 1


    def create_srt_from_dict_timed(self, word_list, words_on_screen=3, spoken_time=0.5):
        """
        Generates an SRT file from a list of words and timings, limit how many words are on screen at once and for how long
        
        :param word_list: List in the format [(word, start_time, end_time),......}.
        :param output_filename: Name of the output SRT file.
        :param words_on_screen: how many words will be shown at once
        :param spoken_time: min time a word must take to be shown on the screen by itself (for longer words)
        """
        srt_data = ""

        counter = 1
        word_len = 0
        prev_word = None
        prev_start = None
        prev_end = None

        for word_triple in word_list:
            word = word_triple[0]
            start = word_triple[1]
            end = word_triple[2]
            #print(f"{word}: {start}--->{end}")

            if prev_word and end-prev_start < spoken_time: # If the combined word takes less than this time to speak
                if word_len < words_on_screen: # Only n words together
                    prev_word += " " + word  # Combine the previous and current word into one entry
                    prev_end = end  # Extend the end time to the current word's end
                    word_len += 1 # Increment the words-on-screen length

            else:
                # Write the previous word entry if it exists
                if prev_word:
                    srt_data += f"{counter}\n"
                    srt_data += f"{self.format_time(prev_start)} --> {self.format_time(prev_end)}\n"
                    srt_data += f"{prev_word}\n\n"
                    counter += 1
                    word_len = 0

                # Store the current word details for the next iteration
                prev_word = word
                prev_start = start
                prev_end = end
            
        # Write the last word entry if it hasn't been written yet
        if prev_word:
            srt_data += f"{counter}\n"
            srt_data += f"{self.format_time(prev_start)} --> {self.format_time(prev_end)}\n"
            srt_data += f"{prev_word}\n\n"

        return srt_data


    def format_time(self, seconds):
        """
        Converts seconds to SRT time format (HH:MM:SS,MMM).
        
        :param seconds: Time in seconds.
        :return: Time in SRT format (HH:MM:SS,MMM).
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"


    async def generate_subtitles_video(self, text, base_video, output_video, model_id=None):

        #audio_and_timings = asyncio.run(self.creator.text_to_speech_timestamps(text)) 
        audio_and_timings = await self.creator.text_to_speech_timestamps(text, model_id)
        output_video_path = self.add_subtitles_to_video(base_video, output_video, audio_and_timings)

        return output_video_path


if __name__ == "__main__":



    # Example usage
    current_working_dir = os.getcwd()
    temp_location = "temp/"
    temp_path = os.path.join(current_working_dir, temp_location)

    base_video_path = "basevideogenerated.mp4"  # Replace with your video file pat




    text = "In a small village, a young girl named Yuki discovered she had the power to control time."
    
    words_in_title = text.split()
    output_video_path = f"{words_in_title[0]}_{words_in_title[1]}_{words_in_title[2]}_{str(uuid.uuid4())}.mp4"
    os.path.join(temp_path, output_video_path)

    #generate_subtitles_video(text, base_video_path, output_video_path)
