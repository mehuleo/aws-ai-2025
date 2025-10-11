import React, { Component, RefObject } from 'react';
import './GoogleLoginButton.css';

// Extend Window interface to include Google Identity Services
declare global {
  interface Window {
    google: any;
  }
}

interface GoogleLoginButtonProps {
  onLoginSuccess: (user: any) => void;
  onTokenResponse?: (response: any) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

interface GoogleLoginButtonState {
  isLoading: boolean;
}

class GoogleLoginButton extends Component<GoogleLoginButtonProps, GoogleLoginButtonState> {
  private buttonRef: RefObject<HTMLDivElement | null>;

  constructor(props: GoogleLoginButtonProps) {
    super(props);
    this.state = {
      isLoading: props.isLoading || false
    };
    this.buttonRef = React.createRef<HTMLDivElement | null>();
  }

  componentDidMount(): void {
    this.initializeGoogleAuth();
  }

  validateTokenWithBackend = async (token: string): Promise<any> => {
    try {
      const response = await fetch('https://api.superagent.diy/v1/validateGoogleAuth', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'validate_token',
          token: token
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Authentication failed');
      }

      return data.user;
    } catch (error) {
      console.error('Error validating token with backend:', error);
      throw error;
    }
  };

  initializeGoogleAuth = (): void => {
    if (window.google) {
      const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
      console.log('Google Client ID:', clientId ? 'Set' : 'Not set');
      
      if (!clientId) {
        console.error('REACT_APP_GOOGLE_CLIENT_ID is not set in environment variables');
        return;
      }

      // Initialize Google Identity Services
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: this.handleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true
      });

      // Configure OAuth scope for additional permissions
      if (this.props.onTokenResponse) {
        window.google.accounts.oauth2.initTokenClient({
          client_id: clientId,
          scope: 'email profile https://www.googleapis.com/auth/calendar',
          callback: this.props.onTokenResponse
        });
      }

      // Render the Google Sign-In button
      if (this.buttonRef.current) {
        window.google.accounts.id.renderButton(this.buttonRef.current, {
          theme: 'outline',
          size: 'large',
          width: 250,
          text: 'signin_with',
          shape: 'rectangular'
        });
      }
      
      console.log('Google Identity Services initialized successfully');
    } else {
      // Retry if Google script hasn't loaded yet
      setTimeout(this.initializeGoogleAuth, 100);
    }
  };

  handleCredentialResponse = async (response: any): Promise<void> => {
    console.log('Received credential response:', response);
    
    try {
      if (!response.credential) {
        throw new Error('No credential received from Google');
      }

      // Validate token with backend
      const user = await this.validateTokenWithBackend(response.credential);
      
      // Store specific user data fields in localStorage
      if (user.email) {
        localStorage.setItem('email', user.email);
      }
      if (user.sid) {
        localStorage.setItem('sid', user.sid);
      }
      if (user.user_name) {
        localStorage.setItem('user_name', user.user_name);
      }
      if (user.picture) {
        localStorage.setItem('picture', user.picture);
      }
      if (user.email_verified !== undefined) {
        localStorage.setItem('email_verified', user.email_verified.toString());
      }
      if (user.calendar_access !== undefined) {
        localStorage.setItem('calendar_access', user.calendar_access.toString());
      }
      
      // Also store the complete user object for backward compatibility
      localStorage.setItem('user', JSON.stringify(user));
      
      // Call the parent component's success handler with user data
      this.props.onLoginSuccess(user);
      
      // Also request OAuth token for additional scopes if callback is provided
      if (this.props.onTokenResponse && window.google) {
        console.log('Requesting OAuth access token...');
        try {
          window.google.accounts.oauth2.requestAccessToken();
        } catch (error) {
          console.log('OAuth token request failed:', error);
        }
      }
      
    } catch (error) {
      console.error('Error processing Google auth response:', error);
      // You might want to show an error message to the user here
    }
  };

  handleGoogleLogin = (): void => {
    if (window.google && !this.props.disabled && !this.props.isLoading) {
      console.log('Attempting Google login...');
      try {
        // Trigger the Google Sign-In prompt
        window.google.accounts.id.prompt();
      } catch (error) {
        console.error('Error during Google login prompt:', error);
      }
    } else if (!window.google) {
      console.error('Google Identity Services not loaded');
    }
  };

  render(): React.JSX.Element {
    const { isLoading } = this.props;

    return (
      <div className="google-login-container">
        <div 
          ref={this.buttonRef} 
          className="google-login-button-wrapper"
          onClick={this.handleGoogleLogin}
        />
        {isLoading && (
          <div className="google-login-loading">
            <div className="loading-spinner" />
            <span>Signing in...</span>
          </div>
        )}
      </div>
    );
  }
}

export default GoogleLoginButton;
