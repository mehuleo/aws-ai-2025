import React, { useEffect, useRef } from 'react';
import './GoogleLoginButton.css';

// Extend Window interface to include Google Identity Services
declare global {
  interface Window {
    google: any;
  }
}

interface GoogleLoginButtonProps {
  onLoginSuccess: (token: string) => void;
  onTokenResponse?: (response: any) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const GoogleLoginButton: React.FC<GoogleLoginButtonProps> = ({
  onLoginSuccess,
  onTokenResponse,
  isLoading = false,
  disabled = false
}) => {
  const buttonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    initializeGoogleAuth();
  }, []);

  const initializeGoogleAuth = () => {
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
        callback: handleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true
      });

      // Configure OAuth scope for additional permissions
      if (onTokenResponse) {
        window.google.accounts.oauth2.initTokenClient({
          client_id: clientId,
          scope: 'email profile https://www.googleapis.com/auth/calendar',
          callback: onTokenResponse
        });
      }

      // Render the Google Sign-In button
      if (buttonRef.current) {
        window.google.accounts.id.renderButton(buttonRef.current, {
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
      setTimeout(initializeGoogleAuth, 100);
    }
  };

  const handleCredentialResponse = (response: any) => {
    console.log('Received credential response:', response);
    
    try {
      if (!response.credential) {
        throw new Error('No credential received from Google');
      }

      // Call the parent component's success handler
      onLoginSuccess(response.credential);
      
      // Also request OAuth token for additional scopes if callback is provided
      if (onTokenResponse && window.google) {
        console.log('Requesting OAuth access token...');
        try {
          window.google.accounts.oauth2.requestAccessToken();
        } catch (error) {
          console.log('OAuth token request failed:', error);
        }
      }
      
    } catch (error) {
      console.error('Error processing Google auth response:', error);
    }
  };

  const handleGoogleLogin = () => {
    if (window.google && !disabled && !isLoading) {
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

  return (
    <div className="google-login-container">
      <div 
        ref={buttonRef} 
        className="google-login-button-wrapper"
        onClick={handleGoogleLogin}
      />
      {isLoading && (
        <div className="google-login-loading">
          <div className="loading-spinner" />
          <span>Signing in...</span>
        </div>
      )}
    </div>
  );
};

export default GoogleLoginButton;
