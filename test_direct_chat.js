// Direct test of the chat API to debug issues

async function testChatAPI() {
  try {
    console.log('Testing chat API at http://localhost:8000/chat...\n');
    
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: 'Show me artists from Bihar',
        conversation_history: []
      })
    });
    
    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const error = await response.text();
      console.log('Error response:', error);
      return;
    }
    
    const data = await response.json();
    console.log('\n=== Chat Response ===');
    console.log('Message:', data.message);
    console.log('Artists found:', data.artists ? data.artists.length : 0);
    console.log('Language:', data.language);
    console.log('Intent:', data.intent);
    console.log('LLM Message:', data.llm_message);
    
    if (data.artists && data.artists.length > 0) {
      console.log('\nFirst artist:', {
        name: data.artists[0].name,
        craft: data.artists[0].craft_type,
        state: data.artists[0].location.state,
        cluster_code: data.artists[0].cluster_code
      });
    }
    
    if (data.clustering_info) {
      console.log('\nClustering info:', {
        cluster_count: data.clustering_info.cluster_count,
        districts_covered: data.clustering_info.districts_covered.slice(0, 3),
        crafts_found: data.clustering_info.crafts_found
      });
    }
    
  } catch (error) {
    console.error('Fetch error:', error);
  }
}

testChatAPI();