import React, { useState, useRef } from 'react';
import axios from 'axios';

function MainComponent() {
  // State for subtitles input (text or file)
  const [subtitlesText, setSubtitlesText] = useState('');
  const [subtitlesFile, setSubtitlesFile] = useState(null);
  // State for base video file
  const [baseVideoFile, setBaseVideoFile] = useState(null);
  // Previews
  const [uploadedVideoPreview, setUploadedVideoPreview] = useState(null);
  const [processedVideoPreview, setProcessedVideoPreview] = useState(null);
  // Placeholder text input
  const [placeholderText, setPlaceholderText] = useState('');
  // Ref to file input for subtitles text file
  const subtitlesFileRef = useRef(null);

  // Read the text file if uploaded and update subtitlesText
  const handleSubtitlesFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSubtitlesFile(file);
      const reader = new FileReader();
      reader.onload = (ev) => {
        setSubtitlesText(ev.target.result);
      };
      reader.readAsText(file);
    }
  };

  // When a base video is selected, create a preview URL
  const handleBaseVideoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setBaseVideoFile(file);
      const videoUrl = URL.createObjectURL(file);
      setUploadedVideoPreview(videoUrl);
    }
  };

  // Form submission: send video, and subtitles text, then handle the returned video preview
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!baseVideoFile) {
      alert("Please upload a base video file.");
      return;
    }
    if (!subtitlesText) {
      alert("Please enter subtitles text or upload a txt file.");
      return;
    }

    // Build form data to send to FastAPI endpoint
    const formData = new FormData();
    formData.append('text', subtitlesText);
    formData.append('base_video', baseVideoFile);

    try {
      // POST the form data to FastAPI (adjust the URL if necessary)
      const response = await axios.post('http://localhost:8000/generate_video', formData, {
        responseType: 'blob', // important for receiving video file as blob
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Create a URL for the returned video blob and update state
      const processedVideoUrl = URL.createObjectURL(response.data);
      setProcessedVideoPreview(processedVideoUrl);
    } catch (error) {
      console.error('Error uploading files:', error);
      alert("There was an error processing your video.");
    }
  };

  // Handle the placeholder text form submission
  const handlePlaceholderSubmit = async (e) => {
    e.preventDefault();
    try {
      // Call the empty endpoint; adjust the URL as needed
      await axios.post('http://localhost:8000/empty', { placeholder: placeholderText });
      alert("Placeholder endpoint called successfully.");
    } catch (error) {
      console.error('Placeholder call error:', error);
      alert("Error calling the placeholder endpoint.");
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "1rem" }}>
      <h2>Upload Video and Subtitles</h2>
      <form onSubmit={handleSubmit}>
        {/* Subtitles text input */}
        <div>
          <label>Subtitles Text:</label>
          <textarea
            placeholder="Enter subtitles text here..."
            value={subtitlesText}
            onChange={(e) => setSubtitlesText(e.target.value)}
            rows={3}
            style={{ width: "100%" }}
          />
        </div>
        <div>
          <p>OR upload a TXT file:</p>
          <input
            type="file"
            accept=".txt"
            ref={subtitlesFileRef}
            onChange={handleSubtitlesFileChange}
          />
        </div>
        <br />
        {/* Base video upload */}
        <div>
          <label>Base Video File:</label>
          <input type="file" accept="video/*" onChange={handleBaseVideoChange} />
        </div>
        {uploadedVideoPreview && (
          <div>
            <h4>Uploaded Video Preview:</h4>
            <video width="400" controls src={uploadedVideoPreview}></video>
          </div>
        )}
        <br />
        <button type="submit">Submit for Processing</button>
      </form>

      {processedVideoPreview && (
        <div style={{ marginTop: "2rem" }}>
          <h3>Processed Video Preview</h3>
          <video width="400" controls src={processedVideoPreview}></video>
          <div>
            <a
              href={processedVideoPreview}
              download="processed_video.mp4"
              style={{ display: "inline-block", marginTop: "1rem", padding: "0.5rem 1rem", backgroundColor: "#007BFF", color: "#fff", textDecoration: "none", borderRadius: "4px" }}
            >
              Download Processed Video
            </a>
          </div>
        </div>
      )}

      <hr style={{ margin: "2rem 0" }} />

      <h2>Placeholder Endpoint</h2>
      <form onSubmit={handlePlaceholderSubmit}>
        <div>
          <label>Placeholder Text:</label>
          <input
            type="text"
            placeholder="Enter placeholder text..."
            value={placeholderText}
            onChange={(e) => setPlaceholderText(e.target.value)}
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </div>
        <br />
        <button type="submit">Call Placeholder Endpoint</button>
      </form>
    </div>
  );
}

export default MainComponent;
