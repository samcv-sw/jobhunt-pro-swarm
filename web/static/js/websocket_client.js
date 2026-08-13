/**
 * JobHunt Pro SaaS — Real-Time WebSocket Telemetry Client
 * Handles auto-reconnect, status pulse updates, and live event handling.
 */

(function () {
  'use strict';

  class JobHuntWebSocket {
    constructor() {
      this.ws = null;
      this.reconnectDelay = 1000;
      this.maxReconnectDelay = 10000;
      this.listeners = new Set();
      this.init();
    }

    init() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/live-feed`;

      try {
        this.ws = new WebSocket(wsUrl);
      } catch (err) {
        console.warn('[WebSocket] Init failed, retrying...', err);
        this.scheduleReconnect();
        return;
      }

      this.ws.onopen = () => {
        console.log('[WebSocket] Real-time event bus connected.');
        this.reconnectDelay = 1000;
        this.updateBadge('CONNECTED', 'bp-green');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.notifyListeners(data);
        } catch (e) {
          // Plain text fallback
          this.notifyListeners({ type: 'text', payload: event.data });
        }
      };

      this.ws.onclose = () => {
        this.updateBadge('DISCONNECTED — RECONNECTING', 'bp-red');
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.error('[WebSocket] Socket error:', err);
        if (this.ws) this.ws.close();
      };
    }

    scheduleReconnect() {
      setTimeout(() => {
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
        this.init();
      }, this.reconnectDelay);
    }

    updateBadge(text, className) {
      const badge = document.getElementById('ws-status-badge');
      if (badge) {
        badge.innerText = text;
        badge.className = `badge-pill ${className}`;
      }
    }

    subscribe(callback) {
      this.listeners.add(callback);
      return () => this.listeners.delete(callback);
    }

    notifyListeners(data) {
      this.listeners.forEach((callback) => {
        try {
          callback(data);
        } catch (err) {
          console.error('[WebSocket] Listener error:', err);
        }
      });
    }

    send(data) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(typeof data === 'string' ? data : JSON.stringify(data));
      }
    }
  }

  // Expose globally on window
  window.JobHuntWS = new JobHuntWebSocket();
})();
