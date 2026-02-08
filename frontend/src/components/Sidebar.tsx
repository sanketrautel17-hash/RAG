import { useState, useRef } from 'react';
import { ingestDocument, ingestText, ingestWeb } from '../api/client';
import type { IngestResponse } from '../types';
import './Sidebar.css';

type IngestTab = 'document' | 'text' | 'web';

interface SidebarProps {
    isOpen: boolean;
    onToggle: () => void;
    onIngestSuccess: (response: IngestResponse) => void;
}

export function Sidebar({ isOpen, onToggle, onIngestSuccess }: SidebarProps) {
    const [activeTab, setActiveTab] = useState<IngestTab>('document');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Document tab
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Text tab
    const [textContent, setTextContent] = useState('');
    const [textTitle, setTextTitle] = useState('');

    // Web tab
    const [webUrl, setWebUrl] = useState('');

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            setError(null);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file) {
            setSelectedFile(file);
            setError(null);
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
    };

    const clearMessages = () => {
        setError(null);
        setSuccess(null);
    };

    const handleDocumentIngest = async () => {
        if (!selectedFile) return;

        setIsLoading(true);
        clearMessages();

        try {
            const response = await ingestDocument(selectedFile);
            setSuccess(`Successfully ingested "${selectedFile.name}" - ${response.chunks_created} chunks created`);
            setSelectedFile(null);
            if (fileInputRef.current) fileInputRef.current.value = '';
            onIngestSuccess(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to ingest document');
        } finally {
            setIsLoading(false);
        }
    };

    const handleTextIngest = async () => {
        if (!textContent.trim()) return;

        setIsLoading(true);
        clearMessages();

        try {
            const response = await ingestText({
                text: textContent,
                title: textTitle || undefined,
            });
            setSuccess(`Successfully ingested text - ${response.chunks_created} chunks created`);
            setTextContent('');
            setTextTitle('');
            onIngestSuccess(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to ingest text');
        } finally {
            setIsLoading(false);
        }
    };

    const handleWebIngest = async () => {
        if (!webUrl.trim()) return;

        setIsLoading(true);
        clearMessages();

        try {
            const response = await ingestWeb({ url: webUrl });
            setSuccess(`Successfully ingested web page - ${response.chunks_created} chunks created`);
            setWebUrl('');
            onIngestSuccess(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to ingest web page');
        } finally {
            setIsLoading(false);
        }
    };

    const getFileIcon = (filename: string) => {
        const ext = filename.split('.').pop()?.toLowerCase();
        switch (ext) {
            case 'pdf':
                return '📕';
            case 'doc':
            case 'docx':
                return '📘';
            case 'txt':
                return '📄';
            case 'md':
                return '📝';
            default:
                return '📎';
        }
    };

    return (
        <>
            {/* Toggle Button */}
            <button
                className={`sidebar-toggle ${isOpen ? 'open' : ''}`}
                onClick={onToggle}
                aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
            >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    {isOpen ? (
                        <path d="M15 18l-6-6 6-6" />
                    ) : (
                        <path d="M9 18l6-6-6-6" />
                    )}
                </svg>
            </button>

            {/* Sidebar */}
            <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                            <polyline points="17,8 12,3 7,8" />
                            <line x1="12" y1="3" x2="12" y2="15" />
                        </svg>
                        Add Content
                    </h2>
                </div>

                {/* Tabs */}
                <div className="ingest-tabs">
                    {(['document', 'text', 'web'] as IngestTab[]).map((tab) => (
                        <button
                            key={tab}
                            className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
                            onClick={() => { setActiveTab(tab); clearMessages(); }}
                        >
                            {tab === 'document' && '📄'}
                            {tab === 'text' && '📝'}
                            {tab === 'web' && '🌐'}
                            <span>{tab.charAt(0).toUpperCase() + tab.slice(1)}</span>
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="tab-content">
                    {/* Document Tab */}
                    {activeTab === 'document' && (
                        <div className="ingest-form animate-fade-in">
                            <div
                                className={`drop-zone ${selectedFile ? 'has-file' : ''}`}
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".pdf,.doc,.docx,.txt,.md"
                                    onChange={handleFileSelect}
                                    hidden
                                />
                                {selectedFile ? (
                                    <div className="selected-file">
                                        <span className="file-icon">{getFileIcon(selectedFile.name)}</span>
                                        <span className="file-name">{selectedFile.name}</span>
                                        <span className="file-size">
                                            {(selectedFile.size / 1024).toFixed(1)} KB
                                        </span>
                                    </div>
                                ) : (
                                    <>
                                        <div className="drop-icon">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                                <path d="M7 18a4.6 4.4 0 01-.9-8.7 5.7 5.7 0 0110.9-1.2A4.6 4.4 0 0118 18H7z" />
                                                <polyline points="15,11 12,8 9,11" />
                                                <line x1="12" y1="8" x2="12" y2="16" />
                                            </svg>
                                        </div>
                                        <p className="drop-text">
                                            Drag & drop or <span>browse</span>
                                        </p>
                                        <p className="drop-hint">PDF, DOCX, TXT, MD (max 10MB)</p>
                                    </>
                                )}
                            </div>
                            <button
                                className="ingest-btn"
                                onClick={handleDocumentIngest}
                                disabled={!selectedFile || isLoading}
                            >
                                {isLoading ? (
                                    <>
                                        <span className="spinner"></span>
                                        Processing...
                                    </>
                                ) : (
                                    <>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                                            <polyline points="17,8 12,3 7,8" />
                                            <line x1="12" y1="3" x2="12" y2="15" />
                                        </svg>
                                        Upload Document
                                    </>
                                )}
                            </button>
                        </div>
                    )}

                    {/* Text Tab */}
                    {activeTab === 'text' && (
                        <div className="ingest-form animate-fade-in">
                            <div className="form-group">
                                <label htmlFor="text-title">Title (optional)</label>
                                <input
                                    id="text-title"
                                    type="text"
                                    value={textTitle}
                                    onChange={(e) => setTextTitle(e.target.value)}
                                    placeholder="Enter a title..."
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="text-content">Content</label>
                                <textarea
                                    id="text-content"
                                    value={textContent}
                                    onChange={(e) => setTextContent(e.target.value)}
                                    placeholder="Paste or type your text content here..."
                                    rows={8}
                                />
                                <span className="char-count">
                                    {textContent.length.toLocaleString()} characters
                                </span>
                            </div>
                            <button
                                className="ingest-btn"
                                onClick={handleTextIngest}
                                disabled={!textContent.trim() || isLoading}
                            >
                                {isLoading ? (
                                    <>
                                        <span className="spinner"></span>
                                        Processing...
                                    </>
                                ) : (
                                    <>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M12 5v14M5 12h14" />
                                        </svg>
                                        Add Text
                                    </>
                                )}
                            </button>
                        </div>
                    )}

                    {/* Web Tab */}
                    {activeTab === 'web' && (
                        <div className="ingest-form animate-fade-in">
                            <div className="form-group">
                                <label htmlFor="web-url">Web URL</label>
                                <div className="url-input-wrapper">
                                    <span className="url-prefix">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <circle cx="12" cy="12" r="10" />
                                            <line x1="2" y1="12" x2="22" y2="12" />
                                            <path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
                                        </svg>
                                    </span>
                                    <input
                                        id="web-url"
                                        type="url"
                                        value={webUrl}
                                        onChange={(e) => setWebUrl(e.target.value)}
                                        placeholder="https://example.com/article"
                                    />
                                </div>
                                <p className="form-hint">
                                    Enter a URL to scrape and add its content to your knowledge base.
                                </p>
                            </div>
                            <button
                                className="ingest-btn"
                                onClick={handleWebIngest}
                                disabled={!webUrl.trim() || isLoading}
                            >
                                {isLoading ? (
                                    <>
                                        <span className="spinner"></span>
                                        Scraping...
                                    </>
                                ) : (
                                    <>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                                        </svg>
                                        Import from Web
                                    </>
                                )}
                            </button>
                        </div>
                    )}
                </div>

                {/* Messages */}
                {error && (
                    <div className="message-alert error animate-slide-up">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="15" y1="9" x2="9" y2="15" />
                            <line x1="9" y1="9" x2="15" y2="15" />
                        </svg>
                        <p>{error}</p>
                        <button onClick={() => setError(null)}>×</button>
                    </div>
                )}
                {success && (
                    <div className="message-alert success animate-slide-up">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                            <polyline points="22,4 12,14.01 9,11.01" />
                        </svg>
                        <p>{success}</p>
                        <button onClick={() => setSuccess(null)}>×</button>
                    </div>
                )}

                {/* Info */}
                <div className="sidebar-info">
                    <h4>Supported Formats</h4>
                    <ul>
                        <li>📕 PDF documents</li>
                        <li>📘 Word documents (.doc, .docx)</li>
                        <li>📄 Text files (.txt)</li>
                        <li>📝 Markdown files (.md)</li>
                        <li>🌐 Web pages (HTML)</li>
                    </ul>
                </div>
            </aside>

            {/* Overlay for mobile */}
            {isOpen && <div className="sidebar-overlay" onClick={onToggle} />}
        </>
    );
}
