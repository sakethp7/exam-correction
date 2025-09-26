# from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy.orm import Session
# import base64
# import os
# import json
# import re
# import time
# import threading
# from threading import Semaphore
# import concurrent.futures
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from typing import List, Dict, Any, Optional, Tuple, Union
# from pydantic import BaseModel, Field
# import PyPDF2
# from io import BytesIO
# import traceback
# import io
# from PIL import Image
# import os
# from dotenv import load_dotenv
# from datetime import datetime

# # LangChain imports
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import HumanMessage
# from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI
# # Import PyMuPDF
# import fitz

# # Import database components
# from database import (
#     create_tables, get_db, DatabaseOperations,
#     Teacher, ClassSection, Exam, StudentResult
# )

# load_dotenv()

# # Initialize FastAPI app
# app = FastAPI(
#     title="Exam Hub API",
#     description="Complete exam management system with AI-powered evaluation",
#     version="2.0.0"
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Create database tables on startup
# create_tables()

# # Initialize LangChain model
# llm = None
# # Semaphore for rate limiting
# api_semaphore = Semaphore(5)  # Allow max 5 concurrent API calls

# # ============= Pydantic Models =============

# class TeacherCreate(BaseModel):
#     name: str
#     email: str

# class ClassSectionCreate(BaseModel):
#     class_name: str
#     section: str

# class ExamCreate(BaseModel):
#     name: str
#     exam_type: str
#     teacher_name: str
#     teacher_email: str
#     class_name: str
#     section: str

# class ExtractedContent(BaseModel):
#     """Extracted content from student answer sheet"""
#     roll_number: str = Field(description="Student's roll number")
#     page_number: int = Field(description="Page number of the answer sheet")
#     content: str = Field(description="Full content in LaTeX format")
#     questions_found: List[str] = Field(description="List of question numbers found on this page")

# class QuestionEvaluation(BaseModel):
#     """Evaluation result for a single question"""
#     question_number: str = Field(description="Question number (e.g., '1', '2a', '3(i)')")
#     max_marks: float = Field(description="Maximum marks for this question")
#     total_score: float = Field(description="Total score obtained for this question")
#     error_type: str = Field(description="Type of error: conceptual_error, calculation_error, logical_error, no_error or unattempted")
#     mistakes_made: str = Field(description="Specific mistakes made in the question or 'None' if no errors or unattempted")
#     mistake_section: str = Field(description="Content of specific line of mistake made by student")
#     concepts_required: List[str] = Field(description="List of correct concepts required to solve this question")
#     gap_analysis: str = Field(description="Specific learning gaps")
#     percentage: float = Field(description="Percentage score for this question")

# class EvaluationResult(BaseModel):
#     """Complete evaluation result for a student"""
#     roll_number: str = Field(description="Student's roll number")
#     questions: List[QuestionEvaluation] = Field(description="Evaluation for each question")
#     total_marks_obtained: float = Field(description="Total marks obtained")
#     total_max_marks: float = Field(description="Total maximum marks")
#     overall_percentage: float = Field(description="Overall percentage score")
#     strengths: List[str] = Field(description="Student's key strengths identified")
#     areas_for_improvement: List[str] = Field(description="Specific areas needing improvement")
#     grade: str = Field(description="Letter grade (A+, A, B+, B, C+, C, D, F)")
#     detailed_analysis: str = Field(description="Detailed analysis of student performance")

# # ============= Helper Functions =============

# def initialize_llm(api_key: str):
#     """Initialize LangChain Google GenAI model"""
#     global llm
#     try:
#         llm = ChatGoogleGenerativeAI(
#             model="gemini-2.5-flash",
#             temperature=0.1,
#             max_tokens=None,
#             timeout=None,
#             max_retries=2,
#             api_key=api_key
#         )
#         return True, "Successfully initialized"
#     except Exception as e:
#         return False, str(e)

# def get_extraction_prompt() -> str:
#     return """
# Extract ALL text from this student answer sheet image with extreme precision.

# **CRITICAL: FIRST IDENTIFY THE ROLL NUMBER**
# - Look for roll number, registration number, student ID anywhere on the page
# - format: ID: 10HPS24,9PAG35 it is the combination of numeric and alphabets 
# - Output format: "ROLL_NUMBER: [exact number found]"

# **EXTRACTION RULES:**
# 1. **ROLL NUMBER & PAGE:**
#    - MUST extract roll number from top right inside boxes on every page
#    - Roll Number will be in format - 9PAG11,10PAG41 it will be 5-6 digits 
#    - Format: "ROLL_NUMBER: [number], PAGE: [number]"

# 2. **QUESTION STRUCTURE:**
#    - Main questions: "1)", "2)", "Q1", "Question 1", etc.
#    - Sub-questions: "(i)", "(ii)", "(iii)", "(a)", "(b)", "(c)", etc.
#    - Nested sub-questions: "1(a)(i)", "2(b)(ii)", etc.

# 3. **MATHEMATICAL CONTENT:**
#    - Use LaTeX notation for ALL mathematical expressions
#    - Inline math: $expression$
#    - Display math: $$expression$$
#    - Preserve ALL steps, calculations, and working

# 4. **TEXT CONTENT:**
#    - Preserve ALL written explanations
#    - Include margin notes, corrections, and annotations

# 5. **VISUAL ELEMENTS:**
#    - Describe diagrams: [DIAGRAM: description]
#    - Describe graphs: [GRAPH: axes labels, curves, points]
#    - Describe tables: [TABLE: structure and content]
#    - Describe geometric figures: [FIGURE: shape, labels, measurements]

# 6. **FORMATTING:**
#    - Maintain original structure and indentation
#    - Preserve bullet points, numbering, and lists
#    - Keep line breaks where significant

# 7. **CROSSING OUT RULES:**
#    - If student crosses out something, don't retrieve that
#    - If student crossed out using big X for text or diagram entirely, don't mention that
#    - Leave text/figure/diagram if crossed out with X
#    - If student scratched equation for simplifying, mention in [Simplification]

# **OUTPUT FORMAT:**
# ROLL_NUMBER: [exact roll number found]
# PAGE: [page number if visible]
# [Question Number])
# [Original question text if visible]
# [Student's Solution:]
# [All work, steps, calculations in exact order]
# [Final answer if marked]
# [Continue for all questions on page...]

# **IMPORTANT: If no roll number is visible, output "ROLL_NUMBER: UNKNOWN"**
# **START EXTRACTION NOW:**"""

# def get_evaluation_prompt_with_images(student_answers: str, question_paper_images: List[str]) -> List:
#     """Create evaluation prompt with question paper images"""
#     content = [
#         {
#             "type": "text",
#             "text": f"""
# You are an expert examiner with years of experience in student evaluation. Evaluate the student's answers comprehensively.

# **QUESTION PAPER:**
# The question paper is provided as images below. Carefully review all questions and their marks.

# **STUDENT'S ANSWERS:**
# {student_answers}

