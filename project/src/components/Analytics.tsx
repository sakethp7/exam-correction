import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { TrendingUp, TrendingDown, Users, Target, BookOpen, Award } from 'lucide-react';

const Analytics: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState({
    progressData: [
    { midterm: 'Midterm 1', averageScore: 72, mathScore: 68, scienceScore: 76, englishScore: 74 },
    { midterm: 'Midterm 2', averageScore: 75, mathScore: 71, scienceScore: 78, englishScore: 76 },
    { midterm: 'Midterm 3', averageScore: 78, mathScore: 75, scienceScore: 80, englishScore: 79 },
    { midterm: 'Midterm 4', averageScore: 82, mathScore: 79, scienceScore: 84, englishScore: 83 },
    ],
    subjectProblems: [
    { subject: 'Mathematics', studentsWithIssues: 12, totalStudents: 35, percentage: 34 },
    { subject: 'Science', studentsWithIssues: 8, totalStudents: 35, percentage: 23 },
    { subject: 'English', studentsWithIssues: 6, totalStudents: 35, percentage: 17 },
    { subject: 'Social Studies', studentsWithIssues: 10, totalStudents: 35, percentage: 29 },
    ],
    performanceDistribution: [
    { grade: 'A+', count: 8, color: '#10B981' },
    { grade: 'A', count: 12, color: '#34D399' },
    { grade: 'B+', count: 10, color: '#FBBF24' },
    { grade: 'B', count: 5, color: '#F59E0B' },
    { grade: 'C', count: 3, color: '#F97316' },
    { grade: 'F', count: 2, color: '#EF4444' },
    ]
  });

  useEffect(() => {
    // Load analytics from API
    const loadAnalytics = async () => {
      try {
        const params = new URLSearchParams({
          teacher_name: 'John Doe', // This should come from context
          teacher_email: 'john.doe@school.edu', // This should come from context
          class_name: '10', // This should come from context
          section: 'A' // This should come from context
        });
        
        const response = await fetch(`http://localhost:8000/analytics/?${params}`);
        const data = await response.json();
        
        if (data.progressData) {
          setAnalyticsData(data);
        }
      } catch (error) {
        console.error('Error loading analytics:', error);
      }
    };

    loadAnalytics();
  }, []);

  const attendanceData = [
    { month: 'Jan', attendance: 92 },
    { month: 'Feb', attendance: 88 },
    { month: 'Mar', attendance: 94 },
    { month: 'Apr', attendance: 87 },
    { month: 'May', attendance: 91 },
  ];

  const StatCard: React.FC<{
    title: string;
    value: string;
    change: string;
    trend: 'up' | 'down';
    icon: React.ElementType;
    color: string;
  }> = ({ title, value, change, trend, icon: Icon, color }) => (
    <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          <div className="flex items-center mt-2">
            {trend === 'up' ? (
              <TrendingUp className="h-4 w-4 text-green-500" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500" />
            )}
            <span className={`text-sm font-medium ml-1 ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
              {change}
            </span>
          </div>
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h2>
        <div className="bg-indigo-50 px-4 py-2 rounded-lg">
          <span className="text-indigo-700 text-sm font-medium">Class 10-A • 35 Students</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Class Average"
          value="78.5%"
          change="+5.2%"
          trend="up"
          icon={Target}
          color="bg-indigo-500"
        />
        <StatCard
          title="Total Students"
          value="35"
          change="+2"
          trend="up"
          icon={Users}
          color="bg-green-500"
        />
        <StatCard
          title="Exams Completed"
          value="24"
          change="+4"
          trend="up"
          icon={BookOpen}
          color="bg-blue-500"
        />
        <StatCard
          title="Top Performers"
          value="12"
          change="+3"
          trend="up"
          icon={Award}
          color="bg-yellow-500"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Progress Over Time */}
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Student Progress Over Midterms</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analyticsData.progressData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="midterm" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#F9FAFB', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Line type="monotone" dataKey="averageScore" stroke="#6366F1" strokeWidth={3} name="Average" />
              <Line type="monotone" dataKey="mathScore" stroke="#EF4444" strokeWidth={2} name="Math" />
              <Line type="monotone" dataKey="scienceScore" stroke="#10B981" strokeWidth={2} name="Science" />
              <Line type="monotone" dataKey="englishScore" stroke="#F59E0B" strokeWidth={2} name="English" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Subject-wise Problems */}
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Students with Subject Difficulties</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.subjectProblems} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis type="number" stroke="#6B7280" />
              <YAxis type="category" dataKey="subject" stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#F9FAFB', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                formatter={(value) => [`${value} students`, 'Students with Issues']}
              />
              <Bar dataKey="studentsWithIssues" fill="#EF4444" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Performance Distribution */}
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Grade Distribution</h3>
          <div className="flex justify-center">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData.performanceDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ grade, count }) => `${grade}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {analyticsData.performanceDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Attendance Trend */}
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Monthly Attendance Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={attendanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="month" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#F9FAFB', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                formatter={(value) => [`${value}%`, 'Attendance']}
              />
              <Area 
                type="monotone" 
                dataKey="attendance" 
                stroke="#10B981" 
                fill="#10B981" 
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Additional Insights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl p-6 border border-blue-200">
          <h4 className="text-lg font-semibold text-blue-900 mb-2">Top Performance</h4>
          <p className="text-blue-700">Mathematics scores improved by 11 points from Midterm 1 to 4</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-emerald-100 rounded-xl p-6 border border-green-200">
          <h4 className="text-lg font-semibold text-green-900 mb-2">Class Strength</h4>
          <p className="text-green-700">83% of students show consistent improvement across subjects</p>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-orange-100 rounded-xl p-6 border border-yellow-200">
          <h4 className="text-lg font-semibold text-orange-900 mb-2">Focus Area</h4>
          <p className="text-orange-700">12 students need additional support in Mathematics</p>
        </div>
      </div>
    </div>
  );
};

export default Analytics;