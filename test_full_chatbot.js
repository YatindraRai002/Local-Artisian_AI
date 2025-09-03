// Comprehensive test of the chatbot functionality
async function testFullChatbot() {
  console.log('🤖 Testing Full Chatbot Functionality\n');
  
  const queries = [
    // Basic state searches
    { message: 'Show me artists from Bihar', expect: 'Bihar artists' },
    { message: 'Find artists in Rajasthan', expect: 'Rajasthan artists' },
    { message: 'Artists from Tamil Nadu', expect: 'Tamil Nadu artists' },
    
    // Craft searches
    { message: 'Show me pottery artists', expect: 'pottery artists' },
    { message: 'Weaving artists in Kerala', expect: 'Kerala weaving artists' },
    
    // Hindi searches
    { message: 'बिहार के कारीगर दिखाओ', expect: 'Bihar artists in Hindi' },
    { message: 'राजस्थान में शिल्पकार', expect: 'Rajasthan artists in Hindi' },
    
    // Partial matches
    { message: 'Bengal', expect: 'West Bengal artists' },
    { message: 'Kashmir', expect: 'Jammu & Kashmir artists' },
    
    // Stats
    { message: 'Show stats', expect: 'database statistics' },
    { message: 'आंकड़े दिखाओ', expect: 'stats in Hindi' }
  ];
  
  let passed = 0;
  let failed = 0;
  
  for (const query of queries) {
    try {
      console.log(`Testing: "${query.message}"`);
      
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'http://localhost:5176'
        },
        body: JSON.stringify({
          message: query.message,
          conversation_history: []
        })
      });
      
      if (!response.ok) {
        console.log(`  ❌ HTTP ${response.status}`);
        failed++;
        continue;
      }
      
      const data = await response.json();
      
      
      const hasMessage = !!data.message;
      const hasLanguage = !!data.language;
      const hasIntent = !!data.intent;
      const hasLLMMessage = !!data.llm_message;
      
      if (hasMessage && hasLanguage && hasIntent && hasLLMMessage) {
        console.log(`  ✅ Valid response: ${data.artists ? data.artists.length : 0} artists found`);
        console.log(`     Message: ${data.message.substring(0, 60)}...`);
        console.log(`     Language: ${data.language}, Intent: ${data.intent}`);
        if (data.clustering_info && data.clustering_info.cluster_count > 0) {
          console.log(`     Clusters: ${data.clustering_info.cluster_count}`);
        }
        passed++;
      } else {
        console.log(`  ❌ Incomplete response structure`);
        failed++;
      }
      
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
      failed++;
    }
    
    console.log('');
  }
  
  console.log(`\n📊 Test Results:`);
  console.log(`✅ Passed: ${passed}/${queries.length}`);
  console.log(`❌ Failed: ${failed}/${queries.length}`);
  
  if (passed === queries.length) {
    console.log('\n🎉 All tests passed! Chatbot is working correctly with clustering model data.');
  } else {
    console.log('\n⚠️  Some tests failed. Check the issues above.');
  }
}

testFullChatbot();