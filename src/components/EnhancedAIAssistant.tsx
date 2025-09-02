import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Phone, Mail, MapPin, Palette, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '../utils/cn';
import { Message, Artist } from '../types';
import { apiService } from '../data/artistsData';

const TypingIndicator = () => (
  <div className="flex items-center space-x-1 p-3">
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
    </div>
    <span className="text-sm text-gray-500 ml-2">AI is analyzing...</span>
  </div>
);

const ErrorMessage = ({ message }: { message: string }) => (
  <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
    <AlertCircle className="w-4 h-4 text-red-500" />
    <span className="text-sm text-red-700">{message}</span>
  </div>
);

const ArtistCard: React.FC<{ artist: Artist; onSimilarClick?: (artist: Artist) => void }> = ({ 
  artist, 
  onSimilarClick 
}) => (
  <div className="bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-200 rounded-lg p-4 mb-3 hover:shadow-md transition-shadow">
    <div className="flex items-center justify-between mb-2">
      <h3 className="font-semibold text-gray-900 flex items-center">
        <User className="w-4 h-4 mr-2 text-orange-600" />
        {artist.name}
      </h3>
      <span className="text-sm text-gray-600">{artist.age} years, {artist.gender}</span>
    </div>
    
    <div className="space-y-2">
      <div className="flex items-center text-sm text-gray-700">
        <Palette className="w-4 h-4 mr-2 text-purple-600" />
        <span className="font-medium">{artist.craft_type}</span>
      </div>
      
      <div className="flex items-center text-sm text-gray-700">
        <MapPin className="w-4 h-4 mr-2 text-green-600" />
        <span>{artist.location.village}, {artist.location.district}, {artist.location.state}</span>
      </div>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center text-sm text-blue-700">
          <Phone className="w-4 h-4 mr-2" />
          <span className="font-mono">{artist.contact.phone}</span>
          {!artist.contact.phone_available && (
            <span className="text-xs text-gray-500 ml-1">(Limited)</span>
          )}
        </div>
        <div className="flex items-center text-sm text-gray-600">
          <Mail className="w-4 h-4 mr-2" />
          <span className="truncate max-w-32">{artist.contact.email}</span>
        </div>
      </div>
      
      <div className="text-xs text-gray-500">
        Languages: {artist.languages.join(', ')}
      </div>
      
      <div className="text-xs text-gray-400">
        ID: {artist.government_id} | Cluster: {artist.cluster_code}
      </div>
      
      {onSimilarClick && (
        <button
          onClick={() => onSimilarClick(artist)}
          className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full hover:bg-orange-200 transition-colors"
        >
          Find Similar Artists
        </button>
      )}
    </div>
  </div>
);

interface ChatResponse {
  intent: string;
  entities: any;
  message: string;
  llm_message?: string;
  artists: Artist[];
  suggestions: string[];
  stats: any;
}

