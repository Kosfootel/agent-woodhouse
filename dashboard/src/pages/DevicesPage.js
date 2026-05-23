import React, { useState, useEffect } from 'react';

const DevicesPage = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const response = await fetch(`${'http://192.168.50.30:8005'}/api/devices`);
        if (response.ok) {
          const data = await response.json();
          setDevices(data.devices || []);
        }
      } catch (error) {
        console.error('Failed to fetch devices:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDevices();
    const interval = setInterval(fetchDevices, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online': return '🟢';
      case 'offline': return '🔴';
      case 'warning': return '🟡';
      default: return '⚪';
    }
  };

  if (loading) {
    return (
      <div className="widget">
        <h3>📱 Connected Devices</h3>
        <p>Loading devices...</p>
      </div>
    );
  }

  return (
    <div className="widget">
      <div className="widget-header">
        <h3>📱 Connected Devices</h3>
        <span className="alert-badge">{devices.length}</span>
      </div>
      
      {devices.length === 0 ? (
        <div className="no-alerts">
          <p>No devices registered</p>
          <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>Visit Setup to add devices</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="timeline-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Device</th>
                <th>Type</th>
                <th>IP Address</th>
                <th>Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((device, index) => (
                <tr key={index}>
                  <td>{getStatusIcon(device.status)}</td>
                  <td>{device.name || 'Unknown'}</td>
                  <td>{device.type || 'Unknown'}</td>
                  <td>{device.ip || 'N/A'}</td>
                  <td>{device.last_seen ? new Date(device.last_seen).toLocaleString() : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default DevicesPage;
