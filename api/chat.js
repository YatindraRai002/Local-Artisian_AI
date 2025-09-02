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
    const headers = parseCSVLine(lines[0]);
    
    artistsData = [];
    
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      const values = parseCSVLine(line);
      if (values.length < headers.length) continue;
      
      try {
        const artist = {
          id: values[0] || '',
          name: values[1] || '',
          gender: values[2] || '',
          age: parseInt(values[3]) || 0,
          craft_type: values[4] || '',
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
    console.log(`Successfully loaded ${artistsData.length} artists from clustering model`);
  } catch (error) {
    console.error('Error loading CSV:', error);
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
    
    // Detect if message contains Hindi characters
    const isHindi = /[\u0900-\u097F]/.test(message);
    
    let intent = 'general';
    let responseMessage = '';
    let artists = [];
    
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
    
    // Enhanced bilingual chat response logic with comprehensive search
    if (isHindi) {
      // Hindi pattern matching with comprehensive search
      if (hindiPatterns.greeting.test(message)) {
        intent = 'greeting';
        responseMessage = 'नमस्ते! मैं आपकी पारंपरिक कारीगरों की खोज में मदद कर सकूं हूँ।';
      } else if (hindiPatterns.stats.test(message)) {
        intent = 'get_stats';
        responseMessage = 'यहाँ हमारे डेटाबेस की जानकारी है:';
      } else {
        // Use comprehensive search for Hindi queries too
        const searchFilters = {};
        const lowerHindiMessage = message.toLowerCase();
        
        // Hindi state mapping
        const hindiStateMap = {
          'राजस्थान': 'rajasthan',
          'गुजरात': 'gujarat',
          'उत्तर प्रदेश': 'uttar pradesh',
          'मध्य प्रदेश': 'madhya pradesh',
          'महाराष्ट्र': 'maharashtra',
          'पश्चिम बंगाल': 'west bengal',
          'तमिल नाडु': 'tamil nadu',
          'कर्नाटक': 'karnataka',
          'केरल': 'kerala',
          'बिहार': 'bihar',
          'पंजाब': 'punjab',
          'हरियाणा': 'haryana',
          'हिमाचल प्रदेश': 'himachal pradesh',
          'जम्मू कश्मीर': 'jammu kashmir',
          'असम': 'assam',
          'ओडिशा': 'odisha',
          'उड़ीसा': 'odisha',
          'झारखंड': 'jharkhand',
          'छत्तीसगढ़': 'chhattisgarh',
          'तेलंगाना': 'telangana',
          'आंध्र प्रदेश': 'andhra pradesh'
        };
        
        // Check for Hindi state names
        for (const [hindiState, englishState] of Object.entries(hindiStateMap)) {
          if (message.includes(hindiState)) {
            searchFilters.state = englishState;
            break;
          }
        }
        
        // Hindi craft mapping
        const hindiCraftMap = {
          'कुम्हारी': 'pottery',
          'मिट्टी': 'pottery',
          'बर्तन': 'pottery',
          'कढ़ाई': 'embroidery',
          'चिकनकारी': 'chikankari',
          'बुनाई': 'weaving',
          'कालीन': 'carpet weaving',
          'रंगाई': 'tie dye',
          'चित्रकारी': 'painting',
          'मधुबनी': 'madhubani painting',
          'वार्ली': 'warli painting',
          'लकड़ी': 'wood carving',
          'पत्थर': 'stone carving',
          'धातु': 'metalwork',
          'आभूषण': 'jewelry',
          'गहने': 'jewelry',
          'बांस': 'bamboo',
          'चमड़ा': 'leather craft',
          'हस्तकरघा': 'handloom weaving',
          'रेशम': 'silk'
        };
        
        // Check for Hindi craft names
        for (const [hindiCraft, englishCraft] of Object.entries(hindiCraftMap)) {
          if (message.includes(hindiCraft)) {
            searchFilters.craft_type = englishCraft;
            break;
          }
        }
        
        // Perform search using filters for Hindi
        if (Object.keys(searchFilters).length > 0) {
          artists = artistsData.filter(artist => {
            let matches = true;
            
            if (searchFilters.state) {
              const artistState = artist.location.state.toLowerCase().trim();
              const searchState = searchFilters.state.toLowerCase().trim();
              matches = matches && (
                artistState.includes(searchState) || 
                artistState === searchState ||
                searchState.includes(artistState)
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
          
          // Generate Hindi response messages
          if (searchFilters.state && searchFilters.craft_type) {
            intent = 'search_combined';
            const stateHindi = Object.keys(hindiStateMap).find(key => hindiStateMap[key] === searchFilters.state) || searchFilters.state;
            const craftHindi = Object.keys(hindiCraftMap).find(key => hindiCraftMap[key] === searchFilters.craft_type) || searchFilters.craft_type;
            responseMessage = `मुझे ${stateHindi} में ${artists.length} ${craftHindi} कारीगर मिले हैं।`;
          } else if (searchFilters.state) {
            intent = 'search_location';
            const stateHindi = Object.keys(hindiStateMap).find(key => hindiStateMap[key] === searchFilters.state) || searchFilters.state;
            responseMessage = `${stateHindi} में मुझे ${artists.length} कारीगर मिले हैं।`;
          } else if (searchFilters.craft_type) {
            intent = 'search_craft';
            const craftHindi = Object.keys(hindiCraftMap).find(key => hindiCraftMap[key] === searchFilters.craft_type) || searchFilters.craft_type;
            responseMessage = `मुझे ${artists.length} ${craftHindi} कारीगर मिले हैं।`;
          }
        } else if (hindiPatterns.search_artisan.test(message)) {
          intent = 'search_artisan';
          artists = artistsData.slice(0, 10);
          responseMessage = `हमारे डेटाबेस में ${artistsData.length} कारीगर हैं। यहाँ कुछ हैं:`;
        } else {
          responseMessage = 'मैं आपकी कैसे मदद कर सकता हूँ? आप कारीगरों के बारे में हिंदी या अंग्रेजी में पूछ सकते हैं।';
        }
      }
    } else {
      // English pattern matching using comprehensive search
      if (lowerMessage.includes('stats') || lowerMessage.includes('statistic')) {
        intent = 'get_stats';
        responseMessage = 'Here are the current database statistics:';
      } else {
        // Use comprehensive search algorithm instead of hardcoded patterns
        const searchFilters = {};
        
        // Extract state from message using comprehensive list with variations
        const stateMap = {
          'andhra pradesh': ['andhra pradesh', 'ap', 'andhra'],
          'assam': ['assam'],
          'bihar': ['bihar'],
          'chhattisgarh': ['chhattisgarh', 'chattisgarh'],
          'goa': ['goa'],
          'gujarat': ['gujarat'],
          'haryana': ['haryana'],
          'himachal pradesh': ['himachal pradesh', 'himachal', 'hp', 'h.p.'],
          'jammu kashmir': ['jammu kashmir', 'jammu & kashmir', 'kashmir', 'j&k', 'jk'],
          'jharkhand': ['jharkhand'],
          'karnataka': ['karnataka', 'mysore'],
          'kerala': ['kerala', 'kerela'],
          'madhya pradesh': ['madhya pradesh', 'mp', 'm.p.', 'central pradesh'],
          'maharashtra': ['maharashtra'],
          'manipur': ['manipur'],
          'meghalaya': ['meghalaya'],
          'mizoram': ['mizoram'],
          'nagaland': ['nagaland'],
          'odisha': ['odisha', 'orissa'],
          'punjab': ['punjab'],
          'rajasthan': ['rajasthan'],
          'sikkim': ['sikkim'],
          'tamil nadu': ['tamil nadu', 'tamilnadu', 'tamil naidu', 'tn'],
          'telangana': ['telangana'],
          'tripura': ['tripura'],
          'uttar pradesh': ['uttar pradesh', 'up', 'u.p.'],
          'uttarakhand': ['uttarakhand', 'uttaranchal'],
          'west bengal': ['west bengal', 'bengal', 'wb'],
          'ladakh': ['ladakh'],
          'delhi': ['delhi', 'new delhi'],
          'chandigarh': ['chandigarh'],
          'puducherry': ['puducherry', 'pondicherry']
        };
        
        let foundState = null;
        for (const [stateName, variations] of Object.entries(stateMap)) {
          if (variations.some(variation => lowerMessage.includes(variation))) {
            foundState = stateName;
            searchFilters.state = stateName;
            break;
          }
        }
        
        // Extract craft type from message using comprehensive list
        const craftMap = {
          'pottery': ['pottery', 'pot', 'clay', 'ceramic'],
          'blue pottery': ['blue pottery'],
          'black pottery': ['black pottery'],
          'terracotta': ['terracotta'],
          'weaving': ['weaving', 'weaver', 'loom', 'textile'],
          'handloom weaving': ['handloom weaving', 'handloom'],
          'carpet weaving': ['carpet weaving', 'carpet'],
          'durrie weaving': ['durrie weaving', 'durrie'],
          'banarasi weaving': ['banarasi weaving', 'banarasi'],
          'embroidery': ['embroidery'],
          'chikankari': ['chikankari', 'chikan'],
          'phulkari': ['phulkari'],
          'kutch embroidery': ['kutch embroidery', 'kutch'],
          'zardozi': ['zardozi'],
          'zari': ['zari'],
          'painting': ['painting', 'painter', 'paint'],
          'madhubani painting': ['madhubani painting', 'madhubani'],
          'warli painting': ['warli painting', 'warli'],
          'pattachitra': ['pattachitra'],
          'tanjore painting': ['tanjore painting', 'tanjore'],
          'kalamkari': ['kalamkari'],
          'carving': ['carving', 'carver'],
          'wood carving': ['wood carving', 'wooden'],
          'stone carving': ['stone carving', 'stone'],
          'sandalwood carving': ['sandalwood carving', 'sandalwood'],
          'metalwork': ['metalwork', 'metal'],
          'bidriware': ['bidriware'],
          'dokra': ['dokra'],
          'bell metal': ['bell metal'],
          'silver filigree': ['silver filigree', 'filigree'],
          'jewelry': ['jewelry', 'jewellery'],
          'kundan jewellery': ['kundan jewellery', 'kundan'],
          'block printing': ['block printing'],
          'tie dye': ['tie dye', 'bandhani'],
          'bamboo': ['bamboo'],
          'cane': ['cane'],
          'jute craft': ['jute craft', 'jute'],
          'leather craft': ['leather craft', 'leather'],
          'paper mache': ['paper mache'],
          'channapatna toys': ['channapatna toys', 'toys'],
          'shell craft': ['shell craft', 'shell'],
          'sikki grass': ['sikki grass', 'sikki']
        };
        
        let foundCraft = null;
        for (const [craftName, variations] of Object.entries(craftMap)) {
          if (variations.some(variation => lowerMessage.includes(variation))) {
            foundCraft = craftName;
            searchFilters.craft_type = craftName;
            break;
          }
        }
        
        // Perform comprehensive search using filters
        if (Object.keys(searchFilters).length > 0) {
          artists = artistsData.filter(artist => {
            let matches = true;
            
            if (searchFilters.state) {
              const artistState = artist.location.state.toLowerCase().trim();
              const searchState = searchFilters.state.toLowerCase().trim();
              // Flexible matching for state names
              matches = matches && (
                artistState.includes(searchState) || 
                artistState === searchState ||
                searchState.includes(artistState) ||
                // Handle common variations
                (searchState === 'uttar pradesh' && artistState.includes('uttar pradesh')) ||
                (searchState === 'madhya pradesh' && artistState.includes('madhya pradesh')) ||
                (searchState === 'himachal pradesh' && artistState.includes('himachal')) ||
                (searchState === 'jammu kashmir' && (artistState.includes('jammu') || artistState.includes('kashmir'))) ||
                (searchState === 'tamil nadu' && artistState.includes('tamil')) ||
                (searchState === 'west bengal' && artistState.includes('bengal')) ||
                (searchState === 'odisha' && artistState.includes('orissa'))
              );
            }
            
            if (searchFilters.craft_type) {
              const artistCraft = artist.craft_type.toLowerCase().trim();
              const searchCraft = searchFilters.craft_type.toLowerCase().trim();
              // Flexible matching for craft types
              matches = matches && (
                artistCraft.includes(searchCraft) || 
                artistCraft === searchCraft ||
                searchCraft.includes(artistCraft) ||
                // Handle common craft variations
                (searchCraft.includes('weaving') && artistCraft.includes('weaving')) ||
                (searchCraft.includes('pottery') && artistCraft.includes('pottery')) ||
                (searchCraft.includes('embroidery') && artistCraft.includes('embroidery')) ||
                (searchCraft.includes('painting') && artistCraft.includes('painting')) ||
                (searchCraft.includes('carving') && artistCraft.includes('carving'))
              );
            }
            
            return matches;
          }).slice(0, 10);
          
          // Generate appropriate response message
          if (foundState && foundCraft) {
            intent = 'search_combined';
            responseMessage = `Found ${artists.length} ${foundCraft} artists in ${foundState.charAt(0).toUpperCase() + foundState.slice(1)} from our real database.`;
          } else if (foundState) {
            intent = 'search_location';
            responseMessage = `Found ${artists.length} artists in ${foundState.charAt(0).toUpperCase() + foundState.slice(1)} from our real database.`;
          } else if (foundCraft) {
            intent = 'search_craft';
            responseMessage = `Found ${artists.length} ${foundCraft} artists from our real database.`;
          }
        } else {
          // Default response if no specific search terms found
          responseMessage = 'Hello! I can help you find traditional Indian artists. You can search by craft type, location, or ask for database statistics in Hindi or English.';
        }
      }
    }
    
    // Enhanced statistics including Hindi language data
    const hindiSpeakers = artistsData.filter(a => 
      a.languages.some(lang => lang.toLowerCase().includes('hindi'))
    ).length;
    
    const response = {
      intent,
      entities: {},
      message: responseMessage,
      llm_message: isHindi ? 
        'उन्नत हिंदी NLP प्रसंस्करण के साथ बहुभाषी सहायता - वास्तविक डेटा कनेक्शन' :
        'Enhanced Hindi NLP processing with multilingual support - Real Data Connection',
      artists,
      suggestions,
      stats: intent === 'get_stats' ? {
        total_artists: artistsData.length,
        unique_crafts: new Set(artistsData.map(a => a.craft_type)).size,
        unique_states: new Set(artistsData.map(a => a.location.state)).size,
        unique_districts: new Set(artistsData.map(a => a.location.district)).size,
        hindi_speakers: hindiSpeakers,
        hindi_percentage: Math.round((hindiSpeakers / artistsData.length) * 100),
        message_hindi: `हमारे वास्तविक डेटाबेस में ${artistsData.length} कारीगर हैं, जिनमें से ${hindiSpeakers} हिंदी बोलते हैं।`,
        language_support: isHindi ? 'हिंदी और अंग्रेजी दोनों - वास्तविक डेटा' : 'Hindi and English both supported - Real Data'
      } : {},
      language: isHindi ? 'hindi' : 'english',
      status: 'online'
    };
    
    res.json(response);
  } catch (error) {
    console.error('Chat API error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}