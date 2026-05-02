import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import './App.css';

const promptPresets = [
  'Map the key entities, relationships, and repeated themes in this file.',
  'Turn the latest upload into a concise executive briefing.',
  'List the most surprising signals and open questions.',
  'What would be the first 3 follow-up questions I should ask?',
];

const pipelineSteps = [
  {
    title: 'Ingest',
    description: 'Choose a file and stage it for processing.',
  },
  {
    title: 'Forge',
    description: 'Generate a multimodal summary and sync the graph.',
  },
  {
    title: 'Brief',
    description: 'Ask questions and receive grounded answers.',
  },
];

const insightCards = [
  {
    label: 'Product mode',
    value: 'Signal Forge',
    note: 'A research cockpit for turning files into answers.',
  },
  {
    label: 'Query surface',
    value: 'Graph + vector retrieval',
    note: 'The backend keeps both retrieval paths active.',
  },
  {
    label: 'Interaction style',
    value: 'Briefing-led chat',
    note: 'Upload first, then interrogate the knowledge base.',
  },
];

export default function App() {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('Awaiting a document.');
  const transcriptRef = useRef(null);

  const fileLabel = file ? file.name : 'No file selected';
  const fileSize = file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : '0 MB';
  const stageIndex = loading ? 1 : file ? 2 : 0;
  const statusTone = status.toLowerCase().includes('error') ? 'danger' : loading ? 'busy' : 'ready';

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [messages]);

  const onUpload = async () => {
    if (!file || loading) return;
    const formData = new FormData();
    formData.append('file', file);
    setLoading(true);
    setStatus('Uploading artifact and extracting signal...');
    try {
      await axios.post('http://localhost:8000/upload', formData);
      setStatus('Artifact indexed. Graph and vectors are synced.');
    } catch {
      setStatus('Error indexing the upload. Check the backend service.');
    }
    setLoading(false);
  };

  const onChat = async (overrideQuery) => {
    const nextQuery = (overrideQuery ?? query).trim();
    if (!nextQuery || loading) return;
    setLoading(true);
    const userMsg = { role: 'user', text: nextQuery };
    setMessages(prev => [...prev, userMsg]);
    setStatus('Consulting the graph and retrieval layers...');
    
    try {
      const res = await axios.post('http://localhost:8000/chat', { query: nextQuery });
      setMessages(prev => [...prev, { role: 'ai', text: res.data.answer }]);
      setStatus('Answer delivered from the briefing engine.');
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: 'Error reaching backend.' }]);
      setStatus('Error reaching the assistant service.');
    }
    setQuery('');
    setLoading(false);
  };

  const setPresetQuery = (preset) => {
    setQuery(preset);
  };

  return (
    <div className="app-shell">
      <div className="ambient ambient-a" aria-hidden="true" />
      <div className="ambient ambient-b" aria-hidden="true" />

      <main className="workspace">
        <aside className="sidebar">
          <section className="brand-panel">
            <div className="brand-row">
              <div className="brand-mark">S</div>
              <div>
                <p className="eyebrow">Intelligence Studio</p>
                <h1>Signal Forge</h1>
              </div>
            </div>
            <p className="brand-copy">
              A redesigned research cockpit that turns uploads into a briefing stream,
              graph-backed answers, and a sharper project story.
            </p>
            <div className={`status-pill status-${statusTone}`} aria-live="polite">
              <span className="status-dot" />
              {status}
            </div>
          </section>

          <section className="card upload-card">
            <div className="card-header">
              <div>
                <p className="eyebrow">File intake</p>
                <h2>Stage a brief</h2>
              </div>
              <span className="chip">{loading ? 'Working' : 'Ready'}</span>
            </div>

            <label className="upload-zone" htmlFor="signal-upload">
              <span className="upload-title">Choose a document, image, or other source</span>
              <span className="upload-subtitle">{fileLabel}</span>
              <span className="upload-meta">{fileSize}</span>
            </label>
            <input
              id="signal-upload"
              type="file"
              onChange={(event) => {
                const nextFile = event.target.files?.[0] ?? null;
                setFile(nextFile);
                setStatus(nextFile ? 'Document staged and ready to index.' : 'Awaiting a document.');
              }}
              className="file-input"
            />

            <button className="primary-button" onClick={onUpload} disabled={!file || loading}>
              {loading ? 'Processing brief...' : 'Index brief'}
            </button>
          </section>

          <section className="card details-card">
            <div className="card-header">
              <div>
                <p className="eyebrow">Pipeline</p>
                <h2>What happens next</h2>
              </div>
            </div>

            <div className="pipeline">
              {pipelineSteps.map((step, index) => {
                const isActive = index <= stageIndex;
                return (
                  <article className={`pipeline-step ${isActive ? 'is-active' : ''}`} key={step.title}>
                    <div className="step-index">0{index + 1}</div>
                    <div>
                      <h3>{step.title}</h3>
                      <p>{step.description}</p>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        </aside>

        <section className="studio">
          <section className="hero-panel card">
            <div className="hero-copy">
              <p className="eyebrow">New project identity</p>
              <h2>Briefs in, answers out.</h2>
              <p>
                This interface now feels like a different product: part research lab, part
                command deck, and part executive briefing room. Upload a source, then ask the
                system to explain what matters.
              </p>
            </div>

            <div className="hero-metrics">
              {insightCards.map((card) => (
                <article className="metric-card" key={card.label}>
                  <p className="metric-label">{card.label}</p>
                  <h3>{card.value}</h3>
                  <p>{card.note}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="prompt-strip card">
            <div className="card-header">
              <div>
                <p className="eyebrow">Quick prompts</p>
                <h2>Start the conversation</h2>
              </div>
            </div>

            <div className="prompt-grid">
              {promptPresets.map((preset) => (
                <button key={preset} className="prompt-chip" onClick={() => setPresetQuery(preset)}>
                  {preset}
                </button>
              ))}
            </div>
          </section>

          <section className="chat-panel card">
            <div className="card-header chat-header">
              <div>
                <p className="eyebrow">Briefing stream</p>
                <h2>Conversation log</h2>
              </div>
              <div className="mini-stats">
                <span>{messages.length} turns</span>
                <span>{stageIndex === 0 ? 'Idle' : stageIndex === 1 ? 'Loading' : 'Ready'}</span>
              </div>
            </div>

            <div className="transcript" ref={transcriptRef}>
              {messages.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">⌁</div>
                  <h3>No briefing yet</h3>
                  <p>
                    Upload a file, index it, then ask for entities, relationships, summaries, or
                    follow-up questions.
                  </p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div className={`message-row ${message.role === 'user' ? 'is-user' : 'is-ai'}`} key={index}>
                    <div className="message-badge">{message.role === 'user' ? 'You' : 'AI'}</div>
                    <div className="message-bubble">
                      <p>{message.text.replace(/\*\*/g, '')}</p>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="composer">
              <input
                className="composer-input"
                placeholder="Ask for a summary, entities, themes, or a decision-ready take..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    onChat();
                  }
                }}
              />
              <button className="primary-button send-button" onClick={() => onChat()} disabled={loading || !query.trim()}>
                {loading ? 'Sending...' : 'Dispatch'}
              </button>
            </div>
          </section>
        </section>
      </main>
    </div>
  );
}