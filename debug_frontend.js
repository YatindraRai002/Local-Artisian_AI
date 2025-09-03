// Debug script to test frontend API communication
async function testFrontendAPI() {
  console.log('Testing frontend API communication...\n');
  
  const testUrl = 'http://localhost:5176/test-backend.html';
  console.log(`Frontend should be available at: ${testUrl}`);
  console.log('Backend is running at: http://localhost:8000');
  
  // Test direct API call from Node.js (simulating browser)
  try {
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:5176'  // Simulate browser request
      },
      body: JSON.stringify({
        message: 'Test from debug script',
        conversation_history: []
      })
    });
    
    console.log('API Response Status:', response.status);
    console.log('API Response Headers:', Object.fromEntries(response.headers.entries()));
    
    if (response.ok) {
      const data = await response.json();
      console.log('\n✅ API is working correctly!');
      console.log('Message:', data.message);
      console.log('Artists found:', data.artists ? data.artists.length : 0);
    } else {
      console.log('❌ API request failed');
    }
  } catch (error) {
    console.log('❌ API connection error:', error.message);
  }
}

testFrontendAPI();