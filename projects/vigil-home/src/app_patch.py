import re

with open('/home/erik-ross/vigil/dashboard/src/App.js', 'r') as f:
    content = f.read()

# Find and replace the Dashboard component's useEffect
old_effect = '''  useEffect(() => {
    fetch(`http://192.168.50.30:8005/api/setup/status`)
      .then(res => res.json())
      .then(data => setIsSetupComplete(data.is_setup_complete))
      .catch(() => setIsSetupComplete(false));
  }, []);'''

new_effect = '''  useEffect(() => {
    const checkSetup = () => {
      fetch(`http://192.168.50.30:8005/api/setup/status`)
        .then(res => res.json())
        .then(data => setIsSetupComplete(data.is_setup_complete))
        .catch(() => setIsSetupComplete(false));
    };
    
    checkSetup();
    
    // Re-check when user returns to dashboard
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

content = content.replace(old_effect, new_effect)

with open('/home/erik-ross/vigil/dashboard/src/App.js', 'w') as f:
    f.write(content)

# Copy to repo
import shutil
shutil.copy('/home/erik-ross/vigil/dashboard/src/App.js', '/home/erik-ross/projects/vigil-home/dashboard/src/App.js')

print('Patched App.js')