# **EVALUATION GUIDELINES:**
# 1. **SCORING METHODOLOGY:**
#    - Conceptual Understanding: 50% weight
#    - Problem-solving Procedure: 20% weight
#    - Final Answer Accuracy: 10% weight
#    - Mathematical Methods/Formulas: 20% weight

# 2. **ERROR CLASSIFICATION:**
#    - conceptual_error: Wrong concept or theory applied
#    - calculation_error: Arithmetic or computational mistakes
#    - logical_error: Flawed reasoning or incorrect sequence
#    - no_error: Completely correct answer
#    - unattempted: Question not attempted

# 3. **DETAILED ANALYSIS REQUIRED:**
#    - Identify which concepts the student knows vs doesn't know
#    - Provide specific feedback on their solution approach
#    - Give specific recommendations for improvement
#    - Award partial marks fairly for correct steps
#    - Analyze overall performance patterns
#    - If mistakes_made is none, write "None" not empty string

# 4. **MISTAKE SECTION:**
#    - Specific line of content like - y = 2(2)² - 8(2) + 5 = -2.5 in latex format

# 5. **EVALUATION SCOPE:**
#    - ONLY evaluate questions that appear in the question paper images
#    - Match student question numbers to question paper question numbers
#    - If student attempts questions not in the paper, ignore them
#    - Provide comprehensive feedback for each attempted question

# 6. **IMPORTANT INSTRUCTIONS:**
#    - If student did not answer a question, still provide analysis with score as 0
#    - For unattempted questions, set mistakes_made as "Question not attempted"
#    - Always calculate percentage as (total_score/max_marks) * 100

# **MARKS DISTRIBUTION FOR SUB-QUESTIONS:**
#    - When a question has multiple sub-parts, DIVIDE the total marks EQUALLY among sub-parts
#    - Example: Q2 (6 marks) with 3 sub-parts = 2 marks each for (a), (b), (c)
#    - Final result should be for main question numbers
#    - If some sub-questions are not answered or wrong, reduce the score accordingly

# **QUESTION PAPER IMAGES:**
# """
#         }
#     ]
    
#     # Add question paper images
#     for img_base64 in question_paper_images:
#         content.append({
#             "type": "image_url",
#             "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
#         })
    
#     return content

# def calculate_grade(percentage: float) -> str:
#     """Calculate letter grade from percentage"""
#     if percentage >= 95: return "A+"
#     elif percentage >= 85: return "A"
#     elif percentage >= 75: return "B+"
#     elif percentage >= 65: return "B"
#     elif percentage >= 55: return "C+"
#     elif percentage >= 45: return "C"
#     elif percentage >= 35: return "D"
#     else: return "F"

# def calculate_class_analytics(evaluation_results: Dict) -> Dict:
#     """Calculate comprehensive class analytics"""
#     if not evaluation_results:
#         return {
#             "assignment_type": "classwork",
#             "class_analytics": {
#                 "average_score": 0,
#                 "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
#                 "highest_score": 0,
#                 "lowest_score": 0,
#                 "question_analytics": {}
#             },
#             "class_average_percentage": 0,
#             "performance_distribution": {
#                 "Below 50": 0, "50-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0
#             },
#             "processing_summary": {
#                 "files_processed": 0,
#                 "students_evaluated": 0,
#                 "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
#                 "total_pages": 0
#             },
#             "student_results": []
#         }

#     # Extract data for analytics
#     student_scores = []
#     all_grades = []
#     question_analytics = {}

#     for roll_number, result in evaluation_results.items():
#         percentage = result.get("overall_percentage", 0)
#         grade = result.get("grade", "F")
#         student_scores.append(percentage)
#         all_grades.append(grade)

#         # Collect question-level analytics
#         for question in result.get("questions", []):
#             q_num = question.get("question_number", "")
#             if q_num not in question_analytics:
#                 question_analytics[q_num] = {
#                     "attempts": 0,
#                     "average_percentage": 0,
#                     "max_score": question.get("max_marks", 0),
#                     "total_score": 0,
#                     "scores": []
#                 }

#             question_analytics[q_num]["attempts"] += 1
#             question_analytics[q_num]["scores"].append(question.get("total_score", 0))

#     # Calculate question averages
#     for q_num, data in question_analytics.items():
#         if data["scores"]:
#             data["total_score"] = sum(data["scores"])
#             data["average_percentage"] = (data["total_score"] / (data["max_score"] * data["attempts"]) * 100) if data["max_score"] > 0 else 0
#         del data["scores"]

#     # Calculate distributions
#     grade_distribution = {
#         "A": all_grades.count("A+") + all_grades.count("A"),
#         "B": all_grades.count("B+") + all_grades.count("B"),
#         "C": all_grades.count("C+") + all_grades.count("C"),
#         "D": all_grades.count("D"),
#         "F": all_grades.count("F")
#     }

#     performance_distribution = {
#         "Below 50": len([s for s in student_scores if s < 50]),
#         "50-59": len([s for s in student_scores if 50 <= s < 60]),
#         "60-69": len([s for s in student_scores if 60 <= s < 70]),
#         "70-79": len([s for s in student_scores if 70 <= s < 80]),
#         "80-89": len([s for s in student_scores if 80 <= s < 90]),
#         "90-100": len([s for s in student_scores if 90 <= s <= 100])
#     }

#     # Calculate statistics
#     average_score = sum(student_scores) / len(student_scores) if student_scores else 0
#     highest_score = max(student_scores) if student_scores else 0
#     lowest_score = min(student_scores) if student_scores else 0

#     return {
#         "assignment_type": "classwork",
#         "class_analytics": {
#             "average_score": round(average_score, 2),
#             "grade_distribution": grade_distribution,
#             "highest_score": round(highest_score, 2),
#             "lowest_score": round(lowest_score, 2),
#             "question_analytics": question_analytics
#         },
#         "class_average_percentage": round(average_score, 2),
#         "performance_distribution": performance_distribution,
#         "processing_summary": {
#             "files_processed": 1,
#             "students_evaluated": len(evaluation_results),
#             "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
#             "total_pages": 0
#         },
#         "student_results": list(evaluation_results.values())
#     }

# def pdf_to_images_base64(pdf_bytes: bytes) -> Tuple[List[tuple], Optional[str]]:
#     """Convert PDF bytes to base64 encoded images using PyMuPDF"""
#     try:
#         doc = fitz.open(stream=pdf_bytes, filetype="pdf")
#         pages_base64 = []

#         for i, page in enumerate(doc):
#             pix = page.get_pixmap(dpi=200)
#             img_bytes = pix.tobytes("jpeg", jpg_quality=95)
#             img_base64 = base64.b64encode(img_bytes).decode('utf-8')
#             pages_base64.append((i + 1, img_base64))

#         doc.close()
#         return pages_base64, None

#     except Exception as e:
#         return [], str(e)

