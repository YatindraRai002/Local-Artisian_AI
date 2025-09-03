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

// Comprehensive state mapping for enhanced search functionality
const stateMapping = {
  'andhra pradesh': ['andhra pradesh', 'ap', 'andhra'],
  'arunachal pradesh': ['arunachal pradesh', 'arunachal'],
  'assam': ['assam'],
  'bihar': ['bihar'],
  'chhattisgarh': ['chhattisgarh', 'chattisgarh', 'cg'],
  'goa': ['goa'],
  'gujarat': ['gujarat', 'gj'],
  'haryana': ['haryana', 'hr'],
  'himachal pradesh': ['himachal pradesh', 'himachal', 'hp', 'h.p.'],
  'jammu & kashmir': ['jammu & kashmir', 'jammu and kashmir', 'jammu kashmir', 'j&k', 'jk', 'kashmir', 'jammu'],
  'jharkhand': ['jharkhand', 'jh'],
  'karnataka': ['karnataka', 'kn', 'mysore'],
  'kerala': ['kerala', 'kl', 'kerela'],
  'madhya pradesh': ['madhya pradesh', 'mp', 'm.p.', 'central pradesh'],
  'maharashtra': ['maharashtra', 'mh'],
  'manipur': ['manipur', 'mn'],
  'meghalaya': ['meghalaya', 'ml'],
  'mizoram': ['mizoram', 'mz'],
  'nagaland': ['nagaland', 'nl'],
  'odisha': ['odisha', 'orissa', 'or'],
  'punjab': ['punjab', 'pb'],
  'rajasthan': ['rajasthan', 'rj'],
  'sikkim': ['sikkim', 'sk'],
  'tamil nadu': ['tamil nadu', 'tamilnadu', 'tamil naidu', 'tn'],
  'telangana': ['telangana', 'ts'],
  'tripura': ['tripura', 'tr'],
  'uttar pradesh': ['uttar pradesh', 'up', 'u.p.'],
  'uttarakhand': ['uttarakhand', 'uttaranchal', 'uk', 'ua'],
  'west bengal': ['west bengal', 'bengal', 'wb'],
  'ladakh': ['ladakh'],
  'delhi': ['delhi', 'new delhi', 'dl'],
  'chandigarh': ['chandigarh', 'ch'],
  'puducherry': ['puducherry', 'pondicherry', 'py'],
  'andaman and nicobar islands': ['andaman', 'nicobar', 'andaman and nicobar', 'an'],
  'dadra and nagar haveli': ['dadra', 'nagar haveli', 'dadra and nagar haveli', 'dn'],
  'daman and diu': ['daman', 'diu', 'daman and diu', 'dd'],
  'lakshadweep': ['lakshadweep', 'ld']
};

// Enhanced state matching function
function matchState(searchState, artistState) {
  if (!searchState || !artistState) return false;
  
  const searchLower = searchState.toLowerCase().trim();
  const artistLower = artistState.toLowerCase().trim();
  
  // Direct match
  if (artistLower.includes(searchLower) || searchLower.includes(artistLower)) {
    return true;
  }
  
  // Check against state variations
  for (const [canonicalState, variations] of Object.entries(stateMapping)) {
    const searchMatches = variations.some(variation => 
      searchLower === variation || searchLower.includes(variation) || variation.includes(searchLower)
    );
    
    const artistMatches = variations.some(variation => 
      artistLower === variation || artistLower.includes(variation) || variation.includes(artistLower)
    ) || artistLower.includes(canonicalState) || canonicalState.includes(artistLower);
    
    if (searchMatches && artistMatches) {
      return true;
    }
  }
  
  // Handle ampersand variations
  const searchNormalized = searchLower.replace(/&/g, 'and').replace(/\s+/g, ' ');
  const artistNormalized = artistLower.replace(/&/g, 'and').replace(/\s+/g, ' ');
  
  return searchNormalized.includes(artistNormalized) || artistNormalized.includes(searchNormalized);
}

// Get all available states from the dataset
function getAvailableStates() {
  if (!artistsData.length) return [];
  
  const uniqueStates = [...new Set(artistsData.map(a => a.location.state))];
  return uniqueStates.filter(state => state && state.trim()).sort();
}

