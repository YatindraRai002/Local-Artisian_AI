// Path: /Users/abhi/Desktop/Local-Artisian_AI/flask-server/frontend/src/components/EnhancedAIAssistant.tsx

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Bot, User, Phone, Mail, MapPin, Palette, Loader2, AlertCircle, CheckCircle, XCircle, Wifi, WifiOff } from 'lucide-react';
import { apiService, ChatResponse } from '../services/apiService';

// Types
interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

interface ConnectionStatus {
  isConnected: boolean;
  message: string;
  totalArtisans: number;
}

// Utility function for class names (replace with your existing cn utility)
const cn = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};

// Typing Indicator Component
const TypingIndicator: React.FC = () => (
  <div className="flex items-center space-x-1 p-3">
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
    </div>
    <span className="text-sm text-gray-500 ml-2">AI is analyzing...</span>
  </div>
);

// Error Message Component
const ErrorMessage: React.FC<{ message: string; onRetry?: () => void }> = ({ message, onRetry }) => (
  <div className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
    <div className="flex items-center space-x-2">
      <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
      <span className="text-sm text-red-700">{message}</span>
    </div>
    {onRetry && (
      <button
        onClick={onRetry}
        className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200 transition-colors"
      >
        Retry
      </button>
    )}
  </div>
);

// Connection Status Component
const ConnectionStatusIndicator: React.FC<{ status: ConnectionStatus; onReconnect: () => void }> = ({ 
  status, 
  onReconnect 
}) => (
  <div className="flex items-center space-x-3">
    <div className={cn(
      "flex items-center px-3 py-1 rounded-full text-xs font-semibold transition-all",
      status.isConnected 
        ? "bg-green-500/20 text-green-700" 
        : "bg-red-500/20 text-red-700"
    )}>
      {status.isConnected ? (
        <>
          <Wifi className="w-3 h-3 mr-1" />
          <CheckCircle className="w-2 h-2 animate-pulse mr-2" />
          Connected
        </>
      ) : (
        <>
          <WifiOff className="w-3 h-3 mr-1" />
          <XCircle className="w-2 h-2 mr-2" />
          Disconnected
        </>
      )}
    </div>
    
    {!status.isConnected && (
      <button
        onClick={onReconnect}
        className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded hover:bg-orange-200 transition-colors"
      >
        Reconnect
      </button>
    )}
  </div>
);

