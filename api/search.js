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
    console.log(`Loaded ${artistsData.length} artists for Vercel deployment`);
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
    console.error('Search API error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}