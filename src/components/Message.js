import React from 'react';

function Message({ message, darkMode }) {
  const isUser = message.isUser;
  const isLoading = message.isLoading;
  const isStreaming = message.isStreaming;

  // Simple markdown-like rendering
  const renderContent = (content) => {
    // Split by newlines and render
    const lines = content.split('\n');
    return lines.map((line, idx) => {
      // Handle code blocks
      if (line.startsWith('```')) {
        return <div key={idx} className="my-2"><code className="block bg-gray-800 text-white p-2 rounded">{line}</code></div>;
      }
      // Handle bold
      const boldRegex = /\*\*(.+?)\*\*/g;
      let processedLine = line;
      const parts = [];
      let lastIndex = 0;
      let match;
      
      while ((match = boldRegex.exec(line)) !== null) {
        if (match.index > lastIndex) {
          parts.push(line.substring(lastIndex, match.index));
        }
        parts.push(<strong key={match.index}>{match[1]}</strong>);
        lastIndex = match.index + match[0].length;
      }
      if (lastIndex < line.length) {
        parts.push(line.substring(lastIndex));
      }
      
      return <div key={idx}>{parts.length > 0 ? parts : line}</div>;
    });
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-3xl rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-blue-600 text-white ml-auto'
            : darkMode
            ? 'bg-gray-800 text-gray-100'
            : 'bg-gray-100 text-gray-900'
        } ${isLoading || isStreaming ? 'opacity-75' : ''}`}
      >
        <div className="chat-message">
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <span>{message.content}</span>
              <span className="animate-pulse">...</span>
            </div>
          ) : (
            <div className="message-content whitespace-pre-wrap">
              {renderContent(message.content)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Message;

