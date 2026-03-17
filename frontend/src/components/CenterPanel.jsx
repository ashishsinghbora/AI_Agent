import React, { useState, useRef, useEffect } from 'react';
import { Send, Download, Copy, Zap, UploadCloud, Share2, Settings } from 'lucide-react';
import './CenterPanel.css';
import CollapsedThinking from './CollapsedThinking';
import NeuralStreamBadge from './NeuralStreamBadge';

function CenterPanel({
  chatMessages,
  onResearch,
  isResearching,
  thinkingContent,
  responseContent,
  researchProgress,
  onExport,
  onShareConversation,
  uploadItems,
  onUploadFiles,
  activeQuery,
  onToggleSettings
}) {
  const [inputValue, setInputValue] = useState('');
  const [isDragActive, setIsDragActive] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);

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

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = () => {
    setIsDragActive(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragActive(false);
    if (event.dataTransfer?.files?.length) {
      onUploadFiles(event.dataTransfer.files);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    if (event.target.files?.length) {
      onUploadFiles(event.target.files);
      event.target.value = '';
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
    <div
      className={`center-panel ${isDragActive ? 'drag-active' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Header */}
      <div className="center-header">
        <div className="header-left">
          <NeuralStreamBadge isActive={isResearching} />
          <div className="header-meta">
            <h2 className="center-title">Research Assistant</h2>
            <p className="center-subtitle">
              Fast neural routing across sources for synthesis and grounded answers.
            </p>
          </div>
        </div>
        <div className="header-actions">
          <button
            className="header-btn"
            onClick={() => onExport('markdown')}
            title="Export as Markdown"
          >
            <Download size={18} />
            <span className="btn-text">MD</span>
          </button>
          <button
            className="header-btn"
            onClick={() => onExport('pdf')}
            title="Export as PDF"
          >
            <Download size={18} />
            <span className="btn-text">PDF</span>
          </button>
          <button
            className="header-btn"
            onClick={() => onExport('learning-pack')}
            title="Export Learning Pack"
          >
            <Download size={18} />
            <span className="btn-text">Pack</span>
          </button>
          <button
            className="header-btn share-btn"
            onClick={onShareConversation}
            title="Share conversation export"
            disabled={!chatMessages.length}
            type="button"
          >
            <Share2 size={18} />
            <span className="btn-text">Share</span>
          </button>
          <button
            className="header-btn settings-btn"
            onClick={onToggleSettings}
            title="Toggle settings panel"
            type="button"
          >
            <Settings size={18} />
            <span className="btn-text">Settings</span>
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
                <div style={{ marginTop: '8px' }}>
                  <CollapsedThinking content={msg.thinking} isStreaming={false} />
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

        {/* Thinking Content — collapsible panel shown whenever research is active */}
        {isResearching && (
          <div className="message-thinking-wrapper">
            <CollapsedThinking
              content={thinkingContent}
              isStreaming={isResearching && !thinkingContent?.endsWith('...')}
            />
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
        {isDragActive && (
          <div className="drop-overlay">
            <div className="drop-title">Drop files to embed</div>
            <div className="drop-subtitle">PDF, code, and notes supported</div>
          </div>
        )}
        <div className="input-wrapper">
          <button
            type="button"
            className="upload-btn"
            onClick={handleUploadClick}
            title="Upload knowledge"
          >
            <UploadCloud size={18} />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden-file-input"
            onChange={handleFileChange}
          />
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
          <small>Type your research query and press Enter or click Send</small>
          {activeQuery && (
            <small className="active-query">Active: {activeQuery}</small>
          )}
        </div>
        {uploadItems.length > 0 && (
          <div className="upload-queue">
            {uploadItems.map(item => (
              <div key={item.id} className={`upload-item ${item.status}`}>
                <div className="upload-name">{item.name}</div>
                <div className="upload-status">
                  <span className="upload-state">{item.status}</span>
                  {item.detail && <span className="upload-detail">{item.detail}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </form>
    </div>
  );
}

export default CenterPanel;
