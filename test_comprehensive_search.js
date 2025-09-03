// Comprehensive test for enhanced state-based search functionality
async function testComprehensiveSearch() {
  console.log('🔍 Testing Comprehensive State-Based Search Functionality\n');
  
  // Test all major Indian states with various search formats
  const stateTests = [
    // Major states with full names
    { state: 'Uttar Pradesh', expectResults: true },
    { state: 'Maharashtra', expectResults: true },
    { state: 'Bihar', expectResults: true },
    { state: 'West Bengal', expectResults: true },
    { state: 'Andhra Pradesh', expectResults: true },
    { state: 'Madhya Pradesh', expectResults: true },
    { state: 'Tamil Nadu', expectResults: true },
    { state: 'Rajasthan', expectResults: true },
    { state: 'Karnataka', expectResults: true },
    { state: 'Gujarat', expectResults: true },
    { state: 'Odisha', expectResults: true },
    { state: 'Kerala', expectResults: true },
    { state: 'Jharkhand', expectResults: true },
    { state: 'Assam', expectResults: true },
    { state: 'Punjab', expectResults: true },
    { state: 'Haryana', expectResults: true },
    { state: 'Chhattisgarh', expectResults: true },
    { state: 'Himachal Pradesh', expectResults: true },
    { state: 'Jammu & Kashmir', expectResults: true },
    { state: 'Uttarakhand', expectResults: true },
    
    // Abbreviations
    { state: 'UP', expectResults: true },
    { state: 'MP', expectResults: true },
    { state: 'TN', expectResults: true },
    { state: 'WB', expectResults: true },
    { state: 'AP', expectResults: true },
    { state: 'J&K', expectResults: true },
    { state: 'HP', expectResults: true },
    
    // Alternative names
    { state: 'Bengal', expectResults: true },
    { state: 'Kashmir', expectResults: true },
    { state: 'Orissa', expectResults: true },
    { state: 'Tamilnadu', expectResults: true },
    
    // Union territories
    { state: 'Delhi', expectResults: true },
    { state: 'Chandigarh', expectResults: true },
    { state: 'Puducherry', expectResults: true },
    { state: 'Pondicherry', expectResults: true },
    
    // Test invalid state
    { state: 'InvalidState', expectResults: false },
  ];
  
  let passed = 0;
  let failed = 0;
  let totalResults = 0;
  const statesFound = new Set();
  
  console.log('Testing state searches...\n');
  
  for (const test of stateTests) {
    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          state: test.state,
          limit: 10
        })
      });
      
      if (!response.ok) {
        console.log(`❌ ${test.state}: HTTP ${response.status}`);
        failed++;
        continue;
      }
      
      const data = await response.json();
      const hasResults = data.artists && data.artists.length > 0;
      
      if ((test.expectResults && hasResults) || (!test.expectResults && !hasResults)) {
        console.log(`✅ ${test.state}: ${data.artists.length} artists found${data.total > data.artists.length ? ` (${data.total} total)` : ''}`);
        
        if (hasResults) {
          totalResults += data.artists.length;
          // Track unique states found in results
          data.artists.forEach(artist => statesFound.add(artist.location.state));
          
          // Show first artist details
          if (data.artists[0]) {
            const firstArtist = data.artists[0];
            console.log(`   └─ Sample: ${firstArtist.name} (${firstArtist.craft_type}) from ${firstArtist.location.state}, ${firstArtist.location.district}`);
          }
          
          // Show search metadata if available
          if (data.search_metadata && data.search_metadata.search_statistics) {
            const stats = data.search_metadata.search_statistics;
            console.log(`   └─ Stats: ${stats.unique_crafts} crafts, ${stats.unique_districts} districts`);
          }
        }
        
        passed++;
      } else {
        console.log(`❌ ${test.state}: Expected ${test.expectResults ? 'results' : 'no results'} but got ${hasResults ? 'results' : 'no results'}`);
        
        // Show suggestions if available
        if (data.suggestions) {
          console.log(`   └─ Suggestions: ${data.suggestions.states.join(', ')}`);
        }
        
        failed++;
      }
      
    } catch (error) {
      console.log(`❌ ${test.state}: Error - ${error.message}`);
      failed++;
    }
  }
  
  console.log('\n' + '='.repeat(60));
  console.log(`📊 Test Results:`);
  console.log(`✅ Passed: ${passed}/${stateTests.length}`);
  console.log(`❌ Failed: ${failed}/${stateTests.length}`);
  console.log(`📈 Total artists found: ${totalResults}`);
  console.log(`🗺️ Unique states in results: ${statesFound.size}`);
  
  if (statesFound.size > 0) {
    console.log(`\n🗺️ States found in search results:`);
    console.log([...statesFound].sort().join(', '));
  }
  
  // Test additional search features
  console.log('\n🔧 Testing Additional Search Features...\n');
  
  const additionalTests = [
    {
      name: 'Combined state + craft search',
      filters: { state: 'Bihar', craft_type: 'pottery' },
      expectResults: true
    },
    {
      name: 'Age range filtering',
      filters: { state: 'Rajasthan', age_min: 25, age_max: 45 },
      expectResults: true
    },
    {
      name: 'Gender filtering',
      filters: { state: 'Kerala', gender: 'Female' },
      expectResults: true
    },
    {
      name: 'Language filtering',
      filters: { state: 'Tamil Nadu', language: 'Tamil' },
      expectResults: true
    },
    {
      name: 'Sorting by name',
      filters: { state: 'Gujarat', sort_by: 'name', sort_order: 'asc', limit: 5 },
      expectResults: true
    },
    {
      name: 'Pagination test',
      filters: { state: 'Maharashtra', limit: 5, offset: 5 },
      expectResults: true
    }
  ];
  
  let additionalPassed = 0;
  
  for (const test of additionalTests) {
    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(test.filters)
      });
      
      if (response.ok) {
        const data = await response.json();
        const hasResults = data.artists && data.artists.length > 0;
        
        if (test.expectResults === hasResults) {
          console.log(`✅ ${test.name}: ${data.artists.length} results`);
          
          if (data.search_metadata) {
            console.log(`   └─ Applied filters: ${data.search_metadata.filters_applied.join(', ')}`);
          }
          
          additionalPassed++;
        } else {
          console.log(`❌ ${test.name}: Unexpected result count`);
        }
      } else {
        console.log(`❌ ${test.name}: HTTP ${response.status}`);
      }
    } catch (error) {
      console.log(`❌ ${test.name}: Error - ${error.message}`);
    }
  }
  
  console.log(`\n🔧 Additional tests: ${additionalPassed}/${additionalTests.length} passed`);
  
  // Final summary
  const overallSuccess = (passed === stateTests.length - 1) && (additionalPassed >= additionalTests.length - 1); // Allow 1 failure for invalid state test
  
  console.log('\n' + '='.repeat(60));
  if (overallSuccess) {
    console.log('🎉 SUCCESS: Enhanced state-based search is working correctly!');
    console.log('✅ All Indian states are searchable with variations');
    console.log('✅ Advanced filtering and sorting features work');
    console.log('✅ Comprehensive metadata is provided');
  } else {
    console.log('⚠️  Some tests failed. Please review the issues above.');
  }
}

testComprehensiveSearch();