import React, { useState, useRef } from 'react';
import { Button, TextField, Box, Typography, Container, Input, createTheme, ThemeProvider } from '@mui/material';
import axios from 'axios';
import FileTextCall from './FileTextCall';
import DropDownComponent from './DropDownComponent';
import PostComponent from './PostComponent'

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2', // Blue color for primary buttons
    },
    secondary: {
      main: '#f50057', // Pink color for secondary buttons
    },
    error: {
      main: '#d32f2f', // Red for error buttons
    },
    success: {
      main: '#388e3c', // Green for success buttons
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
    },
  },
  typography: {
    h4: {
      color: '#ffffff',
    },
    h6: {
      color: '#ffffff',
    },
    body1: {
      color: '#b0b0b0',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '4px',
          textTransform: 'none', // Remove uppercase transformation
        },
        contained: {
          '&:hover': {
            filter: 'brightness(0.85)', // Dim the button on hover
          },
        },
        outlined: {
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderColor: '#ffffff', // White outline on hover
          },
        },
      },
    },
  },
});

function MainComponent() {
  const [subtitlesText, setSubtitlesText] = useState('');
  const [subtitlesFile, setSubtitlesFile] = useState(null);
  const [baseVideoFile, setBaseVideoFile] = useState(null);
  const [uploadedVideoPreview, setUploadedVideoPreview] = useState(null);
  const [processedVideoPreview, setProcessedVideoPreview] = useState(null);
  const [placeholderText, setPlaceholderText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imageBase64, setImageBase64] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('');
  
  const subtitlesFileRef = useRef(null);
  const imageFileRef = useRef(null);


  const handleSelectionChange = (newSelection) => {
    setSelectedVoice(newSelection);
    console.log("Newly Selected Voice", selectedVoice)

  };

  // Handle subtitles text change
  const handleSubtitlesTextChange = (e) => {
    setSubtitlesText(e.target.value);
  };

  // Handle subtitles file change (upload)
  const handleSubtitlesFileChange = () => {
    subtitlesFileRef.current.click(); // Open the file dialog when clicking the button
  };

  // Handle subtitles file change (upload)
  const handleImageChange = () => {
    document.getElementById('image-upload').click(); // Trigger file input click via button
  };

  const handleFileSelection = (e) => {
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

  // Handle base video selection (upload)
  const handleBaseVideoChange = () => {
    document.getElementById('video-upload').click(); // Trigger file input click via button
  };

  const handleVideoSelection = (e) => {
    const file = e.target.files[0];
    if (file) {
      setBaseVideoFile(file);
      const videoUrl = URL.createObjectURL(file);
      setUploadedVideoPreview(videoUrl);
    }
  };

  // Handle image selection (upload)
  const handleImageSelection = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImageBase64(reader.result); // Store base64 image data
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle form submission for video and subtitles
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

    const formData = new FormData();
    formData.append('text', subtitlesText);
    formData.append('base_video', baseVideoFile);

    try {
      const response = await axios.post('/generate_video', formData, {
        responseType: 'blob',
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const processedVideoUrl = URL.createObjectURL(response.data);
      setProcessedVideoPreview(processedVideoUrl);
    } catch (error) {
      console.error('Error uploading files:', error);
      alert("There was an error processing your video.");
    }
  };

  // Handle form submission for /runway_generate
  const handleRunwayGenerateSubmit = async (e) => {
    e.preventDefault();

    if (!imageFile) {
      alert('Please upload an image.');
      return;
    }

    if (!placeholderText) {
      alert('Please enter placeholder text.');
      return;
    }

    const formData = new FormData();
    formData.append('prompt', placeholderText);
    formData.append('base_image', imageFile); // You might need to convert imageBase64 to a file if needed

    try {
      const response = await axios.post('/runway_generate', formData, {
        responseType: 'blob',
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const videoUrl = response.data.output[0]; // Use the output field for the video URL
      handleVideoSelection(videoUrl)

      alert('Success! Response from /runway_generate endpoint.');
      console.log('Response:', response.data);
    } catch (error) {
      console.error('Error calling /runway_generate:', error);
      alert('Error calling /runway_generate endpoint.');
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <Container maxWidth="false" sx={{ padding: 3 }}>
        <Typography variant="h4" gutterBottom>
          Upload Video and Subtitles
        </Typography>
        
        <div>
            <h2>Select Voice: {selectedVoice}</h2>
            <DropDownComponent onSelectionChange={handleSelectionChange} />
        </div>

        <Box mb={5}>
          <FileTextCall apiEndpoint={"/generate_video"} supportedFileTypes={["video/mp4", "image/jpeg", "image/png"]} model_id={selectedVoice} />
        </Box>


          {/* Base Video File */}
          <Box mb={3}>
            <Typography variant="body1">Base Video File:</Typography>
            <Button
              variant="outlined"
              onClick={handleBaseVideoChange}
              sx={{ marginTop: 1 }}
            >
              Upload Base Video
            </Button>
            <Input
              type="file"
              id="video-upload"
              accept="video/*"
              onChange={handleVideoSelection}
              style={{ display: 'none' }}
            />
          </Box>

        <hr style={{ margin: '2rem 0' }} />

        <Typography variant="h5" gutterBottom>
          Video Post
        </Typography>
        <PostComponent apiEndpoint={"http://localhost:8000/post_to_instagram"} supportedFileTypes={["video/mp4"]} video={false}/>
      </Container>
    </ThemeProvider>
  );
}

export default MainComponent;
