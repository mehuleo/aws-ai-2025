import React, { Component } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
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
import { Settings, Sliders, LogOut, User, Calendar, Plus } from 'lucide-react';
import logoImage from '../../assets/images/logo.png';
import SettingsComponent from './Settings';
import CustomizeAgent from './CustomizeAgent';
import LinkCalendars from './LinkCalendars';
import CreateExecutiveAssistant from './CreateExecutiveAssistant';
import './Dashboard.css';
import { Route, DashboardSection, validDashboardSections } from '../../constants/routes';

// Extend Window interface to include Google Identity Services
declare global {
  interface Window {
    google: any;
  }
}

interface DashboardProps {
  navigate?: any;
  location?: any;
}

interface DashboardState {
  activeSection: DashboardSection;
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
    console.debug('Dashboard component mounted');
    this.initializeSectionFromURL();
    this.checkAuthentication();
  }

  componentDidUpdate(prevProps: DashboardProps): void {
    // Update active section when location changes
    if (prevProps.location?.pathname !== this.props.location?.pathname) {
      this.initializeSectionFromURL();
    }
  }

  async checkAuthentication(): Promise<void> {
    try {
      // Check if required authentication data exists in localStorage
      const userEmail = localStorage.getItem('email');
      const userSid = localStorage.getItem('sid');
      const userData = localStorage.getItem('user');
      
      console.log('Authentication data:', { email: userEmail, sid: userSid, hasUserData: !!userData });
      
      if (userEmail && userSid) {
        // Validate user with backend using email and sid
        try {
          const response = await fetch('https://api.superagent.diy/v1/validateGoogleAuth', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              action: 'get_user',
              email: userEmail,
              sid: userSid
            })
          });

          if (response.ok) {
            const data = await response.json();
            if (data.success && data.user) {
              // Authentication successful - update localStorage with fresh data
              const updatedUser = data.user;
              
              // Update localStorage with fresh user data
              if (updatedUser.email) localStorage.setItem('email', updatedUser.email);
              if (updatedUser.sid) localStorage.setItem('sid', updatedUser.sid);
              if (updatedUser.user_name) localStorage.setItem('user_name', updatedUser.user_name);
              if (updatedUser.picture) localStorage.setItem('picture', updatedUser.picture);
              if (updatedUser.email_verified !== undefined) {
                localStorage.setItem('email_verified', updatedUser.email_verified.toString());
              }
              if (updatedUser.calendar_access !== undefined) {
                localStorage.setItem('calendar_access', updatedUser.calendar_access.toString());
              }
              localStorage.setItem('user', JSON.stringify(updatedUser));
              
              this.setState({
                isAuthenticated: true,
                user: updatedUser,
                isLoading: false
              });
              console.log('User authenticated with backend:', updatedUser);
              return;
            } else {
              // Authentication failed - user not found or invalid
              console.log('Authentication failed - invalid user or session expired');
              this.handleLogout();
              return;
            }
          } else {
            // HTTP error response
            console.log('Authentication failed - HTTP error:', response.status);
            this.handleLogout();
            return;
          }
        } catch (backendError) {
          console.error('Backend validation failed:', backendError);
          // On backend error, logout and redirect
          this.handleLogout();
          return;
        }
      } else {
        // Missing required authentication data
        console.log('Missing authentication data (email or sid), redirecting to home page');
        this.handleLogout();
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
      // On any error, logout and redirect
      this.handleLogout();
    }
  }

  handleSectionChange(section: DashboardSection): void {
    const { navigate } = this.props;
    this.setState({ activeSection: section });
    
    // Navigate to the appropriate path
    const pathMap: Record<DashboardSection, string> = {
      'settings': Route.dashboard.settings,
      'customize': Route.dashboard.customize,
      'calendars': Route.dashboard.calendars,
      'create-assistant': Route.dashboard['create-assistant'],
    };
    
    if (navigate) {
      navigate(pathMap[section]);
    }
  }

  initializeSectionFromURL(): void {
    const { location } = this.props;
    const pathname = location?.pathname || window.location.pathname;
    
    // Extract section from pathname: /dashboard/settings -> settings
    const pathParts = pathname.split('/').filter(Boolean);
    const section = pathParts[pathParts.length - 1];
    
    console.log('Current pathname:', pathname);
    console.log('Extracted section:', section);
    
    if (section && validDashboardSections.includes(section as DashboardSection)) {
      console.log('Section is valid:', section);
      this.setState({ activeSection: section as DashboardSection });
    } else {
      // Default to settings if path doesn't match
      this.setState({ activeSection: 'calendars' });
    }
  }

  handleLogout(): void {
    console.log('Logging out...');
    
    // Clear all authentication data from localStorage
    localStorage.removeItem('user');
    localStorage.removeItem('google_access_token');
    localStorage.removeItem('email');
    localStorage.removeItem('sid');
    localStorage.removeItem('name');
    localStorage.removeItem('picture');
    localStorage.removeItem('email_verified');
    localStorage.removeItem('calendar_access');
    
    // Disable Google auto-select if available
    if (window.google) {
      window.google.accounts.id.disableAutoSelect();
    }
    
    // Redirect to home page
    window.location.href = Route.home;
  }



  renderSidebar(): React.JSX.Element {
    const { activeSection } = this.state;

    // Get user data from localStorage
    const userEmail = localStorage.getItem('email');
    const userName = localStorage.getItem('user_name');
    const userPicture = localStorage.getItem('picture');
    const emailVerified = localStorage.getItem('email_verified') === 'true';
    const calendarAccess = localStorage.getItem('calendar_access') === 'true';

    // Debug: Log user data to console
    console.log('User data from localStorage:', {
      email: userEmail,
      name: userName,
      picture: userPicture,
      email_verified: emailVerified,
      calendar_access: calendarAccess
    });

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
                    onClick={() => this.handleSectionChange('calendars')}
                    isActive={activeSection === 'calendars'}
                    className={activeSection === 'calendars' ? 'bg-purple-100 text-purple-600 font-semibold border-r-4 border-purple-600' : 'text-gray-600 hover:bg-gray-100 hover:text-purple-600'}
                  >
                    <Calendar className="w-5 h-5" />
                    <span>Link Calendars</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>

                <SidebarMenuItem>
                  <SidebarMenuButton
                    onClick={() => this.handleSectionChange('create-assistant')}
                    isActive={activeSection === 'create-assistant'}
                    className={activeSection === 'create-assistant' ? 'bg-purple-100 text-purple-600 font-semibold border-r-4 border-purple-600' : 'text-gray-600 hover:bg-gray-100 hover:text-purple-600'}
                  >
                    <Plus className="w-5 h-5" />
                    <span>Create Executive Assistant</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>

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
              {userPicture ? (
                <img
                  src={userPicture}
                  alt={userName || 'User'}
                  className="w-10 h-10 rounded-full border-2 border-gray-200 flex-shrink-0"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-purple-600" />
                </div>
              )}
              <div className="flex-1 min-w-0 overflow-hidden">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {userName || 'User Name'}
                </p>
                <p className="text-xs text-gray-600 truncate">
                  {userEmail || 'user@example.com'}
                </p>
                {emailVerified && (
                  <div className="flex items-center gap-1 mt-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-green-600">Verified</span>
                  </div>
                )}
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
              {activeSection === 'settings' && (
                <SettingsComponent 
                  onLogout={this.handleLogout}
                  onNavigateToCalendars={() => this.handleSectionChange('calendars')}
                />
              )}
              {activeSection === 'customize' && <CustomizeAgent />}
              {activeSection === 'calendars' && <LinkCalendars />}
              {activeSection === 'create-assistant' && <CreateExecutiveAssistant />}
            </main>
          </SidebarInset>
        </div>
      </SidebarProvider>
    );
  }
}

// HOC to inject navigate and location into class component
function withRouter(Component: typeof Dashboard) {
  return function WrappedComponent(props: any) {
    const navigate = useNavigate();
    const location = useLocation();
    return <Component {...props} navigate={navigate} location={location} />;
  };
}

export default withRouter(Dashboard);

