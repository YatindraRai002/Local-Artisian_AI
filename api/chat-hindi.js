import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

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
    console.log(`Successfully loaded ${artistsData.length} artists from clustering model for Hindi chat`);
  } catch (error) {
    console.error('Error loading CSV:', error);
    artistsData = [];
  }
}

// Enhanced Hindi NLP processing function
function processHindiQuery(message) {
  const hindiPatterns = {
    // Greetings
    greeting: /नमस्ते|नमस्कार|हैलो/,
    
    // Search patterns
    search_pottery: /कुम्हारी|मिट्टी.*बर्तन|pottery/i,
    search_embroidery: /कढ़ाई|embroidery|चिकनकारी/i,
    search_weaving: /बुनाई|कालीन|carpet|weaving/i,
    search_artisan: /कारीगर|शिल्पकार|artisan|craftsman/i,
    
    // Craft patterns - expanded
    search_metalwork: /धातु.*काम|metalwork|metal/i,
    search_woodcarving: /लकड़ी.*काम|wood.*carving|carving/i,
    search_leather: /चमड़ा.*काम|leather.*craft|leather/i,
    search_bamboo: /बांस.*काम|bamboo|cane/i,
    
    // Action words
    show: /दिखाओ|show|find|खोज/i,
    tell: /बताओ|tell|जानकारी/i,
    want: /चाहिए|want|need/i
  };
  
  let intent = 'general_query';
  let entities = {};
  
  // Detect intent
  if (hindiPatterns.greeting.test(message)) {
    intent = 'greeting';
  } else if (hindiPatterns.search_pottery.test(message)) {
    intent = 'search_craft';
    entities.craft_type = 'pottery';
  } else if (hindiPatterns.search_embroidery.test(message)) {
    intent = 'search_craft';
    entities.craft_type = 'embroidery';
  } else if (hindiPatterns.search_weaving.test(message)) {
    intent = 'search_craft';
    entities.craft_type = 'weaving';
  } else if (hindiPatterns.search_metalwork.test(message)) {
    intent = 'search_craft';
    entities.craft_type = 'metalwork';
  } else if (hindiPatterns.search_woodcarving.test(message)) {
    intent = 'search_craft';
    entities.craft_type = 'wood carving';
  } else if (hindiPatterns.search_leather.test(message)) {
    intent = 'search_craft';
    entities.craft_type = 'leather';
  } else if (hindiPatterns.search_bamboo.test(message)) {
    intent = 'search_craft';
    entities.craft_type = 'bamboo';
  } else if (hindiPatterns.search_artisan.test(message)) {
    intent = 'search_artisan';
  }
  
  // Dynamic location detection for all Indian states
  const stateNames = [
    { hindi: ['राजस्थान', 'rajasthan'], english: 'rajasthan' },
    { hindi: ['गुजरात', 'gujarat'], english: 'gujarat' },
    { hindi: ['उत्तर प्रदेश', 'uttar pradesh', 'up'], english: 'uttar pradesh' },
    { hindi: ['बिहार', 'bihar'], english: 'bihar' },
    { hindi: ['केरल', 'kerala', 'kerela'], english: 'kerala' },
    { hindi: ['तमिल नाडु', 'tamil nadu'], english: 'tamil nadu' },
    { hindi: ['महाराष्ट्र', 'maharashtra'], english: 'maharashtra' },
    { hindi: ['पश्चिम बंगाल', 'west bengal', 'bengal'], english: 'west bengal' },
    { hindi: ['कर्नाटक', 'karnataka'], english: 'karnataka' },
    { hindi: ['मध्य प्रदेश', 'madhya pradesh', 'mp'], english: 'madhya pradesh' },
    { hindi: ['हरियाणा', 'haryana'], english: 'haryana' },
    { hindi: ['पंजाब', 'punjab'], english: 'punjab' },
    { hindi: ['हिमाचल प्रदेश', 'himachal pradesh'], english: 'himachal pradesh' },
    { hindi: ['जम्मू कश्मीर', 'jammu kashmir', 'jammu & kashmir'], english: 'jammu & kashmir' },
    { hindi: ['उड़ीसा', 'ओडिशा', 'odisha', 'orissa'], english: 'odisha' },
    { hindi: ['तेलंगाना', 'telangana'], english: 'telangana' },
    { hindi: ['आंध्र प्रदेश', 'andhra pradesh'], english: 'andhra pradesh' }
  ];
  
  const messageLower = message.toLowerCase();
  const foundStateEntry = stateNames.find(state => 
    state.hindi.some(name => messageLower.includes(name))
  );
  
  if (foundStateEntry) {
    entities.location = foundStateEntry.english;
  }
  
  return { intent, entities };
}

