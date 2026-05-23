import React, { useState, useEffect } from 'react';

const AlertsPage = () => {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch(`http://192.168.50.30:8005/api/alerts`);
        if (response.ok) {
          const data = await response.json();
          setAlerts(data.alerts || []);
        }
      } catch (error) {
        console.error('Failed to fetch alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, []);

  const acknowledgeAlert = async (alertId) => {
    try {
      const response = await fetch(
        `http://192.168.50.30:8005/api/alerts/${alertId}/acknowledge`,
        { method: 'POST' }
      );
      if (response.ok) {
        setAlerts(alerts.map(a => a.id === alertId ? { ...a, acknowledged: true } : a));
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const filteredAlerts = filter === 'all' 
    ? alerts 
    : alerts.filter(a => a.severity === filter && !a.acknowledged);

  const unacknowledgedCount = alerts.filter(a => !a.acknowledged).length;

  if (loading) {
    return (
      <div className="widget">
        <h3>🔔 Security Alerts</h3>
        <p>Loading alerts...</p>
      </div>
    );
  }

  return (
    <div className="widget">
      <div className="widget-header">
        <h3>🔔 Security Alerts</h3>
        {unacknowledgedCount > 0 && (
          <span className="alert-badge">{unacknowledgedCount} New</span>
        )}
      </div>

      <div className="filters">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All Alerts</option>
          <option value="critical">Critical Only</option>
          <option value="high">High Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="low">Low Priority</option>
        </select>
      </div>
      
      {filteredAlerts.length === 0 ? (
        <div className="no-alerts">
          <p>✅ No alerts to display</p>
          <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
            {filter === 'all' ? 'System is secure' : `No ${filter} alerts found`}
          </p>
        </div>
      ) : (
        <div className="alerts-list">
          {filteredAlerts.map((alert) => (
            <div key={alert.id} className={`alert-item alert-${alert.severity || 'medium'}`}>
              <div className="alert-header">
                <span className="severity-badge">{alert.severity?.toUpperCase() || 'MEDIUM'}</span>
                <span className="alert-title">{alert.title || 'Alert'}</span>
              </div>
              <div className="alert-meta">
                <span>{alert.source || 'System'}</span>
                <span>•</span>
                <span>{new Date(alert.timestamp || Date.now()).toLocaleString()}</span>
              </div>
              <div className="alert-description">
                {alert.description || 'No description available'}
              </div>
              {!alert.acknowledged && (
                <button 
                  className="ack-button"
                  onClick={() => acknowledgeAlert(alert.id)}
                >
                  Acknowledge
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertsPage;
