import asyncio
import random
from elevenapi import elevenlabs_calls
from moviepy import *
import uuid
import os
import subprocess
from pathlib import Path
import ffmpeg
import tempfile
import time

class VideoGenerator():

    def __init__(self, api_key):
        self.creator = elevenlabs_calls(api_key)
        self.transitions_folder = "./transitions"

    def add_subtitles_to_video(self, output_video_file, audio_and_timings, video_file_path=None, images=None):
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


            audio_duration = self.get_audio_duration(audio_file)
            
            if not video_file_path:
                transition_clips = [os.path.abspath(os.path.join(self.transitions_folder, clip)) for clip in os.listdir(self.transitions_folder)]
                print(transition_clips)
                video_file_path = self.create_video_from_images(images, transition_clips, audio_duration)

            input_video = ffmpeg.input(video_file_path, stream_loop=-1).video.filter("subtitles", f"{srt_file}")
            input_audio = ffmpeg.input(audio_file)
            print(audio_duration)

            ffmpeg.concat(input_video, input_audio, v=1, a=1).output(output_video_file, vcodec='libx264', audio_bitrate='192k', t=audio_duration).run()

        finally:
            os.remove(audio_file)
            os.remove(srt_file)

        return output_video_file
    

    def crossfade_with_moviepy(self, video_clips, transition_clips, transition_durations):
        """
        Crossfades a list of video clips with transition clips in between.
        
        :param video_clips: List of file paths for main video clips.
        :param transition_clips: List of file paths for transition clips.
        :param crossfade_duration: Duration of the crossfade in seconds.
        :return: A final concatenated video clip.
        """
        composite_clips = []
        total_time = 0
        for i in range(len(video_clips)):
            
            current_clip = VideoFileClip(video_clips[i]) # The first clip in the clip,transition,clip group
            current_clip = current_clip.with_layer_index(0)

            # If clip is not the first clip
            if i > 0:
                current_clip = current_clip.with_start(total_time) # After the first clip, every clip starts where the previous one ends

            total_time += current_clip.duration
            composite_clips.append(current_clip)


            # If there are transitions left
            if i < len(transition_clips):
                transition_clip = VideoFileClip(transition_clips[i]).with_opacity(0.5) # The transition at the end of the current clip
                transition_clip = transition_clip.with_layer_index(1)

                # Start the first half of the transition as the current clip ends
                transition_start = current_clip.end - (transition_clip.duration)/2
                transition_clip = transition_clip.with_start(transition_start)
                transition_clip = transition_clip.with_position("center")


                composite_clips.append(transition_clip)


        composite_video = CompositeVideoClip(clips=composite_clips)
        
        #final_video = concatenate_videoclips(clips, method="compose")
        return composite_video

    def create_video_from_images(self, images, transition_clips, audio_duration):
        final_video_path = os.path.join(tempfile.mkdtemp(), f"stitched_{str(uuid.uuid4())}.mp4")
        
        clip_dir = tempfile.mkdtemp()
        num_images = len(images)
        random_transitions = random.choices(transition_clips, k=num_images-1)
        transition_durations = [self.get_video_duration(clip) for clip in random_transitions]


        image_duration = audio_duration / num_images

        image_video_clip_paths = []
        
        # Crop and center all images to 1080x1920 (9:16)
        # then turn them into mp4 clips of calculated duration
        for i, img in enumerate(images):
            crop_filter = self.get_crop_filter(img, 1080, 1920)
            output = os.path.join(clip_dir, f"img_clip_{str(uuid.uuid4())}.mp4")
            #output = f"app/temp/img_clip_{str(uuid.uuid4())}.mp4"
            istream = ffmpeg.input(img, loop=1, t=image_duration)

            crop_filter(istream).filter("fps", fps=30).output(output, vcodec="libx264", pix_fmt="yuv420p", t=image_duration, r=30).run()
            image_video_clip_paths.append(output)


        finalRaw = self.crossfade_with_moviepy(image_video_clip_paths, random_transitions, transition_durations)
        finalRaw.write_videofile(final_video_path, codec="libx264", fps=30)

        self.recursive_delete(clip_dir) # Clean the generated clips

        return final_video_path

    def get_video_duration(self, video_file):
        """
        Get duration of video file
        """
        try:
            probe = ffmpeg.probe(video_file, select_streams='v:0')
            return float(probe["format"]["duration"])
        except ffmpeg.Error as e:
            print(f"FFprobe failed for {video_file}: {e.stderr.decode()}")  # Print the exact error
            raise  # Re-raise the error to see the full traceback
    
    def get_audio_duration(self, audio_file):
        """
        Get duration of audio file
        """
        audio_duration = ffmpeg.probe(audio_file, v='error', select_streams='a:0', show_entries='format=duration')
        audio_duration = float(audio_duration['format']['duration'])

        return audio_duration
    
    def get_crop_filter(self, input_file, target_width, target_height):
        """
        Returns an FFmpeg filter chain that crops and scales an input file dynamically.
        Can be used directly with `.filter()`.
        """
        # Get input image dimensions
        probe = ffmpeg.probe(input_file)
        video_stream = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
        in_width = int(video_stream["width"])
        in_height = int(video_stream["height"])
        
        target_aspect = target_width / target_height
        input_aspect = in_width / in_height

        # Determine cropping dimensions
        if input_aspect > target_aspect:
            # Input is wider than target → Crop width
            crop_width = int(in_height * target_aspect)
            crop_height = in_height
        else:
            # Input is taller than target → Crop height
            crop_width = in_width
            crop_height = int(in_width / target_aspect)

        # Create filter chain dynamically
        def apply_filters(stream):
            return (
                stream
                .filter("crop", crop_width, crop_height, f"(in_w-{crop_width})/2", f"(in_h-{crop_height})/2")
                .filter("scale", target_width, target_height)
            )

        return apply_filters  # Return a function that applies the filters
    
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
        """
        Generate a video using a base video and text
        """

        audio_and_timings = await self.creator.text_to_speech_timestamps(text)
        output_video_path = self.add_subtitles_to_video(output_video, audio_and_timings, video_file_path=base_video)

        return output_video_path

    async def generate_subtitles_image(self, text, images, output_video, model_id=None):
        """
        Generate a video using base images and texts, adding transitions in between
        """
        audio_and_timings = await self.creator.text_to_speech_timestamps(text, model_id)
        output_video_path = self.add_subtitles_to_video(output_video, audio_and_timings, images=images)

        return output_video_path
    
    def recursive_delete(folder_path):
        folder = Path(folder_path)
        if folder.exists() and folder.is_dir():
            for item in folder.glob("**/*"):
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                    elif item.is_dir():
                        item.rmdir()  # Only works if the directory is already empty
                except Exception as e:
                    print(f"Failed to delete {item}: {e}")
            try:
                folder.rmdir()  # Remove the now-empty root folder
            except Exception as e:
                print(f"Failed to remove directory {folder}: {e}")