# def extract_content_from_page_thread(page_data: tuple) -> Dict:
#     """Extract content from a single page using LangChain LLM with semaphore"""
#     page_num, base64_img = page_data

#     with api_semaphore:  # Use semaphore to limit concurrent API calls
#         try:
#             structured_llm = llm.with_structured_output(ExtractedContent)

#             message = HumanMessage(
#                 content=[
#                     {"type": "text", "text": get_extraction_prompt()},
#                     {
#                         "type": "image_url",
#                         "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
#                     }
#                 ]
#             )

#             result = structured_llm.invoke([message])

#             return {
#                 'page_number': page_num,
#                 'content': result.content,
#                 'roll_number': result.roll_number,
#                 'questions_found': result.questions_found,
#                 'success': True
#             }

#         except Exception as e:
#             return {
#                 'page_number': page_num,
#                 'content': f"Error extracting content from page {page_num}: {str(e)}",
#                 'roll_number': "ERROR",
#                 'questions_found': [],
#                 'success': False
#             }

# def extract_content_parallel(pages_data: List[tuple], max_workers: int = 5) -> List[Dict]:
#     """Extract content from multiple pages in parallel with improved threading"""
#     results = []

#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         future_to_page = {executor.submit(extract_content_from_page_thread, page_data): page_data[0]
#                           for page_data in pages_data}

#         for future in as_completed(future_to_page):
#             page_num = future_to_page[future]
#             try:
#                 result = future.result(timeout=60)  # Add timeout
#                 results.append(result)
#                 print(f"Processed page {page_num}")
#             except Exception as e:
#                 results.append({
#                     'page_number': page_num,
#                     'content': f"Failed to process page {page_num}: {str(e)}",
#                     'roll_number': "ERROR",
#                     'questions_found': [],
#                     'success': False
#                 })

#     results.sort(key=lambda x: x['page_number'])
#     return results

# def group_pages_by_roll_number(extraction_results: List[Dict]) -> Dict[str, Dict]:
#     """Group extracted pages by roll number, filtering out UNKNOWN"""
#     student_data = {}
#     unknown_pages = []

#     for result in extraction_results:
#         if not result['success']:
#             continue

#         roll_number = result['roll_number']
        
#         # Filter out UNKNOWN or ERROR roll numbers
#         if roll_number in ["ERROR", "UNKNOWN"] or roll_number.startswith("UNKNOWN"):
#             unknown_pages.append(result['page_number'])
#             continue

#         if roll_number not in student_data:
#             student_data[roll_number] = {
#                 'roll_number': roll_number,
#                 'pages': [],
#                 'combined_content': "",
#                 'pdf_pages': [],
#                 'questions_found': set()
#             }

#         student_data[roll_number]['pages'].append({
#             'page_number': result['page_number'],
#             'content': result['content']
#         })
#         student_data[roll_number]['pdf_pages'].append(result['page_number'])
#         student_data[roll_number]['questions_found'].update(result.get('questions_found', []))

#     # Create combined content for each student
#     for roll_number, data in student_data.items():
#         combined_content = ""
#         for page in sorted(data['pages'], key=lambda x: x['page_number']):
#             combined_content += f"<page {page['page_number']}>\n{page['content']}\n</page {page['page_number']}>\n\n"

#         data['combined_content'] = combined_content
#         data['content_for_llm'] = combined_content
#         data['questions_found'] = list(data['questions_found'])

#     # Log filtered pages
#     if unknown_pages:
#         print(f"Filtered out {len(unknown_pages)} pages with unknown roll numbers: {unknown_pages}")

#     return student_data

# def evaluate_single_student_with_images(student_answers: str, question_paper_images: List[str], roll_number: str) -> Dict:
#     """Evaluate a single student using structured LLM output with question paper images"""
#     with api_semaphore:  # Use semaphore for evaluation API calls
#         try:
#             structured_llm = llm.with_structured_output(EvaluationResult)
            
#             # Create content with images
#             content = get_evaluation_prompt_with_images(student_answers, question_paper_images)
            
#             message = HumanMessage(content=content)
#             result = structured_llm.invoke([message])

#             # Ensure roll number matches
#             if result.roll_number in ["Unknown", "Error", "UNKNOWN"]:
#                 result.roll_number = roll_number

#             # Calculate grade if not set
#             if not result.grade:
#                 result.grade = calculate_grade(result.overall_percentage)

#             # Ensure percentages are calculated for questions
#             for question in result.questions:
#                 if question.max_marks > 0:
#                     question.percentage = (question.total_score / question.max_marks) * 100
#                 else:
#                     question.percentage = 0.0

#             return result.dict()

#         except Exception as e:
#             return {
#                 "roll_number": roll_number,
#                 "questions": [],
#                 "total_marks_obtained": 0.0,
#                 "total_max_marks": 0.0,
#                 "overall_percentage": 0.0,
#                 "strengths": [],
#                 "areas_for_improvement": [f"Evaluation failed: {str(e)}"],
#                 "grade": "F",
#                 "detailed_analysis": f"Error in evaluation: {str(e)}"
#             }

# def evaluate_students_parallel(students_data: Dict, question_paper_images: List[str], max_workers: int = 5) -> Dict:
#     """Evaluate all students in parallel"""
#     evaluation_results = {}
    
#     def evaluate_student(item):
#         roll_number, student_data = item
#         return roll_number, evaluate_single_student_with_images(
#             student_data['content_for_llm'],
#             question_paper_images,
#             roll_number
#         )
    
#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         futures = {executor.submit(evaluate_student, item): item[0] 
#                   for item in students_data.items()}
        
#         for future in as_completed(futures):
#             roll_number = futures[future]
#             try:
#                 roll_number, result = future.result(timeout=120)
#                 evaluation_results[roll_number] = result
#                 print(f"Evaluated student: {roll_number}")
#             except Exception as e:
#                 print(f"Error evaluating student {roll_number}: {str(e)}")
#                 evaluation_results[roll_number] = {
#                     "roll_number": roll_number,
#                     "questions": [],
#                     "total_marks_obtained": 0.0,
#                     "total_max_marks": 0.0,
#                     "overall_percentage": 0.0,
#                     "strengths": [],
#                     "areas_for_improvement": [f"Evaluation failed: {str(e)}"],
#                     "grade": "F",
#                     "detailed_analysis": f"Error in evaluation: {str(e)}"
#                 }
    
#     return evaluation_results

# # ============= FastAPI Endpoints =============

# @app.get("/")
# async def root():
#     return {"message": "Welcome to Exam Hub API!", "version": "2.0.0"}

# @app.post("/evaluate/")
# async def evaluate_student_answers(
#     exam_name: str = Form(...),
#     exam_type: str = Form(...),
#     teacher_name: str = Form(...),
#     teacher_email: str = Form(...),
#     class_name: str = Form(...),
#     section: str = Form(...),
#     question_paper: UploadFile = File(...),
#     answer_sheets: UploadFile = File(...),
#     max_workers: Optional[int] = 5,
#     db: Session = Depends(get_db)
# ):
#     """Process and evaluate student answer sheets with question paper and save to database"""
    
