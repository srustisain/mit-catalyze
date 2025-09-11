import React from 'react';
import { Loader2 } from 'lucide-react';

const LoadingSpinner = () => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-8 flex flex-col items-center space-y-4">
      <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Processing Your Query
        </h3>
        <p className="text-sm text-gray-500">
          Analyzing chemistry data and generating protocol...
        </p>
      </div>
    </div>
  );
};

export default LoadingSpinner;
