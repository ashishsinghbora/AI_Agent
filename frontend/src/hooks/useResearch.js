import { useState, useCallback } from 'react';

/**
 * useResearch — manages the active research session state and API streaming.
 *
 * @param {string} apiBaseUrl
 * @returns research state + handlers
 */
export function useResearch(apiBaseUrl) {
  const [isResearching, setIsResearching] = useState(false);
  const [researchProgress, setResearchProgress] = useState(0);
  const [thinkingContent, setThinkingContent] = useState('');
  const [responseContent, setResponseContent] = useState('');
  const [sources, setSources] = useState([]);
  const [crawlEvents, setCrawlEvents] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  const [conflictAlert, setConflictAlert] = useState(null);
  const [knowledgeGraph, setKnowledgeGraph] = useState(null);
  const [activeQuery, setActiveQuery] = useState('');
  const [chatMessages, setChatMessages] = useState([]);

  const clearResearchState = useCallback(() => {
    setThinkingContent('');
    setResponseContent('');
    setSources([]);
    setCrawlEvents([]);
    setSelectedSource(null);
    setConflictAlert(null);
    setKnowledgeGraph(null);
    setActiveQuery('');
  }, []);

  const startNewSession = useCallback(() => {
    clearResearchState();
    setChatMessages([]);
  }, [clearResearchState]);

  const handleResearch = useCallback(
    async (query, options = {}) => {
      if (!query.trim()) return;

      const {
        maxSources = 5,
        cpuBudget = 80,
        outputMode = 'quick',
        speedMode = 'fast',
        useThinking = true,
        thinkingChars = 180,
        preferredDomains = [],
      } = options;

      const userMessage = { role: 'user', content: query, timestamp: new Date() };
      const requestHistory = [...chatMessages, userMessage];

      setIsResearching(true);
      setResearchProgress(0);
      setThinkingContent('');
      setResponseContent('');
      setActiveQuery(query);
      setCrawlEvents([]);
      setSelectedSource(null);
      setConflictAlert(null);
      setKnowledgeGraph(null);
      setChatMessages(requestHistory);

      let accumulatedThinking = '';
      let accumulatedResponse = '';
      let researchCompleted = false;
      let latestSources = [];

      const processEvent = (event) => {
        if (event.type === 'thinking') {
          accumulatedThinking += event.content || '';
          setThinkingContent(accumulatedThinking);
        } else if (event.type === 'response') {
          accumulatedResponse += event.content || '';
          setResponseContent(accumulatedResponse);
        } else if (event.type === 'sources_found') {
          latestSources = event.sources || [];
          setSources(latestSources);
          setResearchProgress(event.progress || 30);
        } else if (event.type === 'crawl_update') {
          setCrawlEvents((prev) => [...prev, event]);
        } else if (event.type === 'conflict_alert') {
          setConflictAlert(event);
        } else if (event.type === 'concept_graph') {
          setKnowledgeGraph(event.graph || null);
        } else if (event.type === 'status') {
          setResearchProgress(event.progress || 50);
        } else if (event.type === 'research_complete') {
          researchCompleted = true;
          setResearchProgress(100);
          if (event.sources) {
            latestSources = event.sources;
            setSources(event.sources);
          }
          const finalResponse = accumulatedResponse || 'No response generated.';
          setChatMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: finalResponse,
              timestamp: new Date(),
              thinking: accumulatedThinking,
              sources: latestSources,
              session_id: event.session_id,
            },
          ]);
        } else if (event.type === 'error') {
          console.error('Research error:', event.error);
          setChatMessages((prev) => [
            ...prev,
            { role: 'system', content: `Error: ${event.error}`, timestamp: new Date() },
          ]);
        }
      };

      try {
        const response = await fetch(`${apiBaseUrl}/api/research`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query,
            chat_history: requestHistory,
            use_thinking_model: useThinking,
            max_sources: maxSources,
            speed_mode: speedMode,
            output_mode: outputMode,
            thinking_chars: thinkingChars,
            cpu_budget_percent: cpuBudget,
            preferred_domains: preferredDomains,
          }),
        });

        if (!response.ok || !response.body) {
          throw new Error(`Research request failed (${response.status})`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            buffer += decoder.decode();
            break;
          }
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop();
          for (const line of lines) {
            if (line.trim()) {
              try {
                processEvent(JSON.parse(line));
              } catch (err) {
                console.error('Error parsing event:', err);
              }
            }
          }
        }

        if (buffer.trim()) {
          try {
            processEvent(JSON.parse(buffer));
          } catch (err) {
            console.error('Error parsing final event:', err);
          }
        }

        if (!researchCompleted && accumulatedResponse.trim()) {
          setChatMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: accumulatedResponse,
              timestamp: new Date(),
              thinking: accumulatedThinking,
              sources: latestSources,
            },
          ]);
        }
      } catch (error) {
        console.error('Error during research:', error);
        setChatMessages((prev) => [
          ...prev,
          { role: 'system', content: `Error: ${error.message}`, timestamp: new Date() },
        ]);
      } finally {
        setIsResearching(false);
        setResearchProgress(0);
      }
    },
    [apiBaseUrl, chatMessages]
  );

  const handleConflictDecision = useCallback(
    (action) => {
      if (!activeQuery) {
        setConflictAlert(null);
        return;
      }
      if (action === 'third_source') {
        handleResearch(activeQuery, { maxSources: 8, speedMode: 'deep' });
      } else if (action === 'prefer_official') {
        handleResearch(activeQuery, {
          maxSources: 5,
          speedMode: 'balanced',
          preferredDomains: ['.gov', '.edu', 'wikipedia.org', 'ibm.com', 'microsoft.com', 'oracle.com'],
        });
      }
      setConflictAlert(null);
    },
    [activeQuery, handleResearch]
  );

  return {
    isResearching,
    researchProgress,
    thinkingContent,
    responseContent,
    sources,
    crawlEvents,
    selectedSource,
    conflictAlert,
    knowledgeGraph,
    activeQuery,
    chatMessages,
    setChatMessages,
    setSelectedSource,
    setConflictAlert,
    handleResearch,
    handleConflictDecision,
    startNewSession,
    clearResearchState,
  };
}