#     try:
#         # Get API key
#         api_key = os.getenv('GEMINI_API_KEY')
#         if not api_key:
#             raise HTTPException(
#                 status_code=400,
#                 detail="GEMINI_API_KEY environment variable not set"
#             )

#         # Initialize LLM
#         success, message = initialize_llm(api_key)
#         if not success:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Failed to initialize Gemini API: {message}"
#             )

#         # Get or create teacher and class section
#         teacher = DatabaseOperations.get_or_create_teacher(db, teacher_name, teacher_email)
#         class_section = DatabaseOperations.get_or_create_class_section(db, class_name, section)

#         # Process question paper - convert all pages to images
#         question_paper_content = await question_paper.read()
#         question_paper_pages, error = pdf_to_images_base64(question_paper_content)
#         if not question_paper_pages:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Failed to process question paper: {error}"
#             )
        
#         # Extract just the base64 images from question paper
#         question_paper_images = [img_base64 for _, img_base64 in question_paper_pages]
#         print(f"Question paper has {len(question_paper_images)} pages")

#         # Process answer sheets
#         answer_sheets_content = await answer_sheets.read()
#         pages_data, error = pdf_to_images_base64(answer_sheets_content)
#         if not pages_data:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Failed to process answer sheets: {error}"
#             )

#         all_pages_data = [(page_num, img_base64) for page_num, img_base64 in pages_data]
#         print(f"Total pages to process: {len(all_pages_data)}")

#         # Extract content from all pages with improved threading
#         extraction_results = extract_content_parallel(all_pages_data, max_workers)

#         # Group pages by roll number (filtering out UNKNOWN)
#         students_data = group_pages_by_roll_number(extraction_results)

#         if not students_data:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No valid student data could be extracted (all pages had unknown roll numbers)"
#             )

#         print(f"Found {len(students_data)} valid students for evaluation")

#         # Evaluate all students in parallel
#         evaluation_results = evaluate_students_parallel(students_data, question_paper_images, max_workers)

#         # Calculate class analytics
#         class_analytics = calculate_class_analytics(evaluation_results)
#         class_analytics["processing_summary"]["files_processed"] = 2  # question paper + answer sheets
#         class_analytics["processing_summary"]["total_pages"] = len(all_pages_data)

#         # Save to database
#         exam = DatabaseOperations.save_exam_results(
#             db=db,
#             exam_name=exam_name,
#             exam_type=exam_type,
#             teacher_id=teacher.id,
#             class_section_id=class_section.id,
#             evaluation_results=evaluation_results,
#             class_analytics=class_analytics
#         )

#         return {
#             "success": True,
#             "exam_id": exam.id,
#             "files_processed": 2,
#             "total_pages": len(all_pages_data),
#             "students_count": len(students_data),
#             "question_paper_pages": len(question_paper_images),
#             "evaluation_results": evaluation_results,
#             "class_analytics": class_analytics,
#             "message": f"Exam '{exam_name}' processed successfully and saved to database"
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to process request: {str(e)}"
#         )

# @app.get("/exams/")
# async def get_exams(
#     teacher_name: str,
#     teacher_email: str,
#     class_name: str,
#     section: str,
#     exam_type: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     """Get all exams for a teacher and class"""
#     try:
#         # Get teacher and class section
#         teacher = db.query(Teacher).filter(Teacher.email == teacher_email).first()
#         if not teacher:
#             return {"exams": []}
        
#         class_section = db.query(ClassSection).filter(
#             ClassSection.class_name == class_name,
#             ClassSection.section == section
#         ).first()
#         if not class_section:
#             return {"exams": []}

#         # Get exams
#         exams = DatabaseOperations.get_exams_by_teacher_and_class(
#             db, teacher.id, class_section.id, exam_type
#         )

#         exam_list = []
#         for exam in exams:
#             exam_list.append({
#                 "id": exam.id,
#                 "name": exam.name,
#                 "exam_type": exam.exam_type,
#                 "total_students": exam.total_students,
#                 "average_score": exam.average_score,
#                 "created_at": exam.created_at.isoformat(),
#                 "processed_at": exam.processed_at.isoformat() if exam.processed_at else None
#             })

#         return {"exams": exam_list}

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to get exams: {str(e)}"
#         )

# @app.get("/exams/{exam_id}/results")
# async def get_exam_results(exam_id: int, db: Session = Depends(get_db)):
#     """Get detailed results for a specific exam"""
#     try:
#         exam = DatabaseOperations.get_exam_with_results(db, exam_id)
#         if not exam:
#             raise HTTPException(status_code=404, detail="Exam not found")

#         student_results = DatabaseOperations.get_student_results_by_exam(db, exam_id)

#         # Format results
#         results = {}
#         for student in student_results:
#             results[student.roll_number] = {
#                 "roll_number": student.roll_number,
#                 "total_marks_obtained": student.total_marks_obtained,
#                 "total_max_marks": student.total_max_marks,
#                 "overall_percentage": student.overall_percentage,
#                 "grade": student.grade,
#                 "questions": student.questions_evaluation,
#                 "strengths": student.strengths,
#                 "areas_for_improvement": student.areas_for_improvement,
#                 "detailed_analysis": student.detailed_analysis
#             }

#         return {
#             "exam": {
#                 "id": exam.id,
#                 "name": exam.name,
#                 "exam_type": exam.exam_type,
#                 "total_students": exam.total_students,
#                 "average_score": exam.average_score,
#                 "created_at": exam.created_at.isoformat(),
#                 "processed_at": exam.processed_at.isoformat() if exam.processed_at else None
#             },
#             "evaluation_results": results,
#             "class_analytics": exam.class_analytics
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to get exam results: {str(e)}"
#         )

# @app.get("/analytics/")
# async def get_analytics(
#     teacher_name: str,
#     teacher_email: str,
#     class_name: str,
#     section: str,
#     db: Session = Depends(get_db)
# ):
#     """Get analytics data for dashboard"""
#     try:
#         # Get teacher and class section
#         teacher = db.query(Teacher).filter(Teacher.email == teacher_email).first()
#         if not teacher:
#             return DatabaseOperations.get_analytics_data(db, 0, 0)
        
#         class_section = db.query(ClassSection).filter(
#             ClassSection.class_name == class_name,
#             ClassSection.section == section
#         ).first()
#         if not class_section:
#             return DatabaseOperations.get_analytics_data(db, 0, 0)

#         return DatabaseOperations.get_analytics_data(db, teacher.id, class_section.id)

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to get analytics: {str(e)}"
#         )

# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# @app.post("/initialize")
# async def initialize_api():
#     """Initialize the API with Gemini key"""
#     api_key = os.getenv('GEMINI_API_KEY')
#     if not api_key:
#         raise HTTPException(
#             status_code=400,
#             detail="GEMINI_API_KEY environment variable not set"
#         )
    
