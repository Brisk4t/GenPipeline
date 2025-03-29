import { useState, useEffect, useRef } from "react";
import { TextField, Button, Alert, CircularProgress, Typography, Box } from "@mui/material";

function FileTextCall({ apiEndpoint, supportedFileTypes, model_id }) {
    const [text, setText] = useState("");
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [filePreviews, setFilePreviews] = useState([]);
    const [previewHeight, setPreviewHeight] = useState(0);
    const [returnedVideo, setreturnedVideo] = useState(null); // New state for uploaded video URL
    const [firstFileType, setFirstFileType] = useState(null);
    const previewRef = useRef(null); // Reference to the preview element

    // useEffect(() => {
    //     // Update the preview container height whenever it changes
    //     if (previewRef.current) {
    //         setPreviewHeight(previewRef.current.clientHeight);
    //     }
    // }, [filePreviews]); // Recalculate when the preview changes

    

    const handleFileChange = (e) => {
        if (e.target.files) {
            const filesArray = Array.from(e.target.files).map((file) => ({
                file,
                url: URL.createObjectURL(file),
                type: file.type.startsWith("image") ? "image" : file.type.startsWith("video") ? "video" : "other",
            }));
    
        // Check if the type of the first file matches the new files
        
        if (selectedFiles.length === 0){
            const firstFileType = filesArray[0]?.type;
            const validFiles = filesArray.filter((file) => file.type === firstFileType);
            setSelectedFiles(validFiles)
        }

        else{
            const firstFileType = selectedFiles[0]?.type;
            const validFiles = filesArray.filter((file) => file.type === firstFileType);
            const invalidFiles = filesArray.filter((file) => file.type !== firstFileType);

            setSelectedFiles((prevFiles) => [...prevFiles, ...validFiles]);

            if(invalidFiles.length > 0){
                alert("All files must be of the same type as the first file.");
            }
        }

        }
      };


    const renderPreviews = (files) => {
        return files.map((fileObj, index) => (
            <Box key={index} sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "5px" }}>
                <div key={index} className="preview-container" style={{ margin: "5px", borderRadius: "5px", padding: "1px", backgroundColor: "#f9f9f9", 
                    objectFit:"cover", height: "200px", width:"200px", overflow: "hidden", position: "relative"}}  >
                {fileObj.type === "image" && <img src={fileObj.url} alt="Preview" className="preview-media" style={{objectFit: "cover", objectPosition: "center", position:"relative"}} />}
                {fileObj.type === "video" && (
                    <video controls className="preview-media">
                    <source src={fileObj.url} type="video/mp4" style={{objectFit: "cover", objectPosition: "center"}}  />
                    Your browser does not support the video tag.
                    </video>
                )}
                </div>
                <div>
                    <Button variant="outlined" onClick={() => moveFileUp(index)} disabled={index === 0}>Up</Button>
                    <Button variant="outlined" onClick={() => moveFileDown(index)} disabled={index === selectedFiles.length - 1}>Down</Button>
                </div>
            </Box>
        ));
    };  
 
    const handleTextChange = (event) => {
        setText(event.target.value);
    };

    const handleUpload = async () => {
        if (!setSelectedFiles.length && !text) {
            setError("Please provide a file and text.");
            return;
        }

        setUploading(true);
        setError(null);
        setSuccess(null);

        const formData = new FormData();
        selectedFiles.forEach(({ file }) => formData.append("files", file));
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

    const moveFileUp = (index) => {
        if (index > 0) {
            const updatedFiles = [...selectedFiles];
            const [movedFile] = updatedFiles.splice(index, 1);
            updatedFiles.splice(index - 1, 0, movedFile);
            setSelectedFiles(updatedFiles);
        }
    };

    const moveFileDown = (index) => {
        if (index < selectedFiles.length - 1) {
            const updatedFiles = [...selectedFiles];
            const [movedFile] = updatedFiles.splice(index, 1);
            updatedFiles.splice(index + 1, 0, movedFile);
            setSelectedFiles(updatedFiles);
        }
    };

    const rowHeight = 24; // Approximate row height for Material UI TextField
    const calculatedRows = previewHeight ? Math.max(3, Math.floor(previewHeight / rowHeight)) : 3; // Ensure at least 3 rows

    return (
        <Box sx={{ display: "flex", flexDirection: "row", gap: "20px", alignItems: "flex", justifyContent: "center"}}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: "10px", flexGrow: 1, maxWidth: "md"}}>
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
                        multiple
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

            {selectedFiles.length > 0 && (
                <Box
                key={filePreviews}
                ref={previewRef}
                sx={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)",  gap: "10px", maxHeight: "500px", overflowY: "auto", maxWidth:"false"}}>
                    {renderPreviews(selectedFiles)}
                </Box>
            )}
            {returnedVideo && (
                <Box key={returnedVideo} sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", maxWidth: "200px", maxHeight:"500px", border: "1px solid #ccc", padding: "10px", borderRadius: "4px" }}>
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
