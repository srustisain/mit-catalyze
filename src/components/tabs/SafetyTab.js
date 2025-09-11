import React from 'react';
import { Shield, AlertTriangle, CheckCircle, Info, Trash2 } from 'lucide-react';

const SafetyTab = ({ results }) => {
  const safetyInfo = results?.safety_info || {};

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Safety Information</h2>
      
      {/* Identified Hazards */}
      {safetyInfo.hazards && safetyInfo.hazards.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-red-500" />
            Identified Hazards
          </h3>
          <div className="space-y-3">
            {safetyInfo.hazards.map((hazard, index) => (
              <div key={index} className="safety-warning">
                <div className="flex items-center">
                  <AlertTriangle className="w-5 h-5 text-red-500 mr-3 flex-shrink-0" />
                  <span className="font-medium text-red-800">{hazard}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Safety Precautions */}
      {safetyInfo.precautions && safetyInfo.precautions.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
            Safety Precautions
          </h3>
          <div className="space-y-3">
            {safetyInfo.precautions.map((precaution, index) => (
              <div key={index} className="safety-success">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                  <span className="text-green-800">{precaution}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Waste Management */}
      {safetyInfo.waste_info && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Trash2 className="w-5 h-5 mr-2 text-yellow-500" />
            Waste Management
          </h3>
          <div className="safety-info">
            <div className="flex items-start">
              <Info className="w-5 h-5 text-yellow-500 mr-3 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-yellow-800 mb-2">Waste Disposal Guidelines</h4>
                <p className="text-yellow-700">{safetyInfo.waste_info}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* General Safety Guidelines */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Shield className="w-5 h-5 mr-2 text-blue-500" />
          General Safety Guidelines
        </h3>
        <div className="space-y-3">
          {[
            'Always work in a well-ventilated area or fume hood',
            'Wear appropriate personal protective equipment (PPE)',
            'Keep emergency equipment (eyewash, safety shower) accessible',
            'Follow local regulations for chemical disposal',
            'Never work alone with hazardous chemicals',
            'Keep safety data sheets (SDS) readily available'
          ].map((guideline, index) => (
            <div key={index} className="flex items-start">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
              <span className="text-gray-700">{guideline}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Safety Assessment */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Safety Assessment</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {safetyInfo.hazards?.length || 0}
            </div>
            <div className="text-sm text-gray-600">Hazards Identified</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {safetyInfo.precautions?.length || 0}
            </div>
            <div className="text-sm text-gray-600">Precautions Recommended</div>
          </div>
        </div>
        
        <div className="mt-4 text-center">
          <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
            (safetyInfo.hazards?.length || 0) > 0 
              ? 'bg-red-100 text-red-800' 
              : 'bg-green-100 text-green-800'
          }`}>
            {safetyInfo.hazards?.length > 0 ? (
              <>
                <AlertTriangle className="w-4 h-4 mr-2" />
                High Risk Level
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                Low Risk Level
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SafetyTab;
