import React from 'react';
import { X, Keyboard } from 'lucide-react';
import './HelpDialog.css';

function HelpDialog({ isOpen, onClose }) {
  if (!isOpen) return null;

  const shortcuts = [
    { key: 'Ctrl+N', description: 'Start new session' },
    { key: 'Ctrl+E', description: 'Export current session' },
    { key: 'Ctrl+T', description: 'Toggle theme' },
    { key: 'Ctrl+K', description: 'Focus input field' },
    { key: 'Esc', description: 'Close dialogs' },
  ];

  return (
    <div className="help-overlay" onClick={onClose}>
      <div className="help-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="help-header">
          <div className="help-title">
            <Keyboard size={20} />
            <span>Keyboard Shortcuts</span>
          </div>
          <button type="button" className="help-close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
        <div className="help-content">
          {shortcuts.map((shortcut) => (
            <div key={shortcut.key} className="help-shortcut">
              <kbd className="help-key">{shortcut.key}</kbd>
              <span className="help-description">{shortcut.description}</span>
            </div>
          ))}
        </div>
        <div className="help-footer">
          <p>Tip: You can also drag and drop files to upload them directly.</p>
        </div>
      </div>
    </div>
  );
}

export default HelpDialog;