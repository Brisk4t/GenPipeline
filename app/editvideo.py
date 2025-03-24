import asyncio
import random
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
    

    def create_video_from_images(self, image_files_path, transition_clips, audio_duration):
        output_width = 1080  # Example width
        output_height = int(output_width * 16 / 9)

        final_video_path = f"temp/stitched_{str(uuid.uuid4())}.mp4"
        #crop_filter = f"crop=in_w:in_w*(16/9):(in_w-out_w)/2:(in_h-out_h)/2,scale={output_width}:{output_height}"
        #crop_filter = f"crop={output_width}:{output_height}:(in_w-{output_width})/2:(in_h-{output_height})/2,scale={output_width}:{output_height}"
        
        
        images = [os.path.abspath(os.path.join(image_files_path, image)) for image in os.listdir(image_files_path)]
        num_images = len(images)
        random_transitions = random.choices(transition_clips, k=num_images-1)
        transition_durations = [self.get_video_duration(clip) for clip in random_transitions]

        
        total_transition_time = sum(transition_durations)
        remaining_time = audio_duration - total_transition_time

        print("Audio Duration:", audio_duration)
        print("Num images:", num_images)
        print("TTime:", total_transition_time)
        print("RTime:", remaining_time)
        image_duration = remaining_time / num_images

        image_video_clip_paths = []
        
        # Crop and center all images to 1080x1920 (9:16)
        for i, img in enumerate(images):
            crop_filter = self.get_crop_filter(img, 1080, 1920)
            output = f"app/temp/img_clip_{str(uuid.uuid4())}.mp4"
            istream = ffmpeg.input(img, loop=1, t=image_duration)

            crop_filter(istream).filter("fps", fps=30).output(output, vcodec="libx264", pix_fmt="yuv420p", t=image_duration, r=30).run()
            image_video_clip_paths.append(output)

        concat_files = [] # List of video clips to concat
        ffmpeg_transitions = [ffmpeg.input(clip) for clip in random_transitions] # The list of transition video clips randomly chosen from library

        total_time = 0
        prev_clip = None
        # Alternate between adding a video and a transition the the final concat
        for i in range(len(image_video_clip_paths) - 1):
            ivideostream = ffmpeg.input(image_video_clip_paths[i]) # Video stream object created from each image_video_clip
            transitionStream = ffmpeg_transitions[i % len(ffmpeg_transitions)]

            if i == 0:
                prev_clip = ivideostream
            # ivideostream = ffmpeg.filter([ivideostream], 'settb', 'AVTB')
            # transitionStream = ffmpeg.filter([transitionStream], 'settb', 'AVTB')

            total_time = total_time + (image_duration*i)+transition_durations[i]

            #video_with_fade = ffmpeg.filter([ivideostream, transitionStream], 'xfade', transition='dissolve', duration=0.3, offset=total_time)
            video_with_fade = ffmpeg.filter([prev_clip, transitionStream], 'xfade', transition='dissolve', duration=0.3, offset=total_time)
            prev_clip = video_with_fade



            #concat_files.append(video_with_fade)
            
            # Directly stitch the files together
            # concat_files.append(ivideostream)
            # concat_files.append(transitionStream)
            
        #concat_files.append(ffmpeg.input(image_video_clip_paths[-1]))  # Append the last image
        concat_files.append(prev_clip)
        ffmpeg.concat(*concat_files, v=1, a=0).output(final_video_path, vcodec='libx264', audio_bitrate='192k', r=30, t=audio_duration, pix_fmt='yuv420p').run()
        print(concat_files)
        print(image_video_clip_paths)

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


if __name__ == "__main__":

    api_key = os.getenv("elevenlabs_api_key_iyc")
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
    
