import React from 'react';
import { Typography, Box } from '@mui/material';

const CostDisplay = ({ cost, analysis }) => {
  if (cost === null) return null;
  return (
    <Box>
      {analysis && (
        <Box mb={2}>
          <Typography>Brand: {analysis.brand}</Typography>
          <Typography>Model: {analysis.model}</Typography>
          <Typography>Year: {analysis.year}</Typography>
          <Typography>Part: {analysis.damaged_part}</Typography>
          <Typography>Severity: {analysis.severity}</Typography>
        </Box>
      )}
      <Typography variant="h5">Estimated Cost: {cost} MAD</Typography>
    </Box>
  );
};

export default CostDisplay;
