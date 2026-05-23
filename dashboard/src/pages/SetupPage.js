import React from 'react';
import { useNavigate } from 'react-router-dom';
import SetupWizard from '../components/setup/SetupWizard';

const SetupPage = () => {
  const navigate = useNavigate();
  
  const handleSetupComplete = (setupData) => {
    console.log('Setup complete:', setupData);
    // Use React Router navigation instead of page reload
    navigate('/', { replace: true });
  };

  return (
    <div className="setup-page">
      <SetupWizard onComplete={handleSetupComplete} />
    </div>
  );
};

export default SetupPage;
