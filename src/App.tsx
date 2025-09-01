import { useState, useEffect } from 'react';
import { MessageCircle, X, Search, Users, Palette, MapPin, Sparkles, Loader2 } from 'lucide-react';
import { EnhancedAIAssistant } from './components/EnhancedAIAssistant';
import { getArtistsData, apiService, waitForData } from './data/artistsData';

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [artists, setArtists] = useState([]);
  const [filteredArtists, setFilteredArtists] = useState([]);
  const [stats, setStats] = useState({
    totalArtists: 0,
    totalCrafts: 0,
    totalStates: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const toggleChat = () => setIsChatOpen(!isChatOpen);

  // Load data from API on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        
        // Load artists and stats in parallel
        const [artistsResult, statsResult] = await Promise.all([
          apiService.searchArtists({ limit: 1000 }),
          apiService.getStats()
        ]);

        setArtists(artistsResult.artists);
        setStats({
          totalArtists: statsResult.total_artists || 0,
          totalCrafts: statsResult.unique_crafts || 0,
          totalStates: statsResult.unique_states || 0,
        });
        
      } catch (err) {
        console.error('Failed to load data:', err);
        setError('Failed to load data from server');
        
        // Fallback to local data if available
        const localArtists = getArtistsData();
        setArtists(localArtists);
        setStats({
          totalArtists: localArtists.length,
          totalCrafts: new Set(localArtists.map(a => a.craft_type)).size,
          totalStates: new Set(localArtists.map(a => a.location.state)).size,
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // Handle search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredArtists(artists.slice(0, 12)); // Show first 12
    } else {
      const filtered = artists.filter(artist =>
        artist.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        artist.craft_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        artist.location.state.toLowerCase().includes(searchQuery.toLowerCase()) ||
        artist.location.district.toLowerCase().includes(searchQuery.toLowerCase()) ||
        artist.location.village.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredArtists(filtered.slice(0, 20)); // Show more results for search
    }
  }, [searchQuery, artists]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-orange-600 to-amber-600 rounded-lg flex items-center justify-center">
                <Palette className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent">
                Kala-Kaart
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search artists, crafts, locations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 w-80 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Discover India's 
            <span className="bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent"> Traditional Artists</span>
          </h2>
          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Connect with skilled artisans preserving centuries-old crafts. Find their contact information and explore their beautiful work.
          </p>
          
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
              <Users className="w-12 h-12 text-orange-600 mx-auto mb-4" />
              <div className="text-3xl font-bold text-gray-900 mb-2">{stats.totalArtists}+</div>
              <div className="text-gray-600">Verified Artists</div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
              <Palette className="w-12 h-12 text-purple-600 mx-auto mb-4" />
              <div className="text-3xl font-bold text-gray-900 mb-2">{stats.totalCrafts}+</div>
              <div className="text-gray-600">Traditional Crafts</div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
              <MapPin className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <div className="text-3xl font-bold text-gray-900 mb-2">{stats.totalStates}+</div>
              <div className="text-gray-600">States Covered</div>
            </div>
          </div>

          {/* CTA */}
          <div className="space-y-4">
            <button
              onClick={() => setIsChatOpen(true)}
              className="bg-gradient-to-r from-orange-600 to-amber-600 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:from-orange-700 hover:to-amber-700 transition-all duration-200 shadow-lg hover:shadow-xl flex items-center mx-auto"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Chat with AI Assistant
            </button>
            <p className="text-gray-500">Ask about artists, crafts, or get contact information instantly</p>
          </div>
        </div>
      </section>

      {/* Artists Grid */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4">
          <h3 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            {searchQuery ? `Search Results (${filteredArtists.length})` : 'Featured Artists'}
          </h3>
          
          {isLoading ? (
            <div className="flex justify-center items-center py-20">
              <div className="text-center">
                <Loader2 className="w-12 h-12 text-orange-600 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading artists from our AI-powered database...</p>
              </div>
            </div>
          ) : error ? (
            <div className="text-center py-16">
              <div className="text-red-400 mb-4">
                <X className="w-16 h-16 mx-auto" />
              </div>
              <h4 className="text-xl font-semibold text-red-600 mb-2">Connection Error</h4>
              <p className="text-gray-500 mb-4">{error}</p>
              <button 
                onClick={() => window.location.reload()}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
              >
                Retry
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredArtists.map((artist) => (
              <div key={artist.id} className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-200 hover:-translate-y-1">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900 text-lg">{artist.name}</h4>
                  <span className="text-sm text-gray-500">{artist.age}y</span>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center text-purple-600">
                    <Palette className="w-4 h-4 mr-2" />
                    <span className="font-medium text-sm">{artist.craft_type}</span>
                  </div>
                  
                  <div className="flex items-center text-green-600">
                    <MapPin className="w-4 h-4 mr-2" />
                    <span className="text-sm">{artist.location.district}, {artist.location.state}</span>
                  </div>
                  
                  <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg p-3">
                    <div className="text-xs text-gray-600 mb-1">Contact:</div>
                    <div className="text-sm font-mono text-blue-700">{artist.contact.phone}</div>
                    <div className="text-xs text-gray-600 truncate">{artist.contact.email}</div>
                  </div>
                  
                  <div className="text-xs text-gray-500">
                    Languages: {artist.languages.join(', ')}
                  </div>
                </div>
              </div>
              ))}
            </div>
          )}
          
          {filteredArtists.length === 0 && (
            <div className="text-center py-16">
              <div className="text-gray-400 mb-4">
                <Search className="w-16 h-16 mx-auto" />
              </div>
              <h4 className="text-xl font-semibold text-gray-600 mb-2">No artists found</h4>
              <p className="text-gray-500">Try adjusting your search or use the AI assistant for help</p>
            </div>
          )}
        </div>
      </section>

      {/* Chat Assistant */}
      {isChatOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg w-full max-w-2xl h-[600px] flex flex-col relative">
            <button
              onClick={toggleChat}
              className="absolute top-4 right-4 z-10 p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-gray-600" />
            </button>
            <EnhancedAIAssistant />
          </div>
        </div>
      )}

      {/* Floating Chat Button */}
      {!isChatOpen && (
        <button
          onClick={toggleChat}
          className="fixed bottom-6 right-6 bg-gradient-to-r from-orange-600 to-amber-600 text-white p-4 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 z-40"
        >
          <MessageCircle className="w-6 h-6" />
        </button>
      )}
    </div>
  );
}

export default App;