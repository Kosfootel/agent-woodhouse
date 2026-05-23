import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getToolUsage } from '../api';

const ToolChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getToolUsage('24h');
      setData(response.data?.tools || []);
    } catch (err) {
      console.error('Failed to fetch tool usage:', err);
      setError(err.message);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="widget">
        <h3>Tool Usage (24h)</h3>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="widget">
      <h3>Tool Usage (24h)</h3>
      
      {data.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#6b7280', padding: '60px 0' }}>
          <p>No tool usage recorded yet</p>
        </div>
      ) : (
        <div className="chart-container" style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 10 }}
              />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [value, name]}
              />
              <Bar 
                dataKey="count" 
                name="Invocations"
                fill="#16a34a"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default ToolChart;
