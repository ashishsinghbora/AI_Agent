import React, { useState, useEffect } from 'react';
import { ResearchProvider, useResearchContext } from './context/ResearchContext';
import LeftSidebar from './components/LeftSidebar';
import CenterPanel from './components/CenterPanel';
import RightSidebar from './components/RightSidebar';
import SourceCountDialog from './components/SourceCountDialog';
import OutputModeSelector from './components/OutputModeSelector';
import ThemeToggle from './components/ThemeToggle';
import HelpDialog from './components/HelpDialog';
import { HelpCircle } from 'lucide-react';
import { exportConversationTranscript } from './utils/conversationExport';

function AppInner() {
  const {
    apiBaseUrl,
    // research
    chatMessages,
    isResearching,
    researchProgress,
    thinkingContent,
    responseContent,
    sources,
    crawlEvents,
    selectedSource,
    setSelectedSource,
    conflictAlert,
    handleConflictDecision,
    knowledgeGraph,
    activeQuery,
    handleResearch,
    // sessions
    sessions,
    currentSessionId,
    handleSelectSession,
    handleDeleteSession,
    handleNewSession,
    // resources
    maxSources,
    setMaxSources,
    cpuBudget,
    setCpuBudget,
    outputMode,
    setOutputMode,
    speedMode,
    handlePerformanceModeChange,
    buildRequestOptions,
    // uploads + export
    uploadItems,
    handleUploadFiles,
    handleExport,
    // system
    systemStats,
    theme,
    toggleTheme,
  } = useResearchContext();

  const [showSourceDialog, setShowSourceDialog] = useState(false);
  const [showHelpDialog, setShowHelpDialog] = useState(false);
  const [showRightSidebar, setShowRightSidebar] = useState(false);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'n':
            e.preventDefault();
            handleNewSession();
            break;
          case 'e':
            e.preventDefault();
            handleExport();
            break;
          case 't':
            e.preventDefault();
            toggleTheme();
            break;
          case 'k':
            e.preventDefault();
            // Focus input
            {
              const input = document.querySelector('.research-input');
              if (input) input.focus();
            }
            break;
          case '/':
            e.preventDefault();
            setShowHelpDialog(true);
            break;
          default:
            break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleNewSession, handleExport, toggleTheme]);

  // Map speed mode → legacy performanceMode label for RightSidebar
  const performanceMode = speedMode === 'deep' ? 'high' : 'eco';

  const onResearch = (query) => {
    const options = buildRequestOptions();
    handleResearch(query, options);
  };

  const onPerformanceChange = (mode) => {
    handlePerformanceModeChange(mode);
  };

  const onShareConversation = () => {
    const result = exportConversationTranscript({
      chatMessages,
      activeQuery,
      sessionId: currentSessionId,
    });

    if (!result.ok) {
      window.alert(result.message);
      return;
    }

    const blob = new Blob([result.content], { type: result.mimeType });
    const objectUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = result.fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(objectUrl);
  };

  return (
    <div className="app-container" data-theme={theme}>
      <div className="main-layout">
        <LeftSidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          onNewSession={handleNewSession}
        />

        <div className="center-wrapper">
          {/* Output mode & source count controls above chat */}
          <div className="center-controls">
            <OutputModeSelector value={outputMode} onChange={setOutputMode} />
            <div className="center-controls-right">
              <button
                type="button"
                className="source-count-btn"
                onClick={() => setShowSourceDialog(true)}
                title="Change source count"
              >
                <span className="source-count-icon">🔍</span>
                <span>{maxSources} sources</span>
              </button>
              <button
                type="button"
                className="help-btn"
                onClick={() => setShowHelpDialog(true)}
                title="Keyboard shortcuts (Ctrl+/)"
              >
                <HelpCircle size={16} />
              </button>
              <ThemeToggle theme={theme} onToggle={toggleTheme} />
            </div>
          </div>

          <CenterPanel
            chatMessages={chatMessages}
            onResearch={onResearch}
            isResearching={isResearching}
            thinkingContent={thinkingContent}
            responseContent={responseContent}
            researchProgress={researchProgress}
            onExport={handleExport}
            onShareConversation={onShareConversation}
            uploadItems={uploadItems}
            onUploadFiles={handleUploadFiles}
            activeQuery={activeQuery}
            onToggleSettings={() => setShowRightSidebar(!showRightSidebar)}
          />
        </div>

        {showRightSidebar && (
          <RightSidebar
            systemStats={systemStats}
            sources={sources}
            isResearching={isResearching}
            researchProgress={researchProgress}
            onSourceSelect={setSelectedSource}
            selectedSource={selectedSource}
            onCloseSource={() => setSelectedSource(null)}
            crawlEvents={crawlEvents}
            activeQuery={activeQuery}
            performanceMode={performanceMode}
            onPerformanceChange={onPerformanceChange}
            conflictAlert={conflictAlert}
            onResolveConflict={handleConflictDecision}
            knowledgeGraph={knowledgeGraph}
            apiBaseUrl={apiBaseUrl}
            cpuBudget={cpuBudget}
            onCpuBudgetChange={setCpuBudget}
            onRestartSession={handleNewSession}
            isVisible={showRightSidebar}
          />
        )}
      </div>

      {showSourceDialog && (
        <SourceCountDialog
          currentValue={maxSources}
          onConfirm={(val) => {
            setMaxSources(val);
            setShowSourceDialog(false);
          }}
          onCancel={() => setShowSourceDialog(false)}
        />
      )}

      <HelpDialog
        isOpen={showHelpDialog}
        onClose={() => setShowHelpDialog(false)}
      />
    </div>
  );
}

function App() {
  return (
    <ResearchProvider>
      <AppInner />
    </ResearchProvider>
  );
}

export default App;
