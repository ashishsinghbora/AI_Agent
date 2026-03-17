import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useResearch } from '../hooks/useResearch';
import { useSessionHistory } from '../hooks/useSessionHistory';
import { useResourceControl } from '../hooks/useResourceControl';

const ResearchContext = createContext(null);

/**
 * ResearchProvider — top-level state provider for the Research Agent UI.
 *
 * Children can call `useResearchContext()` to access all shared state.
 */
export function ResearchProvider({ children }) {
  const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  // System stats
  const [systemStats, setSystemStats] = useState({
    cpu_percent: 0,
    memory: { percent: 0, used: 0, total: 0 },
  });
  const [uploadItems, setUploadItems] = useState([]);
  const [theme, setTheme] = useState('dark'); // Add theme state
  const systemStatsIntervalRef = useRef(null);

  // Resource controls
  const resourceControl = useResourceControl();

  // Session history
  const sessionHistory = useSessionHistory(apiBaseUrl);
  const { registerNewSession } = sessionHistory;

  // Active research
  const research = useResearch(apiBaseUrl);

  // Sync new session_id from completed research into session history
  const { chatMessages } = research;
  useEffect(() => {
    if (chatMessages.length === 0) return;
    const last = chatMessages[chatMessages.length - 1];
    if (last?.session_id) {
      registerNewSession(last.session_id);
    }
  }, [chatMessages, registerNewSession]);

  // Poll system stats
  useEffect(() => {
    const fetchSystemStats = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/system-stats`);
        const data = await response.json();
        setSystemStats(data);
      } catch (err) {
        console.error('Error fetching system stats:', err);
      }
    };
    fetchSystemStats();
    systemStatsIntervalRef.current = setInterval(fetchSystemStats, 1000);
    return () => {
      if (systemStatsIntervalRef.current) clearInterval(systemStatsIntervalRef.current);
    };
  }, [apiBaseUrl]);

  // File upload
  const handleFileUpload = async (file) => {
    if (!file) return;
    const uploadId = `${file.name}-${Date.now()}`;
    setUploadItems((prev) => [
      ...prev,
      { id: uploadId, name: file.name, status: 'embedding', detail: '' },
    ]);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await fetch(`${apiBaseUrl}/api/ingest`, { method: 'POST', body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Upload failed');
      setUploadItems((prev) =>
        prev.map((item) =>
          item.id === uploadId ? { ...item, status: 'embedded', detail: `${data.chars || 0} chars` } : item
        )
      );
    } catch (error) {
      setUploadItems((prev) =>
        prev.map((item) =>
          item.id === uploadId ? { ...item, status: 'failed', detail: error.message } : item
        )
      );
    }
  };

  const handleUploadFiles = (files) => {
    Array.from(files || []).forEach((file) => handleFileUpload(file));
  };

  // Export
  const handleExport = async (format = 'markdown') => {
    const { currentSessionId } = sessionHistory;
    if (!currentSessionId) return;
    try {
      const response = await fetch(`${apiBaseUrl}/api/export/${currentSessionId}?format=${format}`, {
        method: 'POST',
      });
      const data = await response.json();
      alert(`Research exported to: ${data.path}`);
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  // Wrap handleResearch to inject resource options
  const handleResearch = (query, overrides = {}) => {
    const savedGeminiKey =
      typeof window !== 'undefined'
        ? (window.localStorage.getItem('researchAgent.geminiApiKey') || '').trim()
        : '';

    const options = {
      ...resourceControl.buildRequestOptions(),
      ...overrides,
      geminiApiKey: overrides.geminiApiKey ?? savedGeminiKey,
    };
    research.handleResearch(query, options);
  };

  // New session helper that also resets research state
  const handleNewSession = () => {
    sessionHistory.setCurrentSessionId(null);
    research.startNewSession();
    setUploadItems([]);
  };

  // Theme toggle
  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const value = {
    apiBaseUrl,
    systemStats,
    uploadItems,
    theme,
    toggleTheme,
    handleUploadFiles,
    handleExport,
    handleResearch,
    handleNewSession,
    ...resourceControl,
    ...sessionHistory,
    ...research,
  };

  return <ResearchContext.Provider value={value}>{children}</ResearchContext.Provider>;
}

/** Convenience hook — throw if used outside provider. */
export function useResearchContext() {
  const ctx = useContext(ResearchContext);
  if (!ctx) throw new Error('useResearchContext must be used inside <ResearchProvider>');
  return ctx;
}
