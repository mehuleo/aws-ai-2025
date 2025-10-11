import React, { Component } from 'react';
import './HomePage.css';
import logo from '../../assets/images/logo.png';
import hero from '../../assets/images/hero.png';
import GoogleLoginButton from '../GoogleLoginButton/GoogleLoginButton';

interface HomePageProps {}

class HomePage extends Component<HomePageProps> {
  componentDidMount() {
    // Static landing page - no authentication needed
  }

  handleLoginSuccess = (user: any) => {
    console.log('Login successful:', user);
    // Redirect to dashboard after successful login
    window.location.href = '/dashboard';
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

