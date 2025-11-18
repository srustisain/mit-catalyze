import React from 'react';

function Sidebar({ isOpen, onClose, darkMode }) {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 ${
          darkMode ? 'bg-gray-800' : 'bg-white'
        } border-r ${
          darkMode ? 'border-gray-700' : 'border-gray-200'
        } transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Chat History
            </h2>
            <button
              onClick={onClose}
              className={`lg:hidden p-2 rounded ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
            >
              ✕
            </button>
          </div>
          <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Chat history will appear here
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;

