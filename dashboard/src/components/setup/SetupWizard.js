import React, { useState, useEffect } from 'react';
import {
  getDevices,
  translateError,
  saveProgress,
  loadProgress,
  clearProgress,
  getDeviceIcon,
} from '../../lib/routerDiscovery';
import './SetupWizard.css';

const TOTAL_STEPS = 3;  // Welcome -> Device Scan -> Complete

const SetupWizard = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [routerInfo, setRouterInfo] = useState(null);
  const [devices, setDevices] = useState([]);
  const [scanProgress, setScanProgress] = useState(0);
  const [showFoundMessage, setShowFoundMessage] = useState(false);

  // Hard reset - clear everything on mount
  useEffect(() => {
    clearProgress();
    localStorage.removeItem('vigil_setup_progress');
    setCurrentStep(1);
    setRouterInfo(null);
    setDevices([]);
    setError(null);
  }, []);

  // Clear error when router is found
  useEffect(() => {
    if (routerInfo && error) {
      setError(null);
    }
  }, [routerInfo, error]);

  // Save progress when step changes
  useEffect(() => {
    saveProgress(currentStep, {
      routerInfo,
      devices,
    });
  }, [currentStep, routerInfo, devices]);

  // Step 1: Start device scanning (goes to step 2)
  const handleStartScan = async () => {
    setIsLoading(true);
    setError(null);
    
    // Set default router info for display
    setRouterInfo({
      ip: '192.168.50.1',
      brand: 'Local',
      model: 'Network',
    });
    
    setIsLoading(false);
    setCurrentStep(2);
  };

  // Step 2: Scan for devices (ARP-based, no credentials needed)
  const handleScanDevices = async () => {
    console.log('Scan Devices clicked');
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Scanning network for devices via ARP');
      
      // Call backend API to discover devices via ARP
      const response = await fetch(
        `http://192.168.50.30:8000/api/setup/connect`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ip: routerInfo?.ip || '192.168.50.1',
            username: '',  // Not used for ARP
            password: '',  // Not used for ARP
          }),
        }
      );
      
      const result = await response.json();
      console.log('Scan result:', result);
      
      if (result.success) {
        // Fetch devices from backend
        const devicesResponse = await fetch(
          `http://192.168.50.30:8000/api/devices`
        );
        const devicesData = await devicesResponse.json();
        setDevices(devicesData.devices || []);
        setCurrentStep(4);
      } else {
        setError(result.message || 'Failed to scan network');
      }
    } catch (err) {
      console.error('Scan error:', err);
      setError(translateError(err));
    } finally {
      setIsLoading(false);
    }
  };

  // Step 3: Complete setup
  const handleComplete = () => {
    clearProgress();
    if (onComplete) {
      onComplete({ routerInfo, devices });
    }
  };

  // Navigation handlers
  const handleNext = () => {
    if (currentStep === 1) {
      // Step 1: Welcome - Start Scan button
      return;
    }
    if (currentStep === 2) {
      setError(null);
      setCurrentStep(2);
    }
  };

  const handleBack = () => {
    setError(null);
    setCurrentStep(Math.max(1, currentStep - 1));
  };

  // Render step indicator
  const renderStepIndicator = () => (
    <div className="step-indicator">
      {Array.from({ length: TOTAL_STEPS }, (_, i) => (
        <div
          key={i}
          className={`step-dot ${i + 1 === currentStep ? 'active' : ''} ${
            i + 1 < currentStep ? 'completed' : ''
          }`}
        >
          {i + 1 < currentStep ? '✓' : i + 1}
        </div>
      ))}
    </div>
  );

  // Render Step 1: Welcome
  const renderWelcome = () => (
    <div className="step-content welcome-step">
      <div className="step-icon">🛡️</div>
      <h2>Let's set up your Vigil device</h2>
      <p>
        We'll help you discover and monitor all the devices on your network.
      </p>
      <ul className="feature-list">
        <li>🔍 Automatically discover network devices</li>
        <li>📱 Monitor all connected devices</li>
        <li>⚡ Real-time security alerts</li>
        <li>🔐 No router credentials required</li>
      </ul>
      <button className="btn btn-primary" onClick={handleNext}>
        Get Started →
      </button>
    </div>
  );

  // Render Step 2: Network Discovery (simplified - no credentials)
  const renderDiscovery = () => (
    <div className="step-content discovery-step">
      <h2>Looking for your network...</h2>
      <p>
        Vigil is scanning your local network to discover connected devices.
        This may take a moment.
      </p>
      
      {isLoading ? (
        <div className="loading-container">
          <div className="spinner large"></div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${scanProgress}%` }}
            ></div>
          </div>
          <p className="loading-text">Scanning network...</p>
        </div>
      ) : routerInfo ? (
        <div className="success-message">
          <div className="success-icon">✓</div>
          <h3>Network found!</h3>
          <p>at {routerInfo.ip}</p>
        </div>
      ) : null}
      
      {error && !routerInfo && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button className="btn btn-secondary" onClick={handleStartScan}>
            Try Again
          </button>
        </div>
      )}
      
      {!isLoading && !routerInfo && !error && (
        <button className="btn btn-primary" onClick={handleStartScan}>
          Scan Network
        </button>
      )}
      
      {!isLoading && routerInfo && showFoundMessage && (
        <div className="found-transition">
          <div className="success-icon">✓</div>
          <h3>Network found at {routerInfo.ip}</h3>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '100%' }}></div>
          </div>
          <p className="loading-text">Preparing device scan...</p>
        </div>
      )}
    </div>
  );

  // Render Step 2: Device Scanning
  const renderDeviceScan = () => (
    <div className="step-content test-step">
      <h2>Discovering devices...</h2>
      <p>
        Vigil is scanning your network to find all connected devices.
        No router credentials are needed for this scan.
      </p>
      
      {isLoading ? (
        <div className="loading-container">
          <div className="spinner large"></div>
          <div className="test-status">
            <p>Scanning ARP tables...</p>
            <p>Identifying devices...</p>
            <p>Building device list...</p>
          </div>
        </div>
      ) : devices.length > 0 ? (
        <div className="success-message">
          <div className="success-icon large">🎉</div>
          <h3>Found {devices.length} devices!</h3>
          <p>Vigil is ready to monitor your network.</p>
        </div>
      ) : null}
      
      {error && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button className="btn btn-secondary" onClick={handleScanDevices}>
            Try Again
          </button>
        </div>
      )}
      
      {!isLoading && devices.length === 0 && !error && (
        <button className="btn btn-primary" onClick={handleScanDevices}>
          Scan for Devices
        </button>
      )}
      
      {!isLoading && devices.length > 0 && (
        <button className="btn btn-primary" onClick={() => setCurrentStep(4)}>
          Continue →
        </button>
      )}
    </div>
  );

  // Render Step 3: Confirmation
  const renderConfirmation = () => (
    <div className="step-content confirmation-step">
      <h2>Does this look right?</h2>
      <p>
        Here are the devices Vigil found on your network. 
        Make sure this matches what you expect.
      </p>
      
      <div className="device-summary">
        <div className="summary-header">
          <span>{devices.length} devices found</span>
          <span className="router-info">Network at {routerInfo?.ip}</span>
        </div>
        
        <div className="device-list">
          {devices.slice(0, 8).map((device) => (
            <div key={device.id} className="device-item">
              <span className="device-icon">{getDeviceIcon(device.type)}</span>
              <span className="device-name">{device.name}</span>
              <span className="device-ip">{device.ip}</span>
            </div>
          ))}
          {devices.length > 8 && (
            <div className="device-item more">
              <span>+{devices.length - 8} more devices</span>
            </div>
          )}
        </div>
      </div>
      
      <div className="confirmation-actions">
        <button className="btn btn-secondary" onClick={() => setCurrentStep(3)}>
          ← Back to scan
        </button>
        <button className="btn btn-success" onClick={handleComplete}>
          Yes, looks good! ✓
        </button>
      </div>
    </div>
  );

  // Render current step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return renderWelcome();
      case 2:
        return renderDiscovery();
      case 3:
        return renderDeviceScan();
      case 4:
        return renderConfirmation();
      default:
        return renderWelcome();
    }
  };

  return (
    <div className="setup-wizard">
      <div className="wizard-header">
        <h1>🛡️ Vigil Setup</h1>
      </div>
      
      {renderStepIndicator()}
      
      <div className="wizard-content">
        {renderStepContent()}
      </div>
      
      {currentStep > 1 && (
        <div className="wizard-footer">
          <button
            className="btn btn-text"
            onClick={handleBack}
            disabled={isLoading}
          >
            ← Back
          </button>
        </div>
      )}
    </div>
  );
};

export default SetupWizard;
