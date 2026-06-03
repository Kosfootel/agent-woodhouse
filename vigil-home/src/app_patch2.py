import re

with open('/home/erik-ross/vigil/dashboard/src/App.js', 'r') as f:
    content = f.read()

# Replace the old useEffect with a more robust version
old_block = '''  useEffect(() => {
    fetch(`${process.env.REACT_APP_API_URL || 'http://192.168.50.30:8005'}/api/setup/status`)
      .then(res => res.json())
      .then(data => setIsSetupComplete(data.is_setup_complete))
      .catch(() => setIsSetupComplete(false));
  }, []);'''

new_block = '''  useEffect(() => {
    const checkSetup = () => {
      fetch(`${process.env.REACT_APP_API_URL || 'http://192.168.50.30:8005'}/api/setup/status`)
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
  }, []);'''

content = content.replace(old_block, new_block)

with open('/home/erik-ross/vigil/dashboard/src/App.js', 'w') as f:
    f.write(content)

# Copy to repo
import shutil
shutil.copy('/home/erik-ross/vigil/dashboard/src/App.js', '/home/erik-ross/projects/vigil-home/dashboard/src/App.js')

print('Patched App.js with visibility change listener')
