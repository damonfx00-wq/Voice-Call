// WebSocket service for real-time voice communication
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/voice';

export class VoiceWebSocketService {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;

    onConnected?: () => void;
    onDisconnected?: () => void;
    onInterim?: (transcript: string) => void;
    onResponseStart?: () => void;
    onResponseChunk?: (chunk: string, fullResponse: string) => void;
    onResponseEnd?: (fullResponse: string) => void;
    onError?: (error: string) => void;

    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(WS_URL);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.reconnectAttempts = 0;
                    this.onConnected?.();
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.onError?.('WebSocket connection error');
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.onDisconnected?.();
                    this.attemptReconnect();
                };
            } catch (error) {
                reject(error);
            }
        });
    }

    private handleMessage(data: any) {
        switch (data.type) {
            case 'connected':
                console.log('Connected to voice assistant:', data.connection_id);
                break;

            case 'interim':
                this.onInterim?.(data.transcript);
                break;

            case 'response_start':
                this.onResponseStart?.();
                break;

            case 'response_chunk':
                this.onResponseChunk?.(data.content, data.full_response);
                break;

            case 'response_end':
                this.onResponseEnd?.(data.full_response);
                break;

            case 'interrupted':
                console.log('AI speech interrupted');
                break;

            case 'error':
                this.onError?.(data.message);
                break;

            case 'pong':
                // Keep-alive response
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    sendTranscript(message: string, isFinal: boolean = false) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'transcript',
                message,
                is_final: isFinal
            }));
        }
    }

    sendInterrupt() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'interrupt'
            }));
        }
    }

    private attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

            setTimeout(() => {
                this.connect().catch(console.error);
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.onError?.('Failed to reconnect to server');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected(): boolean {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }
}

export const voiceWS = new VoiceWebSocketService();
