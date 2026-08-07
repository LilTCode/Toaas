import { useEffect, useRef } from "react";

/**
 * Re-run `fn` every `intervalMs` so new messages arrive without a manual refresh.
 *
 * Polling rather than WebSockets: the backend runs as Vercel serverless
 * functions, which are short-lived and cannot hold an open socket.
 *
 * Skips ticks while the tab is hidden and fires once on becoming visible again,
 * so a backgrounded tab stops burning function invocations but is still current
 * the moment the user returns.
 */
export default function usePolling(fn, intervalMs = 5000) {
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    let cancelled = false;
    const run = () => {
      if (!cancelled && document.visibilityState === "visible") fnRef.current();
    };

    const id = setInterval(run, intervalMs);
    document.addEventListener("visibilitychange", run);

    return () => {
      cancelled = true;
      clearInterval(id);
      document.removeEventListener("visibilitychange", run);
    };
  }, [intervalMs]);
}
