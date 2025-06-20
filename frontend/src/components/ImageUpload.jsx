import React, { useState } from 'react';
import { Button } from '@mui/material';

const ImageUpload = ({ onAnalyze }) => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);

  const handleChange = (e) => {
    const f = e.target.files[0];
    setFile(f);
    if (f) {
      setPreview(URL.createObjectURL(f));
    }
  };

  const handleAnalyze = () => {
    if (file) onAnalyze(file);
  };

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleChange} />
      {preview && (
        <img src={preview} alt="preview" style={{ maxWidth: '100%', marginTop: '1rem' }} />
      )}
      <div>
        <Button variant="outlined" onClick={handleAnalyze} sx={{ mt: 2 }}>
          Analyze Image
        </Button>
      </div>
    </div>
  );
};

export default ImageUpload;
