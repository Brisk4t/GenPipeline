import asyncio
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
from elevenapi import elevenlabs_calls
import uuid
import os
import subprocess

def generate_video_with_subtitles(base_video_path, audio_path, word_timings, output_video_path, str_uuid):
    """
    Use a base video and audio file, stitch them together and add hard coded subtitles to the final video
    """
    # Load the base video and audio
    video = VideoFileClip(base_video_path)
    audio = AudioFileClip(audio_path)

    # Set the audio to the video
    video = video.with_audio(audio)


    # Create SRT subtitles from word timings
    create_srt_from_dict(word_timings, str_uuid)

    # Load subtitles
    generator = lambda text: TextClip('C:\\Windows\\Fonts\\arial.ttf',text=text, font_size=50, color='white', horizontal_align='center', size=video.size)
    subtitles = SubtitlesClip(f"temp/{str_uuid}_subtitles.srt", make_textclip=generator, encoding='utf-8')

    # Combine the video with the subtitles
    video_with_subtitles = CompositeVideoClip([video, subtitles], size=video.size)

    # Set the audio for the video
    video_with_subtitles = video_with_subtitles.with_audio(audio)

    # Write the final video to a file
    video_with_subtitles.write_videofile(output_video_path, fps=video.fps)

def add_subtitles_to_video(video_file, output_video_file, audio_and_timings, str_uuid):
    """
    FFMPEG based video subtitling, significantly faster than moviepy
    
    
    """
    create_srt_from_dict(audio_and_timings[1], str_uuid)
    command = [
        'ffmpeg',
        '-y',
        '-i', video_file,  # Input video file
        '-i', audio_and_timings[0], # Input audio file
        '-vf', f"subtitles=temp/{str_uuid}_subtitles.srt:charenc=UTF-8",  # Apply subtitles filter
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:a', 'copy',  # Copy the audio without re-encoding
        '-c:v', 'libx264',  # Encode video in H.264 format
        '-b:a', '192k',
        output_video_file  # Output video file with subtitles
    ]
    subprocess.run(command, check=True)

def create_srt_from_dict(word_dict, output_filename):
    """
    Generates an SRT file from a dictionary where keys are words and values are tuples 
    representing (start_time, end_time) in seconds.
    
    :param word_dict: Dictionary in the format {word: (start_time, end_time)}.
    :param output_filename: Name of the output SRT file.
    """
    output_filename = 'temp/' + output_filename + '_subtitles.srt'
    with open(output_filename, 'w', encoding='UTF-8') as file:
        counter = 1
        for word, (start, end) in word_dict.items():
            # Convert start and end time to the SRT format (HH:MM:SS,MMM)
            start_time = format_time(start)
            end_time = format_time(end)

            # Write each entry in SRT format
            file.write(f"{counter}\n")
            file.write(f"{start_time} --> {end_time}\n")
            file.write(f"{word}\n\n")
            counter += 1

def format_time(seconds):
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




if __name__ == "__main__":


    creator = elevenlabs_calls()

    # Example usage
    temp_location = "temp/"
    str_uuid = str(uuid.uuid4())


    base_video_path = "BaseVideo_9_16_2.mp4"  # Replace with your video file path
    output_video_path = "output_video.mp4"  # Path to save the output video
    #text = "In a small village, a young girl named Yuki discovered she had the power to control time. Every day, she’d rewind moments to help others, whether it was saving a cat stuck in a tree or preventing a broken vase. But one day, a mysterious boy appeared, claiming to have the ability to erase time altogether. As they clashed, Yuki realized the boy was her future self, lost in a cycle of regret. Together, they learned that true strength wasn’t in controlling time, but in accepting the moments as they are, cherishing both the good and the bad."
    #text = "Hello this is a subtitle test for elevenlabs"
    text = "यामतो, एक कुशल समुराई, अपने गाँव की रक्षा के लिए काले जादूगर रोशिन से लड़ने निकला। उसकी तलवार चंद्रमा की रोशनी में चमकती थी। जादूगर ने अंधकार का जाल फैलाया, लेकिन यामतो की आत्मा अडिग रही। दोनों की तलवारें टकराईं, आग की चिंगारियाँ बिखरीं। एक अंतिम वार में यामतो ने रोशिन का अभिशाप तोड़ दिया। गाँव रोशनी से भर गया, लेकिन यामतो घुटनों पर गिर पड़ा। उसकी आँखों में संतोष था—वह जीत गया था। आखिरी सांस लेते हुए, वह मुस्कुराया। उसका नाम अमर हो गया, कहानियों में, हवाओं में, अनंत तक।"

    audio_and_timings = asyncio.run(creator.text_to_speech_timestamps(text, temp_location + str_uuid)) 


    #generate_video_with_subtitles(base_video_path, audio_and_timings[0], text, audio_and_timings[1], output_video_path)
    #generate_video_with_subtitles(base_video_path, audio_and_timings[0], audio_and_timings[1], output_video_path, str_uuid)
    add_subtitles_to_video(base_video_path, output_video_path, audio_and_timings, str_uuid)


    # if os.path.exists(temp_location):
    #     os.remove(temp_location)
