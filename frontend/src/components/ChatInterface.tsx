import { useState, useRef, useEffect } from 'react';
import type { Message, ChatMode, SourceChunk } from '../types';
import { sendChatMessage } from '../api/client';
import './ChatInterface.css';

interface ChatInterfaceProps {
    conversationId: string | null;
    onNewConversation: () => void;
    onConversationChange: (id: string) => void;
}

export function ChatInterface({
    conversationId,
    onNewConversation,
    onConversationChange,
}: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [chatMode, setChatMode] = useState<ChatMode>('auto');
    const [showSettings, setShowSettings] = useState(false);
    const [temperature, setTemperature] = useState(0.7);
    const [topK, setTopK] = useState(5);
    const [expandedSources, setExpandedSources] = useState<string | null>(null);

    const messagesEndRef = useRef<HTMLDivElement | null>(null);
    const inputRef = useRef<HTMLTextAreaElement | null>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userMessage: Message = {
            id: `msg_${Date.now()}`,
            role: 'user',
            content: inputValue.trim(),
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        // Add loading message
        const loadingMessage: Message = {
            id: `loading_${Date.now()}`,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isLoading: true,
        };
        setMessages(prev => [...prev, loadingMessage]);

        try {
            const response = await sendChatMessage({
                message: userMessage.content,
                conversation_id: conversationId || undefined,
                mode: chatMode,
                temperature,
                top_k: topK,
            });

            // Update conversation ID if new
            if (!conversationId && response.conversation_id) {
                onConversationChange(response.conversation_id);
            }

            // Replace loading message with actual response
            const assistantMessage: Message = {
                id: `msg_${Date.now()}`,
                role: 'assistant',
                content: response.message,
                sources: response.sources,
                timestamp: new Date(),
            };

            setMessages(prev =>
                prev.filter(m => !m.isLoading).concat(assistantMessage)
            );
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage: Message = {
                id: `error_${Date.now()}`,
                role: 'assistant',
                content: `Sorry, an error occurred: ${error instanceof Error ? error.message : 'Unknown error'}`,
                timestamp: new Date(),
            };
            setMessages(prev =>
                prev.filter(m => !m.isLoading).concat(errorMessage)
            );
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const toggleSources = (messageId: string) => {
        setExpandedSources(expandedSources === messageId ? null : messageId);
    };

    const handleNewChat = () => {
        setMessages([]);
        onNewConversation();
    };

    return (
        <div className="chat-interface">
            {/* Header */}
            <header className="chat-header">
                <div className="header-left">
                    <div className="logo">
                        <div className="logo-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                                <path d="M2 17l10 5 10-5" />
                                <path d="M2 12l10 5 10-5" />
                            </svg>
                        </div>
                        <span className="logo-text">RAG<span className="logo-highlight">Chat</span></span>
                    </div>
                </div>
                <div className="header-center">
                    <div className="mode-selector">
                        {(['auto', 'rag', 'direct'] as ChatMode[]).map((mode) => (
                            <button
                                key={mode}
                                className={`mode-btn ${chatMode === mode ? 'active' : ''}`}
                                onClick={() => setChatMode(mode)}
                            >
                                {mode === 'auto' && '✨ Auto'}
                                {mode === 'rag' && '📚 RAG'}
                                {mode === 'direct' && '💬 Direct'}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="header-right">
                    <button
                        className="icon-btn"
                        onClick={() => setShowSettings(!showSettings)}
                        title="Settings"
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="3" />
                            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
                        </svg>
                    </button>
                    <button className="new-chat-btn" onClick={handleNewChat}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 5v14M5 12h14" />
                        </svg>
                        New Chat
                    </button>
                </div>
            </header>

            {/* Settings Panel */}
            {showSettings && (
                <div className="settings-panel animate-slide-down">
                    <div className="setting-item">
                        <label>Temperature: {temperature.toFixed(1)}</label>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={temperature}
                            onChange={(e) => setTemperature(parseFloat(e.target.value))}
                        />
                        <div className="setting-hint">
                            <span>Focused</span>
                            <span>Creative</span>
                        </div>
                    </div>
                    <div className="setting-item">
                        <label>Context Chunks: {topK}</label>
                        <input
                            type="range"
                            min="1"
                            max="10"
                            step="1"
                            value={topK}
                            onChange={(e) => setTopK(parseInt(e.target.value))}
                        />
                        <div className="setting-hint">
                            <span>Few</span>
                            <span>Many</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Messages */}
            <main className="messages-container">
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z" />
                            </svg>
                        </div>
                        <h2>Chat with Your Knowledge Base</h2>
                        <p>Ask questions about your documents and get AI-powered answers with sources.</p>
                        <div className="example-questions">
                            <span className="examples-label">Try asking:</span>
                            <div className="examples-grid">
                                {[
                                    'What are the main topics in my documents?',
                                    'Summarize the key findings',
                                    'Explain the concepts in detail',
                                ].map((q, i) => (
                                    <button
                                        key={i}
                                        className="example-btn"
                                        onClick={() => setInputValue(q)}
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="messages-list">
                        {messages.map((message) => (
                            <div
                                key={message.id}
                                className={`message ${message.role} ${message.isLoading ? 'loading' : ''} animate-slide-up`}
                            >
                                <div className="message-avatar">
                                    {message.role === 'user' ? (
                                        <svg viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                                        </svg>
                                    ) : (
                                        <svg viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                                        </svg>
                                    )}
                                </div>
                                <div className="message-content">
                                    {message.isLoading ? (
                                        <div className="typing-indicator">
                                            <span></span>
                                            <span></span>
                                            <span></span>
                                        </div>
                                    ) : (
                                        <>
                                            <div className="message-text">{message.content}</div>
                                            {message.sources && message.sources.length > 0 && (
                                                <div className="sources-section">
                                                    <button
                                                        className="sources-toggle"
                                                        onClick={() => toggleSources(message.id)}
                                                    >
                                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                            <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                                                        </svg>
                                                        {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
                                                        <svg
                                                            viewBox="0 0 24 24"
                                                            fill="none"
                                                            stroke="currentColor"
                                                            strokeWidth="2"
                                                            className={`chevron ${expandedSources === message.id ? 'expanded' : ''}`}
                                                        >
                                                            <path d="M6 9l6 6 6-6" />
                                                        </svg>
                                                    </button>
                                                    {expandedSources === message.id && (
                                                        <div className="sources-list animate-slide-down">
                                                            {message.sources.map((source: SourceChunk, index: number) => (
                                                                <div key={source.chunk_id} className="source-item">
                                                                    <div className="source-header">
                                                                        <span className="source-number">#{index + 1}</span>
                                                                        <span className="source-score">
                                                                            {(source.score * 100).toFixed(0)}% match
                                                                        </span>
                                                                    </div>
                                                                    <div className="source-text">{source.text}</div>
                                                                    {source.metadata && Object.keys(source.metadata).length > 0 && (
                                                                        <div className="source-meta">
                                                                            {typeof source.metadata.filename === 'string' && (
                                                                                <span className="meta-tag">
                                                                                    📄 {source.metadata.filename}
                                                                                </span>
                                                                            )}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </main>

            {/* Input */}
            <footer className="input-container">
                <form onSubmit={handleSubmit} className="input-form">
                    <div className="input-wrapper">
                        <textarea
                            ref={inputRef}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about your documents..."
                            rows={1}
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            className="send-btn"
                            disabled={!inputValue.trim() || isLoading}
                        >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                            </svg>
                        </button>
                    </div>
                    <p className="input-hint">
                        Press Enter to send, Shift+Enter for new line
                    </p>
                </form>
            </footer>
        </div>
    );
}
