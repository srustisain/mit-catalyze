import React from 'react';

function TabNavigation({ currentTab, onTabChange }) {
  const tabs = [
    { id: 'research', label: 'Research', icon: '🔬' },
    { id: 'protocol', label: 'Protocol', icon: '📋' },
    { id: 'automate', label: 'Automate', icon: '🤖' },
    { id: 'safety', label: 'Safety', icon: '⚠️' },
  ];

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <div className="flex space-x-1 p-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              currentTab === tab.id
                ? 'gradient-bg text-white'
                : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default TabNavigation;

