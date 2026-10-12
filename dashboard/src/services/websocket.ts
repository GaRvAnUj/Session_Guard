type AlertCallback = (alert: any) => void;

class WebSocketClient {
  private socket: WebSocket | null = null;
  private listeners: AlertCallback[] = [];
  private reconnectInterval = 5000;
  private url: string;

  constructor() {
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || 'localhost';
    this.url = `${wsProto}//${host}:8443/ws`;
  }

  connect() {
    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log('[WebSocket] Connected to Secure Session Manager real-time alert feed.');
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach((cb) => cb(data));
        } catch (e) {
          console.error('[WebSocket] Failed to parse message', e);
        }
      };

      this.socket.onclose = () => {
        setTimeout(() => this.connect(), this.reconnectInterval);
      };

      this.socket.onerror = () => {
        this.socket?.close();
      };
    } catch (e) {
      console.warn('[WebSocket] Error creating socket connection, falling back to polling.', e);
    }
  }

  subscribe(callback: AlertCallback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback);
    };
  }
}

export const wsClient = new WebSocketClient();
