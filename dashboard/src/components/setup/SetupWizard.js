import React, { useState, useEffect } from 'react';
import {
  scanForRouter,
  identifyRouter,
  testCredentials,
  getDevices,
  translateError,
  saveProgress,
  loadProgress,
  clearProgress,
  getDeviceIcon,
} from '../../lib/routerDiscovery';
import './SetupWizard.css';

const TOTAL_STEPS = 5;

const SetupWizard = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [routerInfo, setRouterInfo] = useState(null);
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [devices, setDevices] = useState([]);
  const [scanProgress, setScanProgress] = useState(0);
  const [showFoundMessage, setShowFoundMessage] = useState(false);

  // Hard reset - clear everything on mount
  useEffect(() => {
    clearProgress();
    localStorage.removeItem('vigil_setup_progress');
    setCurrentStep(1);
    setRouterInfo(null);
    setCredentials({ username: '', password: '' });
    setDevices([]);
    setError(null);
  }, []);

  // Clear error when router is found (race condition fix)
  useEffect(() => {
    if (routerInfo && error) {
      setError(null);
    }
  }, [routerInfo, error]);

  // Save progress when step changes
  useEffect(() => {
    saveProgress(currentStep, {
      routerInfo,
      credentials,
      devices,
    });
  }, [currentStep, routerInfo, credentials, devices]);

  // Step 2: Scan for router
  const handleScanRouter = async () => {
    setIsLoading(true);
    setError(null);
    setScanProgress(0);
    
    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setScanProgress(prev => Math.min(prev + 10, 80));
    }, 300);
    
    try {
      const result = await scanForRouter();
      clearInterval(progressInterval);
      
      if (result) {
        setScanProgress(100);
        setError(null);  // Clear any previous errors
        const identified = await identifyRouter(result.ip);
        setRouterInfo({
          ...identified,
          ip: result.ip,
        });
        // Show "Found" message for 1.5s before advancing
        setShowFoundMessage(true);
        await new Promise(resolve => setTimeout(resolve, 1500));
        setShowFoundMessage(false);
        setCurrentStep(3);
      } else {
        setError("We couldn't find your router automatically. Please check your network connection and try again.");
      }
    } catch (err) {
      clearInterval(progressInterval);
      setError(translateError(err));
    } finally {
      setIsLoading(false);
    }
  };

  // Step 3: Submit credentials
  const handleCredentialsSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      await testCredentials(routerInfo.ip, credentials.username, credentials.password);
      setCurrentStep(4);
    } catch (err) {
      setError(translateError(err));
    } finally {
      setIsLoading(false);
    }
  };

  // Step 4: Connect to router and import devices
  const handleFetchDevices = async () => {
    console.log('Connect & Scan clicked');
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Connecting to router:', routerInfo?.ip);
      // Call backend API to connect and import devices
      const response = await fetch(
        `http://192.168.50.30:8005/api/setup/connect`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ip: routerInfo?.ip,
            username: credentials?.username,
            password: credentials?.password,
          }),
        }
      );
      
      const result = await response.json();
      console.log('Connect result:', result);
      
      if (result.success) {
        // Fetch devices from backend after import
        const devicesResponse = await fetch(
          `http://192.168.50.30:8005/api/devices`
        );
        const devicesData = await devicesResponse.json();
        setDevices(devicesData.devices || []);
        setCurrentStep(5);
      } else {
        setError(result.message || 'Failed to connect to router');
      }
    } catch (err) {
      console.error('Connect error:', err);
      setError(translateError(err));
    } finally {
      setIsLoading(false);
    }
  };

  // Step 5: Complete setup
  const handleComplete = () => {
    clearProgress();
    if (onComplete) {
      onComplete({ routerInfo, credentials, devices });
    }
  };

  // Navigation handlers
  const handleNext = () => {
    if (currentStep === 1) {
      setError(null);
      setCurrentStep(2);
    }
  };

  const handleBack = () => {
    setError(null);
    setCurrentStep(Math.max(1, currentStep - 1));
  };

  const handleSkip = () => {
    // Allow manual entry if auto-scan fails
    setError(null);  // Clear error when skipping to manual entry
    setRouterInfo({
      brand: 'Router',
      model: 'Manual Entry',
      ip: '192.168.50.1',
      confidence: 'manual',
    });
    setCurrentStep(3);
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
        We'll help you connect Vigil to your router so you can monitor and control
        all the devices on your network.
      </p>
      <ul className="feature-list">
        <li>🔍 Automatically find your router</li>
        <li>🔐 Securely connect with your credentials</li>
        <li>📱 Monitor all network devices</li>
        <li>⚡ Real-time security alerts</li>
      </ul>
      <button className="btn btn-primary" onClick={handleNext}>
        Get Started →
      </button>
    </div>
  );

  // Render Step 2: Router Discovery
  const renderDiscovery = () => (
    <div className="step-content discovery-step">
      <h2>Looking for your router...</h2>
      <p>
        Vigil is scanning your network to find your router.
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
          <h3>Found: {routerInfo.brand} {routerInfo.model}</h3>
          <p>at {routerInfo.ip}</p>
        </div>
      ) : null}
      
      {error && !routerInfo && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button className="btn btn-secondary" onClick={handleSkip}>
            Enter manually
          </button>
        </div>
      )}
      
      {!isLoading && !routerInfo && !error && (
        <button className="btn btn-primary" onClick={handleScanRouter}>
          Scan Network
        </button>
      )}
      
      {!isLoading && routerInfo && showFoundMessage && (
        <div className="found-transition">
          <div className="success-icon">✓</div>
          <h3>Found: {routerInfo.brand} {routerInfo.model}</h3>
          <p>at {routerInfo.ip}</p>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '100%' }}></div>
          </div>
          <p className="loading-text">Preparing next step...</p>
        </div>
      )}
    </div>
  );

  // Render Step 3: Credentials
  const renderCredentials = () => (
    <div className="step-content credentials-step">
      <h2>Enter router credentials</h2>
      <p className="router-found">
        Found: <strong>{routerInfo?.brand} {routerInfo?.model}</strong> at {routerInfo?.ip}
      </p>
      
      <div className="help-text">
        <span className="help-icon">💡</span>
        <span>Found on router label — usually under the device</span>
      </div>
      
      <form onSubmit={handleCredentialsSubmit} className="credentials-form">
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={credentials.username}
            onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            placeholder="admin"
            required
            disabled={isLoading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={credentials.password}
            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
            placeholder="••••••••"
            required
            disabled={isLoading}
          />
        </div>
        
        {error && error.includes('credential') && (
          <div className="error-message small">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}
        
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading || !credentials.username || !credentials.password}
        >
          {isLoading ? (
            <>
              <span className="spinner small"></span>
              Testing...
            </>
          ) : (
            'Continue →'
          )}
        </button>
      </form>
    </div>
  );

  // Render Step 4: Test Connection
  const renderTestConnection = () => (
    <div className="step-content test-step">
      <h2>Testing connection...</h2>
      <p>
        Vigil is connecting to your router and checking what devices are on your network.
      </p>
      
      {isLoading ? (
        <div className="loading-container">
          <div className="spinner large"></div>
          <div className="test-status">
            <p>Authenticating...</p>
            <p>Scanning devices...</p>
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
          <button className="btn btn-secondary" onClick={() => setCurrentStep(3)}>
            Try different credentials
          </button>
        </div>
      )}
      
      {!isLoading && devices.length === 0 && !error && (
        <button className="btn btn-primary" onClick={handleFetchDevices}>
          Connect & Scan
        </button>
      )}
      
      {!isLoading && devices.length > 0 && (
        <button className="btn btn-primary" onClick={() => setCurrentStep(5)}>
          Continue →
        </button>
      )}
    </div>
  );

  // Render Step 5: Confirmation
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
          <span className="router-info">{routerInfo?.brand} {routerInfo?.model}</span>
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
          ← Back to credentials
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
        return renderCredentials();
      case 4:
        return renderTestConnection();
      case 5:
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
