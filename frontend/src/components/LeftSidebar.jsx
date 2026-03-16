import React from 'react';
import { Plus, Search, Trash2, MessageSquare } from 'lucide-react';
import './LeftSidebar.css';

function LeftSidebar({ sessions, currentSessionId, onSelectSession, onNewSession }) {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  };

  return (
    <div className="left-sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">Research Agent</h1>
        <button className="new-session-btn" onClick={onNewSession} title="New Research Session">
          <Plus size={20} />
        </button>
      </div>

      <div className="search-container">
        <Search size={18} className="search-icon" />
        <input
          type="text"
          placeholder="Search sessions..."
          className="search-input"
        />
      </div>

      <div className="sessions-container">
        <div className="sessions-label">Recent Sessions</div>
        
        {sessions.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={24} />
            <p>No research sessions yet</p>
            <small>Start a new research to begin</small>
          </div>
        ) : (
          <div className="sessions-list">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className={`session-item ${currentSessionId === session.session_id ? 'active' : ''}`}
                onClick={() => onSelectSession(session.session_id)}
              >
                <div className="session-content">
                  <div className="session-title">{session.query.substring(0, 40)}...</div>
                  <div className="session-meta">
                    <span className="session-time">{formatDate(session.started_at)}</span>
                    <span className="session-count">{session.findings_count} findings</span>
                  </div>
                </div>
                <button className="session-delete" title="Delete session">
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="sidebar-footer">
        <div className="footer-stats">
          <div className="stat">
            <span className="stat-label">Sessions</span>
            <span className="stat-value">{sessions.length}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Total Findings</span>
            <span className="stat-value">{sessions.reduce((sum, s) => sum + (s.findings_count || 0), 0)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LeftSidebar;
