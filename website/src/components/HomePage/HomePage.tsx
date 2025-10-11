import React, { Component } from 'react';
import './HomePage.css';
import logo from '../../assets/images/logo.png';
import hero from '../../assets/images/hero.png';
import GoogleLoginButton from '../GoogleLoginButton/GoogleLoginButton';
import { Route } from '../../constants/routes';

interface HomePageProps {}

class HomePage extends Component<HomePageProps> {
  componentDidMount() {
    // Check for Google Auth redirect parameters
    this.checkForAuthRedirect();
  }

  checkForAuthRedirect = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const state = urlParams.get('state');
    const code = urlParams.get('code');
    const scope = urlParams.get('scope');
    const error = urlParams.get('error');

    // If we have Google Auth parameters, redirect to dashboard calendars with OAuth parameters
    if (state || code || scope || error) {
      console.log('Google Auth redirect detected:', { state, code, scope, error });
      // Redirect to dashboard calendars page and preserve the OAuth parameters
      const redirectUrl = `${Route.dashboard.calendars}?${urlParams.toString()}`;
      window.location.href = redirectUrl;
    }
  }

  handleLoginSuccess = (user: any) => {
    console.log('Login successful:', user);
    // Redirect to dashboard settings after successful login
    window.location.href = Route.dashboard.settings;
  };

  handleTokenResponse = (response: any) => {
    console.log('OAuth token response:', response);
    // Store access token for API calls
    if (response.access_token) {
      localStorage.setItem('google_access_token', response.access_token);
    }
  };

  render() {
    return (
      <div className="home-page">
        <header className="home-header">
          <img src={logo} alt="Logo" className="home-logo" />
          <div className="header-actions">
            <GoogleLoginButton
              onLoginSuccess={this.handleLoginSuccess}
              onTokenResponse={this.handleTokenResponse}
            />
          </div>
        </header>
        
        <main className="home-main">
          <section className="home-content">
            <h1 className="home-title">Superagent manages your calendar with a finesse of a world class EA.</h1>
            <p className="home-subtitle">Superagent works around the clock, seamlessly adapting to your schedule and time zone — ensuring your calendar stays clean and your day runs smoothly.</p>
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

