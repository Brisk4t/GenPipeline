import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import shutil
from editvideo import VideoGenerator
import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()
react_build_path = os.path.normpath(os.path.abspath("../frontend/build"))

try:
    app.mount("/static", StaticFiles(directory=os.path.join(react_build_path, "static")), name="static")

except:
    pass

# Ensure that the temp folder exists
TEMP_FOLDER = "./temp"
video_generator = VideoGenerator()
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)


def cleanup_files(*file_paths: str):
    """Delete files provided in file_paths."""
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Error deleting {path}: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def serve_react():
    """Serve React index.html for the root path."""
    return FileResponse(os.path.join(react_build_path, "index.html"))

@app.post("/generate_video")
async def generate_video(background_tasks: BackgroundTasks, text: str = Form(...), base_video: UploadFile = File(...)):
    try:
        # Create a unique filename for the uploaded base video
        base_video_filename = f"{uuid.uuid4()}_{base_video.filename}"
        base_video_path = os.path.join(TEMP_FOLDER, base_video_filename)
        
        # Save the uploaded video to the temp folder
        with open(base_video_path, "wb") as buffer:
            shutil.copyfileobj(base_video.file, buffer)
        
        # Create a unique output video name based on the first three words of text
        words_in_title = text.split()
        if len(words_in_title) < 3:
            raise HTTPException(status_code=400, detail="Text must contain at least three words.")
        output_video_filename = f"{words_in_title[0]}_{words_in_title[1]}_{words_in_title[2]}_{uuid.uuid4()}.mp4"
        output_video_path = os.path.join(TEMP_FOLDER, output_video_filename)
        
        # Call your video processing function
        generated_video_path = await video_generator.generate_subtitles_video(text, base_video_path, output_video_path)
        background_tasks.add_task(cleanup_files, base_video_path, generated_video_path)
        
        # Return the generated video file as a response
        return FileResponse(
            generated_video_path,
            media_type="video/mp4",
            filename=os.path.basename(generated_video_path))
    
    except Exception as e:
        logger.error(f"Error during video generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG to capture detailed logs
    logger = logging.getLogger(__name__)


    uvicorn.run(app, host="0.0.0.0", port=8000)
