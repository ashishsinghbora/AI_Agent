import React from 'react';
import { Zap, BookOpen, FileText } from 'lucide-react';
import './OutputModeSelector.css';

const MODES = [
  {
    id: 'quick',
    icon: Zap,
    label: 'Quick',
    description: 'Concise bullet-point answer',
  },
  {
    id: 'full',
    icon: BookOpen,
    label: 'Full',
    description: 'Detailed structured response',
  },
  {
    id: 'paper',
    icon: FileText,
    label: 'Paper',
    description: 'Academic-style with citations',
  },
];

function OutputModeSelector({ value, onChange }) {
  return (
    <div className="oms-container">
      <div className="oms-label">Output Mode</div>
      <div className="oms-options">
        {MODES.map((mode) => {
          const Icon = mode.icon;
          const isActive = value === mode.id;
          return (
            <button
              key={mode.id}
              type="button"
              className={`oms-option ${isActive ? 'active' : ''}`}
              onClick={() => onChange(mode.id)}
              title={mode.description}
            >
              <Icon size={14} className="oms-icon" />
              <span className="oms-option-label">{mode.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default OutputModeSelector;
