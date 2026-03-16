import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Brain } from 'lucide-react';
import './CollapsedThinking.css';

function CollapsedThinking({ content, isStreaming }) {
  const [expanded, setExpanded] = useState(false);

  if (!content && !isStreaming) return null;

  return (
    <div className={`ct-container ${expanded ? 'ct-expanded' : ''}`}>
      <button
        type="button"
        className="ct-toggle"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        aria-controls="ct-body"
      >
        <span className="ct-toggle-left">
          <Brain size={14} className={`ct-brain ${isStreaming ? 'ct-pulse' : ''}`} />
          <span className="ct-toggle-label">Research Plan</span>
          {isStreaming && <span className="ct-streaming-badge">thinking…</span>}
        </span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {expanded && (
        <div id="ct-body" className="ct-body">
          {content ? (
            <pre className="ct-content">{content}</pre>
          ) : (
            <div className="ct-empty">Waiting for thinking output…</div>
          )}
        </div>
      )}
    </div>
  );
}

export default CollapsedThinking;
