import React, { useState } from 'react';
import { Container, Typography, Box } from '@mui/material';
import CarForm from './components/CarForm';
import ImageUpload from './components/ImageUpload';
import CostDisplay from './components/CostDisplay';
import axios from 'axios';

const App = () => {
  const [cost, setCost] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  const handlePredict = async (data) => {
    try {
      const res = await axios.post('http://localhost:8000/predict', data);
      setCost(res.data.estimated_cost);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAnalyze = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post('http://localhost:8000/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setAnalysis(res.data);
      setCost(res.data.estimated_cost);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Container maxWidth="md">
      <Typography variant="h4" gutterBottom>
        Car Repair Cost Estimator
      </Typography>
      <Box my={4}>
        <CarForm onSubmit={handlePredict} />
      </Box>
      <Box my={4}>
        <ImageUpload onAnalyze={handleAnalyze} />
      </Box>
      <Box my={4}>
        <CostDisplay cost={cost} analysis={analysis} />
      </Box>
    </Container>
  );
};

export default App;
