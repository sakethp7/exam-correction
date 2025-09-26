import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Teacher, ClassSection } from '../types';

interface AppContextType {
  teacher: Teacher | null;
  setTeacher: (teacher: Teacher) => void;
  classSection: ClassSection | null;
  setClassSection: (classSection: ClassSection) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [classSection, setClassSection] = useState<ClassSection | null>(null);
  const [activeTab, setActiveTab] = useState('home');

  return (
    <AppContext.Provider
      value={{
        teacher,
        setTeacher,
        classSection,
        setClassSection,
        activeTab,
        setActiveTab,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};