import React from 'react';
import { Beaker, Thermometer, Weight, Hash } from 'lucide-react';

const ChemicalsTab = ({ results }) => {
  const chemicalData = results?.chemical_data || {};

  if (Object.keys(chemicalData).length === 0) {
    return (
      <div className="p-6 text-center">
        <Beaker className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500">No chemical data found for this query.</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Chemical Information</h2>
      
      {Object.entries(chemicalData).map(([chemical, data]) => (
        <div key={chemical} className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{chemical}</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Physical Properties */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                <Weight className="w-4 h-4 mr-2" />
                Physical Properties
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Molecular Weight:</span>
                  <span className="scientific-notation">
                    {data.molecular_weight || 'N/A'} g/mol
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Formula:</span>
                  <span className="chemical-formula">
                    {data.formula || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Density:</span>
                  <span className="scientific-notation">
                    {data.density || 'N/A'} g/mL
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Melting Point:</span>
                  <span className="scientific-notation">
                    {data.melting_point || 'N/A'} °C
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Boiling Point:</span>
                  <span className="scientific-notation">
                    {data.boiling_point || 'N/A'} °C
                  </span>
                </div>
              </div>
            </div>

            {/* Identifiers */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                <Hash className="w-4 h-4 mr-2" />
                Identifiers
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">PubChem CID:</span>
                  <span className="scientific-notation">
                    {data.cid || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">CAS Number:</span>
                  <span className="scientific-notation">
                    {data.cas_number || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">SMILES:</span>
                  <span className="scientific-notation text-xs">
                    {data.smiles || 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Hazards */}
          {data.hazards && data.hazards.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                <Thermometer className="w-4 h-4 mr-2" />
                Safety Hazards
              </h4>
              <div className="flex flex-wrap gap-2">
                {data.hazards.map((hazard, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-red-100 text-red-800 text-sm rounded-full border border-red-200"
                  >
                    {hazard}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ChemicalsTab;
