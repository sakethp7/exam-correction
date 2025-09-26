import React, { useState } from 'react';
import { Users, ArrowRight } from 'lucide-react';
import { useApp } from '../contexts/AppContext';

const ClassSelector: React.FC = () => {
  const { setClassSection } = useApp();
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedSection, setSelectedSection] = useState('');

  const classes = ['6', '7', '8', '9', '10', '11', '12'];
  const sections = ['A', 'B', 'C', 'D'];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedClass && selectedSection) {
      setClassSection({
        class: selectedClass,
        section: selectedSection,
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <Users className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Select Class & Section</h2>
          <p className="text-gray-600">Choose the class and section to manage</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Class</label>
            <div className="grid grid-cols-4 gap-2">
              {classes.map((cls) => (
                <button
                  key={cls}
                  type="button"
                  onClick={() => setSelectedClass(cls)}
                  className={`py-3 px-4 rounded-lg border-2 font-medium transition-all ${
                    selectedClass === cls
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}
                >
                  Class {cls}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Section</label>
            <div className="grid grid-cols-4 gap-2">
              {sections.map((section) => (
                <button
                  key={section}
                  type="button"
                  onClick={() => setSelectedSection(section)}
                  className={`py-3 px-4 rounded-lg border-2 font-medium transition-all ${
                    selectedSection === section
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}
                >
                  Section {section}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={!selectedClass || !selectedSection}
            className="w-full bg-gradient-to-r from-indigo-600 to-green-600 text-white py-3 px-4 rounded-lg font-medium hover:from-indigo-700 hover:to-green-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>Continue</span>
            <ArrowRight className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ClassSelector;