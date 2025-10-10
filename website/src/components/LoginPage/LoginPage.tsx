import React, { Component } from 'react';
import './LoginPage.css';

interface LoginPageProps {}

interface LoginPageState {
  isLoading: boolean;
}

class LoginPage extends Component<LoginPageProps, LoginPageState> {
  constructor(props: LoginPageProps) {
    super(props);
    this.state = {
      isLoading: false
    };
  }

  handleGoogleSignIn(): void {
    this.setState({ isLoading: true });
    
    // TODO: Implement Google OAuth with Calendar API access
    // This will require:
    // 1. Google OAuth Client ID setup
    // 2. Request scopes: 'https://www.googleapis.com/auth/calendar'
    // 3. Handle authentication flow
    // 4. Store authentication token
    // 5. Redirect to dashboard on success
    
    console.log('Google Sign-In initiated');
    
    // Placeholder for development - remove in production
    setTimeout(() => {
      this.setState({ isLoading: false });
      // window.location.href = '/dashboard';
    }, 1500);
  }

  render() {
    const { isLoading } = this.state;

    return (
      <div className="login-page">
        {/* Left Panel - Promotional Content */}
        <div className="promotional-panel">
          <div className="promotional-content">
            <div className="logo-section">
              <h1 className="brand-logo">workstation =</h1>
            </div>
            <h2 className="main-heading">
              Hang out with friends, co-workers, and even AI – all in one place!
            </h2>
            <p className="description">
              Whether you're brainstorming with AI, chatting with friends, or collaborating with your team, it's all happening here. Play games, swap stories, or dive into the future of conversations—all without switching apps. Fun, flexibility, and a dash of AI genius, all in one chat hub.
            </p>
          </div>
        </div>

        {/* Right Panel - Login Interface */}
        <div className="login-panel">
          <div className="browser-window">
            <div className="browser-header">
              <div className="browser-controls">
                <div className="control-dot red"></div>
                <div className="control-dot yellow"></div>
                <div className="control-dot green"></div>
              </div>
              <div className="url-bar">
                <span className="url-text">workstation.com</span>
                <div className="url-icons">
                  <div className="url-icon">↻</div>
                  <div className="url-icon">↑</div>
                  <div className="url-icon">↓</div>
                  <div className="url-icon">+</div>
                </div>
              </div>
            </div>
            
            <div className="app-interface">
              <div className="login-container">
                <div className="login-card">
                  <h1 className="login-title">Welcome Back</h1>
                  <p className="login-subtitle">
                    Sign in with your Google account to access your dashboard
                  </p>
                  
                  <button 
                    className="google-signin-button"
                    onClick={() => this.handleGoogleSignIn()}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <span className="loading-spinner"></span>
                    ) : (
                      <>
                        <svg className="google-icon" viewBox="0 0 24 24">
                          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        Sign in with Google
                      </>
                    )}
                  </button>
                  
                  <div className="login-permissions">
                    <p className="permissions-text">
                      This app requires access to:
                    </p>
                    <ul className="permissions-list">
                      <li>Read and write access to your Google Calendar</li>
                      <li>Basic profile information</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default LoginPage;

