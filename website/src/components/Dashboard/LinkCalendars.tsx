import React, { Component } from 'react';
import { Calendar, Plus, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import './LinkCalendars.css';

interface CalendarItem {
  id: string;
  summary: string;
  description: string;
  primary: boolean;
  accessRole: string;
  backgroundColor: string;
  foregroundColor: string;
}

interface LinkCalendarsProps {}

interface LinkCalendarsState {
  calendars: CalendarItem[];
  isLoading: boolean;
  error: string | null;
  hasCalendarAccess: boolean;
}

class LinkCalendars extends Component<LinkCalendarsProps, LinkCalendarsState> {
  constructor(props: LinkCalendarsProps) {
    super(props);
    this.state = {
      calendars: [],
      isLoading: false,
      error: null,
      hasCalendarAccess: false
    };
  }

  componentDidMount(): void {
    console.debug('LinkCalendars component mounted');
    // Check if we're being accessed with OAuth redirect parameters
    this.checkForOAuthRedirect();
    this.checkCalendarAccess();
  }

  async checkForOAuthRedirect(): Promise<void> {
    console.debug('checkForOAuthRedirect');
    // Check if we have OAuth parameters in the URL
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const scope = urlParams.get('scope');
    const error = urlParams.get('error');

    console.log('OAuth params:', { code, state, scope, error });

    if (code || error) {
      console.log('OAuth redirect detected in calendar component:', { code, state, scope, error });
      
      if (error) {
        this.setState({ error: `OAuth error: ${error}` });
        // Clear URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      }

      if (code) {
        await this.exchangeCodeForToken(code, state);
      }
    }
  }

  async exchangeCodeForToken(code: string, state: string | null): Promise<void> {
    try {
      const userEmail = localStorage.getItem('email');
      const userSid = localStorage.getItem('sid');
      
      if (!userEmail || !userSid) {
        this.setState({ error: 'Authentication required for token exchange' });
        return;
      }

      this.setState({ isLoading: true, error: null });

      const response = await fetch('https://api.superagent.diy/v1/validateGoogleAuth', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'exchange_code',
          email: userEmail,
          sid: userSid,
          code: code,
          state: state,
          redirect_uri: window.location.origin
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log('Token exchange successful');
          // Store calendar access flag
          localStorage.setItem('calendar_access', 'true');
          // Clear URL parameters to avoid re-processing
          window.history.replaceState({}, document.title, window.location.pathname);
          // Refresh calendar access
          await this.checkCalendarAccess();
        } else {
          this.setState({ 
            error: data.error || 'Failed to exchange code for token',
            isLoading: false 
          });
        }
      } else {
        const errorData = await response.json();
        this.setState({ 
          error: errorData.error || 'Failed to exchange code for token',
          isLoading: false 
        });
      }
    } catch (error) {
      console.error('Error exchanging code for token:', error);
      this.setState({ 
        error: 'Network error while exchanging code for token',
        isLoading: false 
      });
    }
  }

  async checkCalendarAccess(): Promise<void> {
    const userEmail = localStorage.getItem('email');
    const userSid = localStorage.getItem('sid');
    const calendarAccess = localStorage.getItem('calendar_access') === 'true';

    if (calendarAccess && userEmail && userSid) {
      this.setState({ hasCalendarAccess: true });
      await this.fetchCalendars();
    } else {
      this.setState({ hasCalendarAccess: false });
    }
  }

  async fetchCalendars(): Promise<void> {
    const userEmail = localStorage.getItem('email');
    const userSid = localStorage.getItem('sid');

    if (!userEmail || !userSid) {
      this.setState({ error: 'Authentication required' });
      return;
    }

    this.setState({ isLoading: true, error: null });

    try {
      const response = await fetch('https://api.superagent.diy/v1/validateGoogleAuth', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'get_calendars',
          email: userEmail,
          sid: userSid
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.calendars) {
          this.setState({ 
            calendars: data.calendars,
            isLoading: false 
          });
        } else {
          this.setState({ 
            error: data.error || 'Failed to fetch calendars',
            isLoading: false 
          });
        }
      } else {
        const errorData = await response.json();
        this.setState({ 
          error: errorData.error || 'Failed to fetch calendars',
          isLoading: false 
        });
      }
    } catch (error) {
      console.error('Error fetching calendars:', error);
      this.setState({ 
        error: 'Network error while fetching calendars',
        isLoading: false 
      });
    }
  }

  async requestCalendarAccess(): Promise<void> {
    try {
      const userEmail = localStorage.getItem('email');
      const userSid = localStorage.getItem('sid');
      
      if (!userEmail || !userSid) {
        this.setState({ error: 'Authentication required' });
        return;
      }

      const response = await fetch('https://api.superagent.diy/v1/validateGoogleAuth', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'get_calendar_access',
          email: userEmail,
          redirect_uri: window.location.origin
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('data', data.success);
        if (data.success && data.oauth_url) {
            console.log('data.oauth_url', data.oauth_url);
          // Redirect to Google OAuth for calendar access
          window.location.href = data.oauth_url;
        }
      } else {
        const errorData = await response.json();
        this.setState({ error: errorData.error || 'Failed to request calendar access' });
      }
    } catch (error) {
      console.error('Error requesting calendar access:', error);
      this.setState({ error: 'Network error while requesting calendar access' });
    }
  }


  handleRefresh = (): void => {
    this.fetchCalendars();
  };

  renderCalendarItem = (calendar: CalendarItem): React.JSX.Element => {
    return (
      <div key={calendar.id} className="calendar-item">
        <div 
          className="calendar-color-indicator"
          style={{ backgroundColor: calendar.backgroundColor }}
        ></div>
        <div className="calendar-info">
          <div className="calendar-name">
            {calendar.summary}
            {calendar.primary && (
              <span className="primary-badge">Primary</span>
            )}
          </div>
          {calendar.description && (
            <div className="calendar-description">{calendar.description}</div>
          )}
          <div className="calendar-access">
            Access: {calendar.accessRole}
          </div>
        </div>
        <div className="calendar-status">
          <CheckCircle className="w-5 h-5 text-green-500" />
        </div>
      </div>
    );
  };

  render(): React.JSX.Element {
    const { calendars, isLoading, error, hasCalendarAccess } = this.state;

    return (
      <div className="link-calendars-container">
        <div className="link-calendars-header">
          <div className="header-content">
            <Calendar className="w-8 h-8 text-purple-600" />
            <div>
              <h2 className="link-calendars-title">Your Linked Calendars</h2>
              <p className="link-calendars-subtitle">
                Connect your Google Calendar to enable intelligent email scheduling and event management.
                Your AI agent can help you find the best times for meetings and automatically respond to calendar-related emails.
              </p>
            </div>
          </div>
        </div>

        <div className="link-calendars-content">
          {!hasCalendarAccess ? (
            <div className="no-access-section">
              <div className="no-access-content">
                <AlertCircle className="w-12 h-12 text-amber-500 mb-4" />
                <h3 className="no-access-title">Calendar Access Required</h3>
                <p className="no-access-description">
                  To view and manage your calendars, you need to grant access to your Google Calendar.
                  This allows your AI agent to help with scheduling and event management.
                </p>
                <button 
                  onClick={this.requestCalendarAccess}
                  className="link-calendar-button"
                >
                  <Plus className="w-5 h-5" />
                  Link Google Calendar
                </button>
              </div>
            </div>
          ) : (
            <div className="calendars-section">
              <div className="calendars-header">
                <h3 className="calendars-title">Connected Calendars</h3>
                <button 
                  onClick={this.handleRefresh}
                  disabled={isLoading}
                  className="refresh-button"
                  title="Refresh calendars"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>

              {isLoading ? (
                <div className="loading-section">
                  <RefreshCw className="w-6 h-6 animate-spin text-purple-600" />
                  <p>Loading calendars...</p>
                </div>
              ) : error ? (
                <div className="error-section">
                  <AlertCircle className="w-6 h-6 text-red-500" />
                  <p className="error-message">{error}</p>
                  <button 
                    onClick={this.handleRefresh}
                    className="retry-button"
                  >
                    Try Again
                  </button>
                </div>
              ) : calendars.length === 0 ? (
                <div className="empty-section">
                  <Calendar className="w-12 h-12 text-gray-400" />
                  <p className="empty-message">No calendars found</p>
                </div>
              ) : (
                <div className="calendars-list">
                  {calendars.map(this.renderCalendarItem)}
                </div>
              )}

              <div className="calendars-footer">
                <p className="footer-text">
                  Need to add more calendars? 
                  <button 
                    onClick={this.requestCalendarAccess}
                    className="link-text-button"
                  >
                    Re-authorize access
                  </button>
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }
}

export default LinkCalendars;
