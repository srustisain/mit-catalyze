import React from 'react';
import { BarChart3, Beaker, FileText, Shield, Zap } from 'lucide-react';

const AnalysisTab = ({ results }) => {
  const analysis = results?.analysis || {};
  const protocol = results?.protocol || {};
  const safetyInfo = results?.safety_info || {};

  const getComplexityLevel = (steps) => {
    if (steps <= 3) return { level: 'Simple', color: 'green' };
    if (steps <= 6) return { level: 'Moderate', color: 'yellow' };
    return { level: 'Complex', color: 'red' };
  };

  const complexity = getComplexityLevel(protocol.steps?.length || 0);

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Query Analysis</h2>
      
      {/* Statistics Overview */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Statistics Overview</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <Beaker className="w-6 h-6 text-blue-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-blue-900">
              {analysis.chemicals_found || 0}
            </div>
            <div className="text-sm text-blue-700">Chemicals Found</div>
          </div>
          
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <FileText className="w-6 h-6 text-purple-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-purple-900">
              {analysis.protocol_steps || 0}
            </div>
            <div className="text-sm text-purple-700">Protocol Steps</div>
          </div>
          
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <Shield className="w-6 h-6 text-red-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-red-900">
              {analysis.safety_hazards || 0}
            </div>
            <div className="text-sm text-red-700">Safety Hazards</div>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <Zap className="w-6 h-6 text-green-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-green-900">
              {analysis.automation_operations || 0}
            </div>
            <div className="text-sm text-green-700">Automation Ops</div>
          </div>
        </div>
      </div>

      {/* Protocol Analysis */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Protocol Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Protocol Details</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Title:</span>
                <span className="text-sm font-medium text-gray-900">
                  {protocol.title || 'Generated Protocol'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Steps:</span>
                <span className="text-sm font-medium text-gray-900">
                  {protocol.steps?.length || 0} procedure steps
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Expected Yield:</span>
                <span className="text-sm font-medium text-gray-900">
                  {protocol.expected_yield || 'Not specified'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Reaction Type:</span>
                <span className="text-sm font-medium text-gray-900">
                  {results?.query?.toLowerCase().includes('benzyl') ? 'SN2 Substitution' : 'General'}
                </span>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Complexity Assessment</h4>
            <div className="text-center">
              <div className={`text-3xl font-bold mb-2 ${
                complexity.color === 'green' ? 'text-green-600' :
                complexity.color === 'yellow' ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {complexity.level}
              </div>
              <div className="text-sm text-gray-600">
                Based on {protocol.steps?.length || 0} protocol steps
              </div>
              <div className="mt-3">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      complexity.color === 'green' ? 'bg-green-500' :
                      complexity.color === 'yellow' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ 
                      width: `${Math.min((protocol.steps?.length || 0) * 10, 100)}%` 
                    }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Safety Assessment */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Safety Assessment</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Risk Level</h4>
            <div className={`p-4 rounded-lg ${
              (safetyInfo.hazards?.length || 0) > 0 
                ? 'bg-red-50 border border-red-200' 
                : 'bg-green-50 border border-green-200'
            }`}>
              <div className={`text-center ${
                (safetyInfo.hazards?.length || 0) > 0 ? 'text-red-800' : 'text-green-800'
              }`}>
                <div className="text-2xl font-bold mb-1">
                  {(safetyInfo.hazards?.length || 0) > 0 ? 'High' : 'Low'}
                </div>
                <div className="text-sm">
                  {(safetyInfo.hazards?.length || 0) > 0 
                    ? `${safetyInfo.hazards?.length || 0} hazards identified`
                    : 'No major hazards identified'
                  }
                </div>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Safety Measures</h4>
            <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
              <div className="text-center text-blue-800">
                <div className="text-2xl font-bold mb-1">
                  {safetyInfo.precautions?.length || 0}
                </div>
                <div className="text-sm">
                  safety precautions recommended
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chemical Properties Summary */}
      {results?.chemical_data && Object.keys(results.chemical_data).length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Chemical Properties Summary</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Chemical
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Molecular Weight
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Formula
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Density
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(results.chemical_data).map(([chemical, data]) => (
                  <tr key={chemical}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {chemical}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {data.molecular_weight || 'N/A'} g/mol
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      <span className="chemical-formula">
                        {data.formula || 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {data.density || 'N/A'} g/mL
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisTab;
