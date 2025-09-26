import React from 'react';
import { User, BookOpen, LogOut } from 'lucide-react';
import { useApp } from '../contexts/AppContext';

const Header: React.FC = () => {
  const { teacher, classSection } = useApp();

  return (
    <header className="bg-white shadow-lg border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <BookOpen className="h-8 w-8 text-indigo-600" />
            <h1 className="text-2xl font-bold text-gray-900">Exam Hub</h1>
          </div>

          {classSection && (
            <div className="flex items-center space-x-4">
              <div className="bg-indigo-50 px-4 py-2 rounded-lg">
                <span className="text-sm font-medium text-indigo-700">
                  Class {classSection.class} - Section {classSection.section}
                </span>
              </div>
            </div>
          )}

          {teacher && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-gray-50 px-4 py-2 rounded-lg">
                <User className="h-5 w-5 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">{teacher.name}</span>
              </div>
              <button className="text-gray-400 hover:text-gray-600 transition-colors">
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;