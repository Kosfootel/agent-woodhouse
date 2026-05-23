import React, { useState, useEffect } from 'react';
import { getMemoryAccess } from '../api';

const SENSITIVITY_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#16a34a',
};

const AccessHeatmap = () => {
  const [accessData, setAccessData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Mock data if API not available
      const mockData = [
        { agent: 'agent-1', file: 'MEMORY.md', sensitivity: 'critical', accesses: 24 },
        { agent: 'agent-1', file: '.env', sensitivity: 'critical', accesses: 12 },
        { agent: 'agent-2', file: 'config/secrets.yaml', sensitivity: 'critical', accesses: 8 },
        { agent: 'agent-1', file: 'auth/tokens.json', sensitivity: 'high', accesses: 15 },
        { agent: 'agent-3', file: 'logs/security.log', sensitivity: 'high', accesses: 32 },
        { agent: 'agent-2', file: 'data/user_prefs.db', sensitivity: 'medium', accesses: 45 },
        { agent: 'agent-1', file: 'cache/responses.tmp', sensitivity: 'low', accesses: 120 },
        { agent: 'agent-3', file: 'docs/readme.md', sensitivity: 'low', accesses: 8 },
        { agent: 'agent-2', file: 'settings.json', sensitivity: 'medium', accesses: 18 },
        { agent: 'agent-1', file: 'api_keys.txt', sensitivity: 'critical', accesses: 3 },
      ];

      try {
        const response = await getMemoryAccess();
        setAccessData(response.data.access || mockData);
      } catch (err) {
        console.log('Using mock memory access data');
        setAccessData(mockData);
      }
    } finally {
      setLoading(false);
    }
  };

  const sortedData = [...accessData].sort((a, b) => {
    const sensitivityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    return sensitivityOrder[a.sensitivity] - sensitivityOrder[b.sensitivity];
  });

  return (
    <div className="widget">
      <h3>Memory Access Heatmap</h3>
      
      {loading ? (
        <p>Loading...</p>
      ) : (
        <table className="heatmap-table">
          <thead>
            <tr>
              <th>Agent</th>
              <th>File</th>
              <th>Sensitivity</th>
              <th>Accesses</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row, index) => (
              <tr key={index}>
                <td>{row.agent}</td>
                <td>{row.file}</td>
                <td>
                  <span
                    className="sensitivity-badge"
                    style={{
                      backgroundColor: SENSITIVITY_COLORS[row.sensitivity],
                      color: '#fff',
                      padding: '4px 12px',
                      borderRadius: '4px',
                      fontSize: '0.8em',
                      fontWeight: 'bold',
                    }}
                  >
                    {row.sensitivity}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div
                      className="access-bar"
                      style={{
                        width: `${Math.min(row.accesses * 2, 100)}px`,
                        height: '8px',
                        backgroundColor: SENSITIVITY_COLORS[row.sensitivity],
                        borderRadius: '4px',
                        opacity: 0.8,
                      }}
                    />
                    <span>{row.accesses}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default AccessHeatmap;
