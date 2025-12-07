import { useState, useEffect } from 'react';
import axios from 'axios';
import GraphCanvas from './GraphCanvas';
import { Network, Play, Save, Download, Trash2, Loader2, AlertCircle, CheckCircle2, Send, Settings, Eye } from 'lucide-react';

interface KGStats {
    nodes: number;
    edges: number;
    entity_types: Record<string, number>;
    relation_types: Record<string, number>;
    density: number;
    components: number;
}

interface KGQueryResult {
    answer: string;
    nodes: Array<{ id: string; label: string; type: string }>;
    edges: string[];
    context: string;
    hops: number;
}

const KnowledgeGraphPanel = () => {
    const [stats, setStats] = useState<KGStats | null>(null);
    const [query, setQuery] = useState('');
    const [queryResult, setQueryResult] = useState<KGQueryResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [ingesting, setIngesting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    // Ingestion settings
    const [useFast, setUseFast] = useState(true);
    const [samplingRate, setSamplingRate] = useState(0.4);
    const [batchSize, setBatchSize] = useState(20);
    const [showSettings, setShowSettings] = useState(false);

    // Visualization
    const [showGraph, setShowGraph] = useState(false);
    const [graphData, setGraphData] = useState<{ nodes: any[], edges: any[] }>({ nodes: [], edges: [] });
    const [loadingGraph, setLoadingGraph] = useState(false);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const res = await axios.get('http://localhost:8000/kg/stats');
            setStats(res.data);
        } catch (err) {
            console.error('Failed to fetch KG stats:', err);
        }
    };

    const handleIngest = async () => {
        setIngesting(true);
        setError(null);
        setSuccessMessage(null);
        try {
            const res = await axios.post('http://localhost:8000/kg/ingest', {
                batch_size: batchSize,
                use_fast: useFast,
                sampling_rate: samplingRate
            });
            setSuccessMessage(`Ingested ${res.data.pages} pages (sampled ${Math.round(samplingRate * 100)}%), extracted ${res.data.unique_nodes} entities and ${res.data.unique_edges} relationships`);
            await fetchStats();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to ingest document');
        } finally {
            setIngesting(false);
        }
    };

    const handleQuery = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        setQueryResult(null);
        try {
            const res = await axios.post('http://localhost:8000/kg/query', {
                query: query.trim(),
                hop_depth: 2
            });
            setQueryResult(res.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Query failed');
        } finally {
            setLoading(false);
        }
    };

    const handleVisualize = async () => {
        if (showGraph) {
            setShowGraph(false);
            return;
        }

        setLoadingGraph(true);
        setError(null);
        try {
            const res = await axios.get('http://localhost:8000/kg/graph');
            setGraphData(res.data);
            setShowGraph(true);
        } catch (err: any) {
            setError('Failed to load graph data for visualization');
        } finally {
            setLoadingGraph(false);
        }
    };

    const handleSave = async () => {
        try {
            await axios.post('http://localhost:8000/kg/save');
            setSuccessMessage('Graph saved to disk');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to save');
        }
    };

    const handleLoad = async () => {
        try {
            const res = await axios.post('http://localhost:8000/kg/load');
            setSuccessMessage(res.data.message);
            await fetchStats();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load');
        }
    };

    const handleClear = async () => {
        if (!confirm('Are you sure you want to clear the knowledge graph?')) return;
        try {
            await axios.delete('http://localhost:8000/kg/clear');
            setSuccessMessage('Graph cleared');
            setQueryResult(null);
            await fetchStats();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to clear');
        }
    };

    return (
        <div style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%)',
            padding: '24px',
            overflowY: 'auto'
        }}>
            {/* Header */}
            <div style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <Network size={28} color="#10b981" />
                    <h2 style={{
                        margin: 0,
                        fontSize: '1.5rem',
                        background: 'linear-gradient(to right, #10b981, #3b82f6)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent'
                    }}>
                        Knowledge Graph
                    </h2>
                </div>
                <p style={{ margin: 0, color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.85rem' }}>
                    Entity extraction with multi-hop traversal
                </p>
            </div>

            {/* Stats Card */}
            <div style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: '12px',
                padding: '16px',
                marginBottom: '20px'
            }}>
                {stats ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                        <div>
                            <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.5)' }}>Entities</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>{stats.nodes}</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.5)' }}>Relations</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#3b82f6' }}>{stats.edges}</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.5)' }}>Components</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#8b5cf6' }}>{stats.components}</div>
                        </div>
                    </div>
                ) : (
                    <div>Loading stats...</div>
                )}
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
                <button
                    onClick={handleIngest}
                    disabled={ingesting}
                    style={{
                        padding: '10px 16px',
                        background: ingesting ? 'rgba(16, 185, 129, 0.3)' : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: ingesting ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.85rem'
                    }}
                >
                    {ingesting ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                    {ingesting ? 'Ingesting...' : 'Build Graph'}
                </button>

                <button
                    onClick={() => setShowSettings(!showSettings)}
                    style={{
                        padding: '10px',
                        background: showSettings ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                        color: 'rgba(255, 255, 255, 0.7)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                    }}
                    title="Ingestion Settings"
                >
                    <Settings size={16} />
                </button>

                <div style={{ width: '1px', height: '24px', background: 'rgba(255,255,255,0.1)', margin: '0 8px' }} />

                <button
                    onClick={handleVisualize}
                    disabled={loadingGraph}
                    style={{
                        padding: '10px 16px',
                        background: showGraph ? 'rgba(59, 130, 246, 0.3)' : 'rgba(255, 255, 255, 0.05)',
                        color: showGraph ? '#60a5fa' : 'white',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: '8px',
                        cursor: loadingGraph ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.85rem'
                    }}
                >
                    {loadingGraph ? <Loader2 size={16} className="animate-spin" /> : <Eye size={16} />}
                    {showGraph ? 'Hide Graph' : 'Visualize'}
                </button>

                <button
                    onClick={handleSave}
                    style={{
                        padding: '10px 16px',
                        background: 'rgba(59, 130, 246, 0.2)',
                        color: '#93c5fd',
                        border: '1px solid rgba(59, 130, 246, 0.4)',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.85rem'
                    }}
                >
                    <Save size={16} />
                    Save
                </button>
                <button
                    onClick={handleLoad}
                    style={{
                        padding: '10px 16px',
                        background: 'rgba(139, 92, 246, 0.2)',
                        color: '#c4b5fd',
                        border: '1px solid rgba(139, 92, 246, 0.4)',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.85rem'
                    }}
                >
                    <Download size={16} />
                    Load
                </button>
                <button
                    onClick={handleClear}
                    style={{
                        padding: '10px 16px',
                        background: 'rgba(239, 68, 68, 0.2)',
                        color: '#fca5a5',
                        border: '1px solid rgba(239, 68, 68, 0.4)',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.85rem'
                    }}
                >
                    <Trash2 size={16} />
                    Clear
                </button>
            </div>

            {/* Settings Panel */}
            {showSettings && (
                <div style={{
                    background: 'rgba(0, 0, 0, 0.2)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    padding: '16px',
                    marginBottom: '20px',
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '16px'
                }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.7)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <input
                                type="checkbox"
                                checked={useFast}
                                onChange={(e) => setUseFast(e.target.checked)}
                                style={{ accentColor: '#10b981' }}
                            />
                            Fast Mode (OpenAI gpt-4o-mini)
                        </label>
                        <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.4)', marginLeft: '24px' }}>
                            ~50x faster than local model. Costs ~$0.15/1M tokens.
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                            Sampling Rate: {Math.round(samplingRate * 100)}%
                        </label>
                        <input
                            type="range"
                            min="0.1"
                            max="1.0"
                            step="0.1"
                            value={samplingRate}
                            onChange={(e) => setSamplingRate(parseFloat(e.target.value))}
                            style={{ width: '100%', accentColor: '#3b82f6' }}
                        />
                        <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.4)' }}>
                            Process fewer chunks to save costs/time.
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                            Batch Size: {batchSize}
                        </label>
                        <input
                            type="range"
                            min="5"
                            max="50"
                            step="5"
                            value={batchSize}
                            onChange={(e) => setBatchSize(parseInt(e.target.value))}
                            style={{ width: '100%', accentColor: '#8b5cf6' }}
                        />
                        <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.4)' }}>
                            Chunks per API call (higher = faster but more tokens).
                        </div>
                    </div>
                </div>
            )}

            {/* Graph Visualization */}
            {showGraph && (
                <div style={{
                    height: '500px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    marginBottom: '20px',
                    overflow: 'hidden'
                }}>
                    <GraphCanvas nodes={graphData.nodes} edges={graphData.edges} />
                </div>
            )}

            {/* Messages */}
            {error && (
                <div style={{
                    padding: '12px',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '8px',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    <AlertCircle size={16} color="#ef4444" />
                    <span style={{ color: '#fca5a5', fontSize: '0.9rem' }}>{error}</span>
                </div>
            )}

            {successMessage && (
                <div style={{
                    padding: '12px',
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: '8px',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    <CheckCircle2 size={16} color="#10b981" />
                    <span style={{ color: '#6ee7b7', fontSize: '0.9rem' }}>{successMessage}</span>
                </div>
            )}

            {/* Query Form */}
            <form onSubmit={handleQuery} style={{ marginBottom: '20px' }}>
                <div style={{ position: 'relative' }}>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Query the knowledge graph..."
                        disabled={loading || (stats?.nodes === 0)}
                        style={{
                            width: '100%',
                            padding: '14px 50px 14px 16px',
                            background: 'rgba(30, 41, 59, 0.6)',
                            border: '1px solid rgba(16, 185, 129, 0.3)',
                            borderRadius: '10px',
                            color: 'white',
                            fontSize: '0.95rem',
                            outline: 'none'
                        }}
                    />
                    <button
                        type="submit"
                        disabled={loading || !query.trim() || (stats?.nodes === 0)}
                        style={{
                            position: 'absolute',
                            right: '8px',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            width: '36px',
                            height: '36px',
                            background: loading || !query.trim() ? 'rgba(16, 185, 129, 0.3)' : '#10b981',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} color="white" />}
                    </button>
                </div>
            </form>

            {/* Query Result */}
            {queryResult && (
                <div style={{
                    background: 'rgba(16, 185, 129, 0.05)',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                    borderRadius: '12px',
                    padding: '16px',
                    flex: 1,
                    overflowY: 'auto'
                }}>
                    {/* Answer */}
                    <div style={{ marginBottom: '16px' }}>
                        <div style={{ fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.5)', marginBottom: '8px' }}>Answer</div>
                        <div style={{ color: 'rgba(255, 255, 255, 0.95)', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>
                            {queryResult.answer}
                        </div>
                    </div>

                    {/* Entities Found */}
                    {queryResult.nodes.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                            <div style={{ fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.5)', marginBottom: '8px' }}>
                                Entities ({queryResult.nodes.length})
                            </div>
                            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                {queryResult.nodes.map((node) => (
                                    <span
                                        key={node.id}
                                        style={{
                                            padding: '4px 10px',
                                            background: 'rgba(16, 185, 129, 0.2)',
                                            border: '1px solid rgba(16, 185, 129, 0.4)',
                                            borderRadius: '6px',
                                            fontSize: '0.8rem',
                                            color: '#6ee7b7'
                                        }}
                                    >
                                        {node.label}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Relationships */}
                    {queryResult.edges.length > 0 && (
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.5)', marginBottom: '8px' }}>
                                Relationships ({queryResult.edges.length})
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.7)', lineHeight: '1.6' }}>
                                {queryResult.edges.slice(0, 10).map((edge, i) => (
                                    <div key={i} style={{ fontFamily: 'monospace' }}>{edge}</div>
                                ))}
                                {queryResult.edges.length > 10 && (
                                    <div style={{ color: 'rgba(255, 255, 255, 0.4)', marginTop: '8px' }}>
                                        + {queryResult.edges.length - 10} more...
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default KnowledgeGraphPanel;
