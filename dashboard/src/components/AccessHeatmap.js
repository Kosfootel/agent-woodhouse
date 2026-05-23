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
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getMemoryAccess();
      setAccessData(response.data?.data || []);
    } catch (err) {
      console.error('Failed to fetch memory access:', err);
      setError(err.message);
      setAccessData([]);
    } finally {
      setLoading(false);
    }
  };

  // Filter to only show entries with count > 0
  const filteredData = accessData.filter(item => item.count > 0);

  if (loading) {
    return (
      <div className="widget">
        <h3>Memory Access Heatmap</h3>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="widget">
      <h3>Memory Access Heatmap</h3>
      
      {filteredData.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#6b7280', padding: '40px 0' }}>
          <p>No memory access recorded yet</p>
        </div>
      ) : (
        <table className="heatmap-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
              <th style={{ textAlign: 'left', padding: '8px' }}>Agent</th>
              <th style={{ textAlign: 'left', padding: '8px' }}>Level</th>
              <th style={{ textAlign: 'right', padding: '8px' }}>Accesses</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #e5e7eb' }}>
                <td style={{ padding: '8px' }}>{item.agent}</td>
                <td style={{ padding: '8px' }}>
                  <span style={{ 
                    color: SENSITIVITY_COLORS[item.level] || '#6b7280',
                    fontWeight: 600,
                    textTransform: 'capitalize'
                  }}>
                    {item.level}
                  </span>
                </td>
                <td style={{ padding: '8px', textAlign: 'right' }}>{item.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default AccessHeatmap;
