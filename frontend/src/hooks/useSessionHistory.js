import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * useSessionHistory — manages session list loaded from the backend database.
 *
 * @param {string} apiBaseUrl
 * @returns session state + handlers
 */
export function useSessionHistory(apiBaseUrl) {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const currentSessionIdRef = useRef(currentSessionId);

  // Keep ref in sync with state to avoid stale closures in fetchSessions
  useEffect(() => {
    currentSessionIdRef.current = currentSessionId;
  }, [currentSessionId]);

  const fetchSessions = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/sessions`);
      const data = await response.json();
      const list = data.sessions || [];
      setSessions(list);
      if (list.length > 0 && !currentSessionIdRef.current) {
        setCurrentSessionId(list[0].session_id);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  }, [apiBaseUrl]);

  // Load sessions on mount
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleSelectSession = useCallback((sessionId) => {
    setCurrentSessionId(sessionId);
  }, []);

  const handleDeleteSession = useCallback(
    async (sessionId, e) => {
      if (e) e.stopPropagation();
      try {
        await fetch(`${apiBaseUrl}/api/sessions/${sessionId}`, { method: 'DELETE' });
        setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
        if (currentSessionId === sessionId) {
          setCurrentSessionId(null);
        }
      } catch (error) {
        console.error('Error deleting session:', error);
      }
    },
    [apiBaseUrl, currentSessionId]
  );

  const registerNewSession = useCallback((sessionId) => {
    setCurrentSessionId(sessionId);
    // Re-fetch so the new session appears in the sidebar
    fetchSessions();
  }, [fetchSessions]);

  return {
    sessions,
    currentSessionId,
    setCurrentSessionId,
    handleSelectSession,
    handleDeleteSession,
    registerNewSession,
    fetchSessions,
  };
}
