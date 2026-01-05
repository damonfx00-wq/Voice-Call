// API Service for MCP Server
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
}

export interface ChatRequest {
    message: string;
    stream?: boolean;
}

export interface ChatResponse {
    response: string;
    success: boolean;
}

export interface CSVReadRequest {
    filename: string;
    filters?: Record<string, any>;
    columns?: string[];
    limit?: number;
}

export interface CSVWriteRequest {
    filename: string;
    data: Record<string, any>[];
    mode?: 'overwrite' | 'append' | 'update';
}

export interface RAGQueryRequest {
    query: string;
    top_k?: number;
}

export interface RAGIngestRequest {
    file_paths?: string[];
}

class APIService {
    private baseURL: string;

    constructor(baseURL: string = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseURL}${endpoint}`;

        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({
                detail: response.statusText,
            }));
            throw new Error(error.detail || 'API request failed');
        }

        return response.json();
    }

    // Health Check
    async healthCheck(): Promise<{ status: string }> {
        return this.request('/health');
    }

    // Chat Endpoints
    async chat(request: ChatRequest): Promise<ChatResponse> {
        return this.request('/api/chat', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async resetChat(): Promise<{ message: string }> {
        return this.request('/api/chat/reset', {
            method: 'POST',
        });
    }

    // CSV Endpoints
    async readCSV(request: CSVReadRequest): Promise<any> {
        return this.request('/api/csv/read', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async writeCSV(request: CSVWriteRequest): Promise<any> {
        return this.request('/api/csv/write', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async listCSVFiles(): Promise<any> {
        return this.request('/api/csv/list');
    }

    // RAG Endpoints
    async ragQuery(request: RAGQueryRequest): Promise<any> {
        return this.request('/api/rag/query', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async ragIngest(request: RAGIngestRequest = {}): Promise<any> {
        return this.request('/api/rag/ingest', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async ragClear(): Promise<any> {
        return this.request('/api/rag/clear', {
            method: 'POST',
        });
    }
}

export const apiService = new APIService();
export default apiService;
