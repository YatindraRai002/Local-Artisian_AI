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
  origin: ['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174', 'http://localhost:5175', 'http://localhost:5176'],
  credentials: true
}));
app.use(express.json());

// Load CSV data
let artistsData = [];

function loadCSVData() {
  try {
    const csvPath = path.join(__dirname, 'public', 'Artisans.csv');
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
    age_range: filteredResults.length > 0 ? {
      min: Math.min(...filteredResults.map(a => a.age)),
      max: Math.max(...filteredResults.map(a => a.age))
    } : { min: 0, max: 0 }
  };
}

app.post('/search', (req, res) => {
  try {
    const filters = req.body;
    let filteredArtists = [...artistsData];
    
    console.log(`Search request with filters:`, filters);
    
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
    
    console.log(`Search completed: ${results.length} results from ${filteredArtists.length} matches`);
    
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
    console.error('Search error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error.message,
      available_states: artistsData.length > 0 ? getAvailableStates() : []
    });
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
    
    // Detect if message contains Hindi characters
    const isHindi = /[\u0900-\u097F]/.test(message);
    
    let intent = 'general';
    let responseMessage = '';
    let artists = [];
    let searchFilters = {};
    
    // Enhanced Hindi pattern matching
    const hindiPatterns = {
      greeting: /नमस्ते|नमस्कार|हैलो/,
      search_pottery: /कुम्हारी|मिट्टी.*बर्तन/,
      search_embroidery: /कढ़ाई|चिकनकारी/,
      search_weaving: /बुनाई|कालीन/,
      search_artisan: /कारीगर|शिल्पकार/,
      location_rajasthan: /राजस्थान/,
      location_gujarat: /गुजरात/,
      location_up: /उत्तर.*प्रदेश/,
      stats: /आंकड़े|सांख्यिकी/
    };
    
    const suggestions = isHindi ? [
      'कुम्हारी कारीगर दिखाओ',
      'राजस्थान में शिल्पकार',
      'चिकनकारी के बारे में बताओ',
      'आंकड़े दिखाओ'
    ] : [
      'Show me pottery artists',
      'Find artists in Rajasthan',
      'Get database statistics',
      'Browse textile crafts'
    ];

    // Enhanced bilingual chat response logic
    if (isHindi) {
      // Hindi processing
      if (hindiPatterns.greeting.test(message)) {
        intent = 'greeting';
        responseMessage = 'नमस्ते! मैं आपकी पारंपरिक कारीगरों की खोज में मदद कर सकूं हूँ।';
      } else if (hindiPatterns.stats.test(message)) {
        intent = 'get_stats';
        responseMessage = 'यहाँ हमारे डेटाबेस की जानकारी है:';
      } else {
        // Hindi state and craft mapping
        const hindiStateMap = {
          'आंध्र प्रदेश': 'andhra pradesh',
          'बिहार': 'bihar',
          'गुजरात': 'gujarat',
          'हरियाणा': 'haryana',
          'हिमाचल प्रदेश': 'himachal pradesh',
          'जम्मू कश्मीर': 'jammu & kashmir',
          'कर्नाटक': 'karnataka',
          'केरल': 'kerala',
          'मध्य प्रदेश': 'madhya pradesh',
          'महाराष्ट्र': 'maharashtra',
          'ओडिशा': 'odisha',
          'पंजाब': 'punjab',
          'राजस्थान': 'rajasthan',
          'तमिल नाडु': 'tamil nadu',
          'तेलंगाना': 'telangana',
          'उत्तर प्रदेश': 'uttar pradesh',
          'उत्तराखंड': 'uttarakhand',
          'पश्चिम बंगाल': 'west bengal',
          'दिल्ली': 'delhi'
        };
        
        const hindiCraftMap = {
          'कुम्हारी': 'pottery',
          'मिट्टी': 'pottery',
          'कढ़ाई': 'embroidery',
          'चिकनकारी': 'chikankari',
          'बुनाई': 'weaving',
          'कालीन': 'carpet weaving'
        };
        
        // Search for Hindi terms
        for (const [hindiState, englishState] of Object.entries(hindiStateMap)) {
          if (message.includes(hindiState)) {
            searchFilters.state = englishState;
            break;
          }
        }
        
        for (const [hindiCraft, englishCraft] of Object.entries(hindiCraftMap)) {
          if (message.includes(hindiCraft)) {
            searchFilters.craft_type = englishCraft;
            break;
          }
        }
        
        // Perform search
        if (Object.keys(searchFilters).length > 0) {
          artists = artistsData.filter(artist => {
            let matches = true;
            if (searchFilters.state) {
              matches = matches && artist.location.state.toLowerCase().includes(searchFilters.state.toLowerCase());
            }
            if (searchFilters.craft_type) {
              matches = matches && artist.craft_type.toLowerCase().includes(searchFilters.craft_type.toLowerCase());
            }
            return matches;
          }).slice(0, 10);
          
          responseMessage = `मुझे ${artists.length} कारीगर मिले हैं।`;
          intent = 'search_hindi';
        } else {
          responseMessage = `मैं आपकी कैसे मदद कर सकता हूँ? हमारे डेटाबेस में ${artistsData.length} कारीगर हैं।`;
        }
      }
    } else {
      // English processing with comprehensive state mapping
      if (lowerMessage.includes('stats') || lowerMessage.includes('statistic')) {
        intent = 'get_stats';
        responseMessage = 'Here are the current database statistics:';
      } else {
        // Comprehensive state mapping
        const stateMap = {
          'andhra pradesh': ['andhra pradesh', 'ap', 'andhra'],
          'bihar': ['bihar'],
          'gujarat': ['gujarat'],
          'haryana': ['haryana'],
          'himachal pradesh': ['himachal pradesh', 'himachal', 'hp'],
          'jammu & kashmir': ['jammu kashmir', 'jammu & kashmir', 'kashmir', 'j&k'],
          'karnataka': ['karnataka'],
          'kerala': ['kerala'],
          'madhya pradesh': ['madhya pradesh', 'mp'],
          'maharashtra': ['maharashtra'],
          'odisha': ['odisha', 'orissa'],
          'punjab': ['punjab'],
          'rajasthan': ['rajasthan'],
          'tamil nadu': ['tamil nadu', 'tamilnadu', 'tn'],
          'telangana': ['telangana'],
          'uttar pradesh': ['uttar pradesh', 'up'],
          'uttarakhand': ['uttarakhand'],
          'west bengal': ['west bengal', 'bengal', 'wb'],
          'delhi': ['delhi', 'new delhi']
        };
        
        // Find state matches
        for (const [stateName, variations] of Object.entries(stateMap)) {
          if (variations.some(variation => lowerMessage.includes(variation))) {
            searchFilters.state = stateName;
            break;
          }
        }
        
        // Comprehensive craft mapping
        const craftMap = {
          'pottery': ['pottery', 'pot', 'clay', 'ceramic'],
          'weaving': ['weaving', 'weaver', 'loom', 'textile'],
          'carpet weaving': ['carpet weaving', 'carpet'],
          'embroidery': ['embroidery'],
          'chikankari': ['chikankari', 'chikan'],
          'painting': ['painting', 'painter']
        };
        
        // Find craft matches
        for (const [craftName, variations] of Object.entries(craftMap)) {
          if (variations.some(variation => lowerMessage.includes(variation))) {
            searchFilters.craft_type = craftName;
            break;
          }
        }
        
        // Perform search
        if (Object.keys(searchFilters).length > 0) {
          artists = artistsData.filter(artist => {
            let matches = true;
            
            if (searchFilters.state) {
              const artistState = artist.location.state.toLowerCase().trim();
              const searchState = searchFilters.state.toLowerCase().trim();
              matches = matches && (
                artistState.includes(searchState) || 
                artistState === searchState ||
                searchState.includes(artistState) ||
                artistState.replace(/&/g, 'and').includes(searchState.replace(/&/g, 'and')) ||
                searchState.replace(/&/g, 'and').includes(artistState.replace(/&/g, 'and'))
              );
            }
            
            if (searchFilters.craft_type) {
              const artistCraft = artist.craft_type.toLowerCase().trim();
              const searchCraft = searchFilters.craft_type.toLowerCase().trim();
              matches = matches && (
                artistCraft.includes(searchCraft) || 
                artistCraft === searchCraft ||
                searchCraft.includes(artistCraft)
              );
            }
            
            return matches;
          }).slice(0, 10);
          
          if (searchFilters.state && searchFilters.craft_type) {
            responseMessage = `Found ${artists.length} ${searchFilters.craft_type} artists in ${searchFilters.state.charAt(0).toUpperCase() + searchFilters.state.slice(1)}.`;
          } else if (searchFilters.state) {
            responseMessage = `Found ${artists.length} artists in ${searchFilters.state.charAt(0).toUpperCase() + searchFilters.state.slice(1)}.`;
          } else if (searchFilters.craft_type) {
            responseMessage = `Found ${artists.length} ${searchFilters.craft_type} artists.`;
          }
          intent = 'search_english';
        } else {
          // Enhanced fallback with partial matching
          const partialMatches = artistsData.filter(artist => {
            const artistText = `${artist.location.state} ${artist.location.district} ${artist.craft_type} ${artist.name}`.toLowerCase();
            const words = lowerMessage.split(' ').filter(word => word.length > 2);
            return words.some(word => artistText.includes(word));
          }).slice(0, 10);
          
          if (partialMatches.length > 0) {
            artists = partialMatches;
            responseMessage = `Found ${artists.length} artists matching your query.`;
            intent = 'partial_search';
          } else {
            responseMessage = `Hello! I have ${artistsData.length} artisans in our database. You can search by craft type, location, or ask for statistics in Hindi or English.`;
          }
        }
      }
    }
    
    // Enhanced statistics
    const hindiSpeakers = artistsData.filter(a => 
      a.languages.some(lang => lang.toLowerCase().includes('hindi'))
    ).length;
    
    // Extract cluster information
    const clusterInfo = artists.length > 0 ? {
      cluster_codes: [...new Set(artists.map(a => a.cluster_code))],
      cluster_count: new Set(artists.map(a => a.cluster_code)).size,
      districts_covered: [...new Set(artists.map(a => a.location.district))],
      crafts_found: [...new Set(artists.map(a => a.craft_type))]
    } : {};

    const response = {
      intent,
      entities: {
        state: searchFilters.state || null,
        craft: searchFilters.craft_type || null
      },
      message: responseMessage,
      llm_message: isHindi ? 
        'उन्नत खोज - बहुभाषी सहायता' :
        'Enhanced Search - Multilingual Support',
      artists,
      clustering_info: clusterInfo,
      suggestions,
      stats: intent === 'get_stats' ? {
        total_artists: artistsData.length,
        unique_crafts: new Set(artistsData.map(a => a.craft_type)).size,
        unique_states: new Set(artistsData.map(a => a.location.state)).size,
        unique_districts: new Set(artistsData.map(a => a.location.district)).size,
        unique_clusters: new Set(artistsData.map(a => a.cluster_code)).size,
        hindi_speakers: hindiSpeakers,
        hindi_percentage: Math.round((hindiSpeakers / artistsData.length) * 100),
        message_hindi: `हमारे क्लस्टरिंग मॉडल डेटाबेस में ${artistsData.length} कारीगर हैं।`,
        language_support: isHindi ? 'हिंदी और अंग्रेजी दोनों' : 'Hindi and English both supported'
      } : {},
      search_query: {
        original_message: message,
        detected_language: isHindi ? 'hindi' : 'english',
        search_filters: searchFilters,
        results_count: artists.length
      },
      language: isHindi ? 'hindi' : 'english',
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