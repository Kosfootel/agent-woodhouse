import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getBlockedStats } from '../api';

const BlockedCounter = () => {
  const [stats, setStats] = useState({
    total: 0,
    byCategory: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      // Mock data if API not available
      const mockData = {
        total: 156,
        byCategory: [
          { category: 'File System', count: 45, color: '#dc2626' },
          { category: 'Network', count: 38, color: '#ea580c' },
          { category: 'Shell Exec', count: 32, color: '#ca8a04' },
          { category: 'Memory', count: 25, color: '#16a34a' },
          { category: 'Config', count: 16, color: '#2563eb' },
        ],
      };

      try {
        const response = await getBlockedStats();
        setStats(response.data);
      } catch (err) {
        console.log('Using mock blocked stats');
        setStats(mockData);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="widget">
      <h3>Blocked Prompts</h3>
      
      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          <div className="big-counter">
            <div className="counter-value">{stats.total}</div>
            <div className="counter-label">blocked today</div>
          </div>

          <div className="chart-container" style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.byCategory} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="category" 
                  angle={-45} 
                  textAnchor="end" 
                  height={60}
                  tick={{ fontSize: 11 }}
                />
                <YAxis />
                <Tooltip 
                  formatter={(value) => [value, 'Count']}
                  labelFormatter={(label) => label}
                />
                <Bar 
                  dataKey="count" 
                  fill="#dc2626"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
};

export default BlockedCounter;
