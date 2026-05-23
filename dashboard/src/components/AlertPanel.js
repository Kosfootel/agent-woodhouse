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

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      // Mock data if API not available
      const mockAlerts = [
        { 
          id: 1, 
          severity: 'critical', 
          title: 'Unusual file deletion pattern', 
          description: 'Agent attempting multiple file deletions in rapid succession',
          agent: 'agent-1',
          timestamp: '2026-05-19T14:30:00Z',
          acknowledged: false,
        },
        { 
          id: 2, 
          severity: 'high', 
          title: 'Memory access anomaly', 
          description: 'Agent accessing critical files outside normal hours',
          agent: 'agent-2',
          timestamp: '2026-05-19T12:15:00Z',
          acknowledged: false,
        },
        { 
          id: 3, 
          severity: 'medium', 
          title: 'Elevated tool usage', 
          description: 'Tool invocation rate 3x above baseline',
          agent: 'agent-3',
          timestamp: '2026-05-19T10:45:00Z',
          acknowledged: false,
        },
      ];

      try {
        const response = await getAnomalies();
        setAlerts(response.data.anomalies || mockAlerts);
      } catch (err) {
        console.log('Using mock alert data');
        setAlerts(mockAlerts);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (id) => {
    try {
      await acknowledgeAnomaly(id);
      setAlerts(alerts.map(alert => 
        alert.id === id ? { ...alert, acknowledged: true } : alert
      ));
    } catch (err) {
      // Just mark as acknowledged locally if API fails
      setAlerts(alerts.map(alert => 
        alert.id === id ? { ...alert, acknowledged: true } : alert
      ));
    }
  };

  const activeAlerts = alerts.filter(a => !a.acknowledged);

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString([], { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="widget">
      <div className="widget-header">
        <h3>Anomaly Alerts</h3>
        <span className="alert-badge">
          {activeAlerts.length} active
        </span>
      </div>
      
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="alerts-list">
          {activeAlerts.length === 0 ? (
            <div className="no-alerts">
              <span>✅ No active alerts</span>
            </div>
          ) : (
            activeAlerts.map(alert => (
              <div 
                key={alert.id} 
                className={`alert-item alert-${alert.severity}`}
              >
                <div className="alert-header">
                  <span className="alert-icon">{SEVERITY_ICONS[alert.severity]}</span>
                  <span className="alert-title">{alert.title}</span>
                </div>
                <div className="alert-meta">
                  <span>{alert.agent}</span>
                  <span>•</span>
                  <span>{formatTime(alert.timestamp)}</span>
                </div>
                <p className="alert-description">{alert.description}</p>
                <button 
                  className="ack-button"
                  onClick={() => handleAcknowledge(alert.id)}
                >
                  Acknowledge
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default AlertPanel;
