import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8080', // Updated to match the backend port
});

export const fetchGameData = async () => {
  try {
    const response = await API.get('/api/v1/games'); // Updated to match backend routes
    return response.data;
  } catch (error) {
    console.error('Error fetching game data:', error);
    throw error;
  }
};