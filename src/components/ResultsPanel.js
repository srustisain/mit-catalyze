import React from 'react';
import { FileText, Beaker, Shield, BarChart3, Download } from 'lucide-react';
import ProtocolTab from './tabs/ProtocolTab';
import ChemicalsTab from './tabs/ChemicalsTab';
import SafetyTab from './tabs/SafetyTab';
import AnalysisTab from './tabs/AnalysisTab';

const ResultsPanel = ({ results, activeTab, onTabChange, onDownloadScript }) => {
  const tabs = [
    { id: 'protocol', label: 'Protocol', icon: FileText },
    { id: 'chemicals', label: 'Chemicals', icon: Beaker },
    { id: 'safety', label: 'Safety', icon: Shield },
    { id: 'analysis', label: 'Analysis', icon: BarChart3 },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'protocol':
        return <ProtocolTab results={results} onDownloadScript={onDownloadScript} />;
      case 'chemicals':
        return <ChemicalsTab results={results} />;
      case 'safety':
        return <SafetyTab results={results} />;
      case 'analysis':
        return <AnalysisTab results={results} />;
      default:
        return <ProtocolTab results={results} onDownloadScript={onDownloadScript} />;
    }
  };

  return (
    <div className="h-96 flex flex-col">
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors duration-200 ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600 bg-white'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default ResultsPanel;
