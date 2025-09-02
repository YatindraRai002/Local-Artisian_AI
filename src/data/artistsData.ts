import { Artist } from '../types';
import { parseCSVToArtists } from '../utils/csvParser';

const API_BASE_URL = import.meta.env.PROD 
  ? '/api' 
  : 'http://localhost:8000';

let artistsData: Artist[] = [];
let isLoading = false;
let isLoaded = false;

// Load artists from CSV file (real data)
const loadArtistsFromCSV = async (): Promise<Artist[]> => {
  try {
    const response = await fetch('/Artisans.csv');
    if (!response.ok) {
      throw new Error(`Failed to fetch CSV: ${response.statusText}`);
    }
    const csvText = await response.text();
    const artists = parseCSVToArtists(csvText);
    console.log(`Loaded ${artists.length} real artists from CSV`);
    return artists;
  } catch (error) {
    console.error('Error loading CSV:', error);
    // If CSV loading fails, return empty array instead of mock data
    return [];
  }
};

// Enhanced API service with offline fallback
export const apiService = {
  async searchArtists(filters: any = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters),
      });
      if (!response.ok) throw new Error('Failed to search artists');
      const result = await response.json();
      console.log(`🟢 API Online: Loaded ${result.artists.length} artists from server`);
      return result;
    } catch (error) {
      // Offline fallback - load real data from CSV
      console.warn('🔴 API unavailable, using CSV data');
      const csvData = await loadArtistsFromCSV();
      const limit = filters.limit || 20;
      return {
        artists: csvData.slice(0, limit),
        total: csvData.length,
        status: 'offline'
      };
    }
  },

  async chat(message: string, conversationHistory: string[] = []) {
    try {
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
      const result = await response.json();
      console.log('🟢 Chat API Online: Response received from server');
      return result;
    } catch (error) {
      // Offline fallback with basic response
      return this.generateOfflineResponse(message);
    }
  },

  async getStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/stats`);
      if (!response.ok) throw new Error('Failed to get stats');
      return response.json();
    } catch (error) {
      // Offline fallback - use CSV data for stats
      const csvData = await loadArtistsFromCSV();
      return {
        total_artists: csvData.length,
        unique_crafts: new Set(csvData.map(a => a.craft_type)).size,
        unique_states: new Set(csvData.map(a => a.location.state)).size,
        unique_districts: new Set(csvData.map(a => a.location.district)).size,
        status: 'offline'
      };
    }
  },

  async getSimilarArtists(artistId: string, limit: number = 5) {
    try {
      const response = await fetch(`${API_BASE_URL}/similar?artistId=${artistId}&limit=${limit}`);
      if (!response.ok) throw new Error('Failed to get similar artists');
      return response.json();
    } catch (error) {
      // Offline fallback - find similar artists from CSV data
      const csvData = await loadArtistsFromCSV();
      const targetArtist = csvData.find(a => a.id === artistId);
      let similarArtists = csvData;
      
      if (targetArtist) {
        // Find artists with same craft type or same state
        similarArtists = csvData.filter(a => 
          a.id !== artistId && (
            a.craft_type === targetArtist.craft_type || 
            a.location.state === targetArtist.location.state
          )
        );
      }
      
      return {
        similar_artists: similarArtists.slice(0, limit),
        status: 'offline'
      };
    }
  },

  async getCategories() {
    try {
      const response = await fetch(`${API_BASE_URL}/categories`);
      if (!response.ok) throw new Error('Failed to get categories');
      return response.json();
    } catch (error) {
      // Offline fallback - get categories from CSV data
      const csvData = await loadArtistsFromCSV();
      return {
        crafts: [...new Set(csvData.map(a => a.craft_type))],
        states: [...new Set(csvData.map(a => a.location.state))],
        status: 'offline'
      };
    }
  },

  // Generate offline chat responses using CSV data
  async generateOfflineResponse(message: string) {
    const lowerMessage = message.toLowerCase();
    let intent = 'general';
    let responseMessage = '';
    let artists: Artist[] = [];
    const suggestions = [
      'Show me pottery artists',
      'Find artists in Rajasthan',
      'Get database statistics',
      'Browse textile crafts'
    ];

    const csvData = await loadArtistsFromCSV();

    if (lowerMessage.includes('pottery') || lowerMessage.includes('pot')) {
      intent = 'search_craft';
      artists = csvData.filter(a => a.craft_type.toLowerCase().includes('pottery')).slice(0, 5);
      responseMessage = `Found ${artists.length} pottery artists in our database.`;
    } else if (lowerMessage.includes('rajasthan')) {
      intent = 'search_location';
      artists = csvData.filter(a => a.location.state.toLowerCase().includes('rajasthan')).slice(0, 5);
      responseMessage = `Found ${artists.length} artists in Rajasthan from our database.`;
    } else if (lowerMessage.includes('stats') || lowerMessage.includes('statistic')) {
      intent = 'get_stats';
      responseMessage = 'Here are the current database statistics from our CSV data:';
    } else if (lowerMessage.includes('weaving') || lowerMessage.includes('textile')) {
      intent = 'search_craft';
      artists = csvData.filter(a => a.craft_type.toLowerCase().includes('weaving')).slice(0, 5);
      responseMessage = `Found ${artists.length} weaving artists in our database.`;
    } else if (lowerMessage.includes('chikankari')) {
      intent = 'search_craft';
      artists = csvData.filter(a => a.craft_type.toLowerCase().includes('chikankari')).slice(0, 5);
      responseMessage = `Found ${artists.length} Chikankari artists in our database.`;
    } else if (lowerMessage.includes('carpet')) {
      intent = 'search_craft';
      artists = csvData.filter(a => a.craft_type.toLowerCase().includes('carpet')).slice(0, 5);
      responseMessage = `Found ${artists.length} carpet weaving artists in our database.`;
    } else {
      responseMessage = 'I\'m currently running in offline mode with real artist data from our CSV database. I can help you search for artists by craft type, location, or view database statistics.';
    }

    return {
      intent,
      entities: {},
      message: responseMessage,
      llm_message: 'Currently operating in offline mode with real CSV data. Full AI features will be available when the backend server is connected.',
      artists,
      suggestions,
      stats: intent === 'get_stats' ? {
        total_artists: csvData.length,
        unique_crafts: new Set(csvData.map(a => a.craft_type)).size,
        unique_states: new Set(csvData.map(a => a.location.state)).size,
        unique_districts: new Set(csvData.map(a => a.location.district)).size
      } : {},
      status: 'offline'
    };
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
    const mode = result.status === 'offline' ? 'offline' : 'online';
    console.log(`Loaded ${artistsData.length} artists (${mode} mode)`);
  } catch (error) {
    console.error('Failed to load artists data:', error);
    // Fallback to CSV data
    artistsData = await loadArtistsFromCSV();
    console.log(`Using ${artistsData.length} real artists from CSV (offline mode)`);
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