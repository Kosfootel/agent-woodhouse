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

const TOTAL_STEPS = 5;  // Welcome -> Router Discovery -> Router Credentials -> Device Scan -> Complete

const SetupWizard = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [routerInfo, setRouterInfo] = useState(null);
  const [devices, setDevices] = useState([]);
  const [scanProgress, setScanProgress] = useState(0);
  const [showFoundMessage, setShowFoundMessage] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // Router discovery state
  const [discoveredRouters, setDiscoveredRouters] = useState([]);
  const [selectedRouter, setSelectedRouter] = useState(null);
  const [isScanning, setIsScanning] = useState(false);

  // Router credentials form state
  const [credentialsForm, setCredentialsForm] = useState({
    routerIp: '192.168.50.1',
    adminUsername: '',
    adminPassword: '',
    vendor: ''
  });
  const [credentialsValidated, setCredentialsValidated] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  // Hard reset - clear everything on mount
  useEffect(() => {
    clearProgress();
    localStorage.removeItem('vigil_setup_progress');
    setCurrentStep(1);
    setRouterInfo(null);
    setDevices([]);
    setError(null);
    setCredentialsValidated(false);
    setValidationResult(null);
    setDiscoveredRouters([]);
    setSelectedRouter(null);
    
    // Create a setup session
    createSetupSession();
  }, []);

  // Create setup session
  const createSetupSession = async () => {
    try {
      const response = await fetch('http://192.168.50.30:8000/api/setup/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      setSessionId(data.session_id);
    } catch (err) {
      console.error('Failed to create setup session:', err);
    }
  };

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

  // Step 1: Start setup (goes to step 2 - router discovery)
  const handleStartSetup = async () => {
    setCurrentStep(2);
  };

  // Step 2: Discover routers on the network
  const handleDiscoverRouters = async () => {
    setIsScanning(true);
    setError(null);
    
    try {
      console.log('Starting router discovery...');
      
      // Call backend API to discover routers
      const response = await fetch(
        `http://192.168.50.30:8000/api/setup/discover`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      );
      
      const result = await response.json();
      console.log('Router discovery result:', result);
      
      if (result.routers && result.routers.length > 0) {
        setDiscoveredRouters(result.routers);
        // Auto-select the first router with highest confidence
        const bestRouter = result.routers[0];
        setSelectedRouter(bestRouter);
        setCredentialsForm(prev => ({
          ...prev,
          routerIp: bestRouter.ip
        }));
      } else {
        setDiscoveredRouters([]);
        setError('No routers found on your network. Please check your connection.');
      }
    } catch (err) {
      console.error('Router discovery error:', err);
      setError(translateError(err));
      setDiscoveredRouters([]);
    } finally {
      setIsScanning(false);
    }
  };

  // Select a discovered router
  const handleSelectRouter = (router) => {
    setSelectedRouter(router);
    setCredentialsForm(prev => ({
      ...prev,
      routerIp: router.ip
    }));
  };

  // Proceed to credentials step after router selection
  const handleRouterSelected = () => {
    if (selectedRouter) {
      setRouterInfo({
        ip: selectedRouter.ip,
        brand: selectedRouter.type || 'Network',
        model: selectedRouter.model || 'Router',
      });
      setCurrentStep(3);
    }
  };

  // Step 3: Submit router credentials
  const handleSubmitCredentials = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setValidationResult(null);

    try {
      const response = await fetch('http://192.168.50.30:8000/api/setup/router-credentials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          router_ip: credentialsForm.routerIp,
          admin_username: credentialsForm.adminUsername,
          admin_password: credentialsForm.adminPassword,
          vendor: credentialsForm.vendor || null,
          session_id: sessionId
        })
      });

      const data = await response.json();

      if (response.ok) {
        setValidationResult({
          success: true,
          router: data.router
        });
        setCredentialsValidated(true);
        setRouterInfo({
          ip: data.router.ip,
          brand: data.router.vendor,
          model: data.router.model
        });
        // Auto-advance after 2 seconds
        setTimeout(() => {
          setCurrentStep(4);
        }, 2000);
      } else {
        setValidationResult({
          success: false,
          error: data.detail || 'Authentication failed'
        });
        setError(data.detail || 'Authentication failed');
      }
    } catch (err) {
      console.error('Credentials submission error:', err);
      setValidationResult({
        success: false,
        error: 'Network error. Please try again.'
      });
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 4: Scan for devices
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
        setCurrentStep(5);
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

  // Step 5: Complete setup
  const handleComplete = () => {
    clearProgress();
    if (onComplete) {
      onComplete({ routerInfo, devices });
    }
  };

  // Navigation handlers
  const handleNext = () => {
    if (currentStep === 1) {
      setCurrentStep(2);
      return;
    }
    if (currentStep === 2) {
      setCurrentStep(3);
      return;
    }
    if (currentStep === 3) {
      setCurrentStep(4);
      return;
    }
    if (currentStep === 4) {
      setCurrentStep(5);
      return;
    }
    if (currentStep === 5) {
      onComplete({ routerInfo, devices });
    }
  };

  const handleBack = () => {
    setError(null);
    setValidationResult(null);
    setCurrentStep(Math.max(1, currentStep - 1));
  };

  // Skip credentials step (for ARP-only mode)
  const handleSkipCredentials = () => {
    setCurrentStep(4);
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
        <li>🔐 Secure router integration</li>
      </ul>
      <button className="btn btn-primary" onClick={handleStartSetup}>
        Get Started →
      </button>
    </div>
  );

  // Render Step 2: Router Discovery
  const renderRouterDiscovery = () => (
    <div className="step-content router-discovery-step">
      <div className="step-icon">🔍</div>
      <h2>Discover Your Router</h2>
      <p>
        We'll scan your network to find your router automatically.
        No need to look up IP addresses.
      </p>
      
      {isScanning ? (
        <div className="loading-container">
          <div className="spinner large"></div>
          <p>Scanning your network for routers...</p>
        </div>
      ) : discoveredRouters.length > 0 ? (
        <div className="router-list">
          <h3>Select your router:</h3>
          {discoveredRouters.map((router, index) => (
            <div
              key={router.ip}
              className={`router-card ${selectedRouter?.ip === router.ip ? 'selected' : ''}`}
              onClick={() => handleSelectRouter(router)}
            >
              <div className="router-icon">🌐</div>
              <div className="router-info">
                <div className="router-ip">{router.ip}</div>
                <div className="router-type">
                  {router.model || router.type || 'Unknown Router'}
                  {index === 0 && <span className="recommended-badge">Recommended</span>}
                </div>
                <div className="confidence-bar">
                  <div 
                    className="confidence-fill" 
                    style={{ width: `${(router.confidence || 0.3) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
          
          <div className="form-actions">
            <button 
              className="btn btn-secondary"
              onClick={handleDiscoverRouters}
            >
              🔃 Rescan
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleRouterSelected}
              disabled={!selectedRouter}
            >
              Continue →
            </button>
          </div>
          
          <button 
            className="btn btn-text"
            onClick={() => setCurrentStep(3)}
          >
            Manually enter router info →
          </button>
        </div>
      ) : (
        <div className="discovery-prompt">
          <p>Click below to scan your network for routers:</p>
          <button 
            className="btn btn-primary btn-large"
            onClick={handleDiscoverRouters}
          >
            🔍 Scan for Routers
          </button>
          
          {error && (
            <div className="error-message">
              <div className="error-icon">⚠️</div>
              <p>{error}</p>
              <button 
                className="btn btn-text"
                onClick={() => setCurrentStep(3)}
              >
                Enter router manually →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Render Step 3: Router Credentials
  const renderRouterCredentials = () => (
    <div className="step-content credentials-step">
      <h2>Router Configuration</h2>
      <p>
        Enter your router admin credentials to enable advanced network defense capabilities.
        Credentials are encrypted and stored securely.
      </p>
      
      <form onSubmit={handleSubmitCredentials} className="credentials-form">
        <div className="form-group">
          <label htmlFor="routerIp">Router IP Address</label>
          <input
            type="text"
            id="routerIp"
            value={credentialsForm.routerIp}
            onChange={(e) => setCredentialsForm({ ...credentialsForm, routerIp: e.target.value })}
            placeholder="192.168.50.1"
            required
            disabled={isLoading}
          />
          <small className="form-hint">
            Pre-filled from router discovery
          </small>
        </div>
        
        <div className="form-group">
          <label htmlFor="adminUsername">Admin Username</label>
          <input
            type="text"
            id="adminUsername"
            value={credentialsForm.adminUsername}
            onChange={(e) => setCredentialsForm({ ...credentialsForm, adminUsername: e.target.value })}
            placeholder="admin"
            required
            disabled={isLoading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="adminPassword">Admin Password</label>
          <input
            type="password"
            id="adminPassword"
            value={credentialsForm.adminPassword}
            onChange={(e) => setCredentialsForm({ ...credentialsForm, adminPassword: e.target.value })}
            required
            disabled={isLoading}
          />
          <small className="form-hint">
            <span className="lock-icon">🔒</span> Credentials are encrypted with AES-256 and never stored in plaintext.
          </small>
        </div>
        
        <div className="form-group">
          <label htmlFor="vendor">Router Vendor (Optional)</label>
          <select
            id="vendor"
            value={credentialsForm.vendor}
            onChange={(e) => setCredentialsForm({ ...credentialsForm, vendor: e.target.value })}
            disabled={isLoading}
          >
            <option value="">Auto-detect</option>
            <option value="asus">ASUS</option>
            <option value="netgear">Netgear</option>
            <option value="tp-link">TP-Link</option>
            <option value="linksys">Linksys</option>
            <option value="other">Other</option>
          </select>
        </div>
        
        <div className="form-actions">
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner-small"></span> Validating...
              </>
            ) : (
              'Connect Router →'
            )}
          </button>
          
          <button 
            type="button"
            className="btn btn-text"
            onClick={handleSkipCredentials}
            disabled={isLoading}
          >
            Skip (Basic mode only) →
          </button>
        </div>
      </form>
      
      {validationResult && (
        <div className={`validation-result ${validationResult.success ? 'success' : 'error'}`}>
          {validationResult.success ? (
            <>
              <div className="validation-icon">✓</div>
              <h3>Router Connected!</h3>
              <div className="router-details">
                <p><strong>Vendor:</strong> {validationResult.router?.vendor}</p>
                <p><strong>Model:</strong> {validationResult.router?.model}</p>
                <p><strong>Firmware:</strong> {validationResult.router?.firmware_version}</p>
                <p><strong>Connected Clients:</strong> {validationResult.router?.connected_clients}</p>
              </div>
              <p className="auto-advance">Continuing to device scan...</p>
            </>
          ) : (
            <>
              <div className="validation-icon">✗</div>
              <h3>Connection Failed</h3>
              <p>{validationResult.error}</p>
              <button 
                className="btn btn-secondary"
                onClick={() => setValidationResult(null)}
              >
                Try Again
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );

  // Render Step 4: Device Scanning
  const renderDeviceScan = () => (
    <div className="step-content test-step">
      <h2>Discovering devices...</h2>
      <p>
        Vigil is scanning your network to find all connected devices.
        This uses multiple discovery protocols for comprehensive coverage.
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
        <button className="btn btn-secondary" onClick={() => setCurrentStep(4)}>
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
        return renderRouterDiscovery();
      case 3:
        return renderRouterCredentials();
      case 4:
        return renderDeviceScan();
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
            disabled={isLoading || isScanning}
          >
            ← Back
          </button>
        </div>
      )}
    </div>
  );
};

export default SetupWizard;
