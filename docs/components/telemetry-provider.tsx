'use client';

import { usePathname, useSearchParams } from 'next/navigation';
import { useEffect, useEffectEvent } from 'react';

type ClientTelemetryEvent = {
  name: 'page_view' | 'cta_click' | 'outbound_click';
  pathname: string;
  title?: string;
  referrer?: string;
  href?: string;
  label?: string;
  sessionId: string;
};

const TELEMETRY_SESSION_KEY = 'docs-telemetry-session-id';

function getClientSessionId(): string {
  const storedValue = window.localStorage.getItem(TELEMETRY_SESSION_KEY);
  if (storedValue) {
    return storedValue;
  }

  const nextValue = crypto.randomUUID();
  window.localStorage.setItem(TELEMETRY_SESSION_KEY, nextValue);
  return nextValue;
}

export function TelemetryProvider() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const searchKey = searchParams.toString();

  const dispatchTelemetry = useEffectEvent((events: ClientTelemetryEvent[]) => {
    if (events.length === 0) {
      return;
    }

    const payload = JSON.stringify({ events });
    if (navigator.sendBeacon) {
      const accepted = navigator.sendBeacon(
        '/api/telemetry/events',
        new Blob([payload], { type: 'application/json' }),
      );
      if (accepted) {
        return;
      }
    }

    void fetch('/api/telemetry/events', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: payload,
      keepalive: true,
    });
  });

  const buildBaseEvent = useEffectEvent(
    (name: ClientTelemetryEvent['name']): ClientTelemetryEvent => ({
      name,
      pathname,
      title: document.title,
      referrer: document.referrer || undefined,
      sessionId: getClientSessionId(),
    }),
  );

  useEffect(() => {
    if (!pathname || pathname.startsWith('/admin')) {
      return;
    }

    dispatchTelemetry([buildBaseEvent('page_view')]);
  }, [buildBaseEvent, dispatchTelemetry, pathname, searchKey]);

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (!pathname || pathname.startsWith('/admin')) {
        return;
      }

      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }

      const anchor = target.closest('a');
      const button = target.closest<HTMLElement>('[data-telemetry-event]');
      const sessionId = getClientSessionId();

      if (button?.dataset.telemetryEvent === 'cta_click') {
        dispatchTelemetry([
          {
            ...buildBaseEvent('cta_click'),
            label:
              button.dataset.telemetryLabel ??
              button.textContent?.trim().slice(0, 80) ??
              'untitled_cta',
            href: anchor?.href,
            sessionId,
          },
        ]);
        return;
      }

      if (anchor) {
        try {
          const destination = new URL(anchor.href, window.location.href);
          if (destination.origin !== window.location.origin) {
            dispatchTelemetry([
              {
                ...buildBaseEvent('outbound_click'),
                href: destination.toString(),
                label: anchor.textContent?.trim().slice(0, 80) ?? destination.hostname,
                sessionId,
              },
            ]);
          }
        } catch {
          // Ignore malformed links.
        }
      }
    };

    document.addEventListener('click', handleClick, { capture: true });
    return () => {
      document.removeEventListener('click', handleClick, { capture: true });
    };
  }, [buildBaseEvent, dispatchTelemetry, pathname]);

  return null;
}