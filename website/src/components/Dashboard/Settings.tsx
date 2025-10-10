import React from 'react';

interface SettingsProps {
  onLogout: () => void;
  onRequestCalendarAccess: () => void;
}

const Settings: React.FC<SettingsProps> = ({ onLogout, onRequestCalendarAccess }) => {
  // Get user data from localStorage for pre-filling form
  const userEmail = localStorage.getItem('email');
  const userName = localStorage.getItem('user_name');
  const emailVerified = localStorage.getItem('email_verified') === 'true';
  const calendarAccess = localStorage.getItem('calendar_access') === 'true';

  return (
    <div className="dashboard-section">
      <h1 className="section-title">Settings</h1>
      <div className="section-content">
        <div className="settings-group">
          <h3 className="settings-group-title">Profile Settings</h3>
          <div className="settings-item">
            <label className="settings-label">Display Name</label>
            <input 
              type="text" 
              className="settings-input" 
              placeholder="Enter your display name"
              defaultValue={userName || ''}
            />
          </div>
          <div className="settings-item">
            <label className="settings-label">Email</label>
            <input 
              type="email" 
              className="settings-input" 
              placeholder="your.email@example.com"
              defaultValue={userEmail || ''}
              disabled
            />
            {emailVerified && (
              <div className="flex items-center gap-2 mt-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-xs text-green-600">Email verified</span>
              </div>
            )}
          </div>
        </div>

        <div className="settings-group">
          <h3 className="settings-group-title">Calendar Integration</h3>
          <div className="settings-item">
            <label className="settings-label">Google Calendar Access</label>
            <div className="flex items-center gap-3">
              <button 
                className="settings-button secondary"
                onClick={onRequestCalendarAccess}
              >
                {calendarAccess ? 'Manage Permissions' : 'Grant Calendar Access'}
              </button>
              {calendarAccess && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-xs text-green-600">Calendar access granted</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="settings-group">
          <h3 className="settings-group-title">Notifications</h3>
          <div className="settings-item checkbox">
            <input type="checkbox" id="email-notifications" className="settings-checkbox" />
            <label htmlFor="email-notifications" className="settings-label">
              Email Notifications
            </label>
          </div>
          <div className="settings-item checkbox">
            <input type="checkbox" id="calendar-reminders" className="settings-checkbox" />
            <label htmlFor="calendar-reminders" className="settings-label">
              Calendar Reminders
            </label>
          </div>
        </div>

        <div className="settings-actions">
          <button className="settings-button primary">Save Changes</button>
          <button className="settings-button danger" onClick={onLogout}>
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