#     success, message = initialize_llm(api_key)
#     if not success:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to initialize: {message}"
#         )
    
#     return {"success": True, "message": message}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import base64
import os
import json
import re
import time
import threading
from threading import Semaphore
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple, Union
from pydantic import BaseModel, Field
import PyPDF2
from io import BytesIO
import traceback
import io
from PIL import Image
import os
from dotenv import load_dotenv
from datetime import datetime

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
# Import PyMuPDF
import fitz

# Import database components
from database import (
    create_tables, get_db, DatabaseOperations,
    Teacher, ClassSection, Exam, StudentResult
)

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Exam Hub API",
    description="Complete exam management system with AI-powered evaluation",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
create_tables()

# Initialize LangChain model
llm = None
# Semaphore for rate limiting
api_semaphore = Semaphore(5)  # Allow max 5 concurrent API calls

# ============= Pydantic Models =============

class TeacherCreate(BaseModel):
    name: str
    email: str

class ClassSectionCreate(BaseModel):
    class_name: str
    section: str

class ExamCreate(BaseModel):
    name: str
    exam_type: str
    teacher_name: str
    teacher_email: str
    class_name: str
    section: str

class ExtractedContent(BaseModel):
    """Extracted content from student answer sheet"""
    roll_number: str = Field(description="Student's roll number")
    page_number: int = Field(description="Page number of the answer sheet")
    content: str = Field(description="Full content in LaTeX format")
    questions_found: List[str] = Field(description="List of question numbers found on this page")

class QuestionEvaluation(BaseModel):
    """Evaluation result for a single question"""
    question_number: str = Field(description="Question number (e.g., '1', '2a', '3(i)')")
    max_marks: float = Field(description="Maximum marks for this question")
    total_score: float = Field(description="Total score obtained for this question")
    error_type: str = Field(description="Type of error: conceptual_error, calculation_error, logical_error, no_error or unattempted")
    mistakes_made: str = Field(description="Specific mistakes made in the question or 'None' if no errors or unattempted")
    mistake_section: str = Field(description="Content of specific line of mistake made by student")
    concepts_required: List[str] = Field(description="List of correct concepts required to solve this question")
    gap_analysis: str = Field(description="Specific learning gaps")
    percentage: float = Field(description="Percentage score for this question")

class EvaluationResult(BaseModel):
    """Complete evaluation result for a student"""
    roll_number: str = Field(description="Student's roll number")
    questions: List[QuestionEvaluation] = Field(description="Evaluation for each question")
    total_marks_obtained: float = Field(description="Total marks obtained")
    total_max_marks: float = Field(description="Total maximum marks from question paper")
    overall_percentage: float = Field(description="Overall percentage score")
    strengths: List[str] = Field(description="Student's key strengths identified")
    areas_for_improvement: List[str] = Field(description="Specific areas needing improvement")
    grade: str = Field(description="Letter grade (A+, A, B+, B, C+, C, D, F)")
    detailed_analysis: str = Field(description="Detailed analysis of student performance")

# ============= New Helper Functions for Multiple PDFs =============

def merge_multiple_pdfs(pdf_files_bytes: List[bytes]) -> bytes:
    """
    Merge multiple PDF files into a single PDF
    
    Args:
        pdf_files_bytes: List of PDF files as bytes in the order they should be merged
    
    Returns:
        bytes: Merged PDF as bytes
    """
    try:
        # Create a new PDF document using PyMuPDF
        merged_doc = fitz.open()  # Create new empty document
        
        for pdf_bytes in pdf_files_bytes:
            # Open each PDF from bytes
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            # Insert all pages from current PDF
            merged_doc.insert_pdf(pdf_doc)
            pdf_doc.close()
        
        # Save merged PDF to bytes
        merged_bytes = merged_doc.tobytes()
        merged_doc.close()
        
        return merged_bytes
        
    except Exception as e:
        print(f"Error merging PDFs: {str(e)}")
        raise Exception(f"Failed to merge PDFs: {str(e)}")

async def process_multiple_pdf_uploads(files: List[UploadFile]) -> bytes:
    """
    Process multiple uploaded PDF files and combine them into one
    
    Args:
        files: List of uploaded files
    
    Returns:
        bytes: Combined PDF as bytes
    """
    pdf_bytes_list = []
    
    for i, file in enumerate(files):
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is not a PDF. Only PDF files are allowed."
            )
        
        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is empty"
            )
        
        pdf_bytes_list.append(content)
        print(f"Processed file {i+1}/{len(files)}: {file.filename}")
    
    # If only one file, return it directly
    if len(pdf_bytes_list) == 1:
        return pdf_bytes_list[0]
    
    # Merge multiple PDFs
    print(f"Merging {len(pdf_bytes_list)} PDF files...")
    merged_pdf = merge_multiple_pdfs(pdf_bytes_list)
    print(f"Successfully merged PDFs into single document")
    
    return merged_pdf

# ============= Helper Functions (keeping existing ones) =============

def initialize_llm(api_key: str):
    """Initialize LangChain Google GenAI model"""
    global llm
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=api_key
        )
        return True, "Successfully initialized"
    except Exception as e:
        return False, str(e)

def get_extraction_prompt() -> str:
    return """
Extract ALL text from this student answer sheet image with extreme precision.

**CRITICAL: FIRST IDENTIFY THE ROLL NUMBER**
- Look for roll number, registration number, student ID anywhere on the page
- format: ID: 10HPS24,9PAG35 it is the combination of numeric and alphabets 
- Output format: "ROLL_NUMBER: [exact number found]"

**EXTRACTION RULES:**
1. **ROLL NUMBER & PAGE:**
   - MUST extract roll number from top right inside boxes on every page
   - Roll Number will ONLY be one of these:8ILB10,8ILB36,8ILB41 
   - Format: "ROLL_NUMBER: [number], PAGE: [number]"

2. **QUESTION STRUCTURE:**
   - Main questions: "1)", "2)", "Q1", "Question 1", etc.
   - Sub-questions: "(i)", "(ii)", "(iii)", "(a)", "(b)", "(c)", etc.
   - Nested sub-questions: "1(a)(i)", "2(b)(ii)", etc.

3. **MATHEMATICAL CONTENT:**
   - Use LaTeX notation for ALL mathematical expressions
   - Inline math: $expression$
   - Display math: $$expression$$
   - Preserve ALL steps, calculations, and working

4. **TEXT CONTENT:**
   - Preserve ALL written explanations
   - Include margin notes, corrections, and annotations

5. **VISUAL ELEMENTS:**
   - Describe diagrams: [DIAGRAM: description]
   - Describe graphs: [GRAPH: axes labels, curves, points]
   - Describe tables: [TABLE: structure and content]
   - Describe geometric figures: [FIGURE: shape, labels, measurements]

6. **FORMATTING:**
   - Maintain original structure and indentation
   - Preserve bullet points, numbering, and lists
   - Keep line breaks where significant

7. **CROSSING OUT RULES:**
   - If student crosses out something, don't retrieve that
   - If student crossed out using big X for text or diagram entirely, don't mention that
   - Leave text/figure/diagram if crossed out with X
   - If student scratched equation for simplifying, mention in [Simplification]

**OUTPUT FORMAT:**
ROLL_NUMBER: [exact roll number found]
PAGE: [page number if visible]
[Question Number])
[Original question text if visible]
[Student's Solution:]
[All work, steps, calculations in exact order]
[Final answer if marked]
[Continue for all questions on page...]

**IMPORTANT: If no roll number is visible, output "ROLL_NUMBER: UNKNOWN"**
**START EXTRACTION NOW:**"""

