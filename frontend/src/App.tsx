import { useState, useEffect } from 'react'

interface HealthStatus {
  status: string;
  service: string;
}

function App() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/health');
        if (response.ok) {
          const data = await response.json();
          setHealthStatus(data);
        } else {
          setError('Backend not responding');
        }
      } catch (err) {
        setError('Cannot connect to backend');
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
  }, []);

  return (
    <div style={{ 
      padding: '40px', 
      fontFamily: 'Arial, sans-serif',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      <h1 style={{ color: '#2563eb', marginBottom: '20px' }}>
        🏗️ Building Compliance Platform
      </h1>
      
      <div style={{ 
        background: '#f8fafc', 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h2>System Status</h2>
        {loading && <p>Checking backend connection...</p>}
        {error && <p style={{ color: 'red' }}>❌ {error}</p>}
        {healthStatus && (
          <p style={{ color: 'green' }}>
            ✅ Backend Status: {healthStatus.status} ({healthStatus.service})
          </p>
        )}
      </div>

      <div style={{ 
        background: '#f0f9ff', 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h2>Quick Links</h2>
        <ul>
          <li><a href="http://localhost:8000/health" target="_blank">Backend Health Check</a></li>
          <li><a href="http://localhost:8000/docs" target="_blank">API Documentation</a></li>
          <li><a href="http://localhost:8000/api/v1/test" target="_blank">API Test Endpoint</a></li>
        </ul>
      </div>

      <div style={{ 
        background: '#fefce8', 
        padding: '20px', 
        borderRadius: '8px'
      }}>
        <h2>Next Steps</h2>
        <ol>
          <li>✅ Frontend and Backend are connected</li>
          <li>🔄 Add database integration</li>
          <li>🔄 Implement buildable analysis</li>
          <li>🔄 Add Singapore building codes</li>
        </ol>
      </div>
    </div>
  )
}

export default App
