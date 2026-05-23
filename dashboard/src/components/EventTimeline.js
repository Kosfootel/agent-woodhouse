import React, { useState, useEffect } from 'react';
import { getSecurityEvents } from '../api';

const SEVERITY_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#16a34a',
};

const EventTimeline = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    agent: '',
    severity: '',
    eventType: '',
  });

  useEffect(() => {
    fetchEvents();
  }, [filters]);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getSecurityEvents(filters);
      setEvents(response.data?.events || []);
    } catch (err) {
      console.error('Failed to fetch events:', err);
      setError(err.message);
      setEvents([]);
    } finally {
      setLoading(false);
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
      day: 'numeric' 
    });
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🟢',
    };
    return icons[severity] || '⚪';
  };

  if (loading) {
    return (
      <div className="widget">
        <h3>Security Event Timeline</h3>
        <p>Loading events...</p>
      </div>
    );
  }

  return (
    <div className="widget">
      <h3>Security Event Timeline</h3>
      
      {events.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#6b7280', padding: '40px 0' }}>
          <p>No security events recorded yet</p>
        </div>
      ) : (
        <div className="timeline" style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {events.map((event) => (
            <div 
              key={event.id}
              className="timeline-item"
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                padding: '12px 0',
                borderBottom: '1px solid #e5e7eb',
              }}
            >
              <div style={{ marginRight: '12px', fontSize: '1.2em' }}>
                {getSeverityIcon(event.severity)}
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                    {event.eventType?.replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: '0.85em', color: '#6b7280' }}>
                    {formatDate(event.timestamp)} {formatTime(event.timestamp)}
                  </span>
                </div>
                
                <div style={{ 
                  fontSize: '0.9em', 
                  color: '#374151',
                  marginTop: '4px' 
                }}>
                  {event.details}
                </div>
                
                <div style={{ fontSize: '0.8em', color: '#9ca3af', marginTop: '4px' }}>
                  Agent: {event.agent}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EventTimeline;