def get_evaluation_prompt_with_images(student_answers: str, question_paper_images: List[str]) -> List:
    """Create evaluation prompt with question paper images"""
    content = [
        {
            "type": "text",
            "text": f"""
You are an expert examiner with years of experience in student evaluation. Evaluate the student's answers comprehensively.

**QUESTION PAPER:**
The question paper is provided as images below. Carefully review all questions and their marks.

**STUDENT'S ANSWERS:**
{student_answers}

**EVALUATION GUIDELINES:**
1. **SCORING METHODOLOGY:**
   - Conceptual Understanding: 50% weight
   - Problem-solving Procedure: 20% weight
   - Final Answer Accuracy: 10% weight
   - Mathematical Methods/Formulas: 20% weight

2. **ERROR CLASSIFICATION:**
   - conceptual_error: Wrong concept or theory applied
   - calculation_error: Arithmetic or computational mistakes
   - logical_error: Flawed reasoning or incorrect sequence
   - no_error: Completely correct answer
   - unattempted: Question not attempted

3. **DETAILED ANALYSIS REQUIRED:**
   - Identify which concepts the student knows vs doesn't know
   - Provide specific feedback on their solution approach
   - Give specific recommendations for improvement
   - Award partial marks fairly for correct steps
   - Analyze overall performance patterns
   - If mistakes_made is none, write "None" not empty string

4. **MISTAKE SECTION:**
   - Specific line of content like - y = 2(2)² - 8(2) + 5 = -2.5 in latex format

5. **EVALUATION SCOPE:**
   - ONLY evaluate questions that appear in the question paper images
   - Match student question numbers to question paper question numbers
   - If student attempts questions not in the paper, ignore them
   - Provide comprehensive feedback for each attempted question

6. **IMPORTANT INSTRUCTIONS:**
   - If student did not answer a question, still provide analysis with score as 0
   - For unattempted questions, set mistakes_made as "Question not attempted"
   - Always calculate percentage as (total_score/max_marks) * 100

**MARKS DISTRIBUTION FOR SUB-QUESTIONS:**
   - When a question has multiple sub-parts, DIVIDE the total marks EQUALLY among sub-parts
   - Example: Q2 (6 marks) with 3 sub-parts = 2 marks each for (a), (b), (c)
   - Final result should be for main question numbers
   - If some sub-questions are not answered or wrong, reduce the score accordingly

   7.Also identify the max marks of the question paper and return it
**QUESTION PAPER IMAGES:**
"""
        }
    ]
    
    # Add question paper images
    for img_base64 in question_paper_images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
        })
    
    return content

def calculate_grade(percentage: float) -> str:
    """Calculate letter grade from percentage"""
    if percentage >= 95: return "A+"
    elif percentage >= 85: return "A"
    elif percentage >= 75: return "B+"
    elif percentage >= 65: return "B"
    elif percentage >= 55: return "C+"
    elif percentage >= 45: return "C"
    elif percentage >= 35: return "D"
    else: return "F"

def calculate_class_analytics(evaluation_results: Dict) -> Dict:
    """Calculate comprehensive class analytics"""
    if not evaluation_results:
        return {
            "assignment_type": "classwork",
            "class_analytics": {
                "average_score": 0,
                "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
                "highest_score": 0,
                "lowest_score": 0,
                "question_analytics": {}
            },
            "class_average_percentage": 0,
            "performance_distribution": {
                "Below 50": 0, "50-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0
            },
            "processing_summary": {
                "files_processed": 0,
                "students_evaluated": 0,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "total_pages": 0
            },
            "student_results": []
        }

    # Extract data for analytics
    student_scores = []
    all_grades = []
    question_analytics = {}

    for roll_number, result in evaluation_results.items():
        percentage = result.get("overall_percentage", 0)
        grade = result.get("grade", "F")
        student_scores.append(percentage)
        all_grades.append(grade)

        # Collect question-level analytics
        for question in result.get("questions", []):
            q_num = question.get("question_number", "")
            if q_num not in question_analytics:
                question_analytics[q_num] = {
                    "attempts": 0,
                    "average_percentage": 0,
                    "max_score": question.get("max_marks", 0),
                    "total_score": 0,
                    "scores": []
                }

            question_analytics[q_num]["attempts"] += 1
            question_analytics[q_num]["scores"].append(question.get("total_score", 0))

    # Calculate question averages
    for q_num, data in question_analytics.items():
        if data["scores"]:
            data["total_score"] = sum(data["scores"])
            data["average_percentage"] = (data["total_score"] / (data["max_score"] * data["attempts"]) * 100) if data["max_score"] > 0 else 0
        del data["scores"]

    # Calculate distributions
    grade_distribution = {
        "A": all_grades.count("A+") + all_grades.count("A"),
        "B": all_grades.count("B+") + all_grades.count("B"),
        "C": all_grades.count("C+") + all_grades.count("C"),
        "D": all_grades.count("D"),
        "F": all_grades.count("F")
    }

    performance_distribution = {
        "Below 50": len([s for s in student_scores if s < 50]),
        "50-59": len([s for s in student_scores if 50 <= s < 60]),
        "60-69": len([s for s in student_scores if 60 <= s < 70]),
        "70-79": len([s for s in student_scores if 70 <= s < 80]),
        "80-89": len([s for s in student_scores if 80 <= s < 90]),
        "90-100": len([s for s in student_scores if 90 <= s <= 100])
    }

    # Calculate statistics
    average_score = sum(student_scores) / len(student_scores) if student_scores else 0
    highest_score = max(student_scores) if student_scores else 0
    lowest_score = min(student_scores) if student_scores else 0

    return {
        "assignment_type": "classwork",
        "class_analytics": {
            "average_score": round(average_score, 2),
            "grade_distribution": grade_distribution,
            "highest_score": round(highest_score, 2),
            "lowest_score": round(lowest_score, 2),
            "question_analytics": question_analytics
        },
        "class_average_percentage": round(average_score, 2),
        "performance_distribution": performance_distribution,
        "processing_summary": {
            "files_processed": 1,
            "students_evaluated": len(evaluation_results),
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "total_pages": 0
        },
        "student_results": list(evaluation_results.values())
    }

