import React from 'react';
import { MessageSquare, Settings, Trash2, Brain, Search } from 'lucide-react';

const Sidebar = ({ 
  demoQueries, 
  onDemoQuery, 
  explainMode, 
  onExplainModeChange, 
  conversationHistory, 
  onClearHistory 
}) => {
  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      {/* Settings */}
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Settings className="w-5 h-5 mr-2" />
          Settings
        </h3>
        
        <label className="flex items-center space-x-3 cursor-pointer">
          <input
            type="checkbox"
            checked={explainMode}
            onChange={(e) => onExplainModeChange(e.target.checked)}
            className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
          />
          <div className="flex items-center">
            <Brain className="w-4 h-4 mr-2 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Explain Like I'm New</span>
          </div>
        </label>
        <p className="text-xs text-gray-500 mt-1 ml-7">Toggle simple explanations for beginners</p>
      </div>

      {/* Demo Queries */}
      <div className="p-6 border-b border-gray-200 flex-1">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Search className="w-5 h-5 mr-2" />
          Demo Queries
        </h3>
        <p className="text-sm text-gray-500 mb-4">Click any query to try it instantly</p>
        
        <div className="space-y-2">
          {demoQueries.map((query) => (
            <button
              key={query.id}
              onClick={() => onDemoQuery(query.query)}
              className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors duration-200 group"
            >
              <div className="text-sm font-medium text-gray-900 group-hover:text-primary-600">
                {query.query}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {query.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Conversation History */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <MessageSquare className="w-5 h-5 mr-2" />
            History
          </h3>
          {conversationHistory.length > 0 && (
            <button
              onClick={onClearHistory}
              className="text-red-500 hover:text-red-700 transition-colors duration-200"
              title="Clear history"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
        
        {conversationHistory.length === 0 ? (
          <p className="text-sm text-gray-500">No conversations yet</p>
        ) : (
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {conversationHistory.slice(-5).reverse().map((conv) => (
              <div
                key={conv.id}
                className="p-2 bg-gray-50 rounded text-sm text-gray-700 cursor-pointer hover:bg-gray-100 transition-colors duration-200"
              >
                <div className="font-medium truncate">{conv.query}</div>
                <div className="text-xs text-gray-500">
                  {new Date(conv.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Data Sources */}
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Sources</h3>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center justify-between">
            <span>PubChem</span>
            <span className="text-green-600 font-medium">Active</span>
          </div>
          <div className="flex items-center justify-between">
            <span>OpenAI</span>
            <span className="text-yellow-600 font-medium">Limited</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Opentrons</span>
            <span className="text-green-600 font-medium">Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
