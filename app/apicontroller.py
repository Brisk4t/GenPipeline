import base64
import os
from typing import List
import uuid
import shutil
import logging
import asyncio
import yaml
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from editvideo import VideoGenerator
from runwayml import RunwayML
import mimetypes
import uvicorn
from instagramPost import Instagram

class VideoApp:
    def __init__(self):
        """Initialize the FastAPI app, dependencies, and configurations."""
        self.app = FastAPI()
        self.config = self.load_config()
        self.video_generator = VideoGenerator(self.config["elevenlabs_api_key"])
        self.runway = RunwayML(api_key=self.config["runway_api_key"])
        self.temp_folder = "./temp"
        self.instagram = Instagram(self.config["instagram_accounts"])

        # Ensure temp directory exists
        os.makedirs(self.temp_folder, exist_ok=True)

        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Set up static file serving
        self.react_build_path = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend/build")))
        self.app.mount("/static", StaticFiles(directory=os.path.join(self.react_build_path, "static")), name="static")

        # Define API routes
        self.setup_routes()

    def load_config(self, filename="config.yaml"):
        """Load API keys from a YAML file."""
        yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")

        with open(yaml_path, "r") as file:
            return yaml.safe_load(file)

    def setup_routes(self):
        """Define API endpoints."""

        @self.app.get("/")
        def serve_react():
            """Serve React frontend."""
            return FileResponse(os.path.join(self.react_build_path, "index.html"))

        @self.app.post("/generate_video")
        async def generate_video(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...), text: str = Form(...), model_id: str = Form(...)):
            """Generate a video with subtitles."""
            try:
                file_paths = []
                for file in files:
                    base_video_path = self.save_uploaded_file(file)
                    file_paths.append(base_video_path)
                    mime_type, _ = mimetypes.guess_type(file.filename)

                output_video_filename = self.generate_output_filename(text)
                output_video_path = os.path.join(self.temp_folder, output_video_filename)

                

                if mime_type:
                    if mime_type.startswith("image/"):  
                        # If the file is an image
                        generated_video_path = await self.video_generator.generate_subtitles_image(text, file_paths, output_video_path, model_id)
                    
                    elif mime_type.startswith("video/"):  
                        generated_video_path = await self.video_generator.generate_subtitles_video(text, base_video_path, output_video_path, model_id)
                
               

                # Schedule cleanup of temporary files
                background_tasks.add_task(self.cleanup_files, base_video_path, generated_video_path)

                return FileResponse(
                    generated_video_path, media_type="video/mp4", filename=os.path.basename(generated_video_path)
                )

            except Exception as e:
                logging.error(f"Error during video generation: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal Server Error")

        @self.app.post("/post_to_instagram")
        async def post_to_instagram(background_tasks: BackgroundTasks, caption: str = Form(...), file: UploadFile = File(...), tags: str = Form(...)):
            """Post a video to all configured instagram accounts"""
            try:
                video = self.save_uploaded_file(file)
                await self.instagram.post_to_instagram(video, caption, tags)

            except Exception as e:
                logging.error(f"Error during video post to instagram: {e}", exc_info=True)



        @self.app.post("/runway_generate")
        async def runway_generate(
            background_tasks: BackgroundTasks, prompt: str = Form(...), base_image: UploadFile = File(...)
        ):
            """Generate a video from an image using RunwayML."""
            try:
                base64_image = await self.encode_image_to_base64(base_image)

                task = self.runway.image_to_video.create(
                    model="gen3a_turbo",
                    prompt_image=f"data:image/png;base64,{base64_image}",
                    prompt_text=prompt,
                )

                background_tasks.add_task(self.poll_task_status, task.id)
                return {"message": "Video generation task is being processed."}

            except Exception as e:
                logging.error(f"Error during RunwayML request: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal Server Error")

    def save_uploaded_file(self, uploaded_file: UploadFile) -> str:
        """Save an uploaded file to the temporary folder."""
        filename = f"{uuid.uuid4()}_{uploaded_file.filename}"
        file_path = os.path.join(self.temp_folder, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

        return file_path

    def generate_output_filename(self, text: str) -> str:
        """Generate a unique output filename based on the text input."""
        words = text.split()
        if len(words) < 3:
            raise HTTPException(status_code=400, detail="Text must contain at least three words.")
        
        return f"{words[0]}_{words[1]}_{words[2]}_{uuid.uuid4()}.mp4"

    async def poll_task_status(self, task_id: str):
        """Periodically check the status of a RunwayML task until completion."""
        task = self.runway.tasks.retrieve(task_id)
        while task.status not in ["SUCCEEDED", "FAILED"]:
            await asyncio.sleep(10)
            task = self.runway.tasks.retrieve(task_id)

    async def encode_image_to_base64(self, image: UploadFile) -> str:
        """Convert an image file to a Base64 string."""
        image_bytes = await image.read()
        return base64.b64encode(image_bytes).decode("utf-8")

    def cleanup_files(self, *file_paths: str):
        """Delete temporary files after processing."""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logging.error(f"Error deleting {path}: {e}")

    def run(self):
        """Start the FastAPI app."""
        logging.basicConfig(level=logging.DEBUG)
        uvicorn.run(self.app, host="0.0.0.0", port=8000)

# Run the app
if __name__ == "__main__":
    app_instance = VideoApp()
    app_instance.run()
