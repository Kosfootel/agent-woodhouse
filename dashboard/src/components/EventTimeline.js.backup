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
      // Fallback mock data if API not available
      const mockEvents = [
        { id: 1, timestamp: '2026-05-19T14:30:00Z', agent: 'agent-1', eventType: 'prompt_blocked', severity: 'high', details: 'Attempted file deletion' },
        { id: 2, timestamp: '2026-05-19T14:15:00Z', agent: 'agent-2', eventType: 'memory_access', severity: 'medium', details: 'Accessed sensitive config' },
        { id: 3, timestamp: '2026-05-19T13:45:00Z', agent: 'agent-1', eventType: 'tool_blocked', severity: 'critical', details: 'Blocked shell execution' },
        { id: 4, timestamp: '2026-05-19T13:20:00Z', agent: 'agent-3', eventType: 'anomaly_detected', severity: 'high', details: 'Unusual file access pattern' },
        { id: 5, timestamp: '2026-05-19T12:55:00Z', agent: 'agent-1', eventType: 'prompt_blocked', severity: 'low', details: 'Attempted network scan' },
      ];
      
      // Try API first, fall back to mock
      try {
        const response = await getSecurityEvents(filters);
        setEvents(response.data.events || mockEvents);
      } catch (err) {
        console.log('Using mock data');
        // Apply filters to mock data
        let filtered = mockEvents;
        if (filters.severity) {
          filtered = filtered.filter(e => e.severity === filters.severity);
        }
        if (filters.agent) {
          filtered = filtered.filter(e => e.agent === filters.agent);
        }
        if (filters.eventType) {
          filtered = filtered.filter(e => e.eventType === filters.eventType);
        }
        setEvents(filtered);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const uniqueAgents = [...new Set(events.map(e => e.agent))];
  const uniqueEventTypes = [...new Set(events.map(e => e.eventType))];

  return (
    <div className="widget">
      <h3>Security Event Timeline</h3>
      
      <div className="filters">
        <select 
          value={filters.agent} 
          onChange={(e) => setFilters({...filters, agent: e.target.value})}
        >
          <option value="">All Agents</option>
          {uniqueAgents.map(agent => (
            <option key={agent} value={agent}>{agent}</option>
          ))}
        </select>
        
        <select 
          value={filters.severity} 
          onChange={(e) => setFilters({...filters, severity: e.target.value})}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        
        <select 
          value={filters.eventType} 
          onChange={(e) => setFilters({...filters, eventType: e.target.value})}
        >
          <option value="">All Event Types</option>
          {uniqueEventTypes.map(type => (
            <option key={type} value={type}>{type.replace('_', ' ')}</option>
          ))}
        </select>
      </div>

      <div className="timeline-container">
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table className="timeline-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Agent</th>
                <th>Event Type</th>
                <th>Severity</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {events.map(event => (
                <tr key={event.id}>
                  <td>{formatTime(event.timestamp)}</td>
                  <td>{event.agent}</td>
                  <td>{event.eventType.replace('_', ' ')}</td>
                  <td>
                    <span 
                      className="severity-badge" 
                      style={{ 
                        backgroundColor: SEVERITY_COLORS[event.severity],
                        color: '#fff',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.8em'
                      }}
                    >
                      {event.severity}
                    </span>
                  </td>
                  <td>{event.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default EventTimeline;
