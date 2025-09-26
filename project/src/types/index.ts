export interface Teacher {
  id: string;
  name: string;
  email: string;
}

export interface ClassSection {
  class: string;
  section: string;
}

export interface Student {
  rollNumber: string;
  name: string;
  score: number;
  totalMarks: number;
  percentage: number;
  grade: string;
}

export interface Exam {
  id: string;
  name: string;
  type: string;
  date: string;
  totalMarks: number;
  studentsCount: number;
  averageScore: number;
}

export interface ExamResult {
  examId: string;
  examName: string;
  students: Student[];
}

export interface QuestionEvaluation {
  question_number: string;
  max_marks: number;
  total_score: number;
  error_type: string;
  mistakes_made: string;
  mistake_section: string;
  concepts_required: string[];
  gap_analysis: string;
  percentage: number;
}

export interface StudentReport {
  roll_number: string;
  questions: QuestionEvaluation[];
  total_marks_obtained: number;
  total_max_marks: number;
  overall_percentage: number;
  strengths: string[];
  areas_for_improvement: string[];
  grade: string;
  detailed_analysis: string;
}

export interface AnalyticsData {
  progressData: {
    midterm: string;
    averageScore: number;
    mathScore: number;
    scienceScore: number;
    englishScore: number;
  }[];
  subjectProblems: {
    subject: string;
    studentsWithIssues: number;
    totalStudents: number;
    percentage: number;
  }[];
  performanceDistribution: {
    grade: string;
    count: number;
  }[];
}