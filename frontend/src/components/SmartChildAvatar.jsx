import React, { useEffect, useRef, useState } from 'react';
import './SmartChildAvatar.css';

function SmartChildAvatar({ isActive, progress }) {
  const [blinks, setBlinks] = useState(0);
  const [thinking, setThinking] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const avatarRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (avatarRef.current) {
        const rect = avatarRef.current.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        // Calculate normalized vector from center to mouse (-1 to 1)
        const dx = (e.clientX - centerX) / 150; 
        const dy = (e.clientY - centerY) / 150;
        
        // Constrain to small movement
        const mag = Math.sqrt(dx * dx + dy * dy);
        const limit = 1.0;
        const finalX = mag > limit ? (dx / mag) * limit : dx;
        const finalY = mag > limit ? (dy / mag) * limit : dy;
        
        setMousePos({ x: finalX, y: finalY });
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useEffect(() => {
    if (!isActive) {
      setBlinks(0);
      setThinking(false);
      return;
    }

    // Random blinking
    const blinkInterval = setInterval(() => {
      setBlinks(prev => prev + 1);
    }, 3000);

    // Thinking animation
    const thinkInterval = setInterval(() => {
      setThinking(prev => !prev);
    }, 800);

    return () => {
      clearInterval(blinkInterval);
      clearInterval(thinkInterval);
    };
  }, [isActive]);

  const isBlinked = blinks % 2 === 1;

  // Calculate transforms based on mouse position
  const eyeTransform = {
    transform: `translate(${mousePos.x * 4}px, ${mousePos.y * 4}px)`
  };
  
  const noseTransform = {
    transform: `translate(${mousePos.x * 2}px, ${mousePos.y * 2}px)`
  };

  const mouthTransform = {
    transform: `translate(${mousePos.x * 1.5}px, ${mousePos.y * 1.5}px)`
  };

  return (
    <div 
      ref={avatarRef}
      className={`smart-child-avatar ${isActive ? 'active' : 'inactive'}`}
    >
      {/* Avatar Container */}
      <div className="avatar-container">
        {/* Hair - Animated via CSS */}
        <div className="hair-container">
          <div className="hair-strand s1"></div>
          <div className="hair-strand s2"></div>
          <div className="hair-strand s3"></div>
        </div>

        {/* Head */}
        <div className="head">
          {/* Eyes */}
          <div className={`eyes ${isBlinked ? 'blink' : ''}`}>
            <div className={`eye ${isBlinked ? 'closed' : ''}`}>
              {!isBlinked && <div className="pupil" style={eyeTransform}></div>}
            </div>
            <div className={`eye ${isBlinked ? 'closed' : ''}`}>
              {!isBlinked && <div className="pupil" style={eyeTransform}></div>}
            </div>
          </div>

          {/* Nose */}
          <div className="nose" style={noseTransform}></div>

          {/* Mouth */}
          <div className={`mouth ${isActive ? 'thinking' : 'neutral'}`} style={mouthTransform}>
            {!isActive && <span>:</span>}
            {isActive && <span>)</span>}
          </div>
        </div>

        {/* Light Bulb (Thinking Indicator) */}
        {isActive && (
          <div className={`light-bulb ${thinking ? 'glowing' : ''}`}>
            <div className="bulb">
              <span>💡</span>
            </div>
          </div>
        )}
      </div>

      {/* Status Text */}
      <div className="avatar-status">
        {!isActive ? (
          <div className="status-text">Ready</div>
        ) : (
          <>
            <div className="status-text">Researching...</div>
            <div className="status-progress">{progress}%</div>
          </>
        )}
      </div>

      {/* Thinking Indicator Line */}
      {isActive && (
        <div className="thinking-lines">
          <div className="line"></div>
          <div className="line"></div>
          <div className="line"></div>
        </div>
      )}
    </div>
  );
}

export default SmartChildAvatar;
