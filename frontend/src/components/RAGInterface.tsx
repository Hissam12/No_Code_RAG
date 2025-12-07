import { useState, useEffect } from 'react';
import axios from 'axios';
import { BookOpen, Send, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

interface RetrievedChunk {
    page: number;
    text: string;
    distance: number;
}

interface RAGResponse {
    answer: string;
    sources: number[];
    retrieved_chunks: RetrievedChunk[];
    question: string;
}

const RAGInterface = () => {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState<RAGResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [stats, setStats] = useState<any>(null);
    const [ingesting, setIngesting] = useState(false);
    const [showChunks, setShowChunks] = useState(false);

    // Fetch stats on component mount
    useEffect(() => {
        fetchStats();
    }, []);


    const fetchStats = async () => {
        try {
            const res = await axios.get('http://localhost:8000/rag/stats');
            setStats(res.data);
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        }
    };

    const handleIngest = async () => {
        setIngesting(true);
        setError(null);
        try {
            const res = await axios.post('http://localhost:8000/rag/ingest');
            alert(`✅ Successfully ingested textbook!\n\nPages: ${res.data.pages}\nChunks: ${res.data.chunks}`);
            await fetchStats();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to ingest PDF');
        } finally {
            setIngesting(false);
        }
    };

    const handleQuery = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        setResponse(null);

        try {
            const res = await axios.post('http://localhost:8000/rag/query', {
                query: query.trim(),
                n_results: 5
            });
            setResponse(res.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to get answer');
        } finally {
            setLoading(false);
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
            <div style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <BookOpen size={28} color="#3b82f6" />
                    <h2 style={{
                        margin: 0,
                        fontSize: '1.5rem',
                        background: 'linear-gradient(to right, #3b82f6, #8b5cf6)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent'
                    }}>
                        RAG Assistant
                    </h2>
                </div>
                <p style={{ margin: 0, color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem' }}>
                    Ask questions about the Computer Science textbook
                </p>
            </div>

            {/* Stats & Ingest */}
            <div style={{
                background: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                borderRadius: '12px',
                padding: '16px',
                marginBottom: '24px'
            }}>
                {stats ? (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.6)' }}>Database Status</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff', marginTop: '4px' }}>
                                {stats.document_count} chunks indexed
                            </div>
                        </div>
                        {stats.status === 'empty' && (
                            <button
                                onClick={handleIngest}
                                disabled={ingesting}
                                style={{
                                    padding: '10px 20px',
                                    background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '8px',
                                    cursor: ingesting ? 'not-allowed' : 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    opacity: ingesting ? 0.6 : 1,
                                    transition: 'all 0.3s ease'
                                }}
                            >
                                {ingesting ? <Loader2 size={18} className="animate-spin" /> : <BookOpen size={18} />}
                                {ingesting ? 'Ingesting...' : 'Ingest Textbook'}
                            </button>
                        )}
                    </div>
                ) : (
                    <div>Loading stats...</div>
                )}
            </div>

            {/* Query Form */}
            <form onSubmit={handleQuery} style={{ marginBottom: '24px' }}>
                <div style={{ position: 'relative' }}>
                    <textarea
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Ask a question about the textbook... (e.g., What is binary?)"
                        disabled={loading || stats?.status === 'empty'}
                        style={{
                            width: '100%',
                            minHeight: '100px',
                            padding: '16px',
                            paddingRight: '60px',
                            background: 'rgba(30, 41, 59, 0.6)',
                            border: '1px solid rgba(59, 130, 246, 0.3)',
                            borderRadius: '12px',
                            color: 'white',
                            fontSize: '1rem',
                            resize: 'vertical',
                            outline: 'none',
                            transition: 'border-color 0.3s ease'
                        }}
                        onFocus={(e) => e.target.style.borderColor = 'rgba(59, 130, 246, 0.6)'}
                        onBlur={(e) => e.target.style.borderColor = 'rgba(59, 130, 246, 0.3)'}
                    />
                    <button
                        type="submit"
                        disabled={loading || !query.trim() || stats?.status === 'empty'}
                        style={{
                            position: 'absolute',
                            bottom: '12px',
                            right: '12px',
                            width: '44px',
                            height: '44px',
                            background: loading || !query.trim() || stats?.status === 'empty'
                                ? 'rgba(59, 130, 246, 0.3)'
                                : 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: loading || !query.trim() || stats?.status === 'empty' ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            transition: 'all 0.3s ease',
                            opacity: loading || !query.trim() || stats?.status === 'empty' ? 0.5 : 1
                        }}
                        onMouseEnter={(e) => {
                            if (!loading && query.trim() && stats?.status !== 'empty') {
                                e.currentTarget.style.transform = 'scale(1.05)';
                            }
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'scale(1)';
                        }}
                    >
                        {loading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} color="white" />}
                    </button>
                </div>
            </form>

            {/* Error Message */}
            {error && (
                <div style={{
                    padding: '16px',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '12px',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                }}>
                    <AlertCircle size={20} color="#ef4444" />
                    <span style={{ color: '#fca5a5' }}>{error}</span>
                </div>
            )}

            {/* Response */}
            {response && (
                <div style={{
                    background: 'rgba(59, 130, 246, 0.05)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    borderRadius: '12px',
                    padding: '20px',
                    flex: 1,
                    overflowY: 'auto'
                }}>
                    {/* Question */}
                    <div style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                        <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.5)', marginBottom: '8px' }}>Question</div>
                        <div style={{ fontSize: '1rem', color: 'rgba(255, 255, 255, 0.9)' }}>{response.question}</div>
                    </div>

                    {/* Answer */}
                    <div style={{ marginBottom: '20px' }}>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            marginBottom: '12px'
                        }}>
                            <CheckCircle2 size={18} color="#10b981" />
                            <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.5)' }}>Answer</div>
                        </div>
                        <div style={{
                            fontSize: '1rem',
                            lineHeight: '1.6',
                            color: 'rgba(255, 255, 255, 0.95)',
                            whiteSpace: 'pre-wrap'
                        }}>
                            {response.answer}
                        </div>
                    </div>

                    {/* Sources */}
                    {response.sources.length > 0 && (
                        <div style={{ marginBottom: '20px' }}>
                            <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.5)', marginBottom: '8px' }}>
                                Sources (Pages)
                            </div>
                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                {response.sources.map((page) => (
                                    <span
                                        key={page}
                                        style={{
                                            padding: '6px 12px',
                                            background: 'rgba(59, 130, 246, 0.2)',
                                            border: '1px solid rgba(59, 130, 246, 0.4)',
                                            borderRadius: '6px',
                                            fontSize: '0.85rem',
                                            color: '#93c5fd'
                                        }}
                                    >
                                        Page {page}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Retrieved Chunks */}
                    {response.retrieved_chunks.length > 0 && (
                        <div>
                            <button
                                onClick={() => setShowChunks(!showChunks)}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: '#3b82f6',
                                    cursor: 'pointer',
                                    fontSize: '0.85rem',
                                    padding: '8px 0',
                                    marginBottom: '12px',
                                    textDecoration: 'underline'
                                }}
                            >
                                {showChunks ? '▼' : '▶'} View Retrieved Context ({response.retrieved_chunks.length} chunks)
                            </button>

                            {showChunks && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                    {response.retrieved_chunks.map((chunk, idx) => (
                                        <div
                                            key={idx}
                                            style={{
                                                padding: '12px',
                                                background: 'rgba(30, 41, 59, 0.4)',
                                                border: '1px solid rgba(59, 130, 246, 0.2)',
                                                borderRadius: '8px'
                                            }}
                                        >
                                            <div style={{
                                                fontSize: '0.75rem',
                                                color: 'rgba(255, 255, 255, 0.5)',
                                                marginBottom: '6px'
                                            }}>
                                                Page {chunk.page} • Relevance: {(1 - chunk.distance).toFixed(3)}
                                            </div>
                                            <div style={{
                                                fontSize: '0.9rem',
                                                color: 'rgba(255, 255, 255, 0.8)',
                                                lineHeight: '1.5'
                                            }}>
                                                {chunk.text}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Empty State */}
            {!response && !loading && !error && stats?.status !== 'empty' && (
                <div style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'rgba(255, 255, 255, 0.4)',
                    fontSize: '0.95rem',
                    textAlign: 'center',
                    padding: '40px'
                }}>
                    Ask a question to get started! 📚
                </div>
            )}
        </div>
    );
};

export default RAGInterface;
