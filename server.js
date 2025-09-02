import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = 8000;

// Middleware
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:5173'],
  credentials: true
}));
app.use(express.json());

// Load CSV data
let artistsData = [];

function loadCSVData() {
  try {
    const csvPath = path.join(__dirname, 'src', 'Artisans.csv');
    const csvContent = fs.readFileSync(csvPath, 'utf-8');
    
    const lines = csvContent.split('\n');
    const headers = lines[0].split(',');
    
    artistsData = [];
    
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      const values = parseCSVLine(line);
      if (values.length < headers.length) continue;
      
      try {
        const artist = {
          id: values[0],
          name: values[1],
          gender: values[2],
          age: parseInt(values[3]) || 0,
          craft_type: values[4],
          location: {
            state: values[5] || '',
            district: values[6] || '',
            village: values[7] || ''
          },
          contact: {
            email: values[9] || '',
            phone: formatPhoneNumber(values[10]),
            phone_available: values[11]?.toLowerCase() === 'yes'
          },
          languages: values[8] ? values[8].split(',').map(lang => lang.trim().replace(/"/g, '')) : [],
          government_id: values[12] || '',
          cluster_code: values[13] || ''
        };
        
        artistsData.push(artist);
      } catch (error) {
        console.warn(`Error parsing line ${i + 1}:`, error);
      }
    }
    
    console.log(`Loaded ${artistsData.length} artists from CSV`);
  } catch (error) {
    console.error('Error loading CSV:', error);
  }
}

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    const nextChar = line[i + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  
  result.push(current.trim());
  return result;
}

function formatPhoneNumber(phone) {
  if (phone && phone.includes('E+')) {
    const num = parseFloat(phone);
    const phoneStr = Math.round(num).toString();
    if (phoneStr.length === 12 && phoneStr.startsWith('91')) {
      return `+${phoneStr}`;
    }
    return phoneStr;
  }
  return phone || '';
}

// Load data on startup
loadCSVData();

// API Routes
app.post('/search', (req, res) => {
  try {
    const filters = req.body;
    let filteredArtists = [...artistsData];
    
    // Apply filters
    if (filters.state) {
      filteredArtists = filteredArtists.filter(a => 
        a.location.state.toLowerCase().includes(filters.state.toLowerCase())
      );
    }
    
    if (filters.district) {
      filteredArtists = filteredArtists.filter(a => 
        a.location.district.toLowerCase().includes(filters.district.toLowerCase())
      );
    }
    
    if (filters.craft_type) {
      filteredArtists = filteredArtists.filter(a => 
        a.craft_type.toLowerCase().includes(filters.craft_type.toLowerCase())
      );
    }
    
    if (filters.name) {
      filteredArtists = filteredArtists.filter(a => 
        a.name.toLowerCase().includes(filters.name.toLowerCase())
      );
    }
    
    if (filters.age_min !== undefined) {
      filteredArtists = filteredArtists.filter(a => a.age >= filters.age_min);
    }
    
    if (filters.age_max !== undefined) {
      filteredArtists = filteredArtists.filter(a => a.age <= filters.age_max);
    }
    
    // Apply limit
    const limit = filters.limit || 20;
    const results = filteredArtists.slice(0, limit);
    
    res.json({
      artists: results,
      total: filteredArtists.length,
      status: 'online'
    });
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/stats', (req, res) => {
  try {
    const stats = {
      total_artists: artistsData.length,
      unique_crafts: new Set(artistsData.map(a => a.craft_type)).size,
      unique_states: new Set(artistsData.map(a => a.location.state)).size,
      unique_districts: new Set(artistsData.map(a => a.location.district)).size,
      status: 'online'
    };
    
    res.json(stats);
  } catch (error) {
    console.error('Stats error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/chat', (req, res) => {
  try {
    const { message, conversation_history = [] } = req.body;
    const lowerMessage = message.toLowerCase();
    
    let intent = 'general';
    let responseMessage = '';
    let artists = [];
    const suggestions = [
      'Show me pottery artists',
      'Find artists in Rajasthan',
      'Get database statistics',
      'Browse textile crafts'
    ];
    
    // Basic chat response logic
    if (lowerMessage.includes('pottery') || lowerMessage.includes('pot')) {
      intent = 'search_craft';
      artists = artistsData.filter(a => a.craft_type.toLowerCase().includes('pottery')).slice(0, 5);
      responseMessage = `Found ${artists.length} pottery artists in our database.`;
    } else if (lowerMessage.includes('rajasthan')) {
      intent = 'search_location';
      artists = artistsData.filter(a => a.location.state.toLowerCase().includes('rajasthan')).slice(0, 5);
      responseMessage = `Found ${artists.length} artists in Rajasthan from our database.`;
    } else if (lowerMessage.includes('stats') || lowerMessage.includes('statistic')) {
      intent = 'get_stats';
      responseMessage = 'Here are the current database statistics:';
    } else if (lowerMessage.includes('weaving') || lowerMessage.includes('textile')) {
      intent = 'search_craft';
      artists = artistsData.filter(a => a.craft_type.toLowerCase().includes('weaving')).slice(0, 5);
      responseMessage = `Found ${artists.length} weaving artists in our database.`;
    } else if (lowerMessage.includes('chikankari')) {
      intent = 'search_craft';
      artists = artistsData.filter(a => a.craft_type.toLowerCase().includes('chikankari')).slice(0, 5);
      responseMessage = `Found ${artists.length} Chikankari artists in our database.`;
    } else if (lowerMessage.includes('carpet')) {
      intent = 'search_craft';
      artists = artistsData.filter(a => a.craft_type.toLowerCase().includes('carpet')).slice(0, 5);
      responseMessage = `Found ${artists.length} carpet weaving artists in our database.`;
    } else if (lowerMessage.includes('ladakh') || lowerMessage.includes('laddak')) {
      intent = 'search_location';
      artists = artistsData.filter(a => 
        a.location.state.toLowerCase().includes('ladakh') ||
        a.location.district.toLowerCase().includes('ladakh') ||
        a.location.village.toLowerCase().includes('ladakh')
      ).slice(0, 5);
      responseMessage = `Found ${artists.length} artists from Ladakh region in our database.`;
    } else {
      responseMessage = 'Hello! I can help you find traditional Indian artists. You can search by craft type, location, or ask for database statistics.';
    }
    
    const response = {
      intent,
      entities: {},
      message: responseMessage,
      llm_message: 'AI-powered search results from our comprehensive artisan database.',
      artists,
      suggestions,
      stats: intent === 'get_stats' ? {
        total_artists: artistsData.length,
        unique_crafts: new Set(artistsData.map(a => a.craft_type)).size,
        unique_states: new Set(artistsData.map(a => a.location.state)).size,
        unique_districts: new Set(artistsData.map(a => a.location.district)).size
      } : {},
      status: 'online'
    };
    
    res.json(response);
  } catch (error) {
    console.error('Chat error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/artists/similar/:id', (req, res) => {
  try {
    const { id } = req.params;
    const limit = parseInt(req.query.limit) || 5;
    
    const targetArtist = artistsData.find(a => a.id === id);
    let similarArtists = artistsData;
    
    if (targetArtist) {
      similarArtists = artistsData.filter(a => 
        a.id !== id && (
          a.craft_type === targetArtist.craft_type || 
          a.location.state === targetArtist.location.state
        )
      );
    }
    
    res.json({
      similar_artists: similarArtists.slice(0, limit),
      status: 'online'
    });
  } catch (error) {
    console.error('Similar artists error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/categories', (req, res) => {
  try {
    res.json({
      crafts: [...new Set(artistsData.map(a => a.craft_type))],
      states: [...new Set(artistsData.map(a => a.location.state))],
      status: 'online'
    });
  } catch (error) {
    console.error('Categories error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    artists_loaded: artistsData.length,
    timestamp: new Date().toISOString()
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Kala-Kaart API Server running on http://localhost:${PORT}`);
  console.log(`📊 Loaded ${artistsData.length} artists`);
  console.log('🔗 CORS enabled for frontend development servers');
});