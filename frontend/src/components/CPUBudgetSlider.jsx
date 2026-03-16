import React from 'react';
import './CPUBudgetSlider.css';

const PRESETS = [
  { value: 50, label: '50%', hint: 'Eco — minimal CPU' },
  { value: 80, label: '80%', hint: 'Balanced' },
  { value: 90, label: '90%', hint: 'High performance' },
];

function CPUBudgetSlider({ value, onChange }) {
  const handlePreset = (preset) => onChange(preset);

  const handleSlider = (e) => onChange(Number(e.target.value));

  const getColor = () => {
    if (value <= 50) return '#4ade80';
    if (value <= 80) return '#facc15';
    return '#f87171';
  };

  return (
    <div className="cpu-slider">
      <div className="cpu-slider-header">
        <span className="cpu-slider-label">CPU Budget</span>
        <span className="cpu-slider-value" style={{ color: getColor() }}>
          {value}%
        </span>
      </div>

      <div className="cpu-presets">
        {PRESETS.map((p) => (
          <button
            key={p.value}
            type="button"
            className={`cpu-preset ${value === p.value ? 'active' : ''}`}
            onClick={() => handlePreset(p.value)}
            title={p.hint}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="cpu-track-wrap">
        <input
          type="range"
          min={10}
          max={100}
          step={5}
          value={value}
          onChange={handleSlider}
          className="cpu-range"
          style={{ '--fill': getColor() }}
          aria-label="CPU budget percentage"
        />
        <div className="cpu-track-labels">
          <span>10%</span>
          <span>55%</span>
          <span>100%</span>
        </div>
      </div>

      <div className="cpu-hint">
        {value <= 50
          ? 'Fewer parallel fetches — saves battery'
          : value <= 80
          ? 'Balanced parallel fetches'
          : 'Maximum parallel fetches — uses more CPU'}
      </div>
    </div>
  );
}

export default CPUBudgetSlider;
