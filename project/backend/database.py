from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./exam_hub.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    exams = relationship("Exam", back_populates="teacher")

class ClassSection(Base):
    __tablename__ = "class_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, nullable=False)
    section = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    exams = relationship("Exam", back_populates="class_section")

class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    exam_type = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id"))
    total_students = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Store class analytics as JSON
    class_analytics = Column(JSON)
    processing_summary = Column(JSON)
    
    # Relationships
    teacher = relationship("Teacher", back_populates="exams")
    class_section = relationship("ClassSection", back_populates="exams")
    student_results = relationship("StudentResult", back_populates="exam")

class StudentResult(Base):
    __tablename__ = "student_results"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    roll_number = Column(String, nullable=False)
    total_marks_obtained = Column(Float, default=0.0)
    total_max_marks = Column(Float, default=0.0)
    overall_percentage = Column(Float, default=0.0)
    grade = Column(String, default="F")
    
    # Store detailed results as JSON
    questions_evaluation = Column(JSON)  # List of question evaluations
    strengths = Column(JSON)  # List of strengths
    areas_for_improvement = Column(JSON)  # List of improvement areas
    detailed_analysis = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    exam = relationship("Exam", back_populates="student_results")

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database operations
class DatabaseOperations:
    
    @staticmethod
    def get_or_create_teacher(db: Session, name: str, email: str) -> Teacher:
        """Get existing teacher or create new one"""
        teacher = db.query(Teacher).filter(Teacher.email == email).first()
        if not teacher:
            teacher = Teacher(name=name, email=email)
            db.add(teacher)
            db.commit()
            db.refresh(teacher)
        return teacher
    
    @staticmethod
    def get_or_create_class_section(db: Session, class_name: str, section: str) -> ClassSection:
        """Get existing class section or create new one"""
        class_section = db.query(ClassSection).filter(
            ClassSection.class_name == class_name,
            ClassSection.section == section
        ).first()
        if not class_section:
            class_section = ClassSection(class_name=class_name, section=section)
            db.add(class_section)
            db.commit()
            db.refresh(class_section)
        return class_section
    
    @staticmethod
    def save_exam_results(
        db: Session,
        exam_name: str,
        exam_type: str,
        teacher_id: int,
        class_section_id: int,
        evaluation_results: Dict[str, Any],
        class_analytics: Dict[str, Any]
    ) -> Exam:
        """Save complete exam results to database"""
        
        # Create exam record
        exam = Exam(
            name=exam_name,
            exam_type=exam_type,
            teacher_id=teacher_id,
            class_section_id=class_section_id,
            total_students=len(evaluation_results),
            average_score=class_analytics.get("class_average_percentage", 0.0),
            class_analytics=class_analytics,
            processing_summary=class_analytics.get("processing_summary", {}),
            processed_at=datetime.utcnow()
        )
        
        db.add(exam)
        db.commit()
        db.refresh(exam)
        
        # Save individual student results
        for roll_number, result in evaluation_results.items():
            student_result = StudentResult(
                exam_id=exam.id,
                roll_number=roll_number,
                total_marks_obtained=result.get("total_marks_obtained", 0.0),
                total_max_marks=result.get("total_max_marks", 0.0),
                overall_percentage=result.get("overall_percentage", 0.0),
                grade=result.get("grade", "F"),
                questions_evaluation=result.get("questions", []),
                strengths=result.get("strengths", []),
                areas_for_improvement=result.get("areas_for_improvement", []),
                detailed_analysis=result.get("detailed_analysis", "")
            )
            db.add(student_result)
        
        db.commit()
        return exam
    
    @staticmethod
    def get_exams_by_teacher_and_class(
        db: Session,
        teacher_id: int,
        class_section_id: int,
        exam_type: Optional[str] = None
    ) -> List[Exam]:
        """Get all exams for a teacher and class"""
        query = db.query(Exam).filter(
            Exam.teacher_id == teacher_id,
            Exam.class_section_id == class_section_id
        )
        
        if exam_type:
            query = query.filter(Exam.exam_type == exam_type)
        
        return query.order_by(Exam.created_at.desc()).all()
    
    @staticmethod
    def get_exam_with_results(db: Session, exam_id: int) -> Optional[Exam]:
        """Get exam with all student results"""
        return db.query(Exam).filter(Exam.id == exam_id).first()
    
    @staticmethod
    def get_student_results_by_exam(db: Session, exam_id: int) -> List[StudentResult]:
        """Get all student results for an exam"""
        return db.query(StudentResult).filter(StudentResult.exam_id == exam_id).all()
    
    @staticmethod
    def get_analytics_data(db: Session, teacher_id: int, class_section_id: int) -> Dict[str, Any]:
        """Generate analytics data for dashboard"""
        exams = db.query(Exam).filter(
            Exam.teacher_id == teacher_id,
            Exam.class_section_id == class_section_id
        ).order_by(Exam.created_at.asc()).all()
        
        if not exams:
            return {
                "progressData": [],
                "subjectProblems": [],
                "performanceDistribution": []
            }
        
        # Generate progress data from midterms
        progress_data = []
        midterm_exams = [exam for exam in exams if "midterm" in exam.exam_type.lower()]
        
        for i, exam in enumerate(midterm_exams[:4], 1):
            # Get subject-wise scores from class analytics
            analytics = exam.class_analytics or {}
            question_analytics = analytics.get("class_analytics", {}).get("question_analytics", {})
            
            # Calculate subject averages (simplified)
            math_score = 75 + (exam.average_score - 75) * 0.8  # Simulate math scores
            science_score = 78 + (exam.average_score - 75) * 1.1  # Simulate science scores
            english_score = 76 + (exam.average_score - 75) * 0.9  # Simulate english scores
            
            progress_data.append({
                "midterm": f"Midterm {i}",
                "averageScore": round(exam.average_score, 1),
                "mathScore": round(max(0, min(100, math_score)), 1),
                "scienceScore": round(max(0, min(100, science_score)), 1),
                "englishScore": round(max(0, min(100, english_score)), 1)
            })
        
        # Generate subject problems data
        latest_exam = exams[-1] if exams else None
        subject_problems = []
        
        if latest_exam and latest_exam.total_students > 0:
            # Simulate subject-wise problems based on performance
            avg_score = latest_exam.average_score
            total_students = latest_exam.total_students
            
            subjects = [
                {"subject": "Mathematics", "difficulty_factor": 1.2},
                {"subject": "Science", "difficulty_factor": 0.9},
                {"subject": "English", "difficulty_factor": 0.8},
                {"subject": "Social Studies", "difficulty_factor": 1.1}
            ]
            
            for subject_info in subjects:
                # Calculate students with issues based on average performance
                base_issues = max(1, int(total_students * (100 - avg_score) / 100))
                issues = int(base_issues * subject_info["difficulty_factor"])
                issues = min(issues, total_students)
                
                subject_problems.append({
                    "subject": subject_info["subject"],
                    "studentsWithIssues": issues,
                    "totalStudents": total_students,
                    "percentage": round((issues / total_students) * 100, 1)
                })
        
        # Generate performance distribution from latest exam
        performance_distribution = []
        if latest_exam and latest_exam.class_analytics:
            grade_dist = latest_exam.class_analytics.get("class_analytics", {}).get("grade_distribution", {})
            
            grade_mapping = [
                {"grade": "A+", "count": grade_dist.get("A", 0) // 2},
                {"grade": "A", "count": grade_dist.get("A", 0) - (grade_dist.get("A", 0) // 2)},
                {"grade": "B+", "count": grade_dist.get("B", 0) // 2},
                {"grade": "B", "count": grade_dist.get("B", 0) - (grade_dist.get("B", 0) // 2)},
                {"grade": "C", "count": grade_dist.get("C", 0)},
                {"grade": "F", "count": grade_dist.get("F", 0)}
            ]
            
            performance_distribution = [item for item in grade_mapping if item["count"] > 0]
        
        return {
            "progressData": progress_data,
            "subjectProblems": subject_problems,
            "performanceDistribution": performance_distribution
        }