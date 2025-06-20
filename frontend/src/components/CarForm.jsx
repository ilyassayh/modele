import React, { useState } from 'react';
import { TextField, MenuItem, Button, Grid } from '@mui/material';

const brands = ['Dacia','Renault','Peugeot','Hyundai','Volkswagen','Toyota','Fiat','Ford','Mercedes','BMW'];
const models = {
  Dacia: ['Logan','Sandero','Duster'],
  Renault: ['Clio','Megane','Kangoo'],
  Peugeot: ['208','301','308'],
  Hyundai: ['i10','i20','Tucson'],
  Volkswagen: ['Polo','Golf','Passat'],
  Toyota: ['Yaris','Corolla','RAV4'],
  Fiat: ['Panda','Tipo','500'],
  Ford: ['Fiesta','Focus','EcoSport'],
  Mercedes: ['C-Class','E-Class','A-Class'],
  BMW: ['Series 1','Series 3','X1']
};
const parts = ['Porte arrière gauche','Aile arrière droite','Aile arrière gauche','Pare-brise arrière','Coffre','Feu arrière droit','Feu arrière gauche','Pare-choc arrière','Plaque d\'immatriculation arrière','Pare-choc avant','Capot','Grille','Phare avant gauche','Phare avant droit'];
const severities = [
  { value: 1, label: 'Mineur' },
  { value: 2, label: 'Modéré' },
  { value: 3, label: 'Grave' }
];

const CarForm = ({ onSubmit }) => {
  const [brand, setBrand] = useState(brands[0]);
  const [model, setModel] = useState(models[brands[0]][0]);
  const [year, setYear] = useState(2020);
  const [part, setPart] = useState(parts[0]);
  const [severity, setSeverity] = useState(1);

  const handleBrandChange = (e) => {
    const value = e.target.value;
    setBrand(value);
    setModel(models[value][0]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ brand, model, year, damaged_part: part, severity });
  };

  return (
    <form onSubmit={handleSubmit}>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField select fullWidth label="Brand" value={brand} onChange={handleBrandChange}>
            {brands.map((b) => (
              <MenuItem key={b} value={b}>{b}</MenuItem>
            ))}
          </TextField>
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField select fullWidth label="Model" value={model} onChange={(e) => setModel(e.target.value)}>
            {models[brand].map((m) => (
              <MenuItem key={m} value={m}>{m}</MenuItem>
            ))}
          </TextField>
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField type="number" fullWidth label="Year" value={year} onChange={(e) => setYear(Number(e.target.value))} />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField select fullWidth label="Damaged Part" value={part} onChange={(e) => setPart(e.target.value)}>
            {parts.map((p) => (
              <MenuItem key={p} value={p}>{p}</MenuItem>
            ))}
          </TextField>
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField select fullWidth label="Severity" value={severity} onChange={(e) => setSeverity(Number(e.target.value))}>
            {severities.map((s) => (
              <MenuItem key={s.value} value={s.value}>{s.label}</MenuItem>
            ))}
          </TextField>
        </Grid>
        <Grid item xs={12}>
          <Button variant="contained" color="primary" type="submit">
            Get Estimate
          </Button>
        </Grid>
      </Grid>
    </form>
  );
};

export default CarForm;
