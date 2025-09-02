import fs from 'fs';
import path from 'path';

let artistsData = [];
let dataLoaded = false;

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

function loadArtistsData() {
  if (dataLoaded) return;
  
  try {
    const csvPath = path.join(process.cwd(), 'public', 'Artisans.csv');
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
    
    dataLoaded = true;
  } catch (error) {
    console.error('Error loading CSV in Vercel:', error);
    artistsData = [];
  }
}

export default function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    loadArtistsData();
    
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
      llm_message: 'AI-powered search results from our comprehensive artisan database (Vercel deployment).',
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
    console.error('Chat API error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}