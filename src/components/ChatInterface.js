import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageCircle } from 'lucide-react';

const ChatInterface = ({ onQuerySubmit, isLoading, error, conversationHistory }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversationHistory]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onQuerySubmit(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto mb-4">
        {conversationHistory.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <MessageCircle className="w-16 h-16 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Welcome to Catalyze
            </h3>
            <p className="text-gray-500 max-w-md">
              Ask me anything about chemistry, materials science, or lab protocols. 
              I'll help you generate detailed procedures and automation scripts.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {conversationHistory.map((conv) => (
              <div key={conv.id} className="space-y-3">
                {/* User Message */}
                <div className="flex justify-end">
                  <div className="max-w-xs lg:max-w-md bg-primary-600 text-white rounded-lg px-4 py-2">
                    <p className="text-sm">{conv.query}</p>
                  </div>
                </div>
                
                {/* Bot Response */}
                <div className="flex justify-start">
                  <div className="max-w-xs lg:max-w-md bg-white border border-gray-200 rounded-lg px-4 py-2">
                    <p className="text-sm text-gray-700">
                      Protocol generated with {conv.response?.analysis?.protocol_steps || 0} steps
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(conv.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex space-x-3">
        <div className="flex-1">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about synthesis, materials properties, reaction conditions, or any chemistry question..."
            className="input-field resize-none"
            rows={2}
            disabled={isLoading}
          />
        </div>
        <button
          type="submit"
          disabled={!inputValue.trim() || isLoading}
          className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
