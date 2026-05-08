"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Alert } from "@/lib/types";

// SSE proxy through nginx on the same host to avoid CORS issues
const SSE_URL = "/events/stream";

interface SSEHookResult {
  lastAlert: Alert | null;
  online: boolean;
}

export function useSSE(): SSEHookResult {
  const [lastAlert, setLastAlert] = useState<Alert | null>(null);
  const [online, setOnline] = useState(true);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    try {
      const es = new EventSource(SSE_URL);
      eventSourceRef.current = es;

      es.onopen = () => setOnline(true);

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "alert") {
            setLastAlert(data.payload);
          }
        } catch {
          // parse error, ignore
        }
      };

      es.onerror = () => {
        setOnline(false);
        es.close();
        // Reconnect after delay
        setTimeout(connect, 5000);
      };
    } catch {
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      eventSourceRef.current?.close();
    };
  }, [connect]);

  return { lastAlert, online };
}
