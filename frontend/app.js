const express = require('express');
const axios = require('axios');
const path = require('path');

const app = express();

// Read API URL from environment so this works in any deployment without
// touching code (development, staging, production all use the same image).
const API_URL = process.env.API_URL || 'http://localhost:8000';

app.use(express.json());
app.use(express.static(path.join(__dirname, 'views')));

app.post('/submit', async (req, res) => {
  try {
    const response = await axios.post(`${API_URL}/jobs`);
    res.status(201).json(response.data);
  } catch (err) {
    console.error('Error creating job:', err?.response?.data || err.message);
    res.status(502).json({ error: 'Failed to create job' });
  }
});

app.get('/status/:id', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/jobs/${req.params.id}`);
    res.json(response.data);
  } catch (err) {
    const status = err?.response?.status;
    if (status === 404) {
      return res.status(404).json({ error: 'Job not found' });
    }
    if (status === 400) {
      return res.status(400).json({ error: 'Invalid job ID' });
    }
    console.error('Error fetching job status:', err?.response?.data || err.message);
    res.status(502).json({ error: 'Failed to fetch job status' });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Frontend running on port ${PORT}`);
});