import React, { useState, useEffect, useRef } from 'react';
import LeftSidebar from './components/LeftSidebar';
import CenterPanel from './components/CenterPanel';
import RightSidebar from './components/RightSidebar';
import SmartChildAvatar from './components/SmartChildAvatar';

function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [systemStats, setSystemStats] = useState({
    cpu_percent: 0,
    memory: { percent: 0, used: 0, total: 0 }
  });
  const [sources, setSources] = useState([]);
  const [isResearching, setIsResearching] = useState(false);
  const [researchProgress, setResearchProgress] = useState(0);
  const [thinkingContent, setThinkingContent] = useState('');
  const [responseContent, setResponseContent] = useState('');
  const [showThinking, setShowThinking] = useState(true);
  const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
  const systemStatsIntervalRef = useRef(null);

  // Fetch system stats periodically
  useEffect(() => {
    const fetchSystemStats = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/system-stats`);
        const data = await response.json();
        setSystemStats(data);
      } catch (error) {
        console.error('Error fetching system stats:', error);
      }
    };

    fetchSystemStats();
    systemStatsIntervalRef.current = setInterval(fetchSystemStats, 1000);

    return () => {
      if (systemStatsIntervalRef.current) {
        clearInterval(systemStatsIntervalRef.current);
      }
    };
  }, [apiBaseUrl]);

  // Fetch sessions on mount
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/sessions`);
        const data = await response.json();
        setSessions(data.sessions || []);
        if (data.sessions && data.sessions.length > 0 && !currentSessionId) {
          setCurrentSessionId(data.sessions[0].session_id);
        }
      } catch (error) {
        console.error('Error fetching sessions:', error);
      }
    };

    fetchSessions();
  }, [apiBaseUrl, currentSessionId]);

  const handleResearch = async (query) => {
    if (!query.trim()) return;

    const userMessage = { role: 'user', content: query, timestamp: new Date() };
    const requestHistory = [...chatMessages, userMessage];

    setIsResearching(true);
    setResearchProgress(0);
    setThinkingContent('');
    setResponseContent('');
    setChatMessages(requestHistory);

    let accumulatedThinking = '';
    let accumulatedResponse = '';
    let researchCompleted = false;
    let latestSources = [];

    const processEvent = (event) => {
      if (event.type === 'thinking') {
        accumulatedThinking += event.content || '';
        setThinkingContent(accumulatedThinking);
      } else if (event.type === 'thinking_end') {
        setShowThinking(true);
      } else if (event.type === 'response') {
        accumulatedResponse += event.content || '';
        setResponseContent(accumulatedResponse);
      } else if (event.type === 'sources_found') {
        latestSources = event.sources || [];
        setSources(latestSources);
        setResearchProgress(event.progress || 30);
      } else if (event.type === 'status') {
        setResearchProgress(event.progress || 50);
      } else if (event.type === 'research_complete') {
        researchCompleted = true;
        setResearchProgress(100);
        const finalResponse = accumulatedResponse || 'No response generated.';
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: finalResponse,
          timestamp: new Date(),
          thinking: accumulatedThinking,
          sources: latestSources
        }]);
        setCurrentSessionId(event.session_id);
      } else if (event.type === 'error') {
        console.error('Research error:', event.error);
        setChatMessages(prev => [...prev, {
          role: 'system',
          content: `Error: ${event.error}`,
          timestamp: new Date()
        }]);
      }
    };

    try {
      const response = await fetch(`${apiBaseUrl}/api/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          chat_history: requestHistory,
          use_thinking_model: true
        })
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
            } catch (error) {
              console.error('Error parsing event:', error);
            }
          }
        }
      }

      if (buffer.trim()) {
        try {
          processEvent(JSON.parse(buffer));
        } catch (error) {
          console.error('Error parsing final event:', error);
        }
      }

      if (!researchCompleted && accumulatedResponse.trim()) {
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: accumulatedResponse,
          timestamp: new Date(),
          thinking: accumulatedThinking,
          sources: latestSources
        }]);
      }
    } catch (error) {
      console.error('Error during research:', error);
      setChatMessages(prev => [...prev, {
        role: 'system',
        content: `Error: ${error.message}`,
        timestamp: new Date()
      }]);
    } finally {
      setIsResearching(false);
      setResearchProgress(0);
    }
  };

  const handleExport = async (format = 'markdown') => {
    if (!currentSessionId) return;

    try {
      const response = await fetch(`${apiBaseUrl}/api/export/${currentSessionId}?format=${format}`, {
        method: 'POST'
      });
      const data = await response.json();
      console.log('Export result:', data);
      alert(`Research exported to: ${data.path}`);
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  return (
    <div className="app-container">
      {/* Smart Child Avatar - Top Right */}
      <SmartChildAvatar isActive={isResearching} progress={researchProgress} />

      {/* Three-Column Layout */}
      <div className="main-layout">
        {/* Left Sidebar */}
        <LeftSidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={setCurrentSessionId}
          onNewSession={() => {
            setCurrentSessionId(null);
            setChatMessages([]);
            setThinkingContent('');
            setResponseContent('');
            setSources([]);
          }}
        />

        {/* Center Panel */}
        <CenterPanel
          chatMessages={chatMessages}
          onResearch={handleResearch}
          isResearching={isResearching}
          thinkingContent={thinkingContent}
          responseContent={responseContent}
          showThinking={showThinking}
          onToggleThinking={() => setShowThinking(!showThinking)}
          researchProgress={researchProgress}
          onExport={handleExport}
        />

        {/* Right Sidebar */}
        <RightSidebar
          systemStats={systemStats}
          sources={sources}
          isResearching={isResearching}
          researchProgress={researchProgress}
        />
      </div>
    </div>
  );
}

export default App;
