import { useState, useRef, useEffect } from 'react';
import { Send, Bot, Loader2 } from 'lucide-react';
import axios from 'axios';
import { Message, ChatResponse } from '../types/chat';
import { cn } from '../utils/cn';

const API_URL = 'http://localhost:5000/api';

export const EnhancedAIAssistant: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            content: "Hello! I'm your AI assistant. How can I help you find information about our artisans?",
            role: 'assistant',
            timestamp: new Date()
        }
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
        setInputMessage('');
        setIsTyping(true);
        setError(null);

        try {
            const response = await axios.post<ChatResponse>(`${API_URL}/chat`, {
                query: userMessage.content
            });

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                content: response.data.response,
                role: 'assistant',
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (err) {
            console.error('Chat error:', err);
            setError('Failed to get response from AI assistant');
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

    return (
        <div className="flex flex-col h-full bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-orange-600 to-amber-600 text-white p-4">
                <div className="flex items-center">
                    <Bot className="w-6 h-6 mr-2" />
                    <h2 className="font-bold text-lg">Artisan AI Assistant</h2>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 text-red-500 p-4 text-sm">
                    {error}
                </div>
            )}

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={cn(
                            "flex w-full mb-4",
                            message.role === 'user' ? 'justify-end' : 'justify-start'
                        )}
                    >
                        <div
                            className={cn(
                                "max-w-[85%] rounded-lg p-4",
                                message.role === 'user'
                                    ? 'bg-orange-500 text-white'
                                    : 'bg-gray-100 text-gray-900'
                            )}
                        >
                            <div className="whitespace-pre-wrap break-words">
                                {message.content}
                            </div>
                            <div className="text-xs opacity-70 mt-2">
                                {message.timestamp.toLocaleTimeString()}
                            </div>
                        </div>
                    </div>
                ))}
                
                {isTyping && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-lg p-4">
                            <Loader2 className="w-5 h-5 animate-spin" />
                        </div>
                    </div>
                )}
                
                <div ref={messagesEndRef} />
            </div>

            <div className="border-t p-4">
                <div className="flex items-center space-x-2">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask about artisans..."
                        className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                        disabled={isTyping}
                    />
                    <button
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim() || isTyping}
                        className={cn(
                            "p-2 rounded-lg text-white",
                            !inputMessage.trim() || isTyping
                                ? "bg-gray-300"
                                : "bg-orange-500 hover:bg-orange-600"
                        )}
                    >
                        {isTyping ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Send className="w-5 h-5" />
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};