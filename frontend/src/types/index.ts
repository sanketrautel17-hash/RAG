// Chat Types
export type ChatMode = 'rag' | 'direct' | 'auto';

export interface ChatRequest {
    message: string;
    conversation_id?: string;
    mode?: ChatMode;
    top_k?: number;
    min_score?: number;
    temperature?: number;
    document_ids?: string[];
}

export interface SourceChunk {
    chunk_id: string;
    document_id: string;
    text: string;
    score: number;
    metadata: Record<string, unknown>;
}

export interface ChatResponse {
    success: boolean;
    message: string;
    conversation_id: string;
    mode_used: ChatMode;
    sources: SourceChunk[];
    context_used: boolean;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: SourceChunk[];
    timestamp: Date;
    isLoading?: boolean;
}

export interface Conversation {
    id: string;
    messages: Message[];
    createdAt: Date;
    updatedAt: Date;
}

// Search Types
export interface SearchRequest {
    query: string;
    top_k?: number;
    document_ids?: string[];
    min_score?: number;
}

export interface SearchResult {
    chunk_id: string;
    document_id: string;
    text: string;
    score: number;
    metadata: Record<string, unknown>;
}

export interface SearchResponse {
    success: boolean;
    query: string;
    total_results: number;
    results: SearchResult[];
}

// Ingest Types
export type SourceType = 'document' | 'text' | 'web';

export interface TextIngestRequest {
    text: string;
    title?: string;
    metadata?: Record<string, unknown>;
}

export interface WebIngestRequest {
    url: string;
    metadata?: Record<string, unknown>;
}

export interface ChunkInfo {
    chunk_id: string;
    text_preview: string;
    char_count: number;
}

export interface IngestResponse {
    success: boolean;
    message: string;
    source_type: SourceType;
    document_id: string;
    filename?: string;
    total_characters: number;
    chunks_created: number;
    chunks?: ChunkInfo[];
}

// Health Types
export interface HealthStatus {
    status: 'healthy' | 'degraded';
    services: {
        api: string;
        database: string;
        embedding: string;
        llm: string;
    };
}

// Document Types
export interface Document {
    id: string;
    filename?: string;
    source_type: SourceType;
    created_at: string;
    metadata: Record<string, unknown>;
}
