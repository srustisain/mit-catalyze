import React from 'react';
import { Beaker, Zap } from 'lucide-react';

const Header = () => {
  return (
    <header className="fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg">
              <Beaker className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Catalyze</h1>
              <p className="text-sm text-gray-500">AI Chemistry Assistant</p>
            </div>
          </div>

          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 px-3 py-1 bg-green-50 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-green-700">Online</span>
            </div>
            <div className="flex items-center space-x-1 text-sm text-gray-500">
              <Zap className="w-4 h-4" />
              <span>Powered by AI</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
