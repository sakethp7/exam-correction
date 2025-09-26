import React, { useState, useEffect } from 'react';
import { Filter, Search, Eye, FileText, Award, TrendingUp } from 'lucide-react';
import { StudentReport } from '../types';

interface ExamData {
  examName: string;
  examType: string;
  results: any;
  timestamp: string;
}

const Results: React.FC = () => {
  const [selectedExamType, setSelectedExamType] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [exams, setExams] = useState<ExamData[]>([]);
  const [selectedExam, setSelectedExam] = useState<ExamData | null>(null);
  const [selectedStudent, setSelectedStudent] = useState<StudentReport | null>(null);

  const examTypes = ['Midterm 1', 'Midterm 2', 'Midterm 3', 'Midterm 4', 'Final Exam', 'Quiz', 'Assignment'];

  useEffect(() => {
    // Load exams from database via API
    const loadExams = () => {
      // Fetch exams from API
      const fetchExams = async () => {
        try {
          const params = new URLSearchParams({
            teacher_name: 'John Doe', // This should come from context
            teacher_email: 'john.doe@school.edu', // This should come from context
            class_name: '10', // This should come from context
            section: 'A' // This should come from context
          });
          
          const response = await fetch(`http://localhost:8000/exams/?${params}`);
          const data = await response.json();
          
          if (data.exams) {
            const examData: ExamData[] = data.exams.map((exam: any) => ({
              examName: exam.name,
              examType: exam.exam_type,
              results: { exam_id: exam.id }, // Store exam ID for fetching detailed results
              timestamp: exam.created_at
            }));
            setExams(examData);
          }
        } catch (error) {
          console.error('Error fetching exams:', error);
        }
      };
      
      fetchExams();
    };

    loadExams();
  }, []);

  const filteredExams = exams.filter(exam => 
    (selectedExamType === '' || exam.examType === selectedExamType) &&
    (searchTerm === '' || exam.examName.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleViewReport = (student: StudentReport) => {
    setSelectedStudent(student);
  };

  const loadExamResults = async (exam: ExamData) => {
    try {
      const examId = exam.results.exam_id;
      const response = await fetch(`http://localhost:8000/exams/${examId}/results`);
      const data = await response.json();
      
      // Update the exam with detailed results
      const updatedExam = {
        ...exam,
        results: data
      };
      setSelectedExam(updatedExam);
    } catch (error) {
      console.error('Error loading exam results:', error);
    }
  };

  const StudentReportModal: React.FC<{ student: StudentReport; onClose: () => void }> = ({ student, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-2xl font-bold text-gray-900">Full Report - Roll {student.roll_number}</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Overall Performance */}
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-6 border border-indigo-200">
            <h4 className="text-lg font-semibold text-indigo-900 mb-4">Overall Performance</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-indigo-600">{student.total_marks_obtained}</div>
                <div className="text-sm text-indigo-800">Marks Obtained</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-indigo-600">{student.total_max_marks}</div>
                <div className="text-sm text-indigo-800">Total Marks</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-indigo-600">{student.overall_percentage.toFixed(1)}%</div>
                <div className="text-sm text-indigo-800">Percentage</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-indigo-600">{student.grade}</div>
                <div className="text-sm text-indigo-800">Grade</div>
              </div>
            </div>
          </div>

          {/* Question-wise Analysis */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Question-wise Analysis</h4>
            <div className="space-y-4">
              {student.questions.map((question, index) => (
                <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <h5 className="font-medium text-gray-900">Question {question.question_number}</h5>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-600">
                        {question.total_score}/{question.max_marks}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        question.percentage >= 80 ? 'bg-green-100 text-green-800' :
                        question.percentage >= 60 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {question.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Error Type:</span>
                      <span className={`ml-2 px-2 py-1 rounded text-xs ${
                        question.error_type === 'no_error' ? 'bg-green-100 text-green-800' :
                        question.error_type === 'unattempted' ? 'bg-gray-100 text-gray-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {question.error_type.replace('_', ' ')}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Mistakes:</span>
                      <span className="ml-2 text-gray-600">{question.mistakes_made}</span>
                    </div>
                  </div>
                  
                  {question.concepts_required.length > 0 && (
                    <div className="mt-3">
                      <span className="font-medium text-gray-700">Required Concepts:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {question.concepts_required.map((concept, i) => (
                          <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {concept}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {question.gap_analysis && (
                    <div className="mt-3">
                      <span className="font-medium text-gray-700">Gap Analysis:</span>
                      <p className="text-gray-600 text-sm mt-1">{question.gap_analysis}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Strengths and Improvements */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <h5 className="font-semibold text-green-900 mb-3 flex items-center">
                <Award className="h-4 w-4 mr-2" />
                Strengths
              </h5>
              <ul className="space-y-1 text-sm text-green-800">
                {student.strengths.map((strength, index) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-2">•</span>
                    {strength}
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
              <h5 className="font-semibold text-orange-900 mb-3 flex items-center">
                <TrendingUp className="h-4 w-4 mr-2" />
                Areas for Improvement
              </h5>
              <ul className="space-y-1 text-sm text-orange-800">
                {student.areas_for_improvement.map((area, index) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-2">•</span>
                    {area}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Detailed Analysis */}
          {student.detailed_analysis && (
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h5 className="font-semibold text-gray-900 mb-3">Detailed Analysis</h5>
              <p className="text-gray-700 text-sm leading-relaxed">{student.detailed_analysis}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-900">Exam Results</h2>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-5 w-5 text-gray-400" />
              <select
                value={selectedExamType}
                onChange={(e) => setSelectedExamType(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">All Exam Types</option>
                {examTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <Search className="h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search exams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>
          {selectedExamType && (
            <button
              onClick={() => setSelectedExamType('')}
              className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
            >
              Clear Filter
            </button>
          )}
        </div>
      </div>

      {/* Exam List */}
      {!selectedExam ? (
        <div className="bg-white rounded-xl shadow-md border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Available Exams</h3>
          </div>
          <div className="p-6">
            {filteredExams.length > 0 ? (
              <div className="space-y-4">
                {filteredExams.map((exam, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="font-medium text-gray-900">{exam.examName}</h4>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                          <span>{exam.examType}</span>
                          <span>•</span>
                          <span>{new Date(exam.timestamp).toLocaleDateString()}</span>
                          <span>•</span>
                          <span>{Object.keys(exam.results.evaluation_results || {}).length} Students</span>
                        </div>
                      </div>
                      <button
                        onClick={() => loadExamResults(exam)}
                        className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center space-x-2"
                      >
                        <Eye className="h-4 w-4" />
                        <span>View Results</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Exams Found</h3>
                <p className="text-gray-600">No exams match your current filters.</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Student Results */
        <div className="bg-white rounded-xl shadow-md border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{selectedExam.examName}</h3>
                <p className="text-sm text-gray-600">{selectedExam.examType} • {new Date(selectedExam.timestamp).toLocaleDateString()}</p>
              </div>
              <button
                onClick={() => setSelectedExam(null)}
                className="text-gray-600 hover:text-gray-800 px-4 py-2 border border-gray-300 rounded-lg transition-colors"
              >
                Back to Exams
              </button>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.values(selectedExam.results.evaluation_results || {}).map((student: any, index) => (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-4 flex items-center justify-between"
                >
                  <div className="flex items-center space-x-4">
                    <div className="bg-indigo-100 rounded-full h-10 w-10 flex items-center justify-center">
                      <span className="text-indigo-600 font-medium">{student.roll_number}</span>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">Roll No. {student.roll_number}</h4>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span>{student.total_marks_obtained}/{student.total_max_marks}</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          student.overall_percentage >= 80 ? 'bg-green-100 text-green-800' :
                          student.overall_percentage >= 60 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {student.overall_percentage.toFixed(1)}% ({student.grade})
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleViewReport(student)}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center space-x-2"
                  >
                    <FileText className="h-4 w-4" />
                    <span>See Full Report</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Student Report Modal */}
      {selectedStudent && (
        <StudentReportModal
          student={selectedStudent}
          onClose={() => setSelectedStudent(null)}
        />
      )}
    </div>
  );
};

export default Results;