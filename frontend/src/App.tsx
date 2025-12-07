import { useState, useEffect } from 'react';
import axios from 'axios';
import GraphCanvas from './components/GraphCanvas';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import RAGInterface from './components/RAGInterface';
import KnowledgeGraphPanel from './components/KnowledgeGraphPanel';
import { Layout, BookOpen, Network } from 'lucide-react';

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [activeTab, setActiveTab] = useState<'graph' | 'rag' | 'kg'>('rag'); // Default to RAG

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
      <div style={{
        width: activeTab === 'rag' || activeTab === 'kg' ? '600px' : '350px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid var(--glass-border)',
        background: 'rgba(15, 23, 42, 0.5)',
        transition: 'width 0.3s ease'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <Layout color="var(--primary-color)" />
          <h1 style={{
            fontSize: '1.5rem',
            margin: 0,
            background: 'linear-gradient(to right, #3b82f6, #8b5cf6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            GraphWeaver
          </h1>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '20px',
          background: 'rgba(30, 41, 59, 0.4)',
          padding: '4px',
          borderRadius: '12px'
        }}>
          <button
            onClick={() => setActiveTab('rag')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'rag'
                ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)'
                : 'transparent',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '0.9rem',
              fontWeight: activeTab === 'rag' ? '600' : '400',
              transition: 'all 0.3s ease',
              opacity: activeTab === 'rag' ? 1 : 0.7
            }}
          >
            <BookOpen size={18} />
            RAG Assistant
          </button>
          <button
            onClick={() => setActiveTab('graph')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'graph'
                ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)'
                : 'transparent',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '0.9rem',
              fontWeight: activeTab === 'graph' ? '600' : '400',
              transition: 'all 0.3s ease',
              opacity: activeTab === 'graph' ? 1 : 0.7
            }}
          >
            <Layout size={18} />
            Graph View
          </button>
          <button
            onClick={() => setActiveTab('kg')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'kg'
                ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                : 'transparent',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '0.9rem',
              fontWeight: activeTab === 'kg' ? '600' : '400',
              transition: 'all 0.3s ease',
              opacity: activeTab === 'kg' ? 1 : 0.7
            }}
          >
            <Network size={18} />
            Knowledge Graph
          </button>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'graph' ? (
          <>
            <FileUpload onUploadComplete={fetchGraph} />
            <div style={{ flex: 1, minHeight: 0 }}>
              <ChatInterface />
            </div>
          </>
        ) : activeTab === 'rag' ? (
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
            <RAGInterface />
          </div>
        ) : (
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
            <KnowledgeGraphPanel />
          </div>
        )}
      </div>

      {/* Main Canvas - Only show for Graph View */}
      {activeTab === 'graph' && (
        <div style={{ flex: 1, position: 'relative' }}>
          <GraphCanvas nodes={graphData.nodes} edges={graphData.edges} />
          <div style={{
            position: 'absolute',
            bottom: '20px',
            right: '20px',
            background: 'var(--glass-bg)',
            padding: '10px',
            borderRadius: '8px',
            fontSize: '0.8rem',
            opacity: 0.7
          }}>
            {graphData.nodes.length} Nodes | {graphData.edges.length} Edges
          </div>
        </div>
      )}

      {/* Full width for RAG view */}
      {activeTab === 'rag' && (
        <div style={{
          flex: 1,
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 1) 0%, rgba(30, 41, 59, 1) 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '40px'
        }}>
          <div style={{
            maxWidth: '800px',
            width: '100%',
            textAlign: 'center',
            color: 'rgba(255, 255, 255, 0.6)'
          }}>
            <BookOpen size={64} color="#3b82f6" style={{ margin: '0 auto 20px' }} />
            <h2 style={{
              fontSize: '1.8rem',
              marginBottom: '12px',
              background: 'linear-gradient(to right, #3b82f6, #8b5cf6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Computer Science Textbook Assistant
            </h2>
            <p style={{ fontSize: '1.1rem', lineHeight: '1.6' }}>
              Ask questions about the Cambridge IGCSE Computer Science textbook.<br />
              Powered by RAG with local embeddings and gpt-oss:20b.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