// Search artisans based on processed query
function searchArtisans(entities) {
  let filtered = artistsData;
  
  if (entities.craft_type) {
    const craftFilter = entities.craft_type.toLowerCase();
    filtered = filtered.filter(a => {
      const craftLower = a.craft_type.toLowerCase();
      return craftLower.includes(craftFilter) ||
             (craftFilter === 'pottery' && craftLower.includes('pottery')) ||
             (craftFilter === 'embroidery' && (craftLower.includes('embroidery') || craftLower.includes('chikankari'))) ||
             (craftFilter === 'weaving' && (craftLower.includes('weaving') || craftLower.includes('carpet') || craftLower.includes('handloom'))) ||
             (craftFilter === 'metalwork' && (craftLower.includes('metal') || craftLower.includes('bidriware') || craftLower.includes('dokra'))) ||
             (craftFilter === 'wood carving' && (craftLower.includes('wood') || craftLower.includes('carving'))) ||
             (craftFilter === 'leather' && craftLower.includes('leather')) ||
             (craftFilter === 'bamboo' && (craftLower.includes('bamboo') || craftLower.includes('cane')));
    });
  }
  
  if (entities.location) {
    const locationFilter = entities.location.toLowerCase();
    filtered = filtered.filter(a => {
      const stateLower = a.location.state.toLowerCase();
      // Handle state name variations
      if (locationFilter.includes('uttar pradesh') && stateLower.includes('uttar pradesh')) return true;
      if (locationFilter.includes('madhya pradesh') && stateLower.includes('madhya pradesh')) return true;
      if (locationFilter.includes('himachal pradesh') && stateLower.includes('himachal pradesh')) return true;
      if (locationFilter.includes('andhra pradesh') && stateLower.includes('andhra pradesh')) return true;
      if (locationFilter.includes('jammu') && stateLower.includes('jammu')) return true;
      if (locationFilter.includes('west bengal') && stateLower.includes('west bengal')) return true;
      if (locationFilter.includes('tamil nadu') && stateLower.includes('tamil nadu')) return true;
      if (locationFilter.includes('kerala') && stateLower.includes('kerala')) return true;
      return stateLower.includes(locationFilter) || stateLower === locationFilter;
    });
  }
  
  return filtered.slice(0, 10); // Limit results
}

// Generate response based on language and intent
function generateResponse(message, intent, entities, artists) {
  const isHindi = /[\u0900-\u097F]/.test(message);
  
  const responses = {
    hindi: {
      greeting: [
        'नमस्ते! मैं आपकी पारंपरिक कारीगरों की खोज में मदद कर सकूं हूँ।',
        'नमस्कार! आप किस प्रकार के शिल्पकार की तलाश में हैं?',
        'आपका स्वागत है! मैं भारतीय हस्तशिल्प कारीगरों के बारे में जानकारी दे सकता हूँ।'
      ],
      found_artisans: `मुझे ${artists.length} कारीगर मिले हैं।`,
      no_artisans: 'क्षमा करें, इस खोज के लिए कोई कारीगर नहीं मिला।',
      general: 'मैं आपकी कैसे मदद कर सकता हूँ? आप कारीगरों के बारे में पूछ सकते हैं।'
    },
    english: {
      greeting: [
        'Hello! I can help you find traditional Indian artisans.',
        'Welcome! What type of craftsperson are you looking for?',
        'Hi there! I can provide information about Indian handicraft artisans.'
      ],
      found_artisans: `I found ${artists.length} artisans matching your criteria.`,
      no_artisans: 'Sorry, no artisans found for this search.',
      general: 'How can I help you? You can ask about artisans and crafts.'
    }
  };
  
  const lang = isHindi ? 'hindi' : 'english';
  let responseText = '';
  
  switch (intent) {
    case 'greeting':
      responseText = responses[lang].greeting[Math.floor(Math.random() * responses[lang].greeting.length)];
      break;
    case 'search_craft':
    case 'search_artisan':
      responseText = artists.length > 0 ? responses[lang].found_artisans : responses[lang].no_artisans;
      break;
    default:
      responseText = responses[lang].general;
  }
  
  return {
    message: responseText,
    language: lang,
    intent: intent,
    entities: entities,
    artisans: artists,
    suggestions: isHindi ? [
      'कुम्हारी कारीगर दिखाओ',
      'राजस्थान में शिल्पकार',
      'चिकनकारी के बारे में बताओ',
      'आंकड़े दिखाओ'
    ] : [
      'Show pottery artisans',
      'Find crafts in Rajasthan',
      'Tell me about Chikankari',
      'Show statistics'
    ]
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
    
    const { message, conversation_history = [] } = req.body;
    
    // Process Hindi query
    const { intent, entities } = processHindiQuery(message);
    
    // Search for artisans if needed
    let artists = [];
    if (intent === 'search_craft' || intent === 'search_artisan') {
      artists = searchArtisans(entities);
    }
    
    // Generate response
    const response = generateResponse(message, intent, entities, artists);
    
    // Add additional metadata
    response.llm_message = 'Enhanced Hindi NLP processing with multilingual support (Vercel deployment)';
    response.stats = intent === 'get_stats' ? {
      total_artists: artistsData.length,
      unique_crafts: new Set(artistsData.map(a => a.craft_type)).size,
      unique_states: new Set(artistsData.map(a => a.location.state)).size,
      unique_districts: new Set(artistsData.map(a => a.location.district)).size,
      hindi_speakers: artistsData.filter(a => 
        a.languages.some(lang => lang.toLowerCase().includes('hindi'))
      ).length
    } : {};
    response.status = 'online';
    
    res.json(response);
  } catch (error) {
    console.error('Hindi Chat API error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: 'क्षमा करें, कुछ त्रुटि हुई है। / Sorry, an error occurred.',
      status: 'error'
    });
  }
}