def pdf_to_images_base64(pdf_bytes: bytes) -> Tuple[List[tuple], Optional[str]]:
    """Convert PDF bytes to base64 encoded images using PyMuPDF"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_base64 = []

        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("jpeg", jpg_quality=95)
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            pages_base64.append((i + 1, img_base64))

        doc.close()
        return pages_base64, None

    except Exception as e:
        return [], str(e)

def extract_content_from_page_thread(page_data: tuple) -> Dict:
    """Extract content from a single page using LangChain LLM with semaphore"""
    page_num, base64_img = page_data

    with api_semaphore:  # Use semaphore to limit concurrent API calls
        try:
            structured_llm = llm.with_structured_output(ExtractedContent)

            message = HumanMessage(
                content=[
                    {"type": "text", "text": get_extraction_prompt()},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                    }
                ]
            )

            result = structured_llm.invoke([message])

            return {
                'page_number': page_num,
                'content': result.content,
                'roll_number': result.roll_number,
                'questions_found': result.questions_found,
                'success': True
            }

        except Exception as e:
            return {
                'page_number': page_num,
                'content': f"Error extracting content from page {page_num}: {str(e)}",
                'roll_number': "ERROR",
                'questions_found': [],
                'success': False
            }

def extract_content_parallel(pages_data: List[tuple], max_workers: int = 5) -> List[Dict]:
    """Extract content from multiple pages in parallel with improved threading"""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_page = {executor.submit(extract_content_from_page_thread, page_data): page_data[0]
                          for page_data in pages_data}

        for future in as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                result = future.result(timeout=60)  # Add timeout
                results.append(result)
                print(f"Processed page {page_num}")
            except Exception as e:
                results.append({
                    'page_number': page_num,
                    'content': f"Failed to process page {page_num}: {str(e)}",
                    'roll_number': "ERROR",
                    'questions_found': [],
                    'success': False
                })

    results.sort(key=lambda x: x['page_number'])
    return results

def group_pages_by_roll_number(extraction_results: List[Dict]) -> Dict[str, Dict]:
    """Group extracted pages by roll number, filtering out UNKNOWN"""
    student_data = {}
    unknown_pages = []

    for result in extraction_results:
        if not result['success']:
            continue

        roll_number = result['roll_number']
        
        # Filter out UNKNOWN or ERROR roll numbers
        if roll_number in ["ERROR", "UNKNOWN"] or roll_number.startswith("UNKNOWN"):
            unknown_pages.append(result['page_number'])
            continue

        if roll_number not in student_data:
            student_data[roll_number] = {
                'roll_number': roll_number,
                'pages': [],
                'combined_content': "",
                'pdf_pages': [],
                'questions_found': set()
            }

        student_data[roll_number]['pages'].append({
            'page_number': result['page_number'],
            'content': result['content']
        })
        student_data[roll_number]['pdf_pages'].append(result['page_number'])
        student_data[roll_number]['questions_found'].update(result.get('questions_found', []))

    # Create combined content for each student
    for roll_number, data in student_data.items():
        combined_content = ""
        for page in sorted(data['pages'], key=lambda x: x['page_number']):
            combined_content += f"<page {page['page_number']}>\n{page['content']}\n</page {page['page_number']}>\n\n"

        data['combined_content'] = combined_content
        data['content_for_llm'] = combined_content
        data['questions_found'] = list(data['questions_found'])

    # Log filtered pages
    if unknown_pages:
        print(f"Filtered out {len(unknown_pages)} pages with unknown roll numbers: {unknown_pages}")

    return student_data

def evaluate_single_student_with_images(student_answers: str, question_paper_images: List[str], roll_number: str) -> Dict:
    """Evaluate a single student using structured LLM output with question paper images"""
    with api_semaphore:  # Use semaphore for evaluation API calls
        try:
            structured_llm = llm.with_structured_output(EvaluationResult)
            
            # Create content with images
            content = get_evaluation_prompt_with_images(student_answers, question_paper_images)
            
            message = HumanMessage(content=content)
            result = structured_llm.invoke([message])

            # Ensure roll number matches
            if result.roll_number in ["Unknown", "Error", "UNKNOWN"]:
                result.roll_number = roll_number

            # Calculate grade if not set
            if not result.grade:
                result.grade = calculate_grade(result.overall_percentage)

            # Ensure percentages are calculated for questions
            for question in result.questions:
                if question.max_marks > 0:
                    question.percentage = (question.total_score / question.max_marks) * 100
                else:
                    question.percentage = 0.0

            return result.dict()

        except Exception as e:
            return {
                "roll_number": roll_number,
                "questions": [],
                "total_marks_obtained": 0.0,
                "total_max_marks": 0.0,
                "overall_percentage": 0.0,
                "strengths": [],
                "areas_for_improvement": [f"Evaluation failed: {str(e)}"],
                "grade": "F",
                "detailed_analysis": f"Error in evaluation: {str(e)}"
            }

def evaluate_students_parallel(students_data: Dict, question_paper_images: List[str], max_workers: int = 5) -> Dict:
    """Evaluate all students in parallel"""
    evaluation_results = {}
    
    def evaluate_student(item):
        roll_number, student_data = item
        return roll_number, evaluate_single_student_with_images(
            student_data['content_for_llm'],
            question_paper_images,
            roll_number
        )
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(evaluate_student, item): item[0] 
                  for item in students_data.items()}
        
        for future in as_completed(futures):
            roll_number = futures[future]
            try:
                roll_number, result = future.result(timeout=120)
                evaluation_results[roll_number] = result
                print(f"Evaluated student: {roll_number}")
            except Exception as e:
                print(f"Error evaluating student {roll_number}: {str(e)}")
                evaluation_results[roll_number] = {
                    "roll_number": roll_number,
                    "questions": [],
                    "total_marks_obtained": 0.0,
                    "total_max_marks": 0.0,
                    "overall_percentage": 0.0,
                    "strengths": [],
                    "areas_for_improvement": [f"Evaluation failed: {str(e)}"],
                    "grade": "F",
                    "detailed_analysis": f"Error in evaluation: {str(e)}"
                }
    
    return evaluation_results

# ============= Modified FastAPI Endpoints =============

@app.get("/")
async def root():
    return {"message": "Welcome to Exam Hub API!", "version": "2.1.0", "feature": "Multiple PDF support"}

@app.post("/evaluate/")
async def evaluate_student_answers(
    exam_name: str = Form(...),
    exam_type: str = Form(...),
    teacher_name: str = Form(...),
    teacher_email: str = Form(...),
    class_name: str = Form(...),
    section: str = Form(...),
    question_paper: List[UploadFile] = File(..., description="One or more question paper PDFs"),
    answer_sheets: List[UploadFile] = File(..., description="One or more answer sheet PDFs"),
    max_workers: Optional[int] = Form(5),
    db: Session = Depends(get_db)
):
    """
    Process and evaluate student answer sheets with question paper and save to database
    
    Now supports:
    - Multiple question paper PDFs (will be merged in order)
    - Multiple answer sheet PDFs (will be merged in order)
    """
    
    try:
        # Get API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="GEMINI_API_KEY environment variable not set"
            )

        # Initialize LLM
        success, message = initialize_llm(api_key)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to initialize Gemini API: {message}"
            )

        # Get or create teacher and class section
        teacher = DatabaseOperations.get_or_create_teacher(db, teacher_name, teacher_email)
        class_section = DatabaseOperations.get_or_create_class_section(db, class_name, section)

        # Process multiple question paper PDFs
        print(f"Processing {len(question_paper)} question paper file(s)...")
        question_paper_content = await process_multiple_pdf_uploads(question_paper)
        
        # Convert merged question paper to images
        question_paper_pages, error = pdf_to_images_base64(question_paper_content)
        if not question_paper_pages:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process question paper: {error}"
            )
        
        # Extract just the base64 images from question paper
        question_paper_images = [img_base64 for _, img_base64 in question_paper_pages]
        print(f"Question paper has {len(question_paper_images)} total pages")

        # Process multiple answer sheet PDFs
        print(f"Processing {len(answer_sheets)} answer sheet file(s)...")
        answer_sheets_content = await process_multiple_pdf_uploads(answer_sheets)
        
        # Convert merged answer sheets to images
        pages_data, error = pdf_to_images_base64(answer_sheets_content)
        if not pages_data:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process answer sheets: {error}"
            )

        all_pages_data = [(page_num, img_base64) for page_num, img_base64 in pages_data]
        print(f"Total answer sheet pages to process: {len(all_pages_data)}")

        # Extract content from all pages with improved threading
        extraction_results = extract_content_parallel(all_pages_data, max_workers)

        # Group pages by roll number (filtering out UNKNOWN)
        students_data = group_pages_by_roll_number(extraction_results)

        if not students_data:
            raise HTTPException(
                status_code=400,
                detail="No valid student data could be extracted (all pages had unknown roll numbers)"
            )

        print(f"Found {len(students_data)} valid students for evaluation")

        # Evaluate all students in parallel
        evaluation_results = evaluate_students_parallel(students_data, question_paper_images, max_workers)

        # Calculate class analytics
        class_analytics = calculate_class_analytics(evaluation_results)
        class_analytics["processing_summary"]["files_processed"] = len(question_paper) + len(answer_sheets)
        class_analytics["processing_summary"]["total_pages"] = len(all_pages_data)
        class_analytics["processing_summary"]["question_paper_files"] = len(question_paper)
        class_analytics["processing_summary"]["answer_sheet_files"] = len(answer_sheets)

        # Save to database
        exam = DatabaseOperations.save_exam_results(
            db=db,
            exam_name=exam_name,
            exam_type=exam_type,
            teacher_id=teacher.id,
            class_section_id=class_section.id,
            evaluation_results=evaluation_results,
            class_analytics=class_analytics
        )

        return {
            "success": True,
            "exam_id": exam.id,
            "files_processed": {
                "question_papers": len(question_paper),
                "answer_sheets": len(answer_sheets),
                "total": len(question_paper) + len(answer_sheets)
            },
            "pages_processed": {
                "question_paper_pages": len(question_paper_images),
                "answer_sheet_pages": len(all_pages_data),
                "total": len(question_paper_images) + len(all_pages_data)
            },
            "students_count": len(students_data),
            "evaluation_results": evaluation_results,
            "class_analytics": class_analytics,
            "message": f"Exam '{exam_name}' processed successfully and saved to database"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request: {str(e)}"
        )

@app.get("/exams/")
async def get_exams(
    teacher_name: str,
    teacher_email: str,
    class_name: str,
    section: str,
    exam_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all exams for a teacher and class"""
    try:
        # Get teacher and class section
        teacher = db.query(Teacher).filter(Teacher.email == teacher_email).first()
        if not teacher:
            return {"exams": []}
        
        class_section = db.query(ClassSection).filter(
            ClassSection.class_name == class_name,
            ClassSection.section == section
        ).first()
        if not class_section:
            return {"exams": []}

        # Get exams
        exams = DatabaseOperations.get_exams_by_teacher_and_class(
            db, teacher.id, class_section.id, exam_type
        )

        exam_list = []
        for exam in exams:
            exam_list.append({
                "id": exam.id,
                "name": exam.name,
                "exam_type": exam.exam_type,
                "total_students": exam.total_students,
                "average_score": exam.average_score,
                "created_at": exam.created_at.isoformat(),
                "processed_at": exam.processed_at.isoformat() if exam.processed_at else None
            })

        return {"exams": exam_list}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get exams: {str(e)}"
        )

