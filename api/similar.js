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
    console.log(`Loaded ${artistsData.length} artists for similar API`);
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

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    loadArtistsData();
    
    const { artistId } = req.query;
    const limit = parseInt(req.query.limit) || 5;
    
    if (!artistId) {
      return res.status(400).json({ error: 'Artist ID is required' });
    }
    
    const targetArtist = artistsData.find(a => a.id === artistId);
    if (!targetArtist) {
      return res.status(404).json({ error: 'Artist not found' });
    }
    
    // Find similar artists based on craft type, location, or cluster
    let similarArtists = artistsData.filter(a => {
      if (a.id === artistId) return false;
      
      // Priority 1: Same craft type
      if (a.craft_type === targetArtist.craft_type) return true;
      
      // Priority 2: Same state
      if (a.location.state === targetArtist.location.state) return true;
      
      // Priority 3: Same cluster code
      if (a.cluster_code && targetArtist.cluster_code && 
          a.cluster_code === targetArtist.cluster_code) return true;
      
      return false;
    });
    
    // Sort by similarity (craft type first, then location)
    similarArtists.sort((a, b) => {
      if (a.craft_type === targetArtist.craft_type && b.craft_type !== targetArtist.craft_type) return -1;
      if (b.craft_type === targetArtist.craft_type && a.craft_type !== targetArtist.craft_type) return 1;
      
      if (a.location.state === targetArtist.location.state && b.location.state !== targetArtist.location.state) return -1;
      if (b.location.state === targetArtist.location.state && a.location.state !== targetArtist.location.state) return 1;
      
      return 0;
    });
    
    res.json({
      similar_artists: similarArtists.slice(0, limit),
      total_found: similarArtists.length,
      target_artist: targetArtist,
      status: 'online'
    });
  } catch (error) {
    console.error('Similar artists API error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}