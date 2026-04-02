/**
 * useSSE — subscribes to the AutoTriage SSE stream at GET /api/v1/tickets/stream.
 *
 * Browser EventSource doesn't support custom headers, so we use fetch + ReadableStream
 * to send the required X-Tenant-Id header.
 *
 * Dispatches `onTicketTriaged` whenever the backend emits a `ticket_triaged` event.
 * Automatically reconnects after errors with exponential backoff (max 30 s).
 */

import { useEffect, useRef } from 'react';
import { getSSEUrl, TENANT_ID } from '@/services/api';

type TicketTriagedPayload = Record<string, unknown>;

interface UseSSEOptions {
  onTicketTriaged: (payload: TicketTriagedPayload) => void;
  enabled?: boolean;
}

export function useSSE({ onTicketTriaged, enabled = true }: UseSSEOptions): void {
  const onTicketTriagedRef = useRef(onTicketTriaged);
  onTicketTriagedRef.current = onTicketTriaged;

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;
    let retryDelay = 1000;

    async function connect() {
      while (!cancelled) {
        try {
          const res = await fetch(getSSEUrl(), {
            headers: {
              'X-Tenant-Id': TENANT_ID,
              Accept: 'text/event-stream',
            },
          });

          if (!res.ok || !res.body) {
            throw new Error(`SSE ${res.status}`);
          }

          retryDelay = 1000; // reset on successful connect

          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (!cancelled) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() ?? '';

            let eventType = '';
            let dataLine = '';

            for (const line of lines) {
              if (line.startsWith('event:')) {
                eventType = line.slice(6).trim();
              } else if (line.startsWith('data:')) {
                dataLine = line.slice(5).trim();
              } else if (line === '' && dataLine) {
                if (eventType === 'ticket_triaged' && dataLine !== '{}') {
                  try {
                    const payload = JSON.parse(dataLine) as TicketTriagedPayload;
                    onTicketTriagedRef.current(payload);
                  } catch {
                    // malformed JSON — ignore
                  }
                }
                eventType = '';
                dataLine = '';
              }
            }
          }
        } catch (err) {
          if (cancelled) break;
          console.warn(`SSE disconnected, retrying in ${retryDelay}ms`, err);
        }

        if (!cancelled) {
          await new Promise(r => setTimeout(r, retryDelay));
          retryDelay = Math.min(retryDelay * 2, 30_000);
        }
      }
    }

    connect();

    return () => {
      cancelled = true;
    };
  }, [enabled]);
}
