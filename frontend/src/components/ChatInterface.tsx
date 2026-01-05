import { useState, useRef, useEffect } from 'react';
import { apiService, ChatMessage } from '../services/api';
import './ChatInterface.css';

export default function ChatInterface() {
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            role: 'assistant',
            content: 'Hello! I\'m your MCP Agent. I can help you with CSV files, search through documents, and answer questions. What would you like to do?',
            timestamp: new Date().toISOString(),
        },
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: ChatMessage = {
            role: 'user',
            content: input.trim(),
            timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await apiService.chat({ message: input.trim() });

            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: response.response,
                timestamp: new Date().toISOString(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage: ChatMessage = {
                role: 'assistant',
                content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please make sure the backend server is running.`,
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const handleClearChat = async () => {
        try {
            await apiService.resetChat();
            setMessages([
                {
                    role: 'assistant',
                    content: 'Chat cleared! How can I help you?',
                    timestamp: new Date().toISOString(),
                },
            ]);
        } catch (error) {
            console.error('Failed to clear chat:', error);
        }
    };

    const examplePrompts = [
        'Show me all employees in the Engineering department',
        'What are the company values?',
        'List all CSV files',
        'How many employees are in each department?',
    ];

    const handleExampleClick = (prompt: string) => {
        setInput(prompt);
        inputRef.current?.focus();
    };

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <div className="chat-title">
                    <h2>AI Assistant</h2>
                    <span className="chat-subtitle">Powered by NVIDIA API</span>
                </div>
                <button className="clear-button" onClick={handleClearChat}>
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M8.5 3.5L9.5 2.5H10.5L11.5 3.5H15V5H5V3.5H8.5Z" />
                        <path d="M6 6H14V16C14 17.1046 13.1046 18 12 18H8C6.89543 18 6 17.1046 6 16V6Z" />
                    </svg>
                    Clear
                </button>
            </div>

            <div className="messages-container">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'} animate-fadeIn`}
                    >
                        <div className="message-avatar">
                            {message.role === 'user' ? (
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                    <circle cx="12" cy="8" r="4" />
                                    <path d="M4 20C4 16.6863 6.68629 14 10 14H14C17.3137 14 20 16.6863 20 20V21H4V20Z" />
                                </svg>
                            ) : (
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2L2 7L12 12L22 7L12 2Z" />
                                    <path d="M2 17L12 22L22 17M2 12L12 17L22 12" opacity="0.6" />
                                </svg>
                            )}
                        </div>
                        <div className="message-content">
                            <div className="message-text">{message.content}</div>
                            {message.timestamp && (
                                <div className="message-time">
                                    {new Date(message.timestamp).toLocaleTimeString()}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="message assistant-message animate-fadeIn">
                        <div className="message-avatar">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2L2 7L12 12L22 7L12 2Z" />
                                <path d="M2 17L12 22L22 17M2 12L12 17L22 12" opacity="0.6" />
                            </svg>
                        </div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {messages.length === 1 && (
                <div className="example-prompts">
                    <p className="example-title">Try asking:</p>
                    <div className="example-grid">
                        {examplePrompts.map((prompt, index) => (
                            <button
                                key={index}
                                className="example-prompt"
                                onClick={() => handleExampleClick(prompt)}
                            >
                                {prompt}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            <form className="chat-input-form" onSubmit={handleSubmit}>
                <div className="input-container">
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask me anything about your data..."
                        rows={1}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        className="send-button"
                        disabled={!input.trim() || isLoading}
                    >
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M2 3L18 10L2 17V11L13 10L2 9V3Z" />
                        </svg>
                    </button>
                </div>
            </form>
        </div>
    );
}
