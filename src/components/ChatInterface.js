import React, { useState, useRef, useEffect } from 'react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

function ChatInterface({ mode, darkMode }) {
  const [messages, setMessages] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [pdfContext, setPdfContext] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      content: messageText,
      isUser: true,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    // Create loading message
    const loadingId = `loading-${Date.now()}`;
    const loadingMessage = {
      id: loadingId,
      content: '🤖 Thinking...',
      isUser: false,
      isLoading: true
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      // Get conversation history
      const conversationHistory = messages
        .filter(m => !m.isLoading)
        .map(msg => ({
          role: msg.isUser ? 'user' : 'assistant',
          content: msg.content
        }));

      // Prepare request
      const requestBody = {
        message: messageText,
        mode: mode,
        conversation_history: conversationHistory
      };

      if (pdfContext) {
        requestBody.pdf_context = pdfContext;
      }

      // Stream response
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Remove loading message
      setMessages(prev => prev.filter(m => m.id !== loadingId));

      // Create streaming message
      const streamMessageId = `stream-${Date.now()}`;
      let accumulatedContent = '';
      let finalResponse = '';

      setMessages(prev => [...prev, {
        id: streamMessageId,
        content: '',
        isUser: false,
        isStreaming: true
      }]);

      // Read stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'content') {
                accumulatedContent += data.content;
                finalResponse += data.content;
                setMessages(prev => prev.map(m =>
                  m.id === streamMessageId
                    ? { ...m, content: accumulatedContent }
                    : m
                ));
              } else if (data.type === 'done') {
                const agentInfo = data.agent_used ? ` (via ${data.agent_used} agent)` : '';
                const pdfInfo = pdfContext ? ` 📄 (analyzing "${pdfContext.filename}")` : '';
                setMessages(prev => prev.map(m =>
                  m.id === streamMessageId
                    ? {
                        ...m,
                        content: (data.content || accumulatedContent) + agentInfo + pdfInfo,
                        isStreaming: false
                      }
                    : m
                ));
              } else if (data.type === 'error') {
                setMessages(prev => prev.map(m =>
                  m.id === streamMessageId
                    ? { ...m, content: `Error: ${data.content}`, isStreaming: false }
                    : m
                ));
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error calling API:', error);
      setMessages(prev => prev.filter(m => m.id !== loadingId));
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        isUser: false
      }]);
    }
  };

  const handlePdfUpload = async (file) => {
    const formData = new FormData();
    formData.append('pdf', file);

    try {
      const response = await fetch('/api/upload-pdf', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (data.success) {
        setPdfContext({
          filename: data.filename,
          content: data.content,
          file_size: data.file_size,
          timestamp: data.timestamp
        });
      }
    } catch (error) {
      console.error('PDF upload error:', error);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Welcome message if no messages */}
      {messages.length === 0 && (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-2xl">
            <div className="text-6xl mb-4">👋</div>
            <h2 className="text-3xl font-bold mb-4 dark:text-white">Hello! I'm Catalyze</h2>
            <p className="text-lg mb-6 dark:text-gray-300">
              Your AI chemistry assistant. I can help you with research questions, protocol generation, lab automation, and safety analysis.
            </p>
            <p className="text-md dark:text-gray-400">What would you like to explore today?</p>
          </div>
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4" id="chatMessages">
        <MessageList messages={messages} darkMode={darkMode} />
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        onPdfUpload={handlePdfUpload}
        pdfContext={pdfContext}
        darkMode={darkMode}
      />
    </div>
  );
}

export default ChatInterface;