export const EnhancedAIAssistant: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: JSON.stringify({
        message: "Hello! I'm your Kala-Kaart AI assistant powered by our live backend server with 50,000+ real artisan profiles! I can help you discover traditional Indian artists, search by crafts and locations, provide database statistics, and answer questions about our comprehensive database.",
        suggestions: [
          "Show me pottery artists",
          "Find artists in Rajasthan", 
          "Get database statistics",
          "Browse textile crafts"
        ],
        llm_message: "🟢 Online mode active: Connected to live backend server with real-time AI responses and comprehensive artisan database."
      }),
      role: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage('');
    setIsTyping(true);
    setError(null);

    try {
      // Add to conversation history
      const newHistory = [...conversationHistory, currentInput];
      setConversationHistory(newHistory);

      // Call the enhanced API
      const response: ChatResponse = await apiService.chat(currentInput, newHistory);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: JSON.stringify(response),
        role: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to get response from AI assistant. Please try again.');
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: JSON.stringify({
          message: "I apologize, but I'm having trouble connecting to my advanced AI engine. Please check if the backend server is running and try again.",
          suggestions: ["Retry your question", "Check server status", "Try a simpler query"]
        }),
        role: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion);
  };

  const handleSimilarArtistsClick = async (artist: Artist) => {
    try {
      setIsTyping(true);
      const response = await apiService.getSimilarArtists(artist.id, 5);
      
      const similarMessage: Message = {
        id: Date.now().toString(),
        content: JSON.stringify({
          message: `Here are artists similar to ${artist.name} (${artist.craft_type} from ${artist.location.state}):`,
          artists: response.similar_artists,
          suggestions: [
            `More ${artist.craft_type} artists`,
            `Artists in ${artist.location.state}`,
            "Search different criteria",
            "Get contact details"
          ]
        }),
        role: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, similarMessage]);
    } catch (err) {
      console.error('Similar artists error:', err);
      setError('Failed to find similar artists');
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Enhanced Chat Header */}
      <div className="bg-gradient-to-r from-orange-600 via-orange-500 to-amber-600 text-white p-6 flex items-center relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 100 20">
            <defs>
              <pattern id="chat-pattern" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
                <circle cx="10" cy="10" r="1" fill="white"/>
              </pattern>
            </defs>
            <rect width="100" height="20" fill="url(#chat-pattern)"/>
          </svg>
        </div>
        
        <div className="relative flex items-center">
          <div className="bg-white/20 p-3 rounded-2xl mr-4">
            <Bot className="w-8 h-8 text-white" />
          </div>
          <div>
            <h2 className="font-bold text-xl">Kala-Kaart AI Assistant</h2>
            <p className="text-orange-100 font-medium">Powered by Advanced NLP & Machine Learning</p>
          </div>
        </div>
        
        <div className="ml-auto flex items-center space-x-3">
          <div className="flex items-center bg-green-500/20 px-3 py-1 rounded-full">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
            <span className="text-xs font-semibold">Online & Connected</span>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-2 bg-red-50 border-b">
          <ErrorMessage message={error} />
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex message-slide-in",
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                "max-w-[85%] rounded-2xl p-4 shadow-md",
                message.role === 'user'
                  ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-orange-200'
                  : 'bg-white text-gray-900 border border-gray-100 shadow-gray-100'
              )}
            >
              {message.role === 'assistant' ? (
                <div>
                  {(() => {
                    try {
                      const response: ChatResponse = JSON.parse(message.content);
                      return (
                        <div>
                          <p className="mb-3">{response.message}</p>
                          
                          {/* LLM Response */}
                          {response.llm_message && (
                            <div className="mb-3 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
                              <div className="flex items-center mb-1">
                                <Bot className="w-4 h-4 mr-1 text-blue-600" />
                                <span className="text-xs text-blue-600 font-medium">AI Analysis:</span>
                              </div>
                              <p className="text-sm">{response.llm_message}</p>
                            </div>
                          )}
                          
                          {/* Artists Results */}
                          {response.artists && response.artists.length > 0 && (
                            <div className="mb-3">
                              <div className="text-sm text-gray-600 mb-2">
                                Found {response.artists.length} artist(s):
                              </div>
                              {response.artists.map((artist: Artist) => (
                                <ArtistCard 
                                  key={artist.id} 
                                  artist={artist} 
                                  onSimilarClick={handleSimilarArtistsClick}
                                />
                              ))}
                            </div>
                          )}
                          
                          {/* Statistics Display */}
                          {response.stats && Object.keys(response.stats).length > 0 && (
                            <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded">
                              <div className="text-sm font-medium text-green-800 mb-2">Database Statistics:</div>
                              <div className="grid grid-cols-2 gap-2 text-xs text-green-700">
                                <div>Total Artists: {response.stats.total_artists}</div>
                                <div>States: {response.stats.unique_states}</div>
                                <div>Crafts: {response.stats.unique_crafts}</div>
                                <div>Districts: {response.stats.unique_districts}</div>
                              </div>
                            </div>
                          )}
                          
                          {/* Intent & Entity Display (for debugging) */}
                          {import.meta.env.DEV && (
                            <div className="mb-2 text-xs text-gray-500">
                              Intent: {response.intent} | Entities: {JSON.stringify(response.entities)}
                            </div>
                          )}
                          
                          {/* Suggestions */}
                          {response.suggestions && response.suggestions.length > 0 && (
                            <div className="flex flex-wrap gap-2">
                              {response.suggestions.map((suggestion: string, index: number) => (
                                <button
                                  key={index}
                                  onClick={() => handleSuggestionClick(suggestion)}
                                  className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full hover:bg-orange-200 transition-colors"
                                >
                                  {suggestion}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    } catch {
                      return <p>{message.content}</p>;
                    }
                  })()}
                </div>
              ) : (
                <p>{message.content}</p>
              )}
              
              <div className="text-xs opacity-70 mt-2">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="max-w-[85%] bg-gray-100 rounded-lg">
              <TypingIndicator />
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Enhanced Input Area */}
      <div className="border-t bg-gradient-to-r from-gray-50 to-orange-25 p-4">
        <div className="flex items-center space-x-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about artists, crafts, locations, or analytics..."
              className="w-full p-4 pr-12 border-2 border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400 shadow-sm placeholder-gray-500 bg-white transition-all duration-200"
              disabled={isTyping}
            />
            {inputMessage && (
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400">
                <span className="text-xs font-medium">{inputMessage.length}/500</span>
              </div>
            )}
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isTyping}
            className={cn(
              "p-4 rounded-2xl text-white transition-all duration-200 flex items-center shadow-lg",
              !inputMessage.trim() || isTyping
                ? "bg-gray-300 cursor-not-allowed scale-95"
                : "bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 hover:scale-105 hover:shadow-xl"
            )}
          >
            {isTyping ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        
        {/* Enhanced Quick Actions */}
        <div className="mt-4">
          <div className="text-xs text-gray-500 font-medium mb-2">Quick suggestions:</div>
          <div className="flex flex-wrap gap-2">
            {[
              { text: "Show database stats", icon: "📊" },
              { text: "Find pottery artists", icon: "🏺" }, 
              { text: "Artists in Rajasthan", icon: "🗺️" },
              { text: "Browse textile crafts", icon: "🧵" }
            ].map((quickAction, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(quickAction.text)}
                className="flex items-center text-xs bg-white border border-gray-200 text-gray-700 px-3 py-2 rounded-full hover:bg-orange-50 hover:border-orange-200 hover:text-orange-700 transition-all duration-200 shadow-sm hover:shadow-md"
                disabled={isTyping}
              >
                <span className="mr-1.5">{quickAction.icon}</span>
                {quickAction.text}
              </button>
            ))}
          </div>
        </div>
        
        {/* Status indicator */}
        <div className="mt-3 flex items-center justify-center">
          <div className="flex items-center text-xs text-gray-500">
            <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
            Online mode - Connected to live server with 50,000+ artists
          </div>
        </div>
      </div>
    </div>
  );
};