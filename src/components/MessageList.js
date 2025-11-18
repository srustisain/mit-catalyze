import React from 'react';
import Message from './Message';

function MessageList({ messages, darkMode }) {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <Message key={message.id} message={message} darkMode={darkMode} />
      ))}
    </div>
  );
}

export default MessageList;

