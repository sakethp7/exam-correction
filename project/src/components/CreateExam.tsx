import React, { useState } from 'react';
import { Upload, FileText, Play, CheckCircle, AlertCircle, Loader } from 'lucide-react';

const CreateExam: React.FC = () => {
  const [examName, setExamName] = useState('');
  const [examType, setExamType] = useState('');
  const [questionFile, setQuestionFile] = useState<File | null>(null);
  const [answerFile, setAnswerFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [processingMessage, setProcessingMessage] = useState('');

  const examTypes = ['Midterm 1', 'Midterm 2', 'Midterm 3', 'Midterm 4', 'Final Exam', 'Quiz', 'Assignment'];

  const handleFileUpload = (file: File, type: 'question' | 'answer') => {
    if (type === 'question') {
      setQuestionFile(file);
    } else {
      setAnswerFile(file);
    }
  };

  const handleStartCorrection = async () => {
    if (!examName || !examType || !questionFile || !answerFile) {
      alert('Please fill all fields and upload both files');
      return;
    }

    setIsProcessing(true);
    setProcessingStatus('processing');
    setProcessingMessage('Initializing correction process...');

    try {
      // Create FormData for the API call
      const formData = new FormData();
      formData.append('exam_name', examName);
      formData.append('exam_type', examType);
      formData.append('teacher_name', 'John Doe'); // This should come from context
      formData.append('teacher_email', 'john.doe@school.edu'); // This should come from context
      formData.append('class_name', '10'); // This should come from context
      formData.append('section', 'A'); // This should come from context
      formData.append('question_paper', questionFile);
      formData.append('answer_sheets', answerFile);

      setProcessingMessage('Analyzing question paper and answer sheets...');

      // Call the FastAPI endpoint
      const response = await fetch('http://localhost:8000/evaluate/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      setProcessingMessage('Processing evaluations...');
      
      const result = await response.json();
      
      setProcessingMessage('Correction completed successfully!');
      setProcessingStatus('success');

      // Store the results (in a real app, you'd save to a database)
      localStorage.setItem(`exam_${Date.now()}`, JSON.stringify({
        examName,
        examType,
        results: result,
        timestamp: new Date().toISOString(),
      }));

      // Reset form after success
      setTimeout(() => {
        setExamName('');
        setExamType('');
        setQuestionFile(null);
        setAnswerFile(null);
        setProcessingStatus('idle');
        setProcessingMessage('');
      }, 3000);

    } catch (error) {
      console.error('Error processing exam:', error);
      setProcessingStatus('error');
      setProcessingMessage('Error occurred during processing. Please check your files and try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const FileUploadArea: React.FC<{
    title: string;
    file: File | null;
    onFileSelect: (file: File) => void;
    acceptedTypes: string;
  }> = ({ title, file, onFileSelect, acceptedTypes }) => (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-400 transition-colors">
      <div className="space-y-4">
        <div className="mx-auto h-12 w-12 bg-gray-100 rounded-full flex items-center justify-center">
          <FileText className="h-6 w-6 text-gray-600" />
        </div>
        <div>
          <h4 className="text-lg font-medium text-gray-900">{title}</h4>
          {file ? (
            <div className="mt-2 flex items-center justify-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm text-green-600 font-medium">{file.name}</span>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Upload PDF file</p>
          )}
        </div>
        <input
          type="file"
          accept={acceptedTypes}
          onChange={(e) => {
            const selectedFile = e.target.files?.[0];
            if (selectedFile) onFileSelect(selectedFile);
          }}
          className="hidden"
          id={title.toLowerCase().replace(' ', '-')}
        />
        <label
          htmlFor={title.toLowerCase().replace(' ', '-')}
          className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 cursor-pointer transition-colors"
        >
          <Upload className="h-4 w-4 mr-2" />
          Choose File
        </label>
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-900">Create New Exam Correction</h2>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Exam Details */}
          <div className="space-y-6">
            <div>
              <label htmlFor="examName" className="block text-sm font-medium text-gray-700 mb-2">
                Exam Name
              </label>
              <input
                id="examName"
                type="text"
                value={examName}
                onChange={(e) => setExamName(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                placeholder="e.g., Mathematics Midterm Exam"
              />
            </div>

            <div>
              <label htmlFor="examType" className="block text-sm font-medium text-gray-700 mb-2">
                Exam Type
              </label>
              <select
                id="examType"
                value={examType}
                onChange={(e) => setExamType(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              >
                <option value="">Select exam type</option>
                {examTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Status Panel */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Processing Status</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                {processingStatus === 'processing' ? (
                  <Loader className="h-5 w-5 text-blue-500 animate-spin" />
                ) : processingStatus === 'success' ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : processingStatus === 'error' ? (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                ) : (
                  <div className="h-5 w-5 bg-gray-300 rounded-full"></div>
                )}
                <span className="text-sm text-gray-600">
                  {processingMessage || 'Ready to process'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* File Upload Areas */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <FileUploadArea
            title="Question Paper"
            file={questionFile}
            onFileSelect={(file) => handleFileUpload(file, 'question')}
            acceptedTypes=".pdf"
          />
          <FileUploadArea
            title="Answer Sheets"
            file={answerFile}
            onFileSelect={(file) => handleFileUpload(file, 'answer')}
            acceptedTypes=".pdf"
          />
        </div>

        {/* Action Button */}
        <div className="flex justify-center">
          <button
            onClick={handleStartCorrection}
            disabled={!examName || !examType || !questionFile || !answerFile || isProcessing}
            className="flex items-center space-x-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-3 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing ? (
              <Loader className="h-5 w-5 animate-spin" />
            ) : (
              <Play className="h-5 w-5" />
            )}
            <span>
              {isProcessing ? 'Processing...' : 'Start Correction'}
            </span>
          </button>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Instructions</h3>
        <ul className="text-blue-800 space-y-2 text-sm">
          <li>• Upload the question paper as a PDF file</li>
          <li>• Upload the answer sheets as a single PDF with multiple pages</li>
          <li>• Ensure roll numbers are clearly visible on each answer sheet</li>
          <li>• The AI will analyze and provide detailed evaluation for each student</li>
          <li>• Processing time may vary depending on the number of students</li>
        </ul>
      </div>
    </div>
  );
};

export default CreateExam;