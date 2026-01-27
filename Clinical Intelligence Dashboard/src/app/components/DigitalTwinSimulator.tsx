import React, { useState, useEffect, useCallback } from 'react';
import './DigitalTwinSimulator.css';

interface ScenarioAction {
  action_type: string;
  target: string;
  value: number;
}

interface ActionType {
  type: string;
  name: string;
  description: string;
  value_description: string;
}

interface SimulationResult {
  scenario_name: string;
  baseline: {
    dqi: number;
    query_resolution_days: number;
    timeline_risk: number;
  };
  predicted: {
    dqi: number;
    query_resolution_days: number;
    timeline_risk: number;
  };
  changes: {
    dqi_change: number;
    query_resolution_change: number;
    timeline_risk_change: number;
    cost_change: number;
  };
  roi_score: number;
  confidence_score: number;
  explanation: string;
  recommendations: string[];
  risks: string[];
}

interface PresetScenario {
  name: string;
  description: string;
  actions: ScenarioAction[];
}

const API_BASE = 'http://localhost:8000/api/simulator';

export const DigitalTwinSimulator: React.FC = () => {
  const [actions, setActions] = useState<ScenarioAction[]>([]);
  const [scenarioName, setScenarioName] = useState('Custom Scenario');
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [actionTypes, setActionTypes] = useState<ActionType[]>([]);
  const [presets, setPresets] = useState<PresetScenario[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [sites, setSites] = useState<string[]>([]);

  const [newAction, setNewAction] = useState({
    action_type: 'add_cra',
    target: '',
    value: 2
  });

  // Default fallback data
  const defaultActionTypes: ActionType[] = [
    { type: 'add_cra', name: 'Add CRA', description: 'Add CRAs to a region', value_description: 'Number of CRAs' },
    { type: 'remove_cra', name: 'Remove CRA', description: 'Remove CRAs from a region', value_description: 'Number of CRAs' },
    { type: 'increase_monitoring', name: 'Increase Monitoring', description: 'Increase monitoring frequency', value_description: 'Percentage' },
    { type: 'decrease_monitoring', name: 'Decrease Monitoring', description: 'Decrease monitoring frequency', value_description: 'Percentage' },
    { type: 'close_site', name: 'Close Site', description: 'Close an underperforming site', value_description: '1 to close' },
    { type: 'add_training', name: 'Add Training', description: 'Add training sessions', value_description: 'Number of sessions' },
    { type: 'extend_timeline', name: 'Extend Timeline', description: 'Extend trial timeline', value_description: 'Weeks' },
  ];

  const defaultRegions = ['Region Europe', 'Region North America', 'Region Asia Pacific'];
  const defaultSites = ['Site 1', 'Site 2', 'Site 3', 'Site 4', 'Site 5'];
  const defaultPresets: PresetScenario[] = [
    { name: 'Add CRA Support', description: 'Add 2 CRAs to Europe', actions: [{ action_type: 'add_cra', target: 'Region Europe', value: 2 }] },
    { name: 'Increase Monitoring', description: 'Increase monitoring by 25%', actions: [{ action_type: 'increase_monitoring', target: 'All Sites', value: 25 }] },
    { name: 'Add Training', description: 'Add training sessions', actions: [{ action_type: 'add_training', target: 'All Sites', value: 2 }] },
  ];

  // Load initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [actionTypesRes, presetsRes, regionsRes, sitesRes] = await Promise.all([
          fetch(`${API_BASE}/action-types`),
          fetch(`${API_BASE}/presets`),
          fetch(`${API_BASE}/regions`),
          fetch(`${API_BASE}/sites`)
        ]);

        if (actionTypesRes.ok) {
          const data = await actionTypesRes.json();
          setActionTypes(data.action_types || defaultActionTypes);
        } else {
          setActionTypes(defaultActionTypes);
        }
        if (presetsRes.ok) {
          const data = await presetsRes.json();
          setPresets(data.presets || defaultPresets);
        } else {
          setPresets(defaultPresets);
        }
        if (regionsRes.ok) {
          const data = await regionsRes.json();
          setRegions(data.regions || defaultRegions);
          if (data.regions?.length > 0) {
            setNewAction(prev => ({ ...prev, target: data.regions[0] }));
          }
        } else {
          setRegions(defaultRegions);
        }
        if (sitesRes.ok) {
          const data = await sitesRes.json();
          setSites(data.sites || defaultSites);
        } else {
          setSites(defaultSites);
        }
      } catch (err) {
        console.error('Failed to load initial data, using defaults:', err);
        // Use fallback defaults
        setActionTypes(defaultActionTypes);
        setPresets(defaultPresets);
        setRegions(defaultRegions);
        setSites(defaultSites);
      }
    };
    fetchData();
  }, []);

  const addAction = useCallback((action: ScenarioAction) => {
    setActions(prev => [...prev, action]);
    setResult(null);
  }, []);

  const removeAction = useCallback((index: number) => {
    setActions(prev => prev.filter((_, i) => i !== index));
    setResult(null);
  }, []);

  const loadPreset = useCallback((preset: PresetScenario) => {
    setActions(preset.actions);
    setScenarioName(preset.name);
    setResult(null);
  }, []);

  const runSimulation = useCallback(async () => {
    if (actions.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: scenarioName,
          description: `Custom scenario with ${actions.length} action(s)`,
          actions: actions
        })
      });

      if (!response.ok) {
        throw new Error(`Simulation failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setLoading(false);
    }
  }, [actions, scenarioName]);

  const handleAddCustomAction = () => {
    if (newAction.target) {
      addAction({
        action_type: newAction.action_type,
        target: newAction.target,
        value: newAction.value
      });
    }
  };

  const getActionLabel = (action: ScenarioAction) => {
    const actionType = actionTypes.find(a => a.type === action.action_type);
    return actionType?.name || action.action_type;
  };

  const formatChange = (value: number, inverse: boolean = false) => {
    const positive = inverse ? value < 0 : value > 0;
    const sign = value > 0 ? '+' : '';
    return (
      <span className={`change ${positive ? 'positive' : value < 0 ? 'negative' : ''}`}>
        {sign}{value.toFixed(1)}
      </span>
    );
  };

  const formatCurrency = (value: number) => {
    const sign = value > 0 ? '+' : '';
    return `${sign}$${Math.abs(value).toLocaleString()}`;
  };

  return (
    <div className="digital-twin-simulator">
      {/* Header */}
      <div className="simulator-header">
        <div className="header-content">
          <h1>🧬 Digital Twin Simulator</h1>
          <p>Test "what-if" scenarios to optimize your clinical trial operations</p>
        </div>
      </div>

      <div className="simulator-content">
        {/* Left Panel - Scenario Builder */}
        <div className="scenario-builder">
          <div className="panel">
            <h2>📋 Build Your Scenario</h2>

            {/* Scenario Name */}
            <div className="form-group">
              <label>Scenario Name</label>
              <input
                type="text"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                placeholder="Enter scenario name"
              />
            </div>

            {/* Preset Scenarios */}
            <div className="presets-section">
              <h3>Quick Presets</h3>
              <div className="preset-buttons">
                {presets.map((preset, i) => (
                  <button
                    key={i}
                    className="preset-btn"
                    onClick={() => loadPreset(preset)}
                    title={preset.description}
                  >
                    {preset.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Action Builder */}
            <div className="action-builder">
              <h3>Add Custom Action</h3>
              <div className="action-form">
                <select
                  value={newAction.action_type}
                  onChange={(e) => setNewAction(prev => ({ ...prev, action_type: e.target.value }))}
                >
                  {actionTypes.map(at => (
                    <option key={at.type} value={at.type}>{at.name}</option>
                  ))}
                </select>

                <select
                  value={newAction.target}
                  onChange={(e) => setNewAction(prev => ({ ...prev, target: e.target.value }))}
                >
                  <option value="">Select Target</option>
                  <optgroup label="Regions">
                    {regions.map(r => <option key={r} value={r}>{r}</option>)}
                  </optgroup>
                  <optgroup label="Sites">
                    {sites.slice(0, 20).map(s => <option key={s} value={s}>{s}</option>)}
                  </optgroup>
                  <option value="All Sites">All Sites</option>
                </select>

                <input
                  type="number"
                  value={newAction.value}
                  onChange={(e) => setNewAction(prev => ({ ...prev, value: parseFloat(e.target.value) || 0 }))}
                  min="0"
                  step="1"
                />

                <button
                  className="add-btn"
                  onClick={handleAddCustomAction}
                  disabled={!newAction.target}
                >
                  + Add
                </button>
              </div>
            </div>

            {/* Active Actions */}
            <div className="active-actions">
              <h3>Active Actions ({actions.length})</h3>
              {actions.length === 0 ? (
                <p className="no-actions">No actions added yet. Use presets or add custom actions.</p>
              ) : (
                <div className="action-list">
                  {actions.map((action, i) => (
                    <div key={i} className="action-chip">
                      <span className="action-icon">✓</span>
                      <span className="action-text">
                        {getActionLabel(action)}: {action.target} ({action.value})
                      </span>
                      <button
                        className="remove-btn"
                        onClick={() => removeAction(i)}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Run Button */}
            <button
              className="run-simulation-btn"
              onClick={runSimulation}
              disabled={loading || actions.length === 0}
            >
              {loading ? (
                <>⏳ Running Simulation...</>
              ) : (
                <>▶️ Run Simulation</>
              )}
            </button>

            {error && <div className="error-message">{error}</div>}
          </div>
        </div>

        {/* Right Panel - Results */}
        <div className="simulation-results">
          {!result ? (
            <div className="no-results">
              <div className="empty-state">
                <span className="icon">🔮</span>
                <h3>Ready to Simulate</h3>
                <p>Add actions and run simulation to see predicted outcomes</p>
              </div>
            </div>
          ) : (
            <div className="panel results-panel">
              <h2>📊 Simulation Results</h2>

              {/* Key Metrics */}
              <div className="metrics-grid">
                <div className="metric-card dqi">
                  <div className="metric-header">
                    <span className="label">DQI Score</span>
                    <span className={`badge ${result.changes.dqi_change > 0 ? 'positive' : 'negative'}`}>
                      {result.changes.dqi_change > 0 ? '↑' : '↓'}
                    </span>
                  </div>
                  <div className="metric-values">
                    <span className="baseline">{result.baseline.dqi.toFixed(1)}</span>
                    <span className="arrow">→</span>
                    <span className="predicted">{result.predicted.dqi.toFixed(1)}</span>
                  </div>
                  <div className="metric-change">
                    {formatChange(result.changes.dqi_change)}
                  </div>
                </div>

                <div className="metric-card resolution">
                  <div className="metric-header">
                    <span className="label">Query Resolution</span>
                    <span className={`badge ${result.changes.query_resolution_change < 0 ? 'positive' : 'negative'}`}>
                      {result.changes.query_resolution_change < 0 ? '↓' : '↑'}
                    </span>
                  </div>
                  <div className="metric-values">
                    <span className="baseline">{result.baseline.query_resolution_days.toFixed(1)}d</span>
                    <span className="arrow">→</span>
                    <span className="predicted">{result.predicted.query_resolution_days.toFixed(1)}d</span>
                  </div>
                  <div className="metric-change">
                    {formatChange(result.changes.query_resolution_change, true)} days
                  </div>
                </div>

                <div className="metric-card risk">
                  <div className="metric-header">
                    <span className="label">Timeline Risk</span>
                    <span className={`badge ${result.changes.timeline_risk_change < 0 ? 'positive' : 'negative'}`}>
                      {result.changes.timeline_risk_change < 0 ? '↓' : '↑'}
                    </span>
                  </div>
                  <div className="metric-values">
                    <span className="baseline">{result.baseline.timeline_risk.toFixed(1)}%</span>
                    <span className="arrow">→</span>
                    <span className="predicted">{result.predicted.timeline_risk.toFixed(1)}%</span>
                  </div>
                  <div className="metric-change">
                    {formatChange(result.changes.timeline_risk_change, true)}%
                  </div>
                </div>

                <div className="metric-card cost">
                  <div className="metric-header">
                    <span className="label">Cost Impact</span>
                    <span className={`badge ${result.changes.cost_change < 0 ? 'positive' : 'negative'}`}>
                      {result.changes.cost_change < 0 ? '💰' : '📈'}
                    </span>
                  </div>
                  <div className="metric-value-single">
                    <span className={result.changes.cost_change > 0 ? 'negative' : 'positive'}>
                      {formatCurrency(result.changes.cost_change)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Confidence & ROI */}
              <div className="stats-row">
                <div className="stat">
                  <span className="stat-label">Confidence</span>
                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{ width: `${result.confidence_score * 100}%` }}
                    />
                  </div>
                  <span className="stat-value">{(result.confidence_score * 100).toFixed(0)}%</span>
                </div>
                <div className="stat">
                  <span className="stat-label">ROI Score</span>
                  <span className={`stat-value ${result.roi_score > 0 ? 'positive' : 'negative'}`}>
                    {result.roi_score.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* AI Explanation */}
              <div className="explanation-section">
                <h3>🤖 AI Analysis</h3>
                <div className="explanation-content">
                  {result.explanation.split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              </div>

              {/* Recommendations */}
              {result.recommendations.length > 0 && (
                <div className="recommendations-section">
                  <h3>💡 Recommendations</h3>
                  <ul>
                    {result.recommendations.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Risks */}
              {result.risks.length > 0 && (
                <div className="risks-section">
                  <h3>⚠️ Potential Risks</h3>
                  <ul>
                    {result.risks.map((risk, i) => (
                      <li key={i}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DigitalTwinSimulator;
