// Test script for the improved chatbot API
const testQueries = [
  // English state queries
  { message: "Show me artists from Bihar", expected: "should find Bihar artists" },
  { message: "Find artisans in Uttar Pradesh", expected: "should find UP artists" },
  { message: "Artists from Tamil Nadu", expected: "should find Tamil Nadu artists" },
  { message: "Show me pottery artists", expected: "should find pottery artists" },
  { message: "Weaving artists in Kerala", expected: "should find Kerala weavers" },
  
  // Hindi state queries
  { message: "बिहार के कारीगर दिखाओ", expected: "should find Bihar artists in Hindi" },
  { message: "राजस्थान में शिल्पकार", expected: "should find Rajasthan artists in Hindi" },
  { message: "गुजरात के कुम्हार", expected: "should find Gujarat potters in Hindi" },
  
  // Partial matches
  { message: "pottery", expected: "should find pottery artists with partial match" },
  { message: "Bengal", expected: "should find West Bengal artists" },
  { message: "Kashmir", expected: "should find Jammu & Kashmir artists" },
  
  // Stats queries
  { message: "Show stats", expected: "should show database statistics" },
  { message: "आंकड़े दिखाओ", expected: "should show stats in Hindi" }
];

async function testChatbot() {
  console.log("Testing improved chatbot with clustering model data...\n");
  
  for (const query of testQueries) {
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: query.message,
          conversation_history: []
        })
      });
      
      const data = await response.json();
      
      console.log(`Query: "${query.message}"`);
      console.log(`Expected: ${query.expected}`);
      console.log(`Response: ${data.message}`);
      console.log(`Artists found: ${data.artists.length}`);
      console.log(`Intent: ${data.intent}`);
      console.log(`Language: ${data.language}`);
      if (data.clustering_info && data.clustering_info.cluster_count > 0) {
        console.log(`Clusters: ${data.clustering_info.cluster_count}`);
      }
      console.log('---\n');
      
    } catch (error) {
      console.error(`Error testing "${query.message}":`, error.message);
    }
  }
}

// Run tests after a short delay to let server start
setTimeout(testChatbot, 3000);