import React, { Component } from 'react';
import { BrowserRouter as Router, Routes, Route as RouterRoute, Navigate } from 'react-router-dom';
import HomePage from './components/HomePage/HomePage';
import Dashboard from './components/Dashboard/Dashboard';
import Privacy from './components/Privacy/Privacy';
import Terms from './components/Terms/Terms';
import './App.css';
import { Route } from './constants/routes';

interface AppProps {}

class App extends Component<AppProps> {
  render(): React.JSX.Element {
    return (
      <Router>
        <div className="App">
          <Routes>
            <RouterRoute path={Route.home} element={<HomePage />} />
            <RouterRoute path={Route.privacy} element={<Privacy />} />
            <RouterRoute path={Route.terms} element={<Terms />} />
            <RouterRoute path={Route.dashboard.settings} element={<Dashboard />} />
            <RouterRoute path={Route.dashboard.customize} element={<Dashboard />} />
            <RouterRoute path={Route.dashboard.calendars} element={<Dashboard />} />
            <RouterRoute path={Route.dashboard['create-assistant']} element={<Dashboard />} />
            {/* Redirect /dashboard to /dashboard/settings by default */}
            <RouterRoute path={Route.dashboard.base} element={<Navigate to={Route.dashboard.settings} replace />} />
          </Routes>
        </div>
      </Router>
    );
  }
}

export default App;
