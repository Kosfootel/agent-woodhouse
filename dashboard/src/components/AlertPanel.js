import React, { useState, useEffect } from 'react';
import { getAlerts, acknowledgeAlert, acknowledgeAllAlerts } from '../api';

const SEVERITY_ICONS = {
  critical: '🔴',
  high: '🟠',
  medium: '🟡',
  low: '🟢',
};

const SEVERITY_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#16a34a',
};

const AlertPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ new_count: 0, acknowledged_count: 0 });

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getAlerts();
      setAlerts(response.data?.alerts || []);
      setStats({
        new_count: response.data?.new_count || 0,
        acknowledged_count: response.data?.acknowledged_count || 0,
      });
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
      await acknowledgeAlert(id);
      setAlerts(alerts.filter(a => a.id !== id));
      setStats(prev => ({ ...prev, new_count: prev.new_count - 1, acknowledged_count: prev.acknowledged_count + 1 }));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleAcknowledgeAll = async () => {
    try {
      await acknowledgeAllAlerts();
      setAlerts([]);
      setStats(prev => ({ new_count: 0, acknowledged_count: prev.acknowledged_count + prev.new_count }));
    } catch (err) {
      console.error('Failed to acknowledge all alerts:', err);
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

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
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

  const unacknowledgedAlerts = alerts.filter(a => !a.acknowledged);

  return (
    <div className="widget">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ margin: 0 }}>Alerts</h3>
        {unacknowledgedAlerts.length > 0 && (
          <span style={{ 
            backgroundColor: '#dc2626', 
            color: 'white', 
            padding: '2px 8px', 
            borderRadius: '12px',
            fontSize: '0.8em',
            fontWeight: 'bold'
          }}>
            {unacknowledgedAlerts.length} new
          </span>
        )}
      </div>
      
      {alerts.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#6b7280', padding: '40px 0' }}>
          <p>🎉 No active alerts</p>
          <p style={{ fontSize: '0.85em', marginTop: '8px' }}>
            System is operating normally
          </p>
        </div>
      ) : (
        <>
          <div className="alerts-list" style={{ maxHeight: '320px', overflowY: 'auto' }}>
            {alerts.map((alert) => (
              <div 
                key={alert.id}
                className="alert-item"
                style={{
                  padding: '12px',
                  marginBottom: '8px',
                  borderRadius: '6px',
                  backgroundColor: alert.acknowledged ? '#f3f4f6' : '#f9fafb',
                  borderLeft: `4px solid ${SEVERITY_COLORS[alert.severity] || '#6b7280'}`,
                  opacity: alert.acknowledged ? 0.7 : 1,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <span style={{ marginRight: '8px' }}>{SEVERITY_ICONS[alert.severity] || '⚪'}</span>
                    <strong style={{ fontSize: '0.95em' }}>{alert.title || alert.alert_type}</strong>
                    <span style={{ 
                      marginLeft: '8px', 
                      fontSize: '0.7em', 
                      textTransform: 'uppercase',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      backgroundColor: SEVERITY_COLORS[alert.severity] || '#6b7280',
                      color: 'white',
                    }}>
                      {alert.severity}
                    </span>
                  </div>
                  {!alert.acknowledged && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      style={{
                        padding: '4px 8px',
                        fontSize: '0.75em',
                        backgroundColor: '#e5e7eb',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        marginLeft: '8px',
                      }}
                    >
                      Ack
                    </button>
                  )}
                </div>
                
                <p style={{ margin: '8px 0', fontSize: '0.9em', color: '#4b5563' }}>
                  {alert.narrative || alert.description}
                </p>
                
                <div style={{ fontSize: '0.75em', color: '#9ca3af', display: 'flex', justifyContent: 'space-between' }}>
                  <span>{formatDate(alert.timestamp)} {formatTime(alert.timestamp)}</span>
                  <span>Device #{alert.device_id}</span>
                </div>
              </div>
            ))}
          </div>
          
          {unacknowledgedAlerts.length > 0 && (
            <button
              onClick={handleAcknowledgeAll}
              style={{
                width: '100%',
                padding: '10px',
                marginTop: '12px',
                backgroundColor: '#1f2937',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.9em',
                fontWeight: '500',
              }}
            >
              Acknowledge All ({unacknowledgedAlerts.length})
            </button>
          )}
        </>
      )}
    </div>
  );
};

export default AlertPanel;
