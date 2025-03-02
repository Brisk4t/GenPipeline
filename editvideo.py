import asyncio
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
from elevenapi import elevenlabs_calls
import uuid

def generate_video_with_subtitles(base_video_path, audio_path, text, word_timings, output_video_path):
    # Load the base video and audio
    video = VideoFileClip(base_video_path)
    audio = AudioFileClip(audio_path)

    # Set the audio to the video
    video = video.with_audio(audio)

    # Create a list of Subtitle clips based on word timings
    subtitle_clips = []

    for word, timings in word_timings.items():
        # Create a text clip for each word (with desired font size, color, etc.)
        txt_clip = TextClip(text=word, font_size=24, color='white', font='C:\\Windows\\Fonts\\arial.ttf', duration=(timings[1] - timings[0]))
        subtitle_clips.append(txt_clip)

    



    # Combine the video with the subtitles
    video_with_subtitles = CompositeVideoClip([video] + subtitle_clips)

    # Set the audio for the video
    video_with_subtitles = video_with_subtitles.with_audio(audio)

    # Write the final video to a file
    video_with_subtitles.write_videofile(output_video_path, codec="libx264", audio_codec="aac")



def generate_video_with_subtitles_2(base_video_path, audio_path, word_timings, output_video_path):
    # Load the base video and audio
    video = VideoFileClip(base_video_path)
    audio = AudioFileClip(audio_path)

    # Set the audio to the video
    video = video.with_audio(audio)

    # Create SRT subtitles from word timings
    create_srt_from_dict(word_timings)

    # Load subtitles
    generator = lambda text: TextClip('C:\\Windows\\Fonts\\arial.ttf',text=text, font_size=50, color='white', horizontal_align='center', size=video.size)
    subtitles = SubtitlesClip("subtitles.srt", make_textclip=generator, encoding='utf-8')

    # Combine the video with the subtitles
    video_with_subtitles = CompositeVideoClip([video, subtitles], size=video.size)

    # Set the audio for the video
    video_with_subtitles = video_with_subtitles.with_audio(audio)

    # Write the final video to a file
    video_with_subtitles.write_videofile(output_video_path, fps=video.fps)



def create_srt_from_dict(word_dict, output_filename="subtitles.srt"):
    """
    Generates an SRT file from a dictionary where keys are words and values are tuples 
    representing (start_time, end_time) in seconds.
    
    :param word_dict: Dictionary in the format {word: (start_time, end_time)}.
    :param output_filename: Name of the output SRT file.
    """
    with open(output_filename, 'w') as file:
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
    base_video_path = "BaseVideo9_16.mp4"  # Replace with your video file path
    output_video_path = "output_video.mp4"  # Path to save the output video
    text = "Hello this is a test subtitle file for elevenlabs"




    audio_timings = asyncio.run(creator.text_to_speech_timestamps(text, str(uuid.uuid4()))) 

    print(audio_timings[1])


    #generate_video_with_subtitles(base_video_path, audio_timings[0], text, audio_timings[1], output_video_path)
    generate_video_with_subtitles_2(base_video_path, audio_timings[0], audio_timings[1], output_video_path)
