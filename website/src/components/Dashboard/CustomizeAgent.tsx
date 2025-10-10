import React from 'react';

const CustomizeAgent: React.FC = () => {
  return (
    <div className="dashboard-section">
      <h1 className="section-title">Customize Agent</h1>
      <div className="section-content">
        <div className="settings-group">
          <h3 className="settings-group-title">Agent Personality</h3>
          <div className="settings-item">
            <label className="settings-label">Agent Name</label>
            <input 
              type="text" 
              className="settings-input" 
              placeholder="Give your agent a name"
            />
          </div>
          <div className="settings-item">
            <label className="settings-label">Communication Style</label>
            <select className="settings-select">
              <option>Professional</option>
              <option>Casual</option>
              <option>Friendly</option>
              <option>Concise</option>
            </select>
          </div>
        </div>

        <div className="settings-group">
          <h3 className="settings-group-title">Agent Behavior</h3>
          <div className="settings-item">
            <label className="settings-label">Response Time</label>
            <select className="settings-select">
              <option>Instant</option>
              <option>Quick (1-2 seconds)</option>
              <option>Thoughtful (3-5 seconds)</option>
            </select>
          </div>
          <div className="settings-item checkbox">
            <input type="checkbox" id="proactive-suggestions" className="settings-checkbox" defaultChecked />
            <label htmlFor="proactive-suggestions" className="settings-label">
              Enable Proactive Suggestions
            </label>
          </div>
          <div className="settings-item checkbox">
            <input type="checkbox" id="calendar-integration" className="settings-checkbox" defaultChecked />
            <label htmlFor="calendar-integration" className="settings-label">
              Integrate with Calendar
            </label>
          </div>
        </div>

        <div className="settings-group">
          <h3 className="settings-group-title">Custom Instructions</h3>
          <div className="settings-item">
            <label className="settings-label">Additional Context</label>
            <textarea 
              className="settings-textarea" 
              rows={5}
              placeholder="Add any custom instructions or context for your agent..."
            />
          </div>
        </div>

        <div className="settings-actions">
          <button className="settings-button primary">Save Configuration</button>
          <button className="settings-button secondary">Reset to Default</button>
        </div>
      </div>
    </div>
  );
};

export default CustomizeAgent;
