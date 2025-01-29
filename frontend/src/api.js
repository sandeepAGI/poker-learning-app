import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:5000', // Update with your Flask backend URL
});

export const fetchGameData = async () => {
  try {
    const response = await API.get('/game-data'); // Example endpoint
    return response.data;
  } catch (error) {
    console.error('Error fetching game data:', error);
    throw error;
  }
};