import React, { useState, useEffect } from 'react';

const AgentsPage = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [trustFilter, setTrustFilter] = useState('all');
  const [actionInProgress, setActionInProgress] = useState(null);

  const API_URL = 'http://192.168.50.30:8000';

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch(`${API_URL}/api/agents`);
        if (response.ok) {
          const data = await response.json();
          setAgents(data.agents || []);
        }
      } catch (error) {
        console.error('Failed to fetch agents:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();
    const interval = setInterval(fetchAgents, 30000);
    return () => clearInterval(interval);
  }, [API_URL]);

  const trustAgent = async (agentId) => {
    setActionInProgress(agentId);
    try {
      const response = await fetch(`${API_URL}/api/agents/${agentId}/trust`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        setAgents(agents.map(a => a.id === agentId ? { ...a, trust_level: 'trusted' } : a));
      }
    } catch (error) {
      console.error('Failed to trust agent:', error);
    } finally {
      setActionInProgress(null);
    }
  };

  const blockAgent = async (agentId) => {
    setActionInProgress(agentId);
    try {
      const response = await fetch(`${API_URL}/api/agents/${agentId}/block`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        setAgents(agents.map(a => a.id === agentId ? { ...a, trust_level: 'blocked' } : a));
      }
    } catch (error) {
      console.error('Failed to block agent:', error);
    } finally {
      setActionInProgress(null);
    }
  };

  const removeAgent = async (agentId) => {
    if (!window.confirm(`Are you sure you want to remove agent ${agentId}? This action cannot be undone.`)) {
      return;
    }
    setActionInProgress(agentId);
    try {
      const response = await fetch(`${API_URL}/api/agents/${agentId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        setAgents(agents.filter(a => a.id !== agentId));
      }
    } catch (error) {
      console.error('Failed to remove agent:', error);
    } finally {
      setActionInProgress(null);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online': return '🟢';
      case 'offline': return '🔴';
      default: return '⚪';
    }
  };

  const getTrustIcon = (trustLevel) => {
    switch (trustLevel) {
      case 'trusted': return '✅';
      case 'blocked': return '⛔';
      default: return '⚠️';
    }
  };

  const getTrustClass = (trustLevel) => {
    switch (trustLevel) {
      case 'trusted': return 'trust-trusted';
      case 'blocked': return 'trust-blocked';
      default: return 'trust-untrusted';
    }
  };

  const filteredAgents = agents.filter(agent => {
    const statusMatch = statusFilter === 'all' || agent.status === statusFilter;
    const trustMatch = trustFilter === 'all' || agent.trust_level === trustFilter;
    return statusMatch && trustMatch;
  });

  const onlineCount = agents.filter(a => a.status === 'online').length;
  const trustedCount = agents.filter(a => a.trust_level === 'trusted').length;
  const blockedCount = agents.filter(a => a.trust_level === 'blocked').length;

  if (loading) {
    return (
      <div className="widget">
        <h3>Agent Management</h3>
        <p>Loading agents...</p>
      </div>
    );
  }

  return (
    <div className="widget">
      <div className="widget-header">
        <h3>Agent Management</h3>
        <span className="alert-badge">{agents.length} Total</span>
      </div>

      <div className="agent-stats">
        <div className="stat-item">
          <span className="stat-value">{onlineCount}</span>
          <span className="stat-label">Online</span>
        </div>
        <div className="stat-item">
          <span className="stat-value trusted">{trustedCount}</span>
          <span className="stat-label">Trusted</span>
        </div>
        <div className="stat-item">
          <span className="stat-value blocked">{blockedCount}</span>
          <span className="stat-label">Blocked</span>
        </div>
      </div>

      <div className="filters">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All Status</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
        </select>
        <select value={trustFilter} onChange={(e) => setTrustFilter(e.target.value)}>
          <option value="all">All Trust Levels</option>
          <option value="trusted">Trusted</option>
          <option value="untrusted">Untrusted</option>
          <option value="blocked">Blocked</option>
        </select>
      </div>

      {filteredAgents.length === 0 ? (
        <div className="no-alerts">
          <p>No agents found</p>
          <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
            {agents.length === 0 ? 'No agents have connected yet' : 'Try adjusting your filters'}
          </p>
        </div>
      ) : (
        <div className="table-container">
          <table className="timeline-table agents-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Agent</th>
                <th>Trust</th>
                <th>Score</th>
                <th>Alerts</th>
                <th>Last Seen</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredAgents.map((agent) => (
                <tr key={agent.id} className={getTrustClass(agent.trust_level)}>
                  <td>{getStatusIcon(agent.status)}</td>
                  <td>
                    <div className="agent-name">{agent.name || agent.id}</div>
                    <div className="agent-id">{agent.id}</div>
                  </td>
                  <td>
                    <span className={`trust-badge trust-${agent.trust_level}`}>
                      {getTrustIcon(agent.trust_level)} {agent.trust_level}
                    </span>
                  </td>
                  <td>
                    <div className="trust-score-bar">
                      <div 
                        className="trust-score-fill" 
                        style={{ width: `${agent.trust_score}%`, backgroundColor: agent.trust_score >= 80 ? '#22c55e' : agent.trust_score <= 30 ? '#dc2626' : '#ca8a04' }}
                      />
                      <span className="trust-score-value">{agent.trust_score}%</span>
                    </div>
                  </td>
                  <td>{agent.alert_count > 0 ? <span className="alert-count">{agent.alert_count}</span> : '-'}</td>
                  <td>{agent.last_seen ? new Date(agent.last_seen).toLocaleString() : 'Never'}</td>
                  <td>
                    <div className="action-buttons">
                      {agent.trust_level !== 'trusted' && (
                        <button 
                          className="btn-trust"
                          onClick={() => trustAgent(agent.id)}
                          disabled={actionInProgress === agent.id}
                        >
                          {actionInProgress === agent.id ? '...' : 'Trust'}
                        </button>
                      )}
                      {agent.trust_level !== 'blocked' && (
                        <button 
                          className="btn-block"
                          onClick={() => blockAgent(agent.id)}
                          disabled={actionInProgress === agent.id}
                        >
                          {actionInProgress === agent.id ? '...' : 'Block'}
                        </button>
                      )}
                      <button 
                        className="btn-remove"
                        onClick={() => removeAgent(agent.id)}
                        disabled={actionInProgress === agent.id}
                      >
                        {actionInProgress === agent.id ? '...' : 'Remove'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AgentsPage;
