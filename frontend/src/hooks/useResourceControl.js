import { useState, useCallback } from 'react';

/**
 * useResourceControl — manages research resource parameters (sources, CPU, mode).
 *
 * @returns resource state + handlers
 */
export function useResourceControl() {
  const [maxSources, setMaxSources] = useState(5);
  const [cpuBudget, setCpuBudget] = useState(80);
  const [outputMode, setOutputMode] = useState('quick');
  const [speedMode, setSpeedMode] = useState('fast');

  // Map legacy performanceMode strings to speed_mode values
  const handlePerformanceModeChange = useCallback((mode) => {
    if (mode === 'high') {
      setSpeedMode('deep');
      setCpuBudget(90);
      setMaxSources(6);
    } else if (mode === 'eco') {
      setSpeedMode('fast');
      setCpuBudget(50);
      setMaxSources(2);
    }
  }, []);

  // Build request options object to spread into handleResearch
  const buildRequestOptions = useCallback(
    () => ({
      maxSources,
      cpuBudget,
      outputMode,
      speedMode,
      useThinking: speedMode !== 'fast',
      thinkingChars: speedMode === 'deep' ? 240 : speedMode === 'balanced' ? 180 : 0,
    }),
    [maxSources, cpuBudget, outputMode, speedMode]
  );

  return {
    maxSources,
    setMaxSources,
    cpuBudget,
    setCpuBudget,
    outputMode,
    setOutputMode,
    speedMode,
    setSpeedMode,
    handlePerformanceModeChange,
    buildRequestOptions,
  };
}
