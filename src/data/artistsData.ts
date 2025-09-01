import { Artist } from '../types';

const API_BASE_URL = 'http://localhost:8000';

let artistsData: Artist[] = [];
let isLoading = false;
let isLoaded = false;

// API service functions
export const apiService = {
  async searchArtists(filters: any = {}) {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(filters),
    });
    if (!response.ok) throw new Error('Failed to search artists');
    return response.json();
  },

  async chat(message: string, conversationHistory: string[] = []) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message, 
        conversation_history: conversationHistory 
      }),
    });
    if (!response.ok) throw new Error('Failed to get chat response');
    return response.json();
  },

  async getStats() {
    const response = await fetch(`${API_BASE_URL}/stats`);
    if (!response.ok) throw new Error('Failed to get stats');
    return response.json();
  },

  async getSimilarArtists(artistId: string, limit: number = 5) {
    const response = await fetch(`${API_BASE_URL}/artists/similar/${artistId}?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to get similar artists');
    return response.json();
  },

  async getCategories() {
    const response = await fetch(`${API_BASE_URL}/categories`);
    if (!response.ok) throw new Error('Failed to get categories');
    return response.json();
  }
};

// Load initial data from API
const initializeData = async () => {
  if (isLoading || isLoaded) return;
  isLoading = true;
  
  try {
    const result = await apiService.searchArtists({ limit: 1000 });
    artistsData = result.artists;
    isLoaded = true;
    console.log(`Loaded ${artistsData.length} artists from API`);
  } catch (error) {
    console.error('Failed to load artists data:', error);
    // Fallback to empty array if API is not available
    artistsData = [];
  } finally {
    isLoading = false;
  }
};

// Initialize data loading
initializeData();

export const getArtistsData = (): Artist[] => {
  return artistsData;
};

export const waitForData = async (): Promise<Artist[]> => {
  while (isLoading) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  return artistsData;
};

export const getCraftTypes = (): string[] => {
  return [...new Set(artistsData.map(artist => artist.craft_type))];
};

export const getStates = (): string[] => {
  return [...new Set(artistsData.map(artist => artist.location.state))];
};

export const getDistrictsByState = (state: string): string[] => {
  return [...new Set(artistsData
    .filter(artist => artist.location.state === state)
    .map(artist => artist.location.district))];
};

export const getArtistsByState = (state: string): Artist[] => {
  return artistsData.filter(artist => 
    artist.location.state.toLowerCase().includes(state.toLowerCase())
  );
};

export const getArtistsByCity = (city: string): Artist[] => {
  return artistsData.filter(artist => 
    artist.location.district.toLowerCase().includes(city.toLowerCase()) ||
    artist.location.village.toLowerCase().includes(city.toLowerCase())
  );
};

export const getArtistsByCraft = (craft: string): Artist[] => {
  return artistsData.filter(artist => 
    artist.craft_type.toLowerCase().includes(craft.toLowerCase())
  );
};

export const getArtistsByStateAndCraft = (state: string, craft: string): Artist[] => {
  return artistsData.filter(artist => 
    artist.location.state.toLowerCase().includes(state.toLowerCase()) &&
    artist.craft_type.toLowerCase().includes(craft.toLowerCase())
  );
};