import React, { useState, useRef, useEffect } from 'react';
import { Send, Download, Copy, Brain, Zap } from 'lucide-react';
import './CenterPanel.css';

function CenterPanel({
  chatMessages,
  onResearch,
  isResearching,
  thinkingContent,
  responseContent,
  showThinking,
  onToggleThinking,
  researchProgress,
  onExport
}) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, thinkingContent, responseContent]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isResearching) {
      onResearch(inputValue);
      setInputValue('');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  // Simple markdown to HTML converter
  const renderMarkdown = (text) => {
    // Convert basic markdown: **bold**, *italic*, `code`, ## headers, etc.
    let html = text
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/\n/g, '<br/>');
    
    return <div className="markdown-content" dangerouslySetInnerHTML={{ __html: html }} />;
  };

  return (
    <div className="center-panel">
      {/* Header */}
      <div className="center-header">
        <h2 className="center-title">Research Assistant</h2>
        <div className="header-actions">
          <button
            className="header-btn"
            onClick={() => onExport('markdown')}
            title="Export as Markdown"
          >
            <Download size={18} />
          </button>
          <button
            className="header-btn"
            onClick={() => onExport('pdf')}
            title="Export as PDF"
          >
            <Download size={18} />
            <span className="btn-text">PDF</span>
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div className="messages-container">
        {chatMessages.length === 0 && !isResearching && (
          <div className="welcome-message">
            <div className="welcome-icon">🔬</div>
            <h3>Welcome to Research Agent</h3>
            <p>Ask me to research any topic, and I'll search the web, analyze findings, and provide comprehensive insights.</p>
            <div className="example-queries">
              <div className="example">
                <strong>Try asking:</strong>
                <ul>
                  <li>"What are the latest advances in deep learning?"</li>
                  <li>"How does quantum computing work?"</li>
                  <li>"Best practices for Python development in 2024"</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Chat Messages */}
        {chatMessages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : msg.role === 'system' ? '⚠️' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-header">
                <span className="message-role">{msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}</span>
                {msg.timestamp && (
                  <span className="message-time">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                )}
              </div>
              <div className="message-body">
                {renderMarkdown(msg.content)}
              </div>
              {msg.thinking && (
                <div className="message-thinking">
                  <button
                    className="thinking-toggle"
                    onClick={() => onToggleThinking()}
                  >
                    <Brain size={16} />
                    <span>Chain of Thought ({thinkingContent.length} chars)</span>
                  </button>
                </div>
              )}
            </div>
            <button
              className="message-copy"
              onClick={() => copyToClipboard(msg.content)}
              title="Copy message"
            >
              <Copy size={16} />
            </button>
          </div>
        ))}

        {/* Thinking Content Display */}
        {isResearching && thinkingContent && (
          <div className="message message-thinking-display">
            <div className="message-avatar">🧠</div>
            <div className="message-content">
              <div className="message-header">
                <span className="message-role">Chain of Thought</span>
                <button
                  className="thinking-close"
                  onClick={() => onToggleThinking()}
                  title="Hide thinking"
                >
                  ✕
                </button>
              </div>
              <div className="message-body thinking-text">
                <pre>{thinkingContent}</pre>
              </div>
            </div>
          </div>
        )}

        {/* Response Being Generated */}
        {isResearching && responseContent && (
          <div className="message message-assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="message-header">
                <span className="message-role">Assistant</span>
                <span className="generating-indicator">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </span>
              </div>
              <div className="message-body">
                {renderMarkdown(responseContent)}
              </div>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        {isResearching && (
          <div className="research-progress">
            <div className="progress-info">
              <Zap size={16} />
              <span>Researching...</span>
              <span className="progress-percent">{researchProgress}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${researchProgress}%` }}></div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Footer */}
      <form className="input-footer" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask me to research something..."
            disabled={isResearching}
            className="research-input"
          />
          <button
            type="submit"
            disabled={isResearching || !inputValue.trim()}
            className="send-btn"
            title="Send research query"
          >
            <Send size={18} />
          </button>
        </div>
        <div className="input-hints">
          <small>💡 Type your research query and press Enter or click Send</small>
        </div>
      </form>
    </div>
  );
}

export default CenterPanel;
