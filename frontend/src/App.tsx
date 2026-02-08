import { useState, useEffect } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { Sidebar } from './components/Sidebar';
import { getHealth } from './api/client';
import type { IngestResponse, HealthStatus } from './types';
import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [recentIngests, setRecentIngests] = useState<IngestResponse[]>([]);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await getHealth();
      setHealthStatus(health);
    } catch (error) {
      console.error('Failed to check health:', error);
      setHealthStatus({
        status: 'degraded',
        services: {
          api: 'disconnected',
          database: 'unknown',
          embedding: 'unknown',
          llm: 'unknown',
        },
      });
    }
  };

  const handleNewConversation = () => {
    setConversationId(null);
  };

  const handleConversationChange = (id: string) => {
    setConversationId(id);
  };

  const handleIngestSuccess = (response: IngestResponse) => {
    setRecentIngests(prev => [response, ...prev.slice(0, 4)]);
  };

  return (
    <div className="app">
      {/* Status Bar */}
      <div className={`status-bar ${healthStatus?.status === 'healthy' ? 'healthy' : 'degraded'}`}>
        <div className="status-indicator">
          <span className="status-dot"></span>
          <span className="status-text">
            {healthStatus?.status === 'healthy' ? 'All systems operational' : 'Some services unavailable'}
          </span>
        </div>
        {recentIngests.length > 0 && (
          <div className="recent-ingests">
            <span className="ingests-label">Recent:</span>
            {recentIngests.slice(0, 3).map((ingest, i) => (
              <span key={i} className="ingest-badge">
                {ingest.filename || ingest.source_type}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Main Layout */}
      <div className="app-layout">
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          onIngestSuccess={handleIngestSuccess}
        />

        <main className={`app-main ${sidebarOpen ? 'sidebar-open' : ''}`}>
          <ChatInterface
            conversationId={conversationId}
            onNewConversation={handleNewConversation}
            onConversationChange={handleConversationChange}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