@app.get("/exams/{exam_id}/results")
async def get_exam_results(exam_id: int, db: Session = Depends(get_db)):
    """Get detailed results for a specific exam"""
    try:
        exam = DatabaseOperations.get_exam_with_results(db, exam_id)
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        student_results = DatabaseOperations.get_student_results_by_exam(db, exam_id)

        # Format results
        results = {}
        for student in student_results:
            results[student.roll_number] = {
                "roll_number": student.roll_number,
                "total_marks_obtained": student.total_marks_obtained,
                "total_max_marks": student.total_max_marks,
                "overall_percentage": student.overall_percentage,
                "grade": student.grade,
                "questions": student.questions_evaluation,
                "strengths": student.strengths,
                "areas_for_improvement": student.areas_for_improvement,
                "detailed_analysis": student.detailed_analysis
            }

        return {
            "exam": {
                "id": exam.id,
                "name": exam.name,
                "exam_type": exam.exam_type,
                "total_students": exam.total_students,
                "average_score": exam.average_score,
                "created_at": exam.created_at.isoformat(),
                "processed_at": exam.processed_at.isoformat() if exam.processed_at else None
            },
            "evaluation_results": results,
            "class_analytics": exam.class_analytics
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get exam results: {str(e)}"
        )

@app.get("/analytics/")
async def get_analytics(
    teacher_name: str,
    teacher_email: str,
    class_name: str,
    section: str,
    db: Session = Depends(get_db)
):
    """Get analytics data for dashboard"""
    try:
        # Get teacher and class section
        teacher = db.query(Teacher).filter(Teacher.email == teacher_email).first()
        if not teacher:
            return DatabaseOperations.get_analytics_data(db, 0, 0)
        
        class_section = db.query(ClassSection).filter(
            ClassSection.class_name == class_name,
            ClassSection.section == section
        ).first()
        if not class_section:
            return DatabaseOperations.get_analytics_data(db, 0, 0)

        return DatabaseOperations.get_analytics_data(db, teacher.id, class_section.id)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.1.0",
        "features": ["multiple_pdf_support"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/initialize")
async def initialize_api():
    """Initialize the API with Gemini key"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY environment variable not set"
        )
    
    success, message = initialize_llm(api_key)
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize: {message}"
        )
    
    return {"success": True, "message": message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)