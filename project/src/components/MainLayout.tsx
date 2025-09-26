import React from 'react';
import { useApp } from '../contexts/AppContext';
import Header from './Header';
import Sidebar from './Sidebar';
import Analytics from './Analytics';
import CreateExam from './CreateExam';
import Results from './Results';

const MainLayout: React.FC = () => {
  const { activeTab } = useApp();

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return <Analytics />;
      case 'create':
        return <CreateExam />;
      case 'results':
        return <Results />;
      default:
        return <Analytics />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default MainLayout;