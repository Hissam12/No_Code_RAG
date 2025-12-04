import React, { useState } from 'react';
import axios from 'axios';
import { Send } from 'lucide-react';

const ChatInterface: React.FC = () => {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<{ role: 'user' | 'ai'; content: string; citations?: string[] }[]>([]);
    const [loading, setLoading] = useState(false);

    const handleSend = async () => {
        if (!query.trim()) return;

        const userMsg = { role: 'user' as const, content: query };
        setMessages((prev) => [...prev, userMsg]);
        setLoading(true);
        setQuery('');

        try {
            const res = await axios.post('http://localhost:8000/query', { query: userMsg.content });
            const aiMsg = {
                role: 'ai' as const,
                content: res.data.answer,
                citations: res.data.citations
            };
            setMessages((prev) => [...prev, aiMsg]);
        } catch (error) {
            console.error('Query failed:', error);
            setMessages((prev) => [...prev, { role: 'ai', content: 'Error processing query.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '20px' }}>
            <h3 style={{ marginTop: 0 }}>Graph Chat</h3>
            <div style={{ flex: 1, overflowY: 'auto', marginBottom: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {messages.map((msg, i) => (
                    <div key={i} style={{
                        alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        background: msg.role === 'user' ? 'var(--primary-color)' : 'var(--secondary-color)',
                        padding: '10px',
                        borderRadius: '8px',
                        maxWidth: '80%'
                    }}>
                        <div>{msg.content}</div>
                        {msg.citations && msg.citations.length > 0 && (
                            <div style={{ fontSize: '0.8em', opacity: 0.7, marginTop: '5px' }}>
                                Sources: {msg.citations.join(', ')}
                            </div>
                        )}
                    </div>
                ))}
                {loading && <div style={{ alignSelf: 'flex-start', opacity: 0.5 }}>Thinking...</div>}
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask a question..."
                    style={{ flex: 1, padding: '10px', borderRadius: '8px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white' }}
                />
                <button className="btn" onClick={handleSend} disabled={loading}>
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;
