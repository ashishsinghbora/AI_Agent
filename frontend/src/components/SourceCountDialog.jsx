import React, { useState } from 'react';
import './SourceCountDialog.css';

const PRESETS = [
  { value: 3, label: '3', description: 'Quick — fast response' },
  { value: 5, label: '5', description: 'Standard — balanced depth' },
  { value: 10, label: '10', description: 'Deep — thorough research' },
];

function SourceCountDialog({ currentValue, onConfirm, onCancel }) {
  const [selected, setSelected] = useState(currentValue || 5);
  const [customValue, setCustomValue] = useState('');
  const [useCustom, setUseCustom] = useState(false);
  const [customError, setCustomError] = useState('');

  const parsedCustom = parseInt(customValue, 10);
  const effectiveValue = useCustom && !isNaN(parsedCustom) ? parsedCustom : selected;

  const handleConfirm = () => {
    if (useCustom) {
      if (isNaN(parsedCustom) || parsedCustom < 1 || parsedCustom > 20) {
        setCustomError('Please enter a number between 1 and 20.');
        return;
      }
    }
    onConfirm(Math.max(1, Math.min(20, effectiveValue)));
  };

  const handlePresetClick = (value) => {
    setSelected(value);
    setUseCustom(false);
    setCustomValue('');
  };

  const handleCustomChange = (e) => {
    setCustomValue(e.target.value);
    setUseCustom(true);
    setCustomError('');
  };

  return (
    <div className="scd-overlay" role="dialog" aria-modal="true" aria-label="Select source count">
      <div className="scd-card">
        <div className="scd-header">
          <h3 className="scd-title">How many sources?</h3>
          <p className="scd-subtitle">More sources = deeper research, longer wait</p>
        </div>

        <div className="scd-presets">
          {PRESETS.map((preset) => (
            <button
              key={preset.value}
              type="button"
              className={`scd-preset ${!useCustom && selected === preset.value ? 'active' : ''}`}
              onClick={() => handlePresetClick(preset.value)}
            >
              <span className="scd-preset-value">{preset.label}</span>
              <span className="scd-preset-desc">{preset.description}</span>
            </button>
          ))}
        </div>

        <div className="scd-custom">
          <label className="scd-custom-label" htmlFor="scd-custom-input">
            Custom (1–20)
          </label>
          <input
            id="scd-custom-input"
            type="number"
            min={1}
            max={20}
            value={customValue}
            onChange={handleCustomChange}
            placeholder="e.g. 7"
            className={`scd-custom-input ${useCustom ? 'active' : ''} ${customError ? 'error' : ''}`}
          />
        </div>
        {customError && <div className="scd-error">{customError}</div>}

        <div className="scd-actions">
          <button type="button" className="scd-cancel" onClick={onCancel}>
            Cancel
          </button>
          <button type="button" className="scd-confirm" onClick={handleConfirm}>
            Use {effectiveValue} source{effectiveValue !== 1 ? 's' : ''}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SourceCountDialog;
