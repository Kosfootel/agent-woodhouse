import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import EventTimeline from './components/EventTimeline';
import BlockedCounter from './components/BlockedCounter';
import ToolChart from './components/ToolChart';
import AccessHeatmap from './components/AccessHeatmap';
import AlertPanel from './components/AlertPanel';
import SetupPage from './pages/SetupPage';
import DevicesPage from './pages/DevicesPage';
import AlertsPage from './pages/AlertsPage';
import AgentsPage from './pages/AgentsPage';
import './index.css';

// Navigation Component
const Navigation = () => {
  return (
    <nav className="nav-links">
      <NavLink to="/" className="nav-link" end>
        <span className="nav-icon">📊</span>
        <span className="nav-text">Dashboard</span>
      </NavLink>
      <NavLink to="/devices" className="nav-link">
        <span className="nav-icon">📱</span>
        <span className="nav-text">Devices</span>
      </NavLink>
      <NavLink to="/alerts" className="nav-link">
        <span className="nav-icon">🔔</span>
        <span className="nav-text">Alerts</span>
      </NavLink>
      <NavLink to="/agents" className="nav-link">
        <span className="nav-icon">🤖</span>
        <span className="nav-text">Agents</span>
      </NavLink>
      <NavLink to="/setup" className="nav-link">
        <span className="nav-icon">⚙️</span>
        <span className="nav-text">Setup</span>
      </NavLink>
    </nav>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const [isSetupComplete, setIsSetupComplete] = useState(null);
  
  useEffect(() => {
    const checkSetup = () => {
      fetch(`${process.env.REACT_APP_API_URL || 'http://192.168.50.30:8000'}/api/setup/status`)
        .then(res => res.json())
        .then(data => setIsSetupComplete(data.is_setup_complete))
        .catch(() => setIsSetupComplete(false));
    };
    
    checkSetup();
    
    // Re-check when tab becomes visible (e.g., after setup completes)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        checkSetup();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);
  
  if (isSetupComplete === false) {
    return <Navigate to="/setup" replace />;
  }
  
  if (isSetupComplete === null) {
    return (
      <div className="app">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <p>Loading...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div>
            <h1>🛡️ Vigil Dashboard</h1>
            <p>Tier A Security Monitoring</p>
          </div>
          <Navigation />
        </div>
      </header>
      
      <main className="dashboard">
        <div className="grid-row">
          <div className="grid-col-2">
            <EventTimeline />
          </div>
          <div className="grid-col-1">
            <AlertPanel />
          </div>
        </div>
        
        <div className="grid-row">
          <div className="grid-col-1">
            <BlockedCounter />
          </div>
          <div className="grid-col-2">
            <ToolChart />
          </div>
        </div>
        
        <div className="grid-row">
          <div className="grid-col-3">
            <AccessHeatmap />
          </div>
        </div>
      </main>
      
      <footer className="footer">
        <p>Vigil Security Platform • Tier A</p>
      </footer>
    </div>
  );
};

// Page wrapper for non-dashboard pages
const PageWrapper = ({ children, title }) => (
  <div className="app">
    <header className="header">
      <div className="header-content">
        <div>
          <h1>🛡️ Vigil Dashboard</h1>
          <p>{title}</p>
        </div>
        <Navigation />
      </div>
    </header>
    
    <main className="dashboard">
      {children}
    </main>
    
    <footer className="footer">
      <p>Vigil Security Platform • Tier A</p>
    </footer>
  </div>
);

// Devices Page Component
const Devices = () => (
  <PageWrapper title="Device Management">
    <DevicesPage />
  </PageWrapper>
);

// Alerts Page Component
const Alerts = () => (
  <PageWrapper title="Security Alerts">
    <AlertsPage />
  </PageWrapper>
);

// Agents Page Component
const Agents = () => (
  <PageWrapper title="Agent Management">
    <AgentsPage />
  </PageWrapper>
);

// Setup Page Component
const Setup = () => (
  <PageWrapper title="System Setup">
    <SetupPage />
  </PageWrapper>
);

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/devices" element={<Devices />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/setup" element={<Setup />} />
      </Routes>
    </Router>
  );
}

export default App;