// Artist Card Component
const ArtistCard: React.FC<{ 
  artist: any; 
  onSimilarClick?: (artist: any) => void;
}> = ({ artist, onSimilarClick }) => {
  const getArtistData = (artist: any) => {
    return {
      id: artist.artisan_id || artist.id || Math.random().toString(),
      name: artist.name || 'Unknown Artist',
      age: artist.age || 'N/A',
      gender: artist.gender || 'N/A',
      craft_type: artist.craft_type || 'Traditional Craft',
      location: {
        village: artist.village || 'Unknown Village',
        district: artist.district || 'Unknown District', 
        state: artist.state || 'Unknown State'
      },
      contact: {
        phone: artist.phone || 'Not available',
        email: artist.email || 'Not available',
        phone_available: artist.phone_available !== false
      },
      languages: typeof artist.languages === 'string' 
        ? artist.languages.split(',').map((l: string) => l.trim()) 
        : (Array.isArray(artist.languages) ? artist.languages : ['Hindi']),
      government_id: artist.govt_id || artist.artisan_id || 'N/A',
      cluster_code: artist.cluster_code || 'N/A'
    };
  };

  const safeArtist = getArtistData(artist);
  
  return (
    <div className="bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-200 rounded-lg p-4 mb-3 hover:shadow-md transition-all duration-200">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-900 flex items-center">
          <User className="w-4 h-4 mr-2 text-orange-600" />
          {safeArtist.name}
        </h3>
        <span className="text-sm text-gray-600">{safeArtist.age} years, {safeArtist.gender}</span>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center text-sm text-gray-700">
          <Palette className="w-4 h-4 mr-2 text-purple-600" />
          <span className="font-medium">{safeArtist.craft_type}</span>
        </div>
        
        <div className="flex items-center text-sm text-gray-700">
          <MapPin className="w-4 h-4 mr-2 text-green-600" />
          <span>{safeArtist.location.village}, {safeArtist.location.district}, {safeArtist.location.state}</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center text-sm text-blue-700">
            <Phone className="w-4 h-4 mr-2" />
            <span className="font-mono text-xs">{safeArtist.contact.phone}</span>
            {!safeArtist.contact.phone_available && (
              <span className="text-xs text-gray-500 ml-1">(Limited)</span>
            )}
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <Mail className="w-4 h-4 mr-2" />
            <span className="truncate max-w-24 text-xs">{safeArtist.contact.email}</span>
          </div>
        </div>
        
        <div className="text-xs text-gray-500">
          Languages: {safeArtist.languages.join(', ')}
        </div>
        
        <div className="text-xs text-gray-400">
          ID: {safeArtist.government_id} | Cluster: {safeArtist.cluster_code}
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
};

// Main Component
export const EnhancedAIAssistant: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    isConnected: false,
    message: 'Connecting...',
    totalArtisans: 0
  });
  const [retryCount, setRetryCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  // Initialize connection and welcome message
  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const health = await apiService.healthCheck();
      setConnectionStatus({
        isConnected: health.status === 'healthy',
        message: health.message,
        totalArtisans: health.total_artisans
      });

      // Set welcome message if connected and no messages exist
      if (health.status === 'healthy' && messages.length === 0) {
        const welcomeMessage: Message = {
          id: '1',
          content: JSON.stringify({
            message: `Hello! I'm your Kala-Kaart AI assistant powered by our live backend server with ${health.total_artisans.toLocaleString()}+ real artisan profiles! I can help you discover traditional Indian artists, search by crafts and locations, provide database statistics, and answer questions about our comprehensive database.`,
            suggestions: [
              "Show me pottery artists",
              "Find artists in Rajasthan", 
              "Get database statistics",
              "Browse textile crafts"
            ],
            llm_message: `🟢 Online mode active: Connected to live backend server with real-time AI responses and comprehensive artisan database (${health.total_artisans.toLocaleString()} artists loaded).`
          }),
          role: 'assistant',
          timestamp: new Date()
        };
        setMessages([welcomeMessage]);
      }
      
      setError(null);
      setRetryCount(0);
    } catch (err) {
      console.error('Connection check failed:', err);
      setConnectionStatus({
        isConnected: false,
        message: err instanceof Error ? err.message : 'Connection failed',
        totalArtisans: 0
      });
      setError('Unable to connect to AI backend. Please check if the server is running.');
    }
  };

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

      // Call the chat API
      const response: ChatResponse = await apiService.chat(currentInput, newHistory);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: JSON.stringify(response),
        role: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update conversation history with assistant response
      setConversationHistory(prev => [...prev, response.message]);
      
    } catch (err) {
      console.error('Chat error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(`Failed to get response: ${errorMessage}`);
      
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: JSON.stringify({
          message: "I apologize, but I'm having trouble connecting to my AI engine. This could be due to server issues or network problems.",
          suggestions: [
            "Retry your question", 
            "Check server connection", 
            "Try a simpler query",
            "Restart the backend server"
          ],
          llm_message: "🔴 Connection error: Unable to reach the backend RAG system. Please ensure the Flask server is running on the correct port."
        }),
        role: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorResponse]);
      
      // Try to reconnect
      setTimeout(() => {
        checkConnection();
      }, 2000);
      
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

  const handleSimilarArtistsClick = async (artist: any) => {
    try {
      setIsTyping(true);
      setError(null);
      
      const artisanId = artist.artisan_id || artist.id;
      if (!artisanId) {
        throw new Error('Artist ID not found');
      }
      
      const response = await apiService.getSimilarArtists(artisanId, 5);
      
      const similarMessage: Message = {
        id: Date.now().toString(),
        content: JSON.stringify({
          message: `Here are artists similar to ${response.reference_artisan?.name || 'the selected artist'}:`,
          artists: response.similar_artists || [],
          suggestions: [
            "More artists from same craft",
            "Artists in same location",
            "Search different criteria",
            "Get contact details"
          ],
          llm_message: `Found ${response.similar_artists?.length || 0} similar artists based on craft type and location matching.`
        }),
        role: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, similarMessage]);
    } catch (err) {
      console.error('Similar artists error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to find similar artists: ${errorMessage}`);
    } finally {
      setIsTyping(false);
    }
  };

  const handleRetry = () => {
    if (retryCount < 3) {
      setRetryCount(prev => prev + 1);
      checkConnection();
    }
  };

  const handleReconnect = () => {
    checkConnection();
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
        
        <div className="ml-auto">
          <ConnectionStatusIndicator 
            status={connectionStatus} 
            onReconnect={handleReconnect}
          />
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-2 bg-red-50 border-b">
          <ErrorMessage message={error} onRetry={handleRetry} />
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex opacity-0 animate-fadeIn",
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
            style={{
              animation: 'fadeIn 0.3s ease-out forwards',
            }}
          >
            <div
              className={cn(
                "max-w-[85%] rounded-2xl p-4 shadow-md transition-all duration-200",
                message.role === 'user'
                  ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-orange-200 hover:shadow-lg'
                  : 'bg-white text-gray-900 border border-gray-100 shadow-gray-100 hover:shadow-md'
              )}
            >
              {message.role === 'assistant' ? (
                <div>
                  {(() => {
                    try {
                      const response: ChatResponse = JSON.parse(message.content);
                      return (
                        <div>
                          <p className="mb-3 text-gray-800">{response.message}</p>
                          
                          {/* LLM Response */}
                          {response.llm_message && (
                            <div className="mb-3 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
                              <div className="flex items-center mb-1">
                                <Bot className="w-4 h-4 mr-1 text-blue-600" />
                                <span className="text-xs text-blue-600 font-medium">AI Analysis:</span>
                              </div>
                              <p className="text-sm text-blue-800">{response.llm_message}</p>
                            </div>
                          )}
                          
                          {/* Artists Results */}
                          {response.artists && response.artists.length > 0 && (
                            <div className="mb-3">
                              <div className="text-sm text-gray-600 mb-2 font-medium">
                                📋 Found {response.artists.length} artist(s):
                              </div>
                              <div className="max-h-80 overflow-y-auto">
                                {response.artists.map((artist: any, index: number) => (
                                  <ArtistCard 
                                    key={artist.artisan_id || artist.id || index} 
                                    artist={artist} 
                                    onSimilarClick={handleSimilarArtistsClick}
                                  />
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Statistics Display */}
                          {response.stats && Object.keys(response.stats).length > 0 && (
                            <div className="mb-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                              <div className="text-sm font-semibold text-green-800 mb-3 flex items-center">
                                📊 Database Statistics:
                              </div>
                              <div className="grid grid-cols-2 gap-3 text-sm text-green-700">
                                {response.stats.total_artisans && (
                                  <div className="flex justify-between">
                                    <span>Total Artists:</span>
                                    <span className="font-mono font-bold">{response.stats.total_artisans.toLocaleString()}</span>
                                  </div>
                                )}
                                {response.stats.states && Object.keys(response.stats.states).length > 0 && (
                                  <div className="flex justify-between">
                                    <span>States:</span>
                                    <span className="font-mono font-bold">{Object.keys(response.stats.states).length}</span>
                                  </div>
                                )}
                                {response.stats.craft_types && Object.keys(response.stats.craft_types).length > 0 && (
                                  <div className="flex justify-between">
                                    <span>Crafts:</span>
                                    <span className="font-mono font-bold">{Object.keys(response.stats.craft_types).length}</span>
                                  </div>
                                )}
                                {response.stats.districts && Object.keys(response.stats.districts).length > 0 && (
                                  <div className="flex justify-between">
                                    <span>Districts:</span>
                                    <span className="font-mono font-bold">{Object.keys(response.stats.districts).length}</span>
                                  </div>
                                )}
                              </div>
                              
                              {/* Top categories */}
                              {response.stats.craft_types && (
                                <div className="mt-3">
                                  <div className="text-xs font-medium text-green-700 mb-1">Top Crafts:</div>
                                  <div className="flex flex-wrap gap-1">
                                    {Object.entries(response.stats.craft_types).slice(0, 5).map(([craft, count]: [string, any]) => (
                                      <span key={craft} className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                                        {craft}: {count}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Intent & Entity Display (for debugging in development) */}
                          {process.env.NODE_ENV === 'development' && (
                            <div className="mb-2 text-xs text-gray-500 bg-gray-100 p-2 rounded">
                              <strong>Debug:</strong> Intent: {response.intent} | Entities: {JSON.stringify(response.entities)}
                            </div>
                          )}
                          
                          {/* Suggestions */}
                          {response.suggestions && response.suggestions.length > 0 && (
                            <div className="flex flex-wrap gap-2">
                              {response.suggestions.map((suggestion: string, index: number) => (
                                <button
                                  key={`suggestion-${index}`}
                                  onClick={() => handleSuggestionClick(suggestion)}
                                  className="text-xs bg-orange-100 text-orange-800 px-3 py-1.5 rounded-full hover:bg-orange-200 transition-all duration-200 hover:scale-105"
                                >
                                  {suggestion}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    } catch {
                      return <p className="text-gray-800">{message.content}</p>;
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
              placeholder={connectionStatus.isConnected 
                ? "Ask about artists, crafts, locations, or analytics..." 
                : "Connecting to AI backend..."}
              className={cn(
                "w-full p-4 pr-12 border-2 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400 shadow-sm placeholder-gray-500 bg-white transition-all duration-200",
                connectionStatus.isConnected 
                  ? "border-gray-200" 
                  : "border-red-200 bg-red-50"
              )}
              disabled={isTyping || !connectionStatus.isConnected}
            />
            {inputMessage && (
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400">
                <span className="text-xs font-medium">{inputMessage.length}/500</span>
              </div>
            )}
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isTyping || !connectionStatus.isConnected}
            className={cn(
              "p-4 rounded-2xl text-white transition-all duration-200 flex items-center shadow-lg",
              !inputMessage.trim() || isTyping || !connectionStatus.isConnected
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
              { text: "Browse textile crafts", icon: "🧵" },
              { text: "Search by location", icon: "📍" },
              { text: "Filter by craft type", icon: "🎨" }
            ].map((quickAction, index) => (
              <button
                key={`quick-action-${index}`}
                onClick={() => handleSuggestionClick(quickAction.text)}
                className="flex items-center text-xs bg-white border border-gray-200 text-gray-700 px-3 py-2 rounded-full hover:bg-orange-50 hover:border-orange-200 hover:text-orange-700 transition-all duration-200 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isTyping || !connectionStatus.isConnected}
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
            {connectionStatus.isConnected ? (
              <>
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                Online mode - Connected to live server with {connectionStatus.totalArtisans.toLocaleString()}+ artists
              </>
            ) : (
              <>
                <div className="w-2 h-2 bg-red-400 rounded-full mr-2"></div>
                Offline mode - {connectionStatus.message}
              </>
            )}
          </div>
        </div>
      </div>

      {/* CSS for animations */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};