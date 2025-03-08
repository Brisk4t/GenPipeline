import React from 'react';
import logo from './logo.svg';
import './App.css';
import MainComponent from './components/MainComponent';


function App() {
  return (
    <div className="App">
      <h1>Elevenlabs TTS and Video Subtitle Generator</h1>
      <MainComponent /> {/* This will render your custom component */}
    </div>
  );
}
export default App;
