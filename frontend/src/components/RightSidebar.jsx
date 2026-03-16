import React, { useEffect, useState } from 'react';
import { Activity, Cpu, HardDrive, Link2, ExternalLink } from 'lucide-react';
import './RightSidebar.css';

function RightSidebar({ systemStats, sources, isResearching, researchProgress }) {
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
            <div key={idx} className="source-item">
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
                  >
                    {source.url.replace(/^https?:\/\/(www\.)?/, '').substring(0, 35)}...
                  </a>
                )}
              </div>
              {source.url && (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-link-btn"
                  title="Open source"
                >
                  <ExternalLink size={16} />
                </a>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Model Info */}
      <div className="monitor-section bottom">
        <div className="model-info">
          <div className="info-item">
            <span className="info-label">Thinking Model</span>
            <span className="info-value">deepseek-r1:7b</span>
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
    </div>
  );
}

export default RightSidebar;
