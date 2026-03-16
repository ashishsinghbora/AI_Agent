import React, { useState } from 'react';
import { ResearchProvider, useResearchContext } from './context/ResearchContext';
import LeftSidebar from './components/LeftSidebar';
import CenterPanel from './components/CenterPanel';
import RightSidebar from './components/RightSidebar';
import SmartChildAvatar from './components/SmartChildAvatar';
import SourceCountDialog from './components/SourceCountDialog';
import OutputModeSelector from './components/OutputModeSelector';

function AppInner() {
  const {
    // research
    chatMessages,
    isResearching,
    researchProgress,
    thinkingContent,
    responseContent,
    showThinking,
    setShowThinking,
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
  } = useResearchContext();

  const [showSourceDialog, setShowSourceDialog] = useState(false);

  // Map speed mode → legacy performanceMode label for RightSidebar
  const performanceMode = speedMode === 'deep' ? 'high' : 'eco';

  const onResearch = (query) => {
    const options = buildRequestOptions();
    handleResearch(query, options);
  };

  const onPerformanceChange = (mode) => {
    handlePerformanceModeChange(mode);
  };

  return (
    <div className="app-container">
      <SmartChildAvatar isActive={isResearching} progress={researchProgress} />

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
            <button
              type="button"
              className="source-count-btn"
              onClick={() => setShowSourceDialog(true)}
              title="Change source count"
            >
              <span className="source-count-icon">🔍</span>
              <span>{maxSources} sources</span>
            </button>
          </div>

          <CenterPanel
            chatMessages={chatMessages}
            onResearch={onResearch}
            isResearching={isResearching}
            thinkingContent={thinkingContent}
            responseContent={responseContent}
            showThinking={showThinking}
            onToggleThinking={() => setShowThinking(!showThinking)}
            researchProgress={researchProgress}
            onExport={handleExport}
            uploadItems={uploadItems}
            onUploadFiles={handleUploadFiles}
            activeQuery={activeQuery}
          />
        </div>

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
          cpuBudget={cpuBudget}
          onCpuBudgetChange={setCpuBudget}
        />
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
