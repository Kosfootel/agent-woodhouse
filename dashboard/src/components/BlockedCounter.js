import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getBlockedStats } from '../api';

const BlockedCounter = () => {
  const [stats, setStats] = useState({
    total: 0,
    byCategory: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getBlockedStats();
      setStats(response.data || { total: 0, byCategory: [] });
    } catch (err) {
      console.error('Failed to fetch blocked stats:', err);
      setError(err.message);
      setStats({ total: 0, byCategory: [] });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="widget">
        <h3>Blocked Prompts</h3>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="widget">
      <h3>Blocked Prompts</h3>
      
      <div className="big-counter">
        <div className="counter-value">{stats.total}</div>
        <div className="counter-label">blocked today</div>
      </div>

      {stats.byCategory.length > 0 ? (
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
      ) : (
        <p style={{ textAlign: 'center', color: '#6b7280', marginTop: '20px' }}>
          No blocked prompts yet
        </p>
      )}
    </div>
  );
};

export default BlockedCounter;