if __name__ == "__main__":

    api_key = os.getenv("elevenlabs_api_key_uofa")
    current_working_dir = os.getcwd()
    temp_location = "temp/"
    temp_path = os.path.join(current_working_dir, temp_location)
    generator = VideoGenerator(api_key)

    base_video_path = "basevideogenerated.mp4"  # Replace with your video file pat




    #text = "In a small village, a young girl named Yuki discovered she had the power to control time."
    text = "एक छोटे से गाँव में, एक लड़का नामक अर्जुन रहता था। उसका सपना था कि वह एक दिन बड़ा आदमी बनेगा। रोज़ वो गाँव के स्कूल में मेहनत से पढ़ाई करता और खेतों में अपने पिता का हाथ बटाता। एक दिन गाँव में एक बड़ा कार्यक्रम हुआ, जिसमें गाँव के सबसे होशियार लड़के को इनाम दिया जाना था। अर्जुन ने अपनी कड़ी मेहनत से वह इनाम जीत लिया। वह साबित कर दिया कि मेहनत और समर्पण से हर सपना सच हो सकता है।"
    
    words_in_title = text.split()
    output_video_path = f"{words_in_title[0]}_{words_in_title[1]}_{words_in_title[2]}_{str(uuid.uuid4())}.mp4"
    output_video_path = os.path.join(temp_path, output_video_path)

    #generate_subtitles_video(text, base_video_path, output_video_path)
    asyncio.run(generator.generate_subtitles_image(text, "images", output_video_path))
    #asyncio.run(generator.generate_subtitles_video(text, base_video_path, output_video_path))
    
