import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getToolUsage } from '../api';

const ToolChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Mock data if API not available
      const mockData = [
        { hour: '00:00', allowed: 12, blocked: 2 },
        { hour: '01:00', allowed: 8, blocked: 1 },
        { hour: '02:00', allowed: 5, blocked: 0 },
        { hour: '03:00', allowed: 4, blocked: 0 },
        { hour: '04:00', allowed: 6, blocked: 1 },
        { hour: '05:00', allowed: 15, blocked: 3 },
        { hour: '06:00', allowed: 28, blocked: 5 },
        { hour: '07:00', allowed: 42, blocked: 8 },
        { hour: '08:00', allowed: 56, blocked: 12 },
        { hour: '09:00', allowed: 68, blocked: 15 },
        { hour: '10:00', allowed: 72, blocked: 18 },
        { hour: '11:00', allowed: 65, blocked: 14 },
        { hour: '12:00', allowed: 58, blocked: 11 },
        { hour: '13:00', allowed: 62, blocked: 13 },
        { hour: '14:00', allowed: 70, blocked: 16 },
        { hour: '15:00', allowed: 64, blocked: 14 },
        { hour: '16:00', allowed: 55, blocked: 10 },
        { hour: '17:00', allowed: 48, blocked: 9 },
        { hour: '18:00', allowed: 35, blocked: 6 },
        { hour: '19:00', allowed: 25, blocked: 4 },
        { hour: '20:00', allowed: 20, blocked: 3 },
        { hour: '21:00', allowed: 18, blocked: 2 },
        { hour: '22:00', allowed: 14, blocked: 2 },
        { hour: '23:00', allowed: 10, blocked: 1 },
      ];

      try {
        const response = await getToolUsage('24h');
        setData(response.data.usage || mockData);
      } catch (err) {
        console.log('Using mock tool usage data');
        setData(mockData);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="widget">
      <h3>Tool Usage (24h)</h3>
      
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="chart-container" style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="hour" 
                tick={{ fontSize: 10 }}
                interval={2}
              />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [value, name]}
              />
              <Legend />
              <Bar 
                dataKey="allowed" 
                name="Allowed"
                fill="#16a34a"
                radius={[2, 2, 0, 0]}
              />
              <Bar 
                dataKey="blocked" 
                name="Blocked"
                fill="#dc2626"
                radius={[2, 2, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default ToolChart;
