export interface Message {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
}

export interface ChatResponse {
    response: string;
    status: string;
    error?: string;
}