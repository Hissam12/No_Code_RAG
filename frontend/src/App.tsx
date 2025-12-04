import { useState, useEffect } from 'react';
import axios from 'axios';
import GraphCanvas from './components/GraphCanvas';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import { Layout } from 'lucide-react';

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });

  const fetchGraph = async () => {
    try {
      const res = await axios.get('http://localhost:8000/graph');
      setGraphData(res.data);
    } catch (error) {
      console.error('Failed to fetch graph:', error);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw' }}>
      {/* Sidebar */}
      <div style={{ width: '350px', padding: '20px', display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--glass-border)', background: 'rgba(15, 23, 42, 0.5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '30px' }}>
          <Layout color="var(--primary-color)" />
          <h1 style={{ fontSize: '1.5rem', margin: 0, background: 'linear-gradient(to right, #3b82f6, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            GraphWeaver
          </h1>
        </div>

        <FileUpload onUploadComplete={fetchGraph} />

        <div style={{ flex: 1, minHeight: 0 }}>
          <ChatInterface />
        </div>
      </div>

      {/* Main Canvas */}
      <div style={{ flex: 1, position: 'relative' }}>
        <GraphCanvas nodes={graphData.nodes} edges={graphData.edges} />
        <div style={{ position: 'absolute', bottom: '20px', right: '20px', background: 'var(--glass-bg)', padding: '10px', borderRadius: '8px', fontSize: '0.8rem', opacity: 0.7 }}>
          {graphData.nodes.length} Nodes | {graphData.edges.length} Edges
        </div>
      </div>
    </div>
  );
}

export default App;
