import React from 'react';
import { AppProvider, useApp } from './contexts/AppContext';
import TeacherLogin from './components/TeacherLogin';
import ClassSelector from './components/ClassSelector';
import MainLayout from './components/MainLayout';

const AppContent: React.FC = () => {
  const { teacher, classSection } = useApp();

  if (!teacher) {
    return <TeacherLogin />;
  }

  if (!classSection) {
    return <ClassSelector />;
  }

  return <MainLayout />;
};

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;