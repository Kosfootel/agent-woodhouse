import React, { useState, useEffect } from 'react';
import { getAnomalies, acknowledgeAnomaly } from '../api';

const SEVERITY_ICONS = {
  critical: '🔴',
  high: '🟠',
  medium: '🟡',
  low: '🟢',
};

const AlertPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getAnomalies();
      setAlerts(response.data?.anomalies || []);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
      setError(err.message);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (id) => {
    try {
      await acknowledgeAnomaly(id);
      setAlerts(alerts.filter(a => a.id !== id));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  if (loading) {
    return (
      <div className="widget">
        <h3>Alerts</h3>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="widget">
      <h3>Alerts</h3>
      
      {alerts.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#6b7280', padding: '40px 0' }}>
          <p>🎉 No active alerts</p>
          <p style={{ fontSize: '0.85em', marginTop: '8px' }}>
            System is operating normally
          </p>
        </div>
      ) : (
        <div className="alerts-list" style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {alerts.map((alert) => (
            <div 
              key={alert.id}
              className="alert-item"
              style={{
                padding: '12px',
                marginBottom: '8px',
                borderRadius: '6px',
                backgroundColor: '#f9fafb',
                borderLeft: `4px solid ${alert.severity === 'critical' ? '#dc2626' : 
                  alert.severity === 'high' ? '#ea580c' : 
                  alert.severity === 'medium' ? '#ca8a04' : '#16a34a'}`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <span style={{ marginRight: '8px' }}>{SEVERITY_ICONS[alert.severity]}</span>
                  <strong>{alert.title || alert.event_type}</strong>
                </div>
                <button
                  onClick={() => handleAcknowledge(alert.id)}
                  style={{
                    padding: '4px 8px',
                    fontSize: '0.8em',
                    backgroundColor: '#e5e7eb',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Ack
                </button>
              </div>
              
              <p style={{ margin: '8px 0', fontSize: '0.9em', color: '#4b5563' }}>
                {alert.description}
              </p>
              
              <div style={{ fontSize: '0.75em', color: '#9ca3af' }}>
                {formatTime(alert.timestamp)} • {alert.agent_id || alert.agent}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertPanel;