// Get comprehensive search statistics
function getSearchStatistics(filteredResults) {
  if (!filteredResults.length) return {};
  
  return {
    total_artists: filteredResults.length,
    unique_states: new Set(filteredResults.map(a => a.location.state)).size,
    unique_districts: new Set(filteredResults.map(a => a.location.district)).size,
    unique_crafts: new Set(filteredResults.map(a => a.craft_type)).size,
    unique_clusters: new Set(filteredResults.map(a => a.cluster_code)).size,
    states_found: [...new Set(filteredResults.map(a => a.location.state))].sort(),
    crafts_found: [...new Set(filteredResults.map(a => a.craft_type))].sort(),
    age_range: {
      min: Math.min(...filteredResults.map(a => a.age)),
      max: Math.max(...filteredResults.map(a => a.age))
    }
  };
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
    
    // Enhanced state filtering with comprehensive matching
    if (filters.state) {
      filteredArtists = filteredArtists.filter(artist => 
        matchState(filters.state, artist.location.state)
      );
    }
    
    // Enhanced district filtering
    if (filters.district) {
      filteredArtists = filteredArtists.filter(a => {
        const searchDistrict = filters.district.toLowerCase().trim();
        const artistDistrict = a.location.district.toLowerCase().trim();
        return artistDistrict.includes(searchDistrict) || searchDistrict.includes(artistDistrict);
      });
    }
    
    // Enhanced craft type filtering
    if (filters.craft_type) {
      filteredArtists = filteredArtists.filter(a => {
        const searchCraft = filters.craft_type.toLowerCase().trim();
        const artistCraft = a.craft_type.toLowerCase().trim();
        return artistCraft.includes(searchCraft) || searchCraft.includes(artistCraft);
      });
    }
    
    // Enhanced name filtering
    if (filters.name) {
      filteredArtists = filteredArtists.filter(a => {
        const searchName = filters.name.toLowerCase().trim();
        const artistName = a.name.toLowerCase().trim();
        return artistName.includes(searchName) || searchName.includes(artistName);
      });
    }
    
    // Language filtering
    if (filters.language) {
      filteredArtists = filteredArtists.filter(a => 
        a.languages.some(lang => 
          lang.toLowerCase().includes(filters.language.toLowerCase())
        )
      );
    }
    
    // Cluster code filtering
    if (filters.cluster_code) {
      filteredArtists = filteredArtists.filter(a => 
        a.cluster_code && a.cluster_code.toLowerCase().includes(filters.cluster_code.toLowerCase())
      );
    }
    
    // Age range filtering
    if (filters.age_min !== undefined) {
      filteredArtists = filteredArtists.filter(a => a.age >= filters.age_min);
    }
    
    if (filters.age_max !== undefined) {
      filteredArtists = filteredArtists.filter(a => a.age <= filters.age_max);
    }
    
    // Gender filtering
    if (filters.gender) {
      filteredArtists = filteredArtists.filter(a => 
        a.gender.toLowerCase() === filters.gender.toLowerCase()
      );
    }
    
    // Phone availability filtering
    if (filters.phone_available !== undefined) {
      filteredArtists = filteredArtists.filter(a => 
        a.contact.phone_available === filters.phone_available
      );
    }
    
    // Sort results if specified
    if (filters.sort_by) {
      const sortField = filters.sort_by;
      const sortOrder = filters.sort_order || 'asc';
      
      filteredArtists.sort((a, b) => {
        let aVal, bVal;
        
        switch (sortField) {
          case 'name':
            aVal = a.name.toLowerCase();
            bVal = b.name.toLowerCase();
            break;
          case 'age':
            aVal = a.age;
            bVal = b.age;
            break;
          case 'state':
            aVal = a.location.state.toLowerCase();
            bVal = b.location.state.toLowerCase();
            break;
          case 'craft':
            aVal = a.craft_type.toLowerCase();
            bVal = b.craft_type.toLowerCase();
            break;
          default:
            return 0;
        }
        
        if (sortOrder === 'desc') {
          return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
        } else {
          return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
        }
      });
    }
    
    // Apply pagination
    const limit = filters.limit || 20;
    const offset = filters.offset || 0;
    const results = filteredArtists.slice(offset, offset + limit);
    
    // Generate comprehensive response
    const response = {
      artists: results,
      total: filteredArtists.length,
      limit: limit,
      offset: offset,
      has_more: offset + limit < filteredArtists.length,
      status: 'online',
      search_metadata: {
        filters_applied: Object.keys(filters).filter(key => !['limit', 'offset', 'sort_by', 'sort_order'].includes(key)),
        available_states: getAvailableStates(),
        search_statistics: getSearchStatistics(filteredArtists)
      }
    };
    
    // Add state suggestions if state search was attempted but no results found
    if (filters.state && filteredArtists.length === 0) {
      const availableStates = getAvailableStates();
      const suggestions = availableStates.filter(state => 
        state.toLowerCase().includes(filters.state.toLowerCase()) ||
        Object.values(stateMapping).some(variations => 
          variations.some(variation => variation.includes(filters.state.toLowerCase()))
        )
      );
      
      response.suggestions = {
        message: `No artists found for "${filters.state}". Did you mean:`,
        states: suggestions.slice(0, 5)
      };
    }
    
    res.json(response);
  } catch (error) {
    console.error('Search API error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error.message,
      available_states: artistsData.length > 0 ? getAvailableStates() : []
    });
  }
}