import { useState, useEffect, useRef } from "react";
import { TextField, Button, Alert, CircularProgress, Typography, Box } from "@mui/material";

function FileTextCall({ apiEndpoint, supportedFileTypes, model_id }) {
    const [text, setText] = useState("");
    const [file, setFile] = useState(null);
    const [fileType, setFileType] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [filePreview, setFilePreview] = useState(null);
    const [previewHeight, setPreviewHeight] = useState(0);
    const [returnedVideo, setreturnedVideo] = useState(null); // New state for uploaded video URL
    const previewRef = useRef(null); // Reference to the preview element

    useEffect(() => {
        // Update the preview container height whenever it changes
        if (previewRef.current) {
            setPreviewHeight(previewRef.current.clientHeight);
        }
    }, [filePreview]); // Recalculate when the preview changes

    

    const handleFileChange = (event) => {
        const selectedFile = event.target.files[0];
        console.log("HandleFileChange")
        if (selectedFile) {
            const fileType = selectedFile.type;
                
            if (supportedFileTypes.includes(fileType)) {

                setFilePreview(null); 
                setFile(null);
                
                // Set new file and file type
                setFile(selectedFile);
                setFileType(fileType.startsWith("image") ? "image" : fileType.startsWith("video") ? "video" : null);
                
                // Update preview immediately after the new file is selected
                setFilePreview(URL.createObjectURL(selectedFile));
                console.log({filePreview})

                setError(null);
            } else {
                setError(`Unsupported file type. Supported: ${supportedFileTypes.join(", ")}`);
                setFile(null);
                setFileType(null);
                setFilePreview(null);
            }
        }
    };

    const handleTextChange = (event) => {
        setText(event.target.value);
    };

    const handleUpload = async () => {
        if (!file && !text) {
            setError("Please provide either a file and text.");
            return;
        }

        setUploading(true);
        setError(null);
        setSuccess(null);

        const formData = new FormData();
        if (file) formData.append("file", file);
        if (text) formData.append("text", text);
        formData.append("model_id", model_id)
        console.log("model_id", model_id)
        try {
            const response = await fetch(apiEndpoint, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Upload failed. Please try again.");
            }

            setSuccess("Upload successful!");

            const responseData = await response.blob();
            const videoURL = URL.createObjectURL(responseData)
            if (videoURL) {
                setreturnedVideo(videoURL); // Set the returned video URL
                setSuccess("Upload successful!");
            } else {
                setError("Video URL not found in response.");
            }

        } catch (error) {
            setError(error.message);
        } finally {
            setUploading(false);
        }
    };

    const rowHeight = 24; // Approximate row height for Material UI TextField
    const calculatedRows = previewHeight ? Math.max(3, Math.floor(previewHeight / rowHeight)) : 3; // Ensure at least 3 rows

    return (
        <Box sx={{ display: "flex", flexDirection: "row", gap: "20px", alignItems: "flex-start" }}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: "10px", flexGrow: 1 }}>
                <TextField
                    placeholder="Enter text here"
                    value={text}
                    onChange={handleTextChange}
                    multiline
                    rows={calculatedRows} // Adjust rows based on preview height
                    fullWidth
                    sx={{
                        height: previewHeight ? `${previewHeight}px` : "auto", // Dynamically adjust height
                        backgroundColor: "#f0f0f0",
                        marginTop: "10px",
                    }}
                />
                <Button variant="contained" component="label" style={{ marginBottom: "0px" }}>
                    Choose File
                    <input
                        type="file"
                        hidden
                        onChange={handleFileChange}
                        accept={supportedFileTypes.join(", ")}
                    />
                </Button>
                <Button
                    type="submit"
                    variant="contained"
                    color="secondary"
                    onClick={handleUpload}
                    disabled={uploading}
                >
                    {uploading ? <CircularProgress size={24} color="inherit" /> : "Upload"}
                </Button>
                {error && <Typography color="error" sx={{ marginTop: "10px" }}>{error}</Typography>}
                {success && <Typography color="success" sx={{ marginTop: "10px" }}>{success}</Typography>}
            </Box>

            {file && (
                <Box
                key={filePreview}
                ref={previewRef}
                sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", maxWidth: "200px", border: "1px solid #ccc", padding: "10px", borderRadius: "4px" }}>
                    <Typography variant="h6" gutterBottom>Upload Preview</Typography>
                    {file.type.startsWith("image") ? (
                        <img src={filePreview} alt="Preview" style={{ width: "100%", height: "auto", maxWidth: "150px", objectFit: "cover" }} />
                    ) : file.type.startsWith("video") ? (
                        <video width="100%" height="auto" controls>
                            <source src={filePreview} type={file.type} />
                            Your browser does not support the video tag.
                        </video>
                    ) : (
                        <Typography variant="body2" color="textSecondary">No preview available</Typography>
                    )}
                </Box>
            )}
            {returnedVideo && (
                <Box key={returnedVideo} sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", maxWidth: "200px", border: "1px solid #ccc", padding: "10px", borderRadius: "4px" }}>
                    <Typography variant="h6" gutterBottom>Generated Video</Typography>
                    <video width="100%" height="auto" controls>
                        <source src={returnedVideo} type="video/mp4" />
                        Your browser does not support the video tag.
                    </video>
                </Box>
            )}
        </Box>
    );
}


export default FileTextCall;
