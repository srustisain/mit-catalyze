import React from 'react';
import { Download, Clock, Target, Zap } from 'lucide-react';

const ProtocolTab = ({ results, onDownloadScript }) => {
  const protocol = results?.protocol || {};
  const automationScript = results?.automation_script || '';

  const handleDownload = () => {
    if (automationScript) {
      onDownloadScript(automationScript, 'catalyze_protocol.py');
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Protocol Header */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {protocol.title || 'Generated Protocol'}
        </h2>
        
        {protocol.reaction && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Chemical Reaction</h3>
            <div className="chemical-formula text-base">
              {protocol.reaction}
            </div>
          </div>
        )}

        {/* Protocol Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center w-8 h-8 bg-primary-100 rounded-lg mx-auto mb-2">
              <Target className="w-4 h-4 text-primary-600" />
            </div>
            <div className="text-sm font-medium text-gray-900">
              {protocol.expected_yield || 'N/A'}
            </div>
            <div className="text-xs text-gray-500">Expected Yield</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center w-8 h-8 bg-secondary-100 rounded-lg mx-auto mb-2">
              <Zap className="w-4 h-4 text-secondary-600" />
            </div>
            <div className="text-sm font-medium text-gray-900">
              {protocol.steps?.length || 0}
            </div>
            <div className="text-xs text-gray-500">Steps</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center w-8 h-8 bg-green-100 rounded-lg mx-auto mb-2">
              <Clock className="w-4 h-4 text-green-600" />
            </div>
            <div className="text-sm font-medium text-gray-900">
              {protocol.steps?.length > 3 ? 'Complex' : 'Simple'}
            </div>
            <div className="text-xs text-gray-500">Complexity</div>
          </div>
        </div>
      </div>

      {/* Protocol Steps */}
      {protocol.steps && protocol.steps.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Step-by-Step Procedure</h3>
          {protocol.steps.map((step, index) => (
            <div key={index} className="card">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 mb-2">
                    {step.title || `Step ${index + 1}`}
                  </h4>
                  <p className="text-gray-700 mb-3">{step.description}</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {step.reagents && (
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <div className="text-xs font-medium text-blue-800 mb-1">Reagents</div>
                        <div className="text-sm text-blue-700">{step.reagents}</div>
                      </div>
                    )}
                    {step.conditions && (
                      <div className="bg-green-50 p-3 rounded-lg">
                        <div className="text-xs font-medium text-green-800 mb-1">Conditions</div>
                        <div className="text-sm text-green-700">{step.conditions}</div>
                      </div>
                    )}
                    {step.time && (
                      <div className="bg-yellow-50 p-3 rounded-lg">
                        <div className="text-xs font-medium text-yellow-800 mb-1">Time</div>
                        <div className="text-sm text-yellow-700">{step.time}</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Chemical Explanation */}
      {protocol.explanation && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Chemical Explanation</h3>
          <div className="prose prose-sm max-w-none text-gray-700">
            {protocol.explanation.split('\n').map((line, index) => (
              <p key={index} className="mb-2">{line}</p>
            ))}
          </div>
        </div>
      )}

      {/* Automation Script */}
      {automationScript && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Automation Script</h3>
            <button
              onClick={handleDownload}
              className="btn-primary flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-sm text-green-400 font-mono">
              <code>{automationScript}</code>
            </pre>
          </div>
          
          <div className="mt-4 text-sm text-gray-600">
            <p><strong>Usage:</strong> Save as .py file and upload to your Opentrons robot</p>
            <p><strong>Equipment:</strong> Opentrons OT-2/OT-3, 300μL tips, 96-well plate</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProtocolTab;
