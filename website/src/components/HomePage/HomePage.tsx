import React, { Component } from 'react';
import './HomePage.css';
import logo from '../../assets/images/logo.png';
import hero from '../../assets/images/hero.png';
import GoogleLoginButton from '../GoogleLoginButton/GoogleLoginButton';

interface HomePageProps {}

interface HomePageState {
  isAuthenticated: boolean;
  user: any;
  isLoading: boolean;
}

// Extend Window interface to include Google Identity Services
declare global {
  interface Window {
    google: any;
  }
}

class HomePage extends Component<HomePageProps, HomePageState> {
  constructor(props: HomePageProps) {
    super(props);
    this.state = {
      isAuthenticated: false,
      user: null,
      isLoading: false
    };
  }

  componentDidMount() {
    // Component mounted - no Google auth initialization needed here anymore
  }

  handleLoginSuccess = (token: string) => {
    console.log('Received login success with token:', token);
    this.setState({ isLoading: true });
    
    try {
      if (!token) {
        throw new Error('No token received from Google');
      }

      // Decode the JWT token to get user info
      const payload = JSON.parse(atob(token.split('.')[1]));
      
      this.setState({
        isAuthenticated: true,
        user: {
          id: payload.sub,
          name: payload.name,
          email: payload.email,
          picture: payload.picture
        },
        isLoading: false
      });

      console.log('User authenticated successfully:', payload);
      
      // Store user data in localStorage for persistence
      localStorage.setItem('user', JSON.stringify({
        id: payload.sub,
        name: payload.name,
        email: payload.email,
        picture: payload.picture
      }));
      
      // Redirect to Dashboard after successful login (backend call is optional)
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 1000); // Small delay to show success state
      
      // Optionally send token to backend (non-blocking)
      this.sendTokenToBackend(token).catch(error => {
        console.log('Backend not available yet, continuing with frontend-only auth:', error);
      });
      
    } catch (error) {
      console.error('Error processing Google auth response:', error);
      this.setState({ isLoading: false });
    }
  };

  handleTokenResponse = (response: any) => {
    console.log('Received OAuth token response:', response);
    
    if (response.access_token) {
      // Store the access token for API calls
      localStorage.setItem('google_access_token', response.access_token);
      console.log('Access token stored for API calls:', response.access_token);
      
      // You can now make API calls to Google Calendar, Gmail, etc.
      // Example: this.fetchCalendarEvents(response.access_token);
    } else {
      console.log('No access token in OAuth response');
    }
  };

  // Example method to fetch calendar events using the access token
  fetchCalendarEvents = async (accessToken: string) => {
    try {
      const response = await fetch('https://www.googleapis.com/calendar/v3/calendars/primary/events', {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Calendar events:', data);
        return data;
      } else {
        console.error('Failed to fetch calendar events:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching calendar events:', error);
    }
  };

  sendTokenToBackend = async (token: string) => {
    try {
      // TODO: Replace with your actual backend endpoint
      const response = await fetch('/api/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Backend authentication successful:', data);
        // Handle successful backend authentication
      } else {
        console.log('Backend authentication failed - continuing with frontend-only auth');
        // Don't throw error, just log it
      }
    } catch (error) {
      console.log('Backend not available - continuing with frontend-only auth:', error);
      // Don't throw error, just log it
    }
  };


  handleLogout = () => {
    if (window.google) {
      window.google.accounts.id.disableAutoSelect();
    }
    
    // Clear stored access token
    localStorage.removeItem('google_access_token');
    
    this.setState({
      isAuthenticated: false,
      user: null
    });
  };

  render() {
    const { isAuthenticated, user, isLoading } = this.state;

    return (
      <div className="home-page">
        <header className="home-header">
          <img src={logo} alt="Logo" className="home-logo" />
          {isAuthenticated ? (
            <div className="user-info">
              <img src={user.picture} alt={user.name} className="user-avatar" />
              <span className="user-name">{user.name}</span>
              <button className="logout-button" onClick={this.handleLogout}>
                Logout
              </button>
            </div>
          ) : (
            <GoogleLoginButton
              onLoginSuccess={this.handleLoginSuccess}
              onTokenResponse={this.handleTokenResponse}
              isLoading={isLoading}
            />
          )}
        </header>
        
        <main className="home-main">
          <section className="home-content">
            <h1 className="home-title">
              {isAuthenticated 
                ? `Welcome back, ${user.name}!` 
                : 'Hang out with friends, co-workers, and even AI — all in one place!'
              }
            </h1>
            <p className="home-subtitle">
              {isAuthenticated 
                ? 'You\'re all set! Start chatting with friends, collaborating with your team, or exploring AI-powered conversations.'
                : 'Whether you\'re brainstorming with AI, chatting with friends, or collaborating with your team, it\'s all happening here. Play games, swap stories, or dive into the future of conversations — all without switching apps. Fun, flexibility, and a dash of AI genius, all in one chat hub.'
              }
            </p>
            {isAuthenticated && (
              <div className="welcome-actions">
                <button className="cta-button primary">
                  Start Chatting
                </button>
                <button className="cta-button secondary">
                  Explore Features
                </button>
              </div>
            )}
          </section>
          
          <section className="home-hero">
            <img src={hero} alt="Hero" className="home-hero-image" />
          </section>
        </main>
      </div>
    );
  }
}

export default HomePage;

