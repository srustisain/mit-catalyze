import React, { useState, useRef } from 'react';

function ChatInput({ onSendMessage, onPdfUpload, pdfContext, darkMode }) {
  const [input, setInput] = useState('');
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      onPdfUpload(file);
    }
  };

  return (
    <div className={`border-t ${darkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'} p-4`}>
      {pdfContext && (
        <div className={`mb-2 p-2 rounded ${darkMode ? 'bg-gray-700' : 'bg-blue-50'} text-sm`}>
          📄 PDF loaded: {pdfContext.filename}
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex items-center space-x-2">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf"
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className={`p-2 rounded-lg ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} transition`}
          title="Upload PDF"
        >
          📄
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={pdfContext ? `Ask questions about "${pdfContext.filename}"...` : "Type your message..."}
          className={`flex-1 px-4 py-2 rounded-lg border ${
            darkMode
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'bg-white border-gray-300 text-gray-900'
          } focus:outline-none focus:ring-2 focus:ring-blue-500`}
        />
        <button
          type="submit"
          className={`px-6 py-2 rounded-lg gradient-bg text-white font-semibold hover:opacity-90 transition`}
        >
          Send
        </button>
      </form>
    </div>
  );
}

export default ChatInput;

