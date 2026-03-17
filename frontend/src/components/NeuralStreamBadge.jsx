import React from 'react';
import './NeuralStreamBadge.css';

const NODE_LAYOUT = [
  { id: 'n1', x: 12, y: 18 },
  { id: 'n2', x: 52, y: 10 },
  { id: 'n3', x: 96, y: 20 },
  { id: 'n4', x: 20, y: 52 },
  { id: 'n5', x: 62, y: 42 },
  { id: 'n6', x: 106, y: 56 },
  { id: 'n7', x: 30, y: 86 },
  { id: 'n8', x: 74, y: 78 },
  { id: 'n9', x: 114, y: 88 },
];

const LINKS = [
  ['n1', 'n2'], ['n2', 'n3'],
  ['n1', 'n4'], ['n2', 'n5'], ['n3', 'n6'],
  ['n4', 'n5'], ['n5', 'n6'],
  ['n4', 'n7'], ['n5', 'n8'], ['n6', 'n9'],
  ['n7', 'n8'], ['n8', 'n9'],
  ['n2', 'n4'], ['n3', 'n5'], ['n5', 'n7'], ['n6', 'n8'],
];

function getNodeById(id) {
  return NODE_LAYOUT.find((node) => node.id === id);
}

function NeuralStreamBadge({ isActive }) {
  return (
    <div className={`neural-stream-badge ${isActive ? 'active' : ''}`} aria-hidden="true">
      <svg viewBox="0 0 128 96" className="neural-stream-canvas">
        {LINKS.map((pair, index) => {
          const source = getNodeById(pair[0]);
          const target = getNodeById(pair[1]);
          if (!source || !target) return null;

          return (
            <g key={`${pair[0]}-${pair[1]}`}>
              <line
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                className="neural-link"
              />
              <circle
                r="1.8"
                cx={source.x}
                cy={source.y}
                className="neural-packet"
              />
            </g>
          );
        })}

        {NODE_LAYOUT.map((node, index) => (
          <circle
            key={node.id}
            cx={node.x}
            cy={node.y}
            r="3.2"
            className="neural-node"
            style={{ animationDelay: `${index * 0.12}s` }}
          />
        ))}
      </svg>
      <span className="neural-stream-label">Neural Data Flow</span>
    </div>
  );
}

export default NeuralStreamBadge;
