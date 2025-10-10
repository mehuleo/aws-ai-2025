import React, { Component } from 'react';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarInset,
  SidebarSeparator,
} from '../ui/sidebar';
import { Settings, Sliders, LogOut, User } from 'lucide-react';
import logoImage from '../../assets/images/logo.png';
import './Dashboard.css';

// Extend Window interface to include Google Identity Services
declare global {
  interface Window {
    google: any;
  }
}

interface DashboardProps {}

interface DashboardState {
  activeSection: string;
  isAuthenticated: boolean;
  user: any;
  isLoading: boolean;
}

class Dashboard extends Component<DashboardProps, DashboardState> {
  constructor(props: DashboardProps) {
    super(props);
    this.state = {
      activeSection: 'settings',
      isAuthenticated: false,
      user: null,
      isLoading: true
    };
  }

  componentDidMount(): void {
    this.checkAuthentication();
  }

  checkAuthentication(): void {
    try {
      // Check if user data exists in localStorage
      const userData = localStorage.getItem('user');
      const accessToken = localStorage.getItem('google_access_token');
      console.log('userData', userData);
      console.log('accessToken', accessToken);
      
      if (userData) {
        const user = JSON.parse(userData);
        this.setState({
          isAuthenticated: true,
          user: user,
          isLoading: false
        });
        console.log('User authenticated:', user);
        
        // Check if access token is available (optional)
        if (accessToken) {
          console.log('Access token available for API calls');
        } else {
          console.log('No access token available - basic authentication only');
        }
      } else {
        // No authentication data found, redirect to home page
        console.log('No user data found, redirecting to home page');
        window.location.href = '/';
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
      // On error, redirect to home page
      window.location.href = '/';
    }
  }

  handleSectionChange(section: string): void {
    this.setState({ activeSection: section });
  }

  handleLogout(): void {
    console.log('Logging out...');
    
    // Clear all authentication data from localStorage
    localStorage.removeItem('user');
    localStorage.removeItem('google_access_token');
    
    // Disable Google auto-select if available
    if (window.google) {
      window.google.accounts.id.disableAutoSelect();
    }
    
    // Redirect to home page
    window.location.href = '/';
  }

  renderSettings(): React.JSX.Element {
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
              />
            </div>
            <div className="settings-item">
              <label className="settings-label">Email</label>
              <input 
                type="email" 
                className="settings-input" 
                placeholder="your.email@example.com"
              />
            </div>
          </div>

          <div className="settings-group">
            <h3 className="settings-group-title">Calendar Integration</h3>
            <div className="settings-item">
              <label className="settings-label">Google Calendar Access</label>
              <button className="settings-button secondary">
                Manage Permissions
              </button>
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
            <button className="settings-button danger" onClick={() => this.handleLogout()}>
              Logout
            </button>
          </div>
        </div>
      </div>
    );
  }

  renderCustomizeAgent(): React.JSX.Element {
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
  }

  renderSidebar(): React.JSX.Element {
    const { activeSection, user } = this.state;

    // Debug: Log user data to console
    console.log('User data in sidebar:', user);

    return (
      <Sidebar>
        <SidebarHeader>
          <div className="px-2 py-4">
            <img 
              src={logoImage} 
              alt="Logo" 
              className="sidebar-logo"
            />
          </div>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Navigation</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    onClick={() => this.handleSectionChange('settings')}
                    isActive={activeSection === 'settings'}
                    className={activeSection === 'settings' ? 'bg-purple-100 text-purple-600 font-semibold border-r-4 border-purple-600' : 'text-gray-600 hover:bg-gray-100 hover:text-purple-600'}
                  >
                    <Settings className="w-5 h-5" />
                    <span>Settings</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    onClick={() => this.handleSectionChange('customize')}
                    isActive={activeSection === 'customize'}
                    className={activeSection === 'customize' ? 'bg-purple-100 text-purple-600 font-semibold border-r-4 border-purple-600' : 'text-gray-600 hover:bg-gray-100 hover:text-purple-600'}
                  >
                    <Sliders className="w-5 h-5" />
                    <span>Customize Agent</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter>
          <SidebarSeparator />
          <div className="p-3">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
              {user?.picture ? (
                <img
                  src={user.picture}
                  alt={user.name || 'User'}
                  className="w-10 h-10 rounded-full border-2 border-gray-200 flex-shrink-0"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-purple-600" />
                </div>
              )}
              <div className="flex-1 min-w-0 overflow-hidden">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {user?.name || 'User Name'}
                </p>
                <p className="text-xs text-gray-600 truncate">
                  {user?.email || 'user@example.com'}
                </p>
              </div>
              <button
                onClick={() => this.handleLogout()}
                className="flex-shrink-0 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </SidebarFooter>
      </Sidebar>
    );
  }

  render() {
    const { activeSection, isAuthenticated, isLoading } = this.state;

    if (isLoading) {
      return (
        <div className="dashboard-loading">
          <div className="loading-spinner-large"></div>
          <p>Checking authentication...</p>
        </div>
      );
    }

    if (!isAuthenticated) {
      return (
        <div className="dashboard-loading">
          <div className="loading-spinner-large"></div>
          <p>Redirecting to login...</p>
        </div>
      );
    }

    return (
      <SidebarProvider defaultOpen={true}>
        <div className="flex min-h-screen w-full">
          {this.renderSidebar()}
          <SidebarInset className="flex-1">
            <main className="dashboard-main">
              {activeSection === 'settings' && this.renderSettings()}
              {activeSection === 'customize' && this.renderCustomizeAgent()}
            </main>
          </SidebarInset>
        </div>
      </SidebarProvider>
    );
  }
}

export default Dashboard;

