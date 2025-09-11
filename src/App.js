import React, { useState, useEffect } from 'react';
import { chemistryAPI } from './services/api';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import ResultsPanel from './components/ResultsPanel';
import Sidebar from './components/Sidebar';
import LoadingSpinner from './components/LoadingSpinner';

function App() {
  const [currentQuery, setCurrentQuery] = useState('');
  const [explainMode, setExplainMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentResults, setCurrentResults] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [demoQueries, setDemoQueries] = useState([]);
  const [activeTab, setActiveTab] = useState('protocol');
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load demo queries on component mount
    loadDemoQueries();
    loadConversationHistory();
  }, []);

  const loadDemoQueries = async () => {
    try {
      const data = await chemistryAPI.getDemoQueries();
      setDemoQueries(data.queries);
    } catch (error) {
      console.error('Failed to load demo queries:', error);
    }
  };

  const loadConversationHistory = async () => {
    try {
      const data = await chemistryAPI.getHistory();
      setConversationHistory(data.history);
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  };

  const handleQuerySubmit = async (query) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setCurrentQuery(query);

    try {
      const results = await chemistryAPI.processQuery(query, explainMode);
      setCurrentResults(results);
      setActiveTab('protocol');
      
      // Reload conversation history to get the latest entry
      await loadConversationHistory();
    } catch (error) {
      setError(error.message);
      console.error('Query processing error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoQuery = (query) => {
    setCurrentQuery(query);
    handleQuerySubmit(query);
  };

  const handleClearHistory = async () => {
    try {
      await chemistryAPI.clearHistory();
      setConversationHistory([]);
      setCurrentResults(null);
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  };

  const downloadScript = async (script, filename) => {
    try {
      const blob = new Blob([script], { type: 'text/python' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="flex h-screen pt-16">
        {/* Sidebar */}
        <Sidebar
          demoQueries={demoQueries}
          onDemoQuery={handleDemoQuery}
          explainMode={explainMode}
          onExplainModeChange={setExplainMode}
          conversationHistory={conversationHistory}
          onClearHistory={handleClearHistory}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Chat Interface */}
          <div className="flex-1 p-6">
            <ChatInterface
              onQuerySubmit={handleQuerySubmit}
              isLoading={isLoading}
              error={error}
              conversationHistory={conversationHistory}
            />
          </div>

          {/* Results Panel */}
          {currentResults && (
            <div className="border-t border-gray-200 bg-white">
              <ResultsPanel
                results={currentResults}
                activeTab={activeTab}
                onTabChange={setActiveTab}
                onDownloadScript={downloadScript}
              />
            </div>
          )}

          {/* Loading Overlay */}
          {isLoading && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <LoadingSpinner />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
