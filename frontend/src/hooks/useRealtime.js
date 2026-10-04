import { useEffect } from "react";
import { getToken } from "../api/client";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function websocketUrl(token, projectId) {
  const url = new URL(API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${url.pathname.replace(/\/$/, "")}/api/v1/realtime/ws`;
  url.searchParams.set("token", token);
  if (projectId) url.searchParams.set("project_id", projectId);
  return url.toString();
}

export function useRealtime({ projectId, onEvent, enabled = true } = {}) {
  useEffect(() => {
    if (!enabled) return undefined;
    const token = getToken();
    if (!token || typeof WebSocket === "undefined") return undefined;

    let socket;
    let reconnectTimer;
    let pingTimer;
    let stopped = false;
    let attempts = 0;

    const connect = () => {
      if (stopped) return;
      socket = new WebSocket(websocketUrl(token, projectId));

      socket.onopen = () => {
        attempts = 0;
        pingTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) socket.send("ping");
        }, 25000);
      };

      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data);
          window.dispatchEvent(new CustomEvent("sprintnova:realtime", { detail: event }));
          onEvent?.(event);
        } catch {
          // Ignore malformed realtime messages; REST remains authoritative.
        }
      };

      socket.onclose = () => {
        window.clearInterval(pingTimer);
        if (stopped) return;
        const delay = Math.min(30000, 1000 * 2 ** attempts++);
        reconnectTimer = window.setTimeout(connect, delay);
      };

      socket.onerror = () => socket?.close();
    };

    connect();
    return () => {
      stopped = true;
      window.clearTimeout(reconnectTimer);
      window.clearInterval(pingTimer);
      socket?.close();
    };
  }, [projectId, enabled, onEvent]);
}
