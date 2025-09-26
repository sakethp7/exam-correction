import React from 'react';
import { Home, PlusCircle, FileText, BarChart3 } from 'lucide-react';
import { useApp } from '../contexts/AppContext';

const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab } = useApp();

  const tabs = [
    { id: 'home', name: 'Analytics', icon: BarChart3 },
    { id: 'create', name: 'Create Exam', icon: PlusCircle },
    { id: 'results', name: 'Results', icon: FileText },
  ];

  return (
    <div className="w-64 bg-white shadow-lg min-h-screen border-r border-gray-200">
      <nav className="mt-8 px-4">
        <ul className="space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <li key={tab.id}>
                <button
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-indigo-50 text-indigo-700 border-r-4 border-indigo-500'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className={`h-5 w-5 mr-3 ${activeTab === tab.id ? 'text-indigo-500' : 'text-gray-400'}`} />
                  <span className="font-medium">{tab.name}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;