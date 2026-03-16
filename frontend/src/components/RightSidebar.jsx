import React, { useEffect, useState } from 'react';
import { Activity, Cpu, HardDrive, Link2, ExternalLink, Terminal, Zap, AlertTriangle, Share2 } from 'lucide-react';
import './RightSidebar.css';

function RightSidebar({
  systemStats,
  sources,
  isResearching,
  researchProgress,
  onSourceSelect,
  selectedSource,
  onCloseSource,
  crawlEvents,
  activeQuery,
  performanceMode,
  onPerformanceChange,
  conflictAlert,
  onResolveConflict,
  knowledgeGraph
}) {
  const [ramUsage, setRamUsage] = useState(0);

  useEffect(() => {
    if (systemStats && systemStats.memory) {
      setRamUsage(systemStats.memory.percent);
    }
  }, [systemStats]);

  const getStatsColor = (value, threshold = 70) => {
    if (value >= threshold) return 'critical';
    if (value >= threshold - 20) return 'warning';
    return 'normal';
  };

  const formatGB = (value) => {
    return (value || 0).toFixed(1);
  };

  const shortenUrl = (url) => {
    if (!url) return '';
    return url.replace(/^https?:\/\/(www\.)?/, '').substring(0, 38);
  };

  const getHighlightTokens = () => {
    if (!activeQuery) return [];
    return activeQuery
      .toLowerCase()
      .split(/\s+/)
      .map(token => token.replace(/[^a-z0-9-]/g, ''))
      .filter(token => token.length > 3)
      .slice(0, 6);
  };

  const renderHighlightedExcerpt = (text) => {
    if (!text) return <span className="preview-empty">No preview available.</span>;
    const tokens = getHighlightTokens();
    if (!tokens.length) return text;

    const regex = new RegExp(`(${tokens.join('|')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) => {
      const isMatch = tokens.some(token => token.toLowerCase() === part.toLowerCase());
      return isMatch
        ? <mark key={`${part}-${index}`} className="preview-highlight">{part}</mark>
        : <span key={`${part}-${index}`}>{part}</span>;
    });
  };

  const renderKnowledgeGraph = () => {
    if (!knowledgeGraph || !knowledgeGraph.nodes || knowledgeGraph.nodes.length === 0) {
      return (
        <div className="graph-empty">
          <span>No graph yet</span>
        </div>
      );
    }

    const width = 240;
    const height = 200;
    const centerX = width / 2;
    const centerY = height / 2;
    const nodes = knowledgeGraph.nodes || [];
    const root = nodes.find(node => node.type === 'root') || nodes[0];
    const concepts = nodes.filter(node => node.id !== root?.id);
    const radius = 70;

    return (
      <svg className="graph-canvas" viewBox={`0 0 ${width} ${height}`}>
        {concepts.map((node, index) => {
          const angle = (index / Math.max(1, concepts.length)) * Math.PI * 2;
          const x = centerX + radius * Math.cos(angle);
          const y = centerY + radius * Math.sin(angle);
          return (
            <g key={node.id}>
              <line x1={centerX} y1={centerY} x2={x} y2={y} className="graph-link" />
              <circle cx={x} cy={y} r={14} className="graph-node" />
              <text x={x} y={y + 30} textAnchor="middle" className="graph-label">
                {node.label}
              </text>
            </g>
          );
        })}
        <circle cx={centerX} cy={centerY} r={18} className="graph-root" />
        <text x={centerX} y={centerY + 40} textAnchor="middle" className="graph-root-label">
          {root?.label || 'Topic'}
        </text>
      </svg>
    );
  };

  return (
    <div className="right-sidebar">
      {/* System Monitor */}
      <div className="monitor-section">
        <div className="monitor-header">
          <Activity size={18} />
          <h3 className="monitor-title">System Monitor</h3>
        </div>

        <div className="stats-grid">
          {/* CPU Stats */}
          <div className={`stat-card ${getStatsColor(systemStats.cpu_percent)}`}>
            <div className="stat-icon">
              <Cpu size={20} />
            </div>
            <div className="stat-info">
              <div className="stat-label">CPU Usage</div>
              <div className="stat-value">{systemStats.cpu_percent.toFixed(1)}%</div>
            </div>
            <div className="stat-bar">
              <div
                className="stat-bar-fill"
                style={{ width: `${Math.min(100, systemStats.cpu_percent)}%` }}
              ></div>
            </div>
          </div>

          {/* Memory Stats */}
          <div className={`stat-card ${getStatsColor(ramUsage)}`}>
            <div className="stat-icon">
              <HardDrive size={20} />
            </div>
            <div className="stat-info">
              <div className="stat-label">Memory Usage</div>
              <div className="stat-value">{ramUsage.toFixed(1)}%</div>
            </div>
            <div className="stat-bar">
              <div
                className="stat-bar-fill"
                style={{ width: `${Math.min(100, ramUsage)}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Detailed Memory Info */}
        <div className="memory-details">
          <div className="memory-row">
            <span className="memory-label">Used</span>
            <span className="memory-value">{formatGB(systemStats.memory?.used)} GB</span>
          </div>
          <div className="memory-row">
            <span className="memory-label">Total</span>
            <span className="memory-value">{formatGB(systemStats.memory?.total)} GB</span>
          </div>
        </div>
      </div>

      {/* Performance Mode */}
      <div className="monitor-section glass-panel">
        <div className="monitor-header">
          <Zap size={18} />
          <h3 className="monitor-title">Performance</h3>
        </div>
        <div className="performance-toggle">
          <button
            className={`toggle-btn ${performanceMode === 'high' ? 'active' : ''}`}
            onClick={() => onPerformanceChange('high')}
            type="button"
          >
            High
          </button>
          <button
            className={`toggle-btn ${performanceMode === 'eco' ? 'active' : ''}`}
            onClick={() => onPerformanceChange('eco')}
            type="button"
          >
            Eco
          </button>
        </div>
        <div className="performance-hint">
          {performanceMode === 'eco'
            ? 'Eco uses fewer sources with fast responses.'
            : 'High uses deeper reasoning and more sources.'}
        </div>
      </div>

      {/* Research Progress */}
      {isResearching && (
        <div className="monitor-section">
          <div className="monitor-header">
            <div className="pulse-dot"></div>
            <h3 className="monitor-title">Research Progress</h3>
          </div>
          <div className="progress-container">
            <div className="progress-bar-large">
              <div
                className="progress-fill-large"
                style={{ width: `${researchProgress}%` }}
              ></div>
            </div>
            <div className="progress-text">
              <span>{researchProgress}%</span>
              <span className="progress-label">
                {researchProgress < 30 ? 'Thinking...' : 
                 researchProgress < 50 ? 'Researching...' :
                 researchProgress < 75 ? 'Processing...' :
                 researchProgress < 100 ? 'Finalizing...' : 'Complete!'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Live Crawl Preview */}
      <div className="monitor-section glass-panel">
        <div className="monitor-header">
          <Terminal size={18} />
          <h3 className="monitor-title">Live Crawl</h3>
        </div>
        <div className="crawl-feed">
          {crawlEvents.length === 0 ? (
            <div className="crawl-empty">Waiting for crawl updates...</div>
          ) : (
            crawlEvents.slice(-6).map((event, idx) => (
              <div key={`${event.url}-${idx}`} className="crawl-item">
                <div className="crawl-title">{event.title || 'Untitled'}</div>
                <div className="crawl-url">{shortenUrl(event.url)}</div>
                <div className="crawl-excerpt">{event.excerpt || 'Processing content...'}</div>
                {event.keywords && event.keywords.length > 0 && (
                  <div className="crawl-keywords">
                    {event.keywords.join(' • ')}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Sources Section */}
      <div className="monitor-section">
        <div className="monitor-header">
          <Link2 size={18} />
          <h3 className="monitor-title">Sources</h3>
          {sources.length > 0 && (
            <span className="source-count">{sources.length}</span>
          )}
        </div>

        <div className="sources-list">
          {sources.length === 0 && !isResearching && (
            <div className="empty-sources">
              <Link2 size={20} />
              <p>No sources yet</p>
              <small>Sources will appear during research</small>
            </div>
          )}

          {sources.map((source, idx) => (
            <div
              key={idx}
              className="source-item"
              onClick={() => onSourceSelect(source)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === 'Enter') onSourceSelect(source);
              }}
            >
              <div className="source-icon">
                <span className="source-number">{idx + 1}</span>
              </div>
              <div className="source-content">
                <div className="source-title">{source.title || 'Untitled Source'}</div>
                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-url"
                    onClick={(event) => event.stopPropagation()}
                  >
                    {shortenUrl(source.url)}...
                  </a>
                )}
                {source.excerpt && (
                  <div className="source-excerpt">{source.excerpt}</div>
                )}
              </div>
              {source.url && (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-link-btn"
                  title="Open source"
                  onClick={(event) => event.stopPropagation()}
                >
                  <ExternalLink size={16} />
                </a>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Knowledge Graph */}
      <div className="monitor-section glass-panel">
        <div className="monitor-header">
          <Share2 size={18} />
          <h3 className="monitor-title">Knowledge Graph</h3>
        </div>
        <div className="graph-wrapper">
          {renderKnowledgeGraph()}
        </div>
      </div>

      {/* Model Info */}
      <div className="monitor-section bottom">
        <div className="model-info">
          <div className="info-item">
            <span className="info-label">Thinking Model</span>
            <span className="info-value">
              {performanceMode === 'eco' ? 'tiny (fast plan)' : 'deepseek-r1:7b'}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Response Model</span>
            <span className="info-value">gemma2:2b</span>
          </div>
          <div className="info-item">
            <span className="info-label">Backend</span>
            <span className="info-value">FastAPI + Ollama</span>
          </div>
        </div>
      </div>

      {selectedSource && (
        <div className="source-preview-overlay" role="dialog" aria-modal="true">
          <div className="source-preview-card">
            <div className="preview-header">
              <div className="preview-title">Source Context</div>
              <button className="preview-close" onClick={onCloseSource} type="button">
                ✕
              </button>
            </div>
            <div className="preview-body">
              <div className="preview-source">{selectedSource.title || 'Untitled Source'}</div>
              {selectedSource.url && (
                <a className="preview-link" href={selectedSource.url} target="_blank" rel="noopener noreferrer">
                  {selectedSource.url}
                </a>
              )}
              <div className="preview-excerpt">
                {renderHighlightedExcerpt(selectedSource.excerpt || selectedSource.snippet)}
              </div>
              {selectedSource.keywords && selectedSource.keywords.length > 0 && (
                <div className="preview-keywords">
                  {selectedSource.keywords.join(' • ')}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {conflictAlert && (
        <div className="conflict-overlay" role="dialog" aria-modal="true">
          <div className="conflict-card">
            <div className="conflict-header">
              <AlertTriangle size={18} />
              <span>Conflict Alert</span>
            </div>
            <div className="conflict-body">
              <p>{conflictAlert.message || 'Conflicting data detected.'}</p>
              <div className="conflict-list">
                {(conflictAlert.conflicts || []).slice(0, 3).map((conflict, idx) => (
                  <div key={`${conflict.unit}-${idx}`} className="conflict-item">
                    <div className="conflict-unit">{conflict.unit}</div>
                    <div className="conflict-values">
                      {conflict.values.map((value, valueIdx) => (
                        <span key={`${value.value}-${valueIdx}`}>{value.value}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="conflict-actions">
                <button type="button" onClick={() => onResolveConflict('third_source')}>
                  Search 3rd Source
                </button>
                <button type="button" onClick={() => onResolveConflict('prefer_official')}>
                  Prefer Official Docs
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RightSidebar;
