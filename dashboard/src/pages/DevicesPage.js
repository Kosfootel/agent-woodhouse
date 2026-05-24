import React, { useState, useEffect } from 'react';

const DevicesPage = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const response = await fetch(`http://192.168.50.30:8000/api/devices`);
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

  const getStatusIcon = (online) => {
    return online ? '🟢' : '🔴';
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
                <th>Vendor</th>
                <th>Type</th>
                <th>IP Address</th>
                <th>MAC Address</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((device, index) => (
                <tr key={index}>
                  <td>{getStatusIcon(device.online)}</td>
                  <td>{device.nickname || device.hostname || 'Unknown'}</td>
                  <td>{device.vendor || 'Unknown'}</td>
                  <td>{device.device_type || 'Unknown'}</td>
                  <td>{device.ip || 'N/A'}</td>
                  <td>{device.mac || 'N/A'}</td>
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